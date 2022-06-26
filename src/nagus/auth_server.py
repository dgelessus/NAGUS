# This file is part of NAGUS, an Uru Live server that is not very good.
# Copyright (C) 2022 dgelessus
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


"""Implements the :ref:`auth server <auth_server>`."""


import logging
import random
import struct
import typing
import uuid

from . import base


logger = logging.getLogger(__name__)


CONNECT_DATA = struct.Struct("<I16s")

PING_HEADER = struct.Struct("<III")
CLIENT_REGISTER_REPLY = struct.Struct("<I")
ACCOUNT_LOGIN_REPLY = struct.Struct("<II16sII4I")
ACCOUNT_LOGIN_REQUEST_HEADER = struct.Struct("<II")


ZERO_UUID = uuid.UUID("00000000-0000-0000-0000-000000000000")


SYSTEM_RANDOM = random.SystemRandom()


class AuthConnection(base.BaseMOULConnection):
	CONNECTION_TYPE = base.ConnectionType.cli2auth
	
	server_challenge: int
	
	async def read_connect_packet_data(self) -> None:
		"""Read and unpack the type-specific connect packet data.
		
		The unpacked information is currently discarded.
		"""
		
		data_length, token = await self.read_unpack(CONNECT_DATA)
		if data_length != CONNECT_DATA.size:
			raise base.ProtocolError(f"Client sent client-to-auth connect data with unexpected length {data_length} (should be {CONNECT_DATA.size})")
		
		token = uuid.UUID(bytes_le=token)
		if token != ZERO_UUID:
			raise base.ProtocolError(f"Client sent client-to-auth connect data with unexpected token {token} (should be {ZERO_UUID})")
	
	@base.message_handler(0)
	async def ping_request(self) -> None:
		"""Reply to ping request."""
		
		header_data = await self.read(PING_HEADER.size)
		ping_time, trans_id, payload_length = PING_HEADER.unpack(header_data)
		logger.debug("Ping request: time %d, transaction %d, payload %d bytes", ping_time, trans_id, payload_length)
		payload = await self.read(payload_length)
		# Send everything back unmodified
		await self.write_message(0, header_data + payload)
	
	async def client_register_reply(self, server_challenge: int) -> None:
		logger.debug("Sending client register reply with server challenge: 0x%08x", server_challenge)
		await self.write_message(3, CLIENT_REGISTER_REPLY.pack(server_challenge))
	
	@base.message_handler(1)
	async def client_register_request(self) -> None:
		(build_id,) = await self.read_unpack(base.DWORD)
		logger.debug("Build ID: %d", build_id)
		if build_id != self.build_id:
			raise base.ProtocolError(f"Client register request build ID ({build_id}) differs from connect packet ({self.build_id})")
		
		# Send ServerCaps message for H'uru clients in a way that doesn't break OpenUru clients.
		# This is barely tested and does some wacky stuff,
		# so I'm commenting it out for now.
		# H'uru clients generally work fine without the ServerCaps message.
		r"""
		await self.write(
			# ServerCaps message type number - recognized by H'uru, but ignored by OpenUru.
			b"\x02\x10"
			# ServerCaps message data for H'uru.
			# OpenUru parses this as the start of a FileDownloadChunk message,
			# which will be ignored,
			# because no file download transaction is active.
			# H'uru sees: 0x25 bytes of data, bit vector is 1 dword long, value is 0
			# OpenUru sees: message type 0x25 (FileDownloadChunk), transaction ID 0x10000, error code 0, file size 0 (continued below)
			b"\x25\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00"
			# ServerCaps message extra data,
			# which is ignored by H'uru,
			# because the bit vector doesn't have this many dwords.
			# OpenUru parses this as the rest of FileDownloadChunk message:
			b"\x00\x00" # file size 0 (continued)
			b"\x00\x00\x00\x00\x13\x00\x00\x00" # chunk offset 0, chunk size 0x13
			b"[ServerCaps compat]" # 0x13 bytes of chunk data
		)
		#"""
		
		# Reply to client register request
		if hasattr(self, "server_challenge"):
			logger.warning("Already registered client sent another client register request - generating new server challenge...")
		self.server_challenge = SYSTEM_RANDOM.randrange(0x100000000)
		await self.client_register_reply(self.server_challenge)
	
	async def account_login_reply(
		self,
		trans_id: int,
		result: int,
		account_id: uuid.UUID,
		account_flags: int,
		billing_type: int,
		ntd_encryption_key: typing.Tuple[int, int, int, int],
	) -> None:
		logger.debug(
			"Sending account login reply: transaction ID %d, result %d, account ID %s, account flags 0x%08x, billing type 0x%08x, NTD encryption key [0x%08x, 0x%08x, 0x%08x, 0x%08x]",
			trans_id, result, account_id, account_flags, billing_type, *ntd_encryption_key,
		)
		await self.write_message(4, ACCOUNT_LOGIN_REPLY.pack(trans_id, result, account_id.bytes_le, account_flags, billing_type, *ntd_encryption_key))
	
	@base.message_handler(3)
	async def account_login_request(self) -> None:
		trans_id, client_challenge = await self.read_unpack(ACCOUNT_LOGIN_REQUEST_HEADER)
		logger.debug("Login request: transaction ID: %d, client challenge 0x%08x", trans_id, client_challenge)
		account_name = await self.read_string_field()
		logger.debug("Account name: %r", account_name)
		challenge_hash = await self.read(20)
		logger.debug("Challenge hash: %r", challenge_hash)
		auth_token = await self.read_string_field()
		logger.debug("Auth token: %r", auth_token)
		os_name = await self.read_string_field()
		logger.debug("OS name: %r", os_name)
		
		if not hasattr(self, "server_challenge"):
			raise base.ProtocolError("Client attempted to log in without sending a client register request first")
		
		# Reply with "authentication failed"
		await self.account_login_reply(trans_id, 20, ZERO_UUID, 0, 0, (0, 0, 0, 0))
