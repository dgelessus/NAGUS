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
import ipaddress
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
NET_MESSAGE_SDL_STATE = struct.Struct("<???")
NET_MESSAGE_LOAD_CLONE_BOOLS = struct.Struct("<???")


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
		return f"{type(self).__qualname__}({self.sequence_number:#x}, {self.flags!s})"
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "Location":
		sequence_number, flags = structs.stream_unpack(stream, LOCATION)
		return cls(sequence_number, Location.Flags(flags))
	
	def write(self, stream: typing.BinaryIO) -> None:
		stream.write(LOCATION.pack(self.sequence_number, self.flags))


class GroupId(object):
	class Flags(enum.IntFlag):
		constant = 1 << 0
		local = 1 << 1
	
	location: Location
	flags: "GroupId.Flags"
	
	def __init__(self, id: Location, flags: "GroupId.Flags") -> None:
		super().__init__()
		
		self.location = id
		self.flags = flags
	
	def __eq__(self, other: object) -> bool:
		if not isinstance(other, GroupId):
			return NotImplemented
		
		return self.location == other.location and self.flags == other.flags
	
	def __repr__(self) -> str:
		return f"{type(self).__qualname__}({self.location!r}, {self.flags!s})"
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "GroupId":
		location = Location.from_stream(stream)
		(flags,) = structs.read_exact(stream, 1)
		return cls(location, GroupId.Flags(flags))
	
	def write(self, stream: typing.BinaryIO) -> None:
		self.location.write(stream)
		stream.write(bytes([self.flags]))


class Uoid(object):
	class Flags(enum.IntFlag):
		has_clone_ids = 1 << 0
		has_load_mask = 1 << 1
		
		supported = (
			has_clone_ids
			| has_load_mask
		)
	
	location: Location
	load_mask: int
	class_type: int
	object_id: int
	object_name: bytes
	clone_ids: typing.Optional[typing.Tuple[int, int]]
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = collections.OrderedDict()
		fields["location"] = repr(self.location)
		if self.load_mask != 0xff:
			fields["load_mask"] = hex(self.load_mask)
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
			(self.load_mask,) = structs.read_exact(stream, 1)
		else:
			self.load_mask = 0xff
		
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
		if self.load_mask != 0xff:
			flags |= Uoid.Flags.has_load_mask
		if self.clone_ids is not None:
			flags |= Uoid.Flags.has_clone_ids
		stream.write(bytes([flags]))
		
		self.location.write(stream)
		
		if self.load_mask != 0xff:
			stream.write(bytes([self.load_mask]))
		
		stream.write(UOID_MID_PART.pack(self.class_type, self.object_id))
		structs.write_safe_string(stream, self.object_name)
		
		if self.clone_ids is not None:
			clone_id, clone_player_id = self.clone_ids
			stream.write(UOID_CLONE_IDS.pack(clone_id, 0, clone_player_id))


