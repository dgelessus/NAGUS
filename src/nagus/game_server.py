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


"""Implements the :ref:`game server <game_server>`."""


import asyncio
import datetime
import enum
import logging
import struct
import typing
import uuid

from . import base
from . import state


logger = logging.getLogger(__name__)


CONNECT_DATA = struct.Struct("<I16s16s")

PING_REQUEST = struct.Struct("<I")
PING_REPLY = struct.Struct("<I")
JOIN_AGE_REQUEST = struct.Struct("<II16sI")
JOIN_AGE_REPLY = struct.Struct("<II")
PROPAGATE_BUFFER_HEADER = struct.Struct("<II")

NET_MESSAGE_HEADER = struct.Struct("<HI")
NET_MESSAGE_VERSION = struct.Struct("<BB")
NET_MESSAGE_TIME_SENT = struct.Struct("<II")
NET_MESSAGE_UINT32 = struct.Struct("<I")


class NetMessageClassIndex(enum.IntEnum):
	paging_room = 0x0218
	net_message = 0x025e
	rooms_list = 0x0263
	group_owner = 0x0264
	game_state_request = 0x0265
	object = 0x0268
	game_message = 0x026b
	stream = 0x026c
	voice = 0x0279
	streamed_object = 0x027b
	shared_state = 0x027c
	test_and_set = 0x027d
	get_shared_state = 0x027e
	object_state_request = 0x0286
	object_update_filter = 0x029d
	members_list_req = 0x02ad
	members_list = 0x02ae
	member_update = 0x02b1
	server_to_client = 0x02b2
	initial_age_state_sent = 0x02b8
	listen_list_update = 0x02c8
	sdl_state = 0x02cd
	sdl_state_broadcast = 0x0329
	game_message_directed = 0x032e
	relevance_regions = 0x03ac
	load_clone = 0x03b3
	player_page = 0x03b4


class NetMessageFlags(enum.IntFlag):
	has_time_sent = 1 << 0
	has_game_message_receivers = 1 << 1
	echo_back_to_sender = 1 << 2
	request_p2p = 1 << 3
	allow_time_out = 1 << 4
	indirect_member = 1 << 5
	public_ip_client = 1 << 6
	has_context = 1 << 7
	ask_vault_for_game_state = 1 << 8
	has_transaction_id = 1 << 9
	new_sdl_state = 1 << 10
	initial_age_state_request = 1 << 11
	has_player_id = 1 << 12
	use_relevance_regions = 1 << 13
	has_account_uuid = 1 << 14
	inter_age_routing = 1 << 15
	has_version = 1 << 16
	is_system_message = 1 << 17
	needs_reliable_send = 1 << 18
	route_to_all_players = 1 << 19
	
	# Bit mask of all flags that we can handle (or safely ignore).
	# All other flags generate a warning log message.
	all_handled = (
		has_time_sent
		| has_context
		| has_transaction_id
		| new_sdl_state
		| initial_age_state_request
		| has_player_id
		| use_relevance_regions
		| has_account_uuid
		| inter_age_routing
		| has_version
		| is_system_message
		| needs_reliable_send
	)


class NetMessage(object):
	class_index: NetMessageClassIndex
	flags: NetMessageFlags
	protocol_version: typing.Optional[typing.Tuple[int, int]]
	time_sent: typing.Optional[datetime.datetime]
	context: typing.Optional[int]
	trans_id: typing.Optional[int]
	ki_number: typing.Optional[int]
	account_uuid: typing.Optional[uuid.UUID]
	
	@classmethod
	def unpack_header(cls, data: bytes) -> typing.Tuple["NetMessage", bytes]:
		self = cls()
		
		class_index, flags = NET_MESSAGE_HEADER.unpack_from(data)
		data = data[NET_MESSAGE_HEADER.size:]
		self.class_index = NetMessageClassIndex(class_index)
		self.flags = NetMessageFlags(flags)
		
		if NetMessageFlags.has_version in self.flags:
			major, minor = NET_MESSAGE_VERSION.unpack_from(data)
			self.protocol_version = (major, minor)
			data = data[NET_MESSAGE_VERSION.size:]
		else:
			self.protocol_version = None
		
		if NetMessageFlags.has_time_sent in self.flags:
			timestamp, micros = NET_MESSAGE_TIME_SENT.unpack_from(data)
			self.time_sent = datetime.datetime.fromtimestamp(timestamp) + datetime.timedelta(microseconds=micros)
			data = data[NET_MESSAGE_TIME_SENT.size:]
		else:
			self.time_sent = None
		
		if NetMessageFlags.has_context in self.flags:
			(self.context,) = NET_MESSAGE_UINT32.unpack_from(data)
			data = data[NET_MESSAGE_UINT32.size:]
		else:
			self.context = None
		
		if NetMessageFlags.has_transaction_id in self.flags:
			(self.trans_id,) = NET_MESSAGE_UINT32.unpack_from(data)
			data = data[NET_MESSAGE_UINT32.size:]
		else:
			self.trans_id = None
		
		if NetMessageFlags.has_player_id in self.flags:
			(self.ki_number,) = NET_MESSAGE_UINT32.unpack_from(data)
			data = data[NET_MESSAGE_UINT32.size:]
		else:
			self.ki_number = None
		
		if NetMessageFlags.has_account_uuid in self.flags:
			self.account_uuid = uuid.UUID(bytes_le=data[:16])
			data = data[16:]
		else:
			self.account_uuid = None
		
		return self, data
	
	def pack(self) -> bytes:
		data = bytearray(NET_MESSAGE_HEADER.pack(self.class_index, self.flags))
		
		if NetMessageFlags.has_version in self.flags:
			assert self.protocol_version is not None
			data.extend(NET_MESSAGE_VERSION.pack(*self.protocol_version))
		else:
			assert self.protocol_version is None
		
		if NetMessageFlags.has_time_sent in self.flags:
			assert self.time_sent is not None
			data.extend(NET_MESSAGE_VERSION.pack(int(self.time_sent.timestamp()), self.time_sent.microsecond))
		else:
			assert self.time_sent is None
		
		if NetMessageFlags.has_context in self.flags:
			assert self.context is not None
			data.extend(NET_MESSAGE_UINT32.pack(self.context))
		else:
			assert self.context is None
		
		if NetMessageFlags.has_transaction_id in self.flags:
			assert self.trans_id is not None
			data.extend(NET_MESSAGE_UINT32.pack(self.trans_id))
		else:
			assert self.trans_id is None
		
		if NetMessageFlags.has_player_id in self.flags:
			assert self.ki_number is not None
			data.extend(NET_MESSAGE_UINT32.pack(self.ki_number))
		else:
			assert self.ki_number is None
		
		if NetMessageFlags.has_account_uuid in self.flags:
			assert self.account_uuid is not None
			data.extend(NET_MESSAGE_UINT32.pack(self.account_uuid))
		else:
			assert self.account_uuid is None
		
		return data


