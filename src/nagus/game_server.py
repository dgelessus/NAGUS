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
import collections
import datetime
import enum
import io
import logging
import struct
import typing
import uuid
import zlib

from . import base
from . import state
from . import structs


logger = logging.getLogger(__name__)


LOCATION = struct.Struct("<IH")
UOID_MID_PART = struct.Struct("<HI")
UOID_CLONE_IDS = struct.Struct("<HHI")

CONNECT_DATA = struct.Struct("<I16s16s")

PING_REQUEST = struct.Struct("<I")
PING_REPLY = struct.Struct("<I")
JOIN_AGE_REQUEST = struct.Struct("<II16sI")
JOIN_AGE_REPLY = struct.Struct("<II")
PROPAGATE_BUFFER_HEADER = struct.Struct("<II")

NET_MESSAGE_HEADER = struct.Struct("<HI")
NET_MESSAGE_VERSION = struct.Struct("<BB")
NET_MESSAGE_TIME_SENT = struct.Struct("<II")
NET_MESSAGE_STREAMED_OBJECT_HEADER = struct.Struct("<IBI")


class Location(object):
	class Flags(enum.IntFlag):
		local_only = 1 << 0
		volatile = 1 << 1
		reserved = 1 << 2
		built_in = 1 << 3
		itinerant = 1 << 4
	
	sequence_number: int
	flags: "Location.Flags"
	
	def __init__(self, sequence_number: int, flags: "Location.Flags") -> None:
		super().__init__()
		
		self.sequence_number = sequence_number
		self.flags = flags
	
	def __eq__(self, other: object) -> bool:
		if not isinstance(other, Location):
			return NotImplemented
		
		return self.sequence_number == other.sequence_number and self.flags == other.flags
	
	def __repr__(self) -> str:
		return f"{type(self).__qualname__}({self.sequence_number}, {self.flags!s})"
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "Location":
		sequence_number, flags = structs.stream_unpack(stream, LOCATION)
		return cls(sequence_number, Location.Flags(flags))
	
	def write(self, stream: typing.BinaryIO) -> None:
		stream.write(LOCATION.pack(self.sequence_number, self.flags))


class LoadMask(object):
	ALWAYS: "LoadMask"
	
	quality: int
	capability: int
	
	def __init__(self, quality: int, capability: int) -> None:
		super().__init__()
		
		self.quality = quality
		self.capability = capability
	
	def __eq__(self, other: object) -> bool:
		if not isinstance(other, LoadMask):
			return NotImplemented
		
		return self.quality == other.quality and self.capability == other.capability
	
	def __repr__(self) -> str:
		return f"{type(self).__qualname__}({self.quality!r}, {self.capability!r})"
	
	@classmethod
	def decode(cls, qc: int) -> "LoadMask":
		return cls(
			(qc >> 4 & 0xf) | 0xf0,
			(qc >> 0 & 0xf) | 0xf0,
		)
	
	def encode(self) -> int:
		return (self.quality & 0xf) << 4 | (self.capability & 0xf) << 0


LoadMask.ALWAYS = LoadMask(0xff, 0xff)