class ClientInfo(object):
	class Flags(enum.Flag):
		account_uuid = 1 << 0
		ki_number = 1 << 1
		temp_ki_number = 1 << 2
		ccr_level = 1 << 3
		protected_login = 1 << 4
		build_type = 1 << 5
		avatar_name = 1 << 6
		source_ip_address = 1 << 7
		source_port = 1 << 8
		reserved = 1 << 9
		client_key = 1 << 10
	
	account_uuid: typing.Optional[uuid.UUID]
	ki_number: typing.Optional[int]
	temp_ki_number: typing.Optional[int]
	avatar_name: typing.Optional[bytes]
	ccr_level: typing.Optional[int]
	protected_login: typing.Optional[bool]
	build_type: typing.Optional[int]
	source_ip_address: typing.Optional[ipaddress.IPv4Address]
	source_port: typing.Optional[int]
	reserved: typing.Optional[bool]
	client_key: typing.Optional[bytes]
	
	def __init__(
		self,
		account_uuid: typing.Optional[uuid.UUID] = None,
		ki_number: typing.Optional[int] = None,
		temp_ki_number: typing.Optional[int] = None,
		avatar_name: typing.Optional[bytes] = None,
		ccr_level: typing.Optional[int] = None,
		protected_login: typing.Optional[bool] = None,
		build_type: typing.Optional[int] = None,
		source_ip_address: typing.Optional[ipaddress.IPv4Address] = None,
		source_port: typing.Optional[int] = None,
		reserved: typing.Optional[bool] = None,
		client_key: typing.Optional[bytes] = None,
	) -> None:
		super().__init__()
		
		self.account_uuid = account_uuid
		self.ki_number = ki_number
		self.temp_ki_number = temp_ki_number
		self.avatar_name = avatar_name
		self.ccr_level = ccr_level
		self.protected_login = protected_login
		self.build_type = build_type
		self.source_ip_address = source_ip_address
		self.source_port = source_port
		self.reserved = reserved
		self.client_key = client_key
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = collections.OrderedDict()
		if self.account_uuid is not None:
			fields["account_uuid"] = repr(self.account_uuid)
		if self.ki_number is not None:
			fields["ki_number"] = repr(self.ki_number)
		if self.temp_ki_number is not None:
			fields["temp_ki_number"] = repr(self.temp_ki_number)
		if self.avatar_name is not None:
			fields["avatar_name"] = repr(self.avatar_name)
		if self.ccr_level is not None:
			fields["ccr_level"] = repr(self.ccr_level)
		if self.protected_login is not None:
			fields["protected_login"] = repr(self.protected_login)
		if self.build_type is not None:
			fields["build_type"] = repr(self.build_type)
		if self.source_ip_address is not None:
			fields["source_ip_address"] = repr(self.source_ip_address)
		if self.source_port is not None:
			fields["source_port"] = repr(self.source_port)
		if self.reserved is not None:
			fields["reserved"] = repr(self.reserved)
		if self.client_key is not None:
			fields["client_key"] = repr(self.client_key)
		return fields
	
	def __repr__(self) -> str:
		joined_fields = ", ".join(name + "=" + value for name, value in self.repr_fields().items())
		return f"{type(self).__qualname__}({joined_fields})"
	
	def read(self, stream: typing.BinaryIO) -> None:
		(flags,) = structs.stream_unpack(stream, structs.UINT16)
		flags = ClientInfo.Flags(flags)
		
		if ClientInfo.Flags.account_uuid in flags:
			self.account_uuid = uuid.UUID(bytes_le=structs.read_exact(stream, 16))
		
		if ClientInfo.Flags.ki_number in flags:
			(self.ki_number,) = structs.stream_unpack(stream, structs.UINT32)
		
		if ClientInfo.Flags.temp_ki_number in flags:
			(self.temp_ki_number,) = structs.stream_unpack(stream, structs.UINT32)
		
		if ClientInfo.Flags.avatar_name in flags:
			(avatar_name_length,) = structs.stream_unpack(stream, structs.UINT16)
			self.avatar_name = structs.read_exact(stream, avatar_name_length)
		
		if ClientInfo.Flags.ccr_level in flags:
			(self.ccr_level,) = structs.read_exact(stream, 1)
		
		if ClientInfo.Flags.protected_login in flags:
			(protected_login,) = structs.read_exact(stream, 1)
			self.protected_login = bool(protected_login)
		
		if ClientInfo.Flags.build_type in flags:
			(self.build_type,) = structs.read_exact(stream, 1)
		
		if ClientInfo.Flags.source_ip_address in flags:
			(source_ip_address,) = structs.stream_unpack(stream, structs.UINT32)
			self.source_ip_address = ipaddress.IPv4Address(source_ip_address)
		
		if ClientInfo.Flags.source_port in flags:
			(self.source_port,) = structs.stream_unpack(stream, structs.UINT16)
		
		if ClientInfo.Flags.reserved in flags:
			(reserved,) = structs.read_exact(stream, 1)
			self.reserved = bool(reserved)
		
		if ClientInfo.Flags.client_key in flags:
			(client_key_length,) = structs.stream_unpack(stream, structs.UINT16)
			self.client_key = structs.read_exact(stream, client_key_length)
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "ClientInfo":
		self = cls()
		self.read(stream)
		return self
	
	def write(self, stream: typing.BinaryIO) -> None:
		flags = ClientInfo.Flags(0)
		if self.account_uuid is not None:
			flags |= ClientInfo.Flags.account_uuid
		if self.ki_number is not None:
			flags |= ClientInfo.Flags.ki_number
		if self.temp_ki_number is not None:
			flags |= ClientInfo.Flags.temp_ki_number
		if self.avatar_name is not None:
			flags |= ClientInfo.Flags.avatar_name
		if self.ccr_level is not None:
			flags |= ClientInfo.Flags.ccr_level
		if self.protected_login is not None:
			flags |= ClientInfo.Flags.protected_login
		if self.build_type is not None:
			flags |= ClientInfo.Flags.build_type
		if self.source_ip_address is not None:
			flags |= ClientInfo.Flags.source_ip_address
		if self.source_port is not None:
			flags |= ClientInfo.Flags.source_port
		if self.reserved is not None:
			flags |= ClientInfo.Flags.reserved
		if self.client_key is not None:
			flags |= ClientInfo.Flags.client_key
		stream.write(structs.UINT16.pack(flags))
		
		if self.account_uuid is not None:
			stream.write(self.account_uuid.bytes_le)
		
		if self.ki_number is not None:
			stream.write(structs.UINT32.pack(self.ki_number))
		
		if self.temp_ki_number is not None:
			stream.write(structs.UINT32.pack(self.temp_ki_number))
		
		if self.avatar_name:
			stream.write(structs.UINT16.pack(len(self.avatar_name)))
			stream.write(self.avatar_name)
		
		if self.ccr_level is not None:
			stream.write(bytes([self.ccr_level]))
		
		if self.protected_login is not None:
			stream.write(bytes([self.protected_login]))
		
		if self.build_type is not None:
			stream.write(bytes([self.build_type]))
		
		if self.source_ip_address is not None:
			stream.write(structs.UINT32.pack(int(self.source_ip_address)))
		
		if self.source_port:
			stream.write(structs.UINT16.pack(self.source_port))
		
		if self.reserved is not None:
			stream.write(bytes([self.reserved]))
		
		if self.client_key:
			stream.write(structs.UINT16.pack(len(self.client_key)))
			stream.write(self.client_key)