class GameClientState(object):
	mcp_id: int
	account_uuid: uuid.UUID
	ki_number: int


class GameConnection(base.BaseMOULConnection):
	CONNECTION_TYPE = base.ConnectionType.cli2game
	
	client_state: GameClientState
	
	def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, server_state: state.ServerState) -> None:
		super().__init__(reader, writer, server_state)
		
		self.client_state = GameClientState()
	
	async def read_connect_packet_data(self) -> None:
		data_length, account_uuid, age_instance_uuid = await self.read_unpack(CONNECT_DATA)
		if data_length != CONNECT_DATA.size:
			raise base.ProtocolError(f"Client sent client-to-game connect data with unexpected length {data_length} (should be {CONNECT_DATA.size})")
		
		account_uuid = uuid.UUID(bytes_le=account_uuid)
		age_instance_uuid = uuid.UUID(bytes_le=age_instance_uuid)
		if account_uuid != state.ZERO_UUID or age_instance_uuid != state.ZERO_UUID:
			logger.warning("Client connected to game server with non-zero UUIDs: account UUID %s, age instance UUID %s", account_uuid, age_instance_uuid)
	
	@base.message_handler(0)
	async def ping_request(self) -> None:
		(ping_time,) = await self.read_unpack(PING_REQUEST)
		logger.debug("Ping request: time %d", ping_time)
		await self.write_message(0, PING_REPLY.pack(ping_time))
	
	async def join_age_reply(self, trans_id: int, result: base.NetError) -> None:
		logger.debug("Sending join age reply: transaction ID %d, result %r", trans_id, result)
		await self.write_message(1, JOIN_AGE_REPLY.pack(trans_id, result))
	
	@base.message_handler(1)
	async def join_age_request(self) -> None:
		trans_id, mcp_id, account_uuid, ki_number = await self.read_unpack(JOIN_AGE_REQUEST)
		account_uuid = uuid.UUID(bytes_le=account_uuid)
		logger.debug("Join age request: transaction ID %d, MCP ID %d, account UUID %s, KI number %d", trans_id, mcp_id, account_uuid, ki_number)
		
		try:
			self.client_state.mcp_id
		except AttributeError:
			pass
		else:
			await self.join_age_reply(trans_id, base.NetError.invalid_parameter)
			raise base.ProtocolError(f"Client attempted to join another age instance ({mcp_id}) with an already established game server connection (for age instance {self.client_state.mcp_id})")
		
		self.client_state.mcp_id = mcp_id
		self.client_state.account_uuid = account_uuid
		self.client_state.ki_number = ki_number
		
		await self.join_age_reply(trans_id, base.NetError.success)
	
	@base.message_handler(2)
	async def receive_propagate_buffer(self) -> None:
		buffer_type, buffer_length = await self.read_unpack(PROPAGATE_BUFFER_HEADER)
		buffer_type = NetMessageClassIndex(buffer_type)
		buffer = await self.read(buffer_length)
		
		header, subclass_buffer = NetMessage.unpack_header(buffer)
		if buffer_type != header.class_index:
			raise base.ProtocolError(f"PropagateBuffer type {buffer_type!r} doesn't match class index in serialized message: {header.class_index!r}")
		
		logger.debug("Received propagate buffer: class index %r, flags %r, time sent %s, KI number %d, class-specific data %r", header.class_index, header.flags, header.time_sent, header.ki_number, subclass_buffer)
		
		unsupported_flags = header.flags & ~NetMessageFlags.all_handled
		if unsupported_flags:
			logger.warning("PropagateBuffer message %r has flags set that we can't handle yet: %r", header.class_index, unsupported_flags)
		if header.protocol_version is not None:
			logger.warning("PropagateBuffer message %r contains protocol version: %r", header.protocol_version)
		if header.context is not None:
			logger.warning("PropagateBuffer message %r contains context: %d", header.context)
		if header.trans_id is not None:
			logger.warning("PropagateBuffer message %r contains transaction ID: %d", header.trans_id)
		if header.account_uuid is not None:
			logger.warning("PropagateBuffer message %r contains account UUID: %s", header.account_uuid)