class Uoid(object):
	class Flags(enum.IntFlag):
		has_clone_ids = 1 << 0
		has_load_mask = 1 << 1
		
		supported = (
			has_clone_ids
			| has_load_mask
		)
	
	location: Location
	load_mask: LoadMask
	class_type: int
	object_id: int
	object_name: bytes
	clone_ids: typing.Optional[typing.Tuple[int, int]]
	
	def repr_fields(self) -> collections.OrderedDict[str, str]:
		fields = collections.OrderedDict()
		fields["location"] = repr(self.location)
		if self.load_mask != LoadMask.ALWAYS:
			fields["load_mask"] = repr(self.load_mask)
		fields["class_type"] = f"0x{self.class_type:>04x}"
		fields["object_id"] = repr(self.object_id)
		fields["object_name"] = repr(self.object_name)
		if self.clone_ids is not None:
			fields["clone_ids"] = repr(self.clone_ids)
		return fields
	
	def __repr__(self) -> str:
		joined_fields = ", ".join(name + "=" + value for name, value in self.repr_fields().items())
		return f"{type(self).__qualname__}({joined_fields})"
	
	def read(self, stream: typing.BinaryIO) -> None:
		(flags,) = structs.read_exact(stream, 1)
		flags = Uoid.Flags(flags)
		if flags & ~Uoid.Flags.supported:
			raise ValueError(f"Uoid has unsupported flags set: {flags!r}")
		
		self.location = Location.from_stream(stream)
		
		if Uoid.Flags.has_load_mask in flags:
			(load_mask,) = structs.read_exact(stream, 1)
			self.load_mask = LoadMask.decode(load_mask)
		else:
			self.load_mask = LoadMask.ALWAYS
		
		self.class_type, self.object_id = structs.stream_unpack(stream, UOID_MID_PART)
		self.object_name = structs.read_safe_string(stream)
		
		if Uoid.Flags.has_clone_ids in flags:
			clone_id, ignored, clone_player_id = structs.stream_unpack(stream, UOID_CLONE_IDS)
			self.clone_ids = clone_id, clone_player_id
		else:
			self.clone_ids = None
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "Uoid":
		self = cls()
		self.read(stream)
		return self
	
	def write(self, stream: typing.BinaryIO) -> None:
		flags = Uoid.Flags(0)
		if self.load_mask != LoadMask.ALWAYS:
			flags |= Uoid.Flags.has_load_mask
		if self.clone_ids is not None:
			flags |= Uoid.Flags.has_clone_ids
		stream.write(bytes([flags]))
		
		self.location.write(stream)
		
		if self.load_mask != LoadMask.ALWAYS:
			stream.write(bytes([self.load_mask.encode()]))
		
		stream.write(UOID_MID_PART.pack(self.class_type, self.object_id))
		structs.write_safe_string(stream, self.object_name)
		
		if self.clone_ids is not None:
			clone_id, clone_player_id = self.clone_ids
			stream.write(UOID_CLONE_IDS.pack(clone_id, 0, clone_player_id))


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


class CompressionType(enum.Enum):
	none = 0
	failed = 1
	zlib = 2
	dont = 3