class MemberInfo(object):
	class Flags(enum.IntFlag):
		waiting_for_link_query = 1 << 0
		indirect_member = 1 << 1
		request_p2p = 1 << 2
		waiting_for_challenge_response = 1 << 3
		is_server = 1 << 4
		allow_time_out = 1 << 5
	
	flags: "MemberInfo.Flags"
	client_info: ClientInfo
	avatar_uoid: Uoid
	
	def __init__(self, flags: "MemberInfo.Flags", client_info: ClientInfo, avatar_uoid: Uoid) -> None:
		super().__init__()
		
		self.flags = flags
		self.client_info = client_info
		self.avatar_uoid = avatar_uoid
	
	def __repr__(self) -> str:
		return f"{type(self).__qualname__}({self.flags!s}, {self.client_info!r}, {self.avatar_uoid!r})"
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "MemberInfo":
		(flags,) = structs.stream_unpack(stream, structs.UINT32)
		client_info = ClientInfo.from_stream(stream)
		avatar_uoid = Uoid.from_stream(stream)
		return cls(MemberInfo.Flags(flags), client_info, avatar_uoid)
	
	def write(self, stream: typing.BinaryIO) -> None:
		stream.write(structs.UINT32.pack(self.flags))
		self.client_info.write(stream)
		self.avatar_uoid.write(stream)


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
	CLASS_INDEX = 0x025e
	
	class_index: int
	flags: NetMessageFlags
	protocol_version: typing.Optional[typing.Tuple[int, int]]
	time_sent: typing.Optional[datetime.datetime]
	context: typing.Optional[int]
	trans_id: typing.Optional[int]
	ki_number: typing.Optional[int]
	account_uuid: typing.Optional[uuid.UUID]
	
	@classmethod
	def __init_subclass__(cls, **kwargs) -> None:
		super().__init_subclass__(**kwargs)
		
		if cls.CLASS_INDEX in NET_MESSAGE_CLASSES_BY_INDEX:
			raise ValueError(f"Attempted to create NetMessage subclass {cls.__qualname__} with class index 0x{cls.CLASS_INDEX:>04x} which is already used by existing subclass {NET_MESSAGE_CLASSES_BY_INDEX[cls.CLASS_INDEX].__qualname__}")
		
		NET_MESSAGE_CLASSES_BY_INDEX[cls.CLASS_INDEX] = cls
	
	def __init__(self) -> None:
		super().__init__()
		
		self.class_index = type(self).CLASS_INDEX
		self.flags = NetMessageFlags.needs_reliable_send
		self.protocol_version = None
		self.time_sent = None
		self.context = None
		self.trans_id = None
		self.ki_number = None
		self.account_uuid = None
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = collections.OrderedDict()
		fields["class_index"] = f"0x{self.class_index:>04x}"
		fields["flags"] = repr(self.flags)
		
		if self.protocol_version is not None:
			fields["protocol_version"] = repr(self.protocol_version)
		
		if self.time_sent is not None:
			fields["time_sent"] = self.time_sent.isoformat()
		
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
	
	@property
	def class_description(self) -> str:
		return f"{type(self).__qualname__} (0x{self.class_index:>04x})"
	
	def read(self, stream: typing.BinaryIO) -> None:
		self.class_index, flags = structs.stream_unpack(stream, NET_MESSAGE_HEADER)
		self.flags = NetMessageFlags(flags)
		
		if NetMessageFlags.has_version in self.flags:
			major, minor = structs.stream_unpack(stream, NET_MESSAGE_VERSION)
			self.protocol_version = (major, minor)
		else:
			self.protocol_version = None
		
		if NetMessageFlags.has_time_sent in self.flags:
			self.time_sent = structs.read_unified_time(stream)
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
		
		try:
			clazz = NET_MESSAGE_CLASSES_BY_INDEX[class_index]
		except KeyError:
			self = cls()
		else:
			self = clazz()
		
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
			structs.write_unified_time(stream, self.time_sent)
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
	
	async def handle(self, connection: "GameConnection") -> None:
		logger.error("Don't know how to handle plNetMessage of class %s - ignoring", self.class_description)


