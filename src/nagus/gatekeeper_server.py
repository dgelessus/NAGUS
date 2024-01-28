# This file is part of NAGUS, an Uru Live server that is not very good.
# Copyright (C) 2024 dgelessus
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


"""Implements the :ref:`gatekeeper server <gatekeeper_server>`."""


import logging
import struct
import uuid

from . import base
from . import structs


logger = logging.getLogger(__name__)
logger_ping = logger.getChild("ping")


CONNECT_DATA = struct.Struct("<I16s")

PING_HEADER = struct.Struct("<III")
FILE_SERVER_IP_ADDRESS_REQUEST = struct.Struct("<I?")


class GatekeeperConnection(base.BaseMOULConnection):
	CONNECTION_TYPE = base.ConnectionType.cli2gatekeeper
	
	async def read_connect_packet_data(self) -> None:
		data_length, token = await self.read_unpack(CONNECT_DATA)
		if data_length != CONNECT_DATA.size:
			raise base.ProtocolError(f"Client sent client-to-gatekeeper connect data with unexpected length {data_length} (should be {CONNECT_DATA.size})")
		
		token = uuid.UUID(bytes_le=token)
		if token != structs.ZERO_UUID:
			logger.warning("Client connected to gatekeeper server with non-zero token: %s", token)
	
	@base.message_handler(0)
	async def ping_request(self) -> None:
		header_data = await self.read(PING_HEADER.size)
		ping_time, trans_id, payload_length = PING_HEADER.unpack(header_data)
		logger_ping.debug("Ping request: time %d", ping_time)
		if trans_id != 0:
			logger_ping.info("Ping request with non-zero transaction ID: %d", trans_id)
		if payload_length != 0:
			logger_ping.info("Ping request with non-empty payload: %d bytes", payload_length)
		payload = await self.read(payload_length)
		# Send everything back unmodified
		await self.write_message(0, header_data + payload)
	
	async def file_server_ip_address_reply(self, trans_id: int, address: str) -> None:
		logger.debug("Sending file server IP address reply: transaction ID %d, address %r", trans_id, address)
		await self.write_message(1, structs.UINT32.pack(trans_id) + base.pack_string_field(address, 24))
	
	@base.message_handler(1)
	async def file_server_ip_address_request(self) -> None:
		trans_id, is_patcher = await self.read_unpack(FILE_SERVER_IP_ADDRESS_REQUEST)
		logger.debug("File server IP address request: transaction ID %d, is patcher? %r", trans_id, is_patcher)
		address = self.server_state.config.server_gatekeeper_file_server_address
		if address is None:
			raise base.ProtocolError("Client requested a file server IP address, but there's no file server running here and no file server address was configured")
		await self.file_server_ip_address_reply(trans_id, address)
	
	async def auth_server_ip_address_reply(self, trans_id: int, address: str) -> None:
		logger.debug("Sending auth server IP address reply: transaction ID %d, address %r", trans_id, address)
		await self.write_message(2, structs.UINT32.pack(trans_id) + base.pack_string_field(address, 24))
	
	@base.message_handler(2)
	async def auth_server_ip_address_request(self) -> None:
		(trans_id,) = await self.read_unpack(structs.UINT32)
		logger.debug("Auth server IP address request: transaction ID %d", trans_id)
		address = self.server_state.config.server_gatekeeper_auth_server_address
		if address is None:
			address = self.get_own_address_string()
		await self.auth_server_ip_address_reply(trans_id, address)