class NetMessage(object):
	class_index: NetMessageClassIndex
	flags: NetMessageFlags
	protocol_version: typing.Optional[typing.Tuple[int, int]]
	time_sent: typing.Optional[datetime.datetime]
	context: typing.Optional[int]
	trans_id: typing.Optional[int]
	ki_number: typing.Optional[int]
	account_uuid: typing.Optional[uuid.UUID]
	
	def repr_fields(self) -> collections.OrderedDict[str, str]:
		fields = collections.OrderedDict()
		fields["class_index"] = repr(self.class_index)
		fields["flags"] = repr(self.flags)
		
		if self.protocol_version is not None:
			fields["protocol_version"] = repr(self.protocol_version)
		
		if self.time_sent is not None:
			fields["time_sent"] = repr(self.time_sent)
		
		if self.context is not None:
			fields["context"] = repr(self.context)
		
		if self.trans_id is not None:
			fields["trans_id"] = repr(self.trans_id)
		
		if self.ki_number is not None:
			fields["ki_number"] = repr(self.ki_number)
		
		if self.account_uuid is not None:
			fields["account_uuid"] = repr(self.account_uuid)
		
		return fields
	
	def __repr__(self) -> str:
		joined_fields = ", ".join(name + "=" + value for name, value in self.repr_fields().items())
		return f"<{type(self).__qualname__}: {joined_fields}>"
	
	def read(self, stream: typing.BinaryIO) -> None:
		class_index, flags = structs.stream_unpack(stream, NET_MESSAGE_HEADER)
		self.class_index = NetMessageClassIndex(class_index)
		self.flags = NetMessageFlags(flags)
		
		if NetMessageFlags.has_version in self.flags:
			major, minor = structs.stream_unpack(stream, NET_MESSAGE_VERSION)
			self.protocol_version = (major, minor)
		else:
			self.protocol_version = None
		
		if NetMessageFlags.has_time_sent in self.flags:
			timestamp, micros = structs.stream_unpack(stream, NET_MESSAGE_TIME_SENT)
			self.time_sent = datetime.datetime.fromtimestamp(timestamp) + datetime.timedelta(microseconds=micros)
		else:
			self.time_sent = None
		
		if NetMessageFlags.has_context in self.flags:
			(self.context,) = structs.stream_unpack(stream, structs.UINT32)
		else:
			self.context = None
		
		if NetMessageFlags.has_transaction_id in self.flags:
			(self.trans_id,) = structs.stream_unpack(stream, structs.UINT32)
		else:
			self.trans_id = None
		
		if NetMessageFlags.has_player_id in self.flags:
			(self.ki_number,) = structs.stream_unpack(stream, structs.UINT32)
		else:
			self.ki_number = None
		
		if NetMessageFlags.has_account_uuid in self.flags:
			self.account_uuid = uuid.UUID(bytes_le=structs.read_exact(stream, 16))
		else:
			self.account_uuid = None
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "NetMessage":
		# Peek the class index from the beginning of the message
		pos = stream.tell()
		try:
			class_index, _ = structs.stream_unpack(stream, NET_MESSAGE_HEADER)
		finally:
			stream.seek(pos)
		
		class_index = NetMessageClassIndex(class_index)
		
		self: NetMessage
		if class_index == NetMessageClassIndex.rooms_list:
			self = NetMessageRoomsList()
		elif class_index == NetMessageClassIndex.paging_room:
			self = NetMessagePagingRoom()
		elif class_index == NetMessageClassIndex.game_state_request:
			self = NetMessageGameStateRequest()
		elif class_index in {
			NetMessageClassIndex.object,
			NetMessageClassIndex.get_shared_state,
			NetMessageClassIndex.object_state_request,
		}:
			self = NetMessageObject()
		elif class_index in {
			NetMessageClassIndex.streamed_object,
			NetMessageClassIndex.shared_state,
			NetMessageClassIndex.test_and_set,
			NetMessageClassIndex.sdl_state,
			NetMessageClassIndex.sdl_state_broadcast,
		}:
			self = NetMessageStreamedObject()
		else:
			self = cls()
		
		self.read(stream)
		return self
	
	def write(self, stream: typing.BinaryIO) -> None:
		stream.write(NET_MESSAGE_HEADER.pack(self.class_index, self.flags))
		
		if NetMessageFlags.has_version in self.flags:
			assert self.protocol_version is not None
			stream.write(NET_MESSAGE_VERSION.pack(*self.protocol_version))
		else:
			assert self.protocol_version is None
		
		if NetMessageFlags.has_time_sent in self.flags:
			assert self.time_sent is not None
			stream.write(NET_MESSAGE_VERSION.pack(int(self.time_sent.timestamp()), self.time_sent.microsecond))
		else:
			assert self.time_sent is None
		
		if NetMessageFlags.has_context in self.flags:
			assert self.context is not None
			stream.write(structs.UINT32.pack(self.context))
		else:
			assert self.context is None
		
		if NetMessageFlags.has_transaction_id in self.flags:
			assert self.trans_id is not None
			stream.write(structs.UINT32.pack(self.trans_id))
		else:
			assert self.trans_id is None
		
		if NetMessageFlags.has_player_id in self.flags:
			assert self.ki_number is not None
			stream.write(structs.UINT32.pack(self.ki_number))
		else:
			assert self.ki_number is None
		
		if NetMessageFlags.has_account_uuid in self.flags:
			assert self.account_uuid is not None
			stream.write(self.account_uuid.bytes_le)
		else:
			assert self.account_uuid is None


class NetMessageRoomsList(NetMessage):
	rooms: typing.List[typing.Tuple[Location, bytes]]
	
	def repr_fields(self) -> collections.OrderedDict[str, str]:
		fields = super().repr_fields()
		fields["rooms"] = repr(self.rooms)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		
		(room_count,) = structs.stream_unpack(stream, structs.UINT32)
		self.rooms = []
		for _ in range(room_count):
			location = Location.from_stream(stream)
			(name_length,) = structs.stream_unpack(stream, structs.UINT16)
			name = structs.read_exact(stream, name_length)
			self.rooms.append((location, name))
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		
		stream.write(structs.UINT32.pack(len(self.rooms)))
		for location, name in self.rooms:
			location.write(stream)
			stream.write(structs.UINT16.pack(len(name)))
			stream.write(name)