NET_MESSAGE_CLASSES_BY_INDEX: typing.Dict[int, typing.Type[NetMessage]] = {
	NetMessage.CLASS_INDEX: NetMessage,
}


class NetMessageRoomsList(NetMessage):
	CLASS_INDEX = 0x0263
	
	rooms: typing.List[typing.Tuple[Location, bytes]]
	
	def __init__(self) -> None:
		super().__init__()
		self.flags |= NetMessageFlags.is_system_message
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
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
	
	CLASS_INDEX = 0x0218
	
	page_flags: "NetMessagePagingRoom.Flags"
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
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
	CLASS_INDEX = 0x0265
	
	async def handle(self, connection: "GameConnection") -> None:
		initial_age_state_sent = NetMessageInitialAgeStateSent()
		initial_age_state_sent.flags |= NetMessageFlags.has_time_sent
		initial_age_state_sent.time_sent = datetime.datetime.now(tz=datetime.timezone.utc)
		initial_age_state_sent.initial_sdl_state_count = 0
		await connection.send_propagat_buffer(initial_age_state_sent)


class NetMessageObject(NetMessage):
	CLASS_INDEX = 0x0268
	
	uoid: Uoid
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["uoid"] = repr(self.uoid)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		
		self.uoid = Uoid.from_stream(stream)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		
		self.uoid.write(stream)


class NetMessageStream(NetMessage):
	CLASS_INDEX = 0x026c
	
	uncompressed_length: int
	compression_type: CompressionType
	stream_data: bytes
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		if self.uncompressed_length != 0:
			fields["uncompressed_length"] = repr(self.uncompressed_length)
		if self.compression_type != CompressionType.none:
			fields["compression_type"] = str(self.compression_type)
		fields["stream_data"] = repr(self.stream_data)
		return fields
	
	def decompress_data(self) -> bytes:
		if self.compression_type == CompressionType.zlib:
			if len(self.stream_data) < 2:
				raise ValueError(f"Stream message zlib compression requires at least 2 bytes of data, but got {len(self.stream_data)}")
			data = self.stream_data[:2] + zlib.decompress(self.stream_data[2:])
			if self.uncompressed_length != len(data):
				raise ValueError(f"plNetMsgStreamedObject uncompressed length {self.uncompressed_length} doesn't match actual length of data after decompression: {len(data)}")
			return data
		else:
			if self.uncompressed_length != 0:
				raise ValueError(f"plNetMsgStreamedObject uncompressed length {self.uncompressed_length} should be 0 for non-compressed data")
			return self.stream_data
	
	def compress_and_set_data(self, data: bytes) -> None:
		if self.compression_type == CompressionType.zlib:
			self.uncompressed_length = len(data)
			if self.uncompressed_length < 2:
				raise ValueError(f"Stream message zlib compression requires at least 2 bytes of data, but got {self.uncompressed_length}")
			self.stream_data = data[:2] + zlib.compress(data[2:])
		else:
			self.uncompressed_length = 0
			self.stream_data = data
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		
		self.uncompressed_length, compression_type, stream_length = structs.stream_unpack(stream, NET_MESSAGE_STREAMED_OBJECT_HEADER)
		self.compression_type = CompressionType(compression_type)
		if self.compression_type == CompressionType.failed:
			raise ValueError("plNetMsgStreamedObject has its compression type set to failed, this should never happen!")
		
		self.stream_data = structs.read_exact(stream, stream_length)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		
		stream.write(NET_MESSAGE_STREAMED_OBJECT_HEADER.pack(self.uncompressed_length, self.compression_type, len(self.stream_data)))
		stream.write(self.stream_data)


class NetMessageStreamedObject(NetMessageStream, NetMessageObject):
	# Multiple inheritance, yo!
	CLASS_INDEX = 0x027b


class NetMessageSharedState(NetMessageStreamedObject):
	CLASS_INDEX = 0x027c
	
	lock_request: bool
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["lock_request"] = repr(self.lock_request)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		
		(lock_request,) = structs.read_exact(stream, 1)
		self.lock_request = bool(lock_request)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		
		stream.write(bytes([self.lock_request]))


class NetMessageTestAndSet(NetMessageSharedState):
	CLASS_INDEX = 0x027d


class NetMessageSDLState(NetMessageStreamedObject):
	CLASS_INDEX = 0x02cd
	
	is_initial_state: bool
	persist_on_server: bool
	is_avatar_state: bool
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		if self.is_initial_state:
			fields["is_initial_state"] = repr(self.is_initial_state)
		if not self.persist_on_server:
			fields["persist_on_server"] = repr(self.persist_on_server)
		if self.is_avatar_state:
			fields["is_avatar_state"] = repr(self.is_avatar_state)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		self.is_initial_state, self.persist_on_server, self.is_avatar_state = structs.stream_unpack(stream, NET_MESSAGE_SDL_STATE)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		stream.write(NET_MESSAGE_SDL_STATE.pack(self.is_initial_state, self.persist_on_server, self.is_avatar_state))


class NetMessageSDLStateBroadcast(NetMessageSDLState):
	CLASS_INDEX = 0x0329


class NetMessageGetSharedState(NetMessageObject):
	CLASS_INDEX = 0x027e
	
	shared_state_name: bytes
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["shared_state_name"] = repr(self.shared_state_name)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		shared_state_name = structs.read_exact(stream, 32)
		self.shared_state_name = shared_state_name[:shared_state_name.index(b"\x00")]
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		if len(self.shared_state_name) >= 32:
			raise ValueError(f"Shared state name must be less than 32 bytes, but found {len(self.shared_state_name)}")
		stream.write(self.shared_state_name.ljust(32, b"\x00"))