class NetMessagePagingRoom(NetMessageRoomsList):
	class Flags(enum.IntFlag):
		paging_out = 1 << 0
		reset_list = 1 << 1
		request_state = 1 << 2
		final_room_in_age = 1 << 3
	
	page_flags: "NetMessagePagingRoom.Flags"
	
	def repr_fields(self) -> collections.OrderedDict[str, str]:
		fields = super().repr_fields()
		fields["page_flags"] = repr(self.page_flags)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		(flags,) = structs.read_exact(stream, 1)
		self.page_flags = NetMessagePagingRoom.Flags(flags)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		stream.write(bytes([self.page_flags]))


class NetMessageGameStateRequest(NetMessageRoomsList):
	pass


class NetMessageObject(NetMessage):
	uoid: Uoid
	
	def repr_fields(self) -> collections.OrderedDict[str, str]:
		fields = super().repr_fields()
		fields["uoid"] = repr(self.uoid)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		
		self.uoid = Uoid.from_stream(stream)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		
		self.uoid.write(stream)


class NetMessageStreamedObject(NetMessageObject):
	compression_type: CompressionType
	data: bytes
	
	def repr_fields(self) -> collections.OrderedDict[str, str]:
		fields = super().repr_fields()
		if self.compression_type != CompressionType.none:
			fields["compression_type"] = str(self.compression_type)
		fields["data"] = repr(self.data)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		
		uncompressed_length, compression_type, stream_length = structs.stream_unpack(stream, NET_MESSAGE_STREAMED_OBJECT_HEADER)
		self.compression_type = CompressionType(compression_type)
		if self.compression_type == CompressionType.failed:
			raise ValueError("plNetMsgStreamedObject has its compression type set to failed, this should never happen!")
		
		stream_data = structs.read_exact(stream, stream_length)
		if self.compression_type == CompressionType.zlib:
			self.data = zlib.decompress(stream_data)
			if uncompressed_length != len(self.data):
				raise ValueError(f"plNetMsgStreamedObject uncompressed length {uncompressed_length} doesn't match actual length of data after decompression: {len(self.data)}")
		else:
			self.data = stream_data
			if uncompressed_length != 0:
				raise ValueError(f"plNetMsgStreamedObject uncompressed length {uncompressed_length} should be 0  for non-compressed data")
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		
		if self.compression_type == CompressionType.zlib:
			uncompressed_length = len(self.data)
			stream_data = zlib.compress(self.data)
		else:
			uncompressed_length = 0
			stream_data = self.data
		
		stream.write(NET_MESSAGE_STREAMED_OBJECT_HEADER.pack(uncompressed_length, self.compression_type, len(stream_data)))
		stream.write(stream_data)


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
		if account_uuid != structs.ZERO_UUID or age_instance_uuid != structs.ZERO_UUID:
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
		
		with io.BytesIO(await self.read(buffer_length)) as buffer:
			message = NetMessage.from_stream(buffer)
			extra_data = buffer.read()
		
		if buffer_type != message.class_index:
			raise base.ProtocolError(f"PropagateBuffer type {buffer_type!r} doesn't match class index in serialized message: {message.class_index!r}")
		
		logger.debug("Received propagate buffer: %r", message)
		
		unsupported_flags = message.flags & ~NetMessageFlags.all_handled
		if unsupported_flags:
			logger.warning("PropagateBuffer message %r has flags set that we can't handle yet: %r", message.class_index, unsupported_flags)
		if message.protocol_version is not None:
			logger.warning("PropagateBuffer message %r contains protocol version: %r", message.class_index, message.protocol_version)
		if message.context is not None:
			logger.warning("PropagateBuffer message %r contains context: %d", message.class_index, message.context)
		if message.trans_id is not None:
			logger.warning("PropagateBuffer message %r contains transaction ID: %d", message.class_index, message.trans_id)
		if message.account_uuid is not None:
			logger.warning("PropagateBuffer message %r contains account UUID: %s", message.class_index, message.account_uuid)
		if extra_data:
			logger.warning("PropagateBuffer message %r has extra trailing data: %r", message.class_index, extra_data)