class NetMessageObjectStateRequest(NetMessageObject):
	CLASS_INDEX = 0x0286
	
	def __init__(self) -> None:
		super().__init__()
		self.flags |= NetMessageFlags.is_system_message


class NetMessageGameMessage(NetMessageStream):
	CLASS_INDEX = 0x026b
	
	delivery_time: datetime.datetime
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		if self.delivery_time != structs.ZERO_DATETIME:
			fields["delivery_time"] = self.delivery_time.isoformat()
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		(delivery_time_present,) = structs.read_exact(stream, 1)
		if delivery_time_present:
			self.delivery_time = structs.read_unified_time(stream)
		else:
			self.delivery_time = structs.ZERO_DATETIME
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		if self.delivery_time == structs.ZERO_DATETIME:
			stream.write(b"\x00")
		else:
			stream.write(b"\x01")
			structs.write_unified_time(stream, self.delivery_time)


class NetMessageGameMessageDirected(NetMessageGameMessage):
	CLASS_INDEX = 0x032e
	
	receivers: typing.List[int]
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["receivers"] = repr(self.receivers)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		(receiver_count,) = structs.read_exact(stream, 1)
		self.receivers = []
		for _ in range(receiver_count):
			(receiver,) = structs.stream_unpack(stream, structs.UINT32)
			self.receivers.append(receiver)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		stream.write(bytes([len(self.receivers)]))
		for receiver in self.receivers:
			stream.write(structs.UINT32.pack(receiver))


class NetMessageLoadClone(NetMessageGameMessage):
	CLASS_INDEX = 0x03b3
	
	uoid: Uoid
	is_player: bool
	is_loading: bool
	is_initial_state: bool
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["uoid"] = repr(self.uoid)
		if not self.is_player:
			fields["is_player"] = repr(self.is_player)
		if not self.is_loading:
			fields["is_loading"] = repr(self.is_loading)
		if self.is_initial_state:
			fields["is_initial_state"] = repr(self.is_initial_state)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		self.uoid = Uoid.from_stream(stream)
		self.is_player, self.is_loading, self.is_initial_state = structs.stream_unpack(stream, NET_MESSAGE_LOAD_CLONE_BOOLS)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		self.uoid.write(stream)
		stream.write(NET_MESSAGE_LOAD_CLONE_BOOLS.pack(self.is_player, self.is_loading, self.is_initial_state))


class NetMessageMembersListRequest(NetMessage):
	CLASS_INDEX = 0x02ad
	
	def __init__(self) -> None:
		super().__init__()
		self.flags |= NetMessageFlags.is_system_message


class NetMessageServerToClient(NetMessage):
	CLASS_INDEX = 0x02b2
	
	def __init__(self) -> None:
		super().__init__()
		self.flags |= NetMessageFlags.is_system_message
	
	async def handle(self, connection: "GameConnection") -> None:
		raise base.ProtocolError(f"A server-to-client message {self.class_description} was sent from a client to the server!")


class NetMessageGroupOwner(NetMessageServerToClient):
	CLASS_INDEX = 0x0264
	
	groups: typing.List[typing.Tuple[GroupId, bool]]
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["groups"] = repr(self.groups)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		
		(group_count,) = structs.stream_unpack(stream, structs.INT32)
		self.groups = []
		for _ in range(group_count):
			group_id = GroupId.from_stream(stream)
			(owned,) = structs.read_exact(stream, 1)
			self.groups.append((group_id, bool(owned)))
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		
		stream.write(structs.INT32.pack(len(self.groups)))
		for group_id, owned in self.groups:
			group_id.write(stream)
			stream.write(bytes([owned]))


class NetMessageMembersList(NetMessageServerToClient):
	CLASS_INDEX = 0x02ae
	
	members: typing.List[MemberInfo]
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["members"] = repr(self.members)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		(member_count,) = structs.stream_unpack(stream, structs.INT16)
		self.members = []
		for _ in range(member_count):
			self.members.append(MemberInfo.from_stream(stream))
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)


class NetMessageMemberUpdate(NetMessageServerToClient):
	CLASS_INDEX = 0x02b1
	
	member: MemberInfo
	was_added: bool
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["member"] = repr(self.member)
		fields["was_added"] = repr(self.was_added)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		self.member = MemberInfo.from_stream(stream)
		(was_addded,) = structs.read_exact(stream, 1)
		self.was_added = bool(was_addded)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		self.member.write(stream)
		stream.write(bytes([self.was_added]))


class NetMessageInitialAgeStateSent(NetMessageServerToClient):
	CLASS_INDEX = 0x02b8
	
	initial_sdl_state_count: int
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["initial_sdl_state_count"] = repr(self.initial_sdl_state_count)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		(self.initial_sdl_state_count,) = structs.stream_unpack(stream, structs.UINT32)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		stream.write(structs.UINT32.pack(self.initial_sdl_state_count))


class NetMessageRelevanceRegions(NetMessage):
	CLASS_INDEX = 0x03ac
	
	regions_i_care_about: int
	regions_im_in: int
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["regions_i_care_about"] = bin(self.regions_i_care_about)
		fields["regions_im_in"] = bin(self.regions_im_in)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		self.regions_i_care_about = structs.read_bit_vector(stream)
		self.regions_im_in = structs.read_bit_vector(stream)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		structs.write_bit_vector(stream, self.regions_i_care_about)
		structs.write_bit_vector(stream, self.regions_im_in)


class NetMessagePlayerPage(NetMessage):
	CLASS_INDEX = 0x03b4
	
	unload: bool
	uoid: Uoid
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		if self.unload:
			fields["unload"] = repr(self.unload)
		fields["uoid"] = repr(self.uoid)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		(unload,) = structs.read_exact(stream, 1)
		self.unload = bool(unload)
		self.uoid = Uoid.from_stream(stream)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		stream.write(bytes([self.unload]))
		self.uoid.write(stream)


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
	
	async def send_propagat_buffer(self, message: NetMessage) -> None:
		logger.debug("Sending propagate buffer: %r", message)
		
		with io.BytesIO() as stream:
			message.write(stream)
			buffer = stream.getvalue()
		
		await self.write_message(2, PROPAGATE_BUFFER_HEADER.pack(message.class_index, len(buffer)) + buffer)
	
	@base.message_handler(2)
	async def receive_propagate_buffer(self) -> None:
		buffer_type, buffer_length = await self.read_unpack(PROPAGATE_BUFFER_HEADER)
		
		with io.BytesIO(await self.read(buffer_length)) as buffer:
			message = NetMessage.from_stream(buffer)
			extra_data = buffer.read()
		
		if buffer_type != message.class_index:
			raise base.ProtocolError(f"PropagateBuffer type 0x{buffer_type:>04x} doesn't match class index in serialized message: 0x{message.class_index:>04x}")
		
		logger.debug("Received propagate buffer: %r", message)
		
		unsupported_flags = message.flags & ~NetMessageFlags.all_handled
		if unsupported_flags:
			logger.warning("PropagateBuffer message %s has flags set that we can't handle yet: %r", message.class_description, unsupported_flags)
		if message.protocol_version is not None:
			logger.warning("PropagateBuffer message %s contains protocol version: %r", message.class_description, message.protocol_version)
		if message.context is not None:
			logger.warning("PropagateBuffer message %s contains context: %d", message.class_description, message.context)
		if message.trans_id is not None:
			logger.warning("PropagateBuffer message %s contains transaction ID: %d", message.class_description, message.trans_id)
		if message.account_uuid is not None:
			logger.warning("PropagateBuffer message %s contains account UUID: %s", message.class_description, message.account_uuid)
		if extra_data:
			logger.warning("PropagateBuffer message %s has extra trailing data: %r", message.class_description, extra_data)
		
		await message.handle(self)
