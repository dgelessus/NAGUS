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
from . import configuration
from . import sdl
from . import state
from . import structs


logger = logging.getLogger(__name__)
logger_join = logger.getChild("join")
logger_net_message = logger.getChild("net_message")
logger_net_message_unhandled = logger_net_message.getChild("unhandled")
logger_ping = logger.getChild("ping")
logger_pl_message = logger.getChild("pl_message")
logger_sdl = logger.getChild("sdl")
logger_sdl_change = logger_sdl.getChild("change")
logger_test_and_set = logger.getChild("test_and_set")


CONNECT_DATA = struct.Struct("<I16s16s")

PING_REQUEST = struct.Struct("<I")
PING_REPLY = struct.Struct("<I")
JOIN_AGE_REQUEST = struct.Struct("<II16sI")
JOIN_AGE_REPLY = struct.Struct("<II")
PROPAGATE_BUFFER_HEADER = struct.Struct("<II")

PLASMA_MESSAGE_HEADER_END = struct.Struct("<dI")
LOAD_CLONE_MESSAGE_MID = struct.Struct("<II??")
PARTICLE_KILL_MESSAGE = struct.Struct("<ffB")

NET_MESSAGE_HEADER = struct.Struct("<HI")
NET_MESSAGE_VERSION = struct.Struct("<BB")
NET_MESSAGE_TIME_SENT = struct.Struct("<II")
NET_MESSAGE_STREAMED_OBJECT_HEADER = struct.Struct("<IBI")
NET_MESSAGE_SDL_STATE = struct.Struct("<???")
NET_MESSAGE_LOAD_CLONE_BOOLS = struct.Struct("<???")

COMPRESSION_THRESHOLD = 256

AGE_SDL_HOOK_NAME = b"AgeSDLHook"


class UnknownClassIndexError(Exception):
	pass


class GroupId(object):
	class Flags(structs.IntFlag):
		constant = 1 << 0
		local = 1 << 1
	
	location: structs.Location
	flags: "GroupId.Flags"
	
	def __init__(self, id: structs.Location, flags: "GroupId.Flags") -> None:
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
		location = structs.Location.from_stream(stream)
		(flags,) = structs.read_exact(stream, 1)
		return cls(location, GroupId.Flags(flags))
	
	def write(self, stream: typing.BinaryIO) -> None:
		self.location.write(stream)
		stream.write(bytes([self.flags]))


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
	class Flags(structs.IntFlag):
		waiting_for_link_query = 1 << 0
		indirect_member = 1 << 1
		request_p2p = 1 << 2
		waiting_for_challenge_response = 1 << 3
		is_server = 1 << 4
		allow_time_out = 1 << 5
	
	flags: "MemberInfo.Flags"
	client_info: ClientInfo
	avatar_uoid: structs.Uoid
	
	def __init__(self, flags: "MemberInfo.Flags", client_info: ClientInfo, avatar_uoid: structs.Uoid) -> None:
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
		avatar_uoid = structs.Uoid.from_stream(stream)
		return cls(MemberInfo.Flags(flags), client_info, avatar_uoid)
	
	def write(self, stream: typing.BinaryIO) -> None:
		stream.write(structs.UINT32.pack(self.flags))
		self.client_info.write(stream)
		self.avatar_uoid.write(stream)


class PlasmaMessageFlags(structs.IntFlag):
	broadcast_by_type = 1 << 0
	broadcast_by_sender_unused = 1 << 1
	propagate_to_children = 1 << 2
	broadcast_by_exact_type = 1 << 3
	propagate_to_modifiers = 1 << 4
	clear_after_broadcast = 1 << 5
	net_propagate = 1 << 6
	net_sent = 1 << 7
	net_use_relevance_regions = 1 << 8
	net_force = 1 << 9
	net_non_local = 1 << 10
	local_propagate = 1 << 11
	message_watch = 1 << 12
	net_start_cascade = 1 << 13
	net_allow_inter_age = 1 << 14
	net_send_unreliable = 1 << 15
	ccr_send_to_all_players = 1 << 16
	net_created_remotely = 1 << 17
	
	all_expected = (
		broadcast_by_type
		| propagate_to_children
		| broadcast_by_exact_type
		| propagate_to_modifiers
		| net_propagate
		| net_sent
		| net_use_relevance_regions
		| net_force
		| local_propagate
		| net_allow_inter_age
		| net_send_unreliable
		| ccr_send_to_all_players
	)


class PlasmaMessage(object):
	CLASS_INDEX = 0x0202
	
	class_index: int
	sender: typing.Optional[structs.Uoid]
	receivers: typing.List[typing.Optional[structs.Uoid]]
	timestamp: float
	flags: PlasmaMessageFlags
	
	@classmethod
	def __init_subclass__(cls, **kwargs: typing.Any) -> None:
		super().__init_subclass__(**kwargs)
		
		if cls.CLASS_INDEX in PLASMA_MESSAGE_CLASSES_BY_INDEX:
			raise ValueError(f"Attempted to create PlasmaMessage subclass {cls.__qualname__} with class index 0x{cls.CLASS_INDEX:>04x} which is already used by existing subclass {PLASMA_MESSAGE_CLASSES_BY_INDEX[cls.CLASS_INDEX].__qualname__}")
		
		PLASMA_MESSAGE_CLASSES_BY_INDEX[cls.CLASS_INDEX] = cls
	
	def __init__(self) -> None:
		super().__init__()
		
		self.class_index = type(self).CLASS_INDEX
		self.sender = None
		self.receivers = []
		self.timestamp = 0.0
		self.flags = PlasmaMessageFlags.local_propagate
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = collections.OrderedDict()
		
		if self.sender is not None:
			fields["sender"] = str(self.sender)
		
		if self.receivers:
			receivers_rep = str(self.receivers[0])
			# For some reason,
			# the receivers list often contains multiple identical UOIDs,
			# so collapse those for readability.
			last_receiver = self.receivers[0]
			count = 1
			for receiver in self.receivers[1:]:
				if receiver == last_receiver:
					count += 1
				else:
					if count > 1:
						receivers_rep += f"*{count}"
					
					receivers_rep += f", {receiver}"
					last_receiver = receiver
					count = 1
			
			if count > 1:
				receivers_rep += f"*{count}"
			
			fields["receivers"] = f"[{receivers_rep}]"
		
		if self.timestamp != 0.0:
			fields["timestamp"] = str(self.timestamp)
		
		fields["flags"] = repr(self.flags)
		
		return fields
	
	def __repr__(self) -> str:
		joined_fields = ", ".join(name + "=" + value for name, value in self.repr_fields().items())
		return f"<{self.class_description}: {joined_fields}>"
	
	@classmethod
	def from_class_index(cls, class_index: int) -> "typing.Optional[PlasmaMessage]":
		if class_index == structs.NULL_CLASS_INDEX:
			return None
		
		try:
			clazz = PLASMA_MESSAGE_CLASSES_BY_INDEX[class_index]
		except KeyError:
			raise UnknownClassIndexError(f"Cannot create/read plMessage with unknown class index 0x{class_index:>04x}")
		else:
			self = clazz()
			self.class_index = class_index
			return self
	
	@property
	def class_description(self) -> str:
		name = type(self).__qualname__
		if self.class_index != type(self).CLASS_INDEX:
			name += " subclass"
		return f"{name} (0x{self.class_index:>04x})"
	
	def read(self, stream: typing.BinaryIO) -> None:
		self.sender = structs.Uoid.key_from_stream(stream)
		
		(receiver_count,) = structs.stream_unpack(stream, structs.INT32)
		self.receivers = []
		for _ in range(receiver_count):
			self.receivers.append(structs.Uoid.key_from_stream(stream))
		
		self.timestamp, flags = structs.stream_unpack(stream, PLASMA_MESSAGE_HEADER_END)
		self.flags = PlasmaMessageFlags(flags)
	
	@classmethod
	def creatable_from_stream(cls, stream: typing.BinaryIO) -> "typing.Optional[PlasmaMessage]":
		(class_index,) = structs.stream_unpack(stream, structs.CLASS_INDEX)
		self = cls.from_class_index(class_index)
		
		if self is not None:
			self.read(stream)
		
		return self
	
	def write(self, stream: typing.BinaryIO) -> None:
		structs.Uoid.key_to_stream(self.sender, stream)
		
		stream.write(structs.INT32.pack(len(self.receivers)))
		for receiver in self.receivers:
			structs.Uoid.key_to_stream(receiver, stream)
		
		stream.write(PLASMA_MESSAGE_HEADER_END.pack(self.timestamp, self.flags))
	
	@classmethod
	def creatable_to_stream(cls, message: "typing.Optional[PlasmaMessage]", stream: typing.BinaryIO) -> None:
		if message is None:
			stream.write(b"\x00\x80")
		else:
			stream.write(structs.CLASS_INDEX.pack(message.class_index))
			message.write(stream)


PLASMA_MESSAGE_CLASSES_BY_INDEX: typing.Dict[int, typing.Type[PlasmaMessage]] = {
	PlasmaMessage.CLASS_INDEX: PlasmaMessage,
}


class LoadCloneMessage(PlasmaMessage):
	CLASS_INDEX = 0x0253
	
	clone: typing.Optional[structs.Uoid]
	requestor: typing.Optional[structs.Uoid]
	originating_ki_number: int
	user_data: int
	is_valid: bool
	is_loading: bool
	trigger_message: typing.Optional[PlasmaMessage]
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["clone"] = str(self.clone)
		fields["requestor"] = str(self.requestor)
		fields["originating_ki_number"] = repr(self.originating_ki_number)
		if self.user_data != 0:
			fields["user_data"] = repr(self.user_data)
		if not self.is_valid:
			fields["is_valid"] = repr(self.is_valid)
		fields["is_loading"] = repr(self.is_loading)
		if self.trigger_message is not None:
			fields["trigger_message"] = repr(self.trigger_message)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		
		self.clone = structs.Uoid.key_from_stream(stream)
		self.requestor = structs.Uoid.key_from_stream(stream)
		(self.originating_ki_number, self.user_data, self.is_valid, self.is_loading) = structs.stream_unpack(stream, LOAD_CLONE_MESSAGE_MID)
		
		if not self.is_valid:
			raise ValueError(f"plLoadCloneMsg has is_valid field set to {self.is_valid!r}, this should never happen!")
		
		self.trigger_message = PlasmaMessage.creatable_from_stream(stream)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		
		structs.Uoid.key_to_stream(self.clone, stream)
		structs.Uoid.key_to_stream(self.requestor, stream)
		stream.write(LOAD_CLONE_MESSAGE_MID.pack(self.originating_ki_number, self.user_data, self.is_valid, self.is_loading))
		PlasmaMessage.creatable_to_stream(self.trigger_message, stream)


class LoadAvatarMessage(LoadCloneMessage):
	CLASS_INDEX = 0x03b1
	
	is_player: bool
	spawn_point: typing.Optional[structs.Uoid]
	initial_task: typing.Any # TODO
	user_string: bytes
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["is_player"] = repr(self.is_player)
		if self.spawn_point:
			fields["spawn_point"] = str(self.spawn_point)
		if self.initial_task:
			fields["initial_task"] = repr(self.initial_task)
		if self.user_string:
			fields["user_string"] = repr(self.user_string)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		
		(is_player,) = stream.read(1)
		self.is_player = bool(is_player)
		self.spawn_point = structs.Uoid.key_from_stream(stream)
		(initial_task_present,) = stream.read(1)
		if initial_task_present:
			raise NotImplementedError("Cannot parse plAvTask yet") # TODO
		else:
			self.initial_task = None
		self.user_string = structs.read_safe_string(stream)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		
		stream.write(bytes([self.is_player]))
		structs.Uoid.key_to_stream(self.spawn_point, stream)
		if self.initial_task is None:
			stream.write(b"\x00")
		else:
			stream.write(b"\x01")
			raise NotImplementedError("Cannot write plAvTask yet") # TODO
		structs.write_safe_string(stream, self.user_string)


class ServerReplyMessage(PlasmaMessage):
	class Type(structs.IntEnum):
		uninitialized = -1
		deny = 0
		affirm = 1
	
	CLASS_INDEX = 0x026f
	
	type: "ServerReplyMessage.Type"
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["type"] = repr(self.type)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		(typ,) = structs.stream_unpack(stream, structs.INT32)
		self.type = ServerReplyMessage.Type(typ)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		stream.write(structs.INT32.pack(self.type))


class ParticleTransferMessage(PlasmaMessage):
	CLASS_INDEX = 0x0333
	
	particle_system: typing.Optional[structs.Uoid]
	transfer_count: int
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["particle_system"] = str(self.particle_system)
		fields["transfer_count"] = repr(self.transfer_count)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		self.particle_system = structs.Uoid.key_from_stream(stream)
		(self.transfer_count,) = structs.stream_unpack(stream, structs.UINT16)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		structs.Uoid.key_to_stream(self.particle_system, stream)
		stream.write(structs.UINT16.pack(self.transfer_count))


class ParticleKillMessage(PlasmaMessage):
	class Flags(structs.IntFlag):
		immortal_only = 1 << 0
		percentage = 1 << 1
	
	CLASS_INDEX = 0x0334
	
	amount: float
	time_left: float
	kill_flags: "ParticleKillMessage.Flags"
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["amount"] = repr(self.amount)
		fields["time_left"] = repr(self.time_left)
		if self.kill_flags:
			fields["kill_flags"] = repr(self.kill_flags)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		(self.amount, self.time_left, flags) = structs.stream_unpack(stream, PARTICLE_KILL_MESSAGE)
		self.kill_flags = ParticleKillMessage.Flags(flags)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		stream.write(PARTICLE_KILL_MESSAGE.pack(self.amount, self.time_left, self.kill_flags))


class NetMessageFlags(structs.IntFlag):
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
		| has_game_message_receivers
		| echo_back_to_sender
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
		| route_to_all_players
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
	def __init_subclass__(cls, **kwargs: typing.Any) -> None:
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
		return f"<{self.class_description}: {joined_fields}>"
	
	@property
	def class_description(self) -> str:
		name = type(self).__qualname__
		if self.class_index != type(self).CLASS_INDEX:
			name += " subclass"
		return f"{name} (0x{self.class_index:>04x})"
	
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
		logger_net_message_unhandled.error("Don't know how to handle plNetMessage of class %s - ignoring", self.class_description)
		logger_net_message_unhandled.debug("Unhandled plNetMessage: %r", self)


NET_MESSAGE_CLASSES_BY_INDEX: typing.Dict[int, typing.Type[NetMessage]] = {
	NetMessage.CLASS_INDEX: NetMessage,
}


class NetMessageRoomsList(NetMessage):
	CLASS_INDEX = 0x0263
	
	rooms: typing.List[typing.Tuple[structs.Location, bytes]]
	
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
			location = structs.Location.from_stream(stream)
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
	class Flags(structs.IntFlag):
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
		logger_sdl.debug("Avatar %d requesting initial game state", self.ki_number)
		
		if self.rooms:
			logger_sdl.warning("Ignoring non-empty rooms list in game state request: %r", self.rooms)
		
		count = 0
		
		# TODO Send currently loaded clones
		
		# Send saved SDL state for the age instance (AgeSDLHook).
		try:
			age_sdl_node_id = await connection.find_age_sdl_node()
		except state.VaultNodeNotFound:
			# No age SDL saved for this instance -
			# assuming that this age has no AgeSDLHook.
			pass
		else:
			# TODO Support global SDL and such
			age_sdl_node_data = await connection.server_state.fetch_vault_node(age_sdl_node_id)
			
			if age_sdl_node_data.string64_1 != connection.client_state.age_file_name:
				raise base.ProtocolError(f"SDL node {age_sdl_node_id} has SDL name {age_sdl_node_data.string64_1!r}, which doesn't match the age file name {connection.client_state.age_file_name!r}")
			
			if age_sdl_node_data.blob_1:
				count += 1
				# TODO It's probably not enough to send the SDL blob from the vault as-is!
				age_sdl_blob = age_sdl_node_data.blob_1
				await connection.send_initial_age_sdl(age_sdl_blob)
		
		# Find and send saved SDL states for objects within the age instance.
		async for uoid, _, sdl_blob in connection.server_state.find_object_sdl_states(connection.client_state.age_node_id):
			logger_sdl.debug("Sending initial state for object %s", uoid)
			object_state_message = NetMessageSDLState()
			object_state_message.uoid = uoid
			object_state_message.compress_and_set_data(sdl_blob)
			object_state_message.is_initial_state = True
			object_state_message.persist_on_server = True
			object_state_message.is_avatar_state = False
			await connection.send_propagate_buffer(object_state_message)
			count += 1
		
		# TODO Send non-persistent object states from the running game server
		
		logger_sdl.debug("Sent/queued %d initial state messages", count)
		initial_age_state_sent = NetMessageInitialAgeStateSent()
		initial_age_state_sent.initial_sdl_state_count = count
		await connection.send_propagate_buffer(initial_age_state_sent)


class NetMessageObject(NetMessage):
	CLASS_INDEX = 0x0268
	
	uoid: structs.Uoid
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["uoid"] = str(self.uoid)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		
		self.uoid = structs.Uoid.from_stream(stream)
	
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
	
	def compress_and_set_data(self, data: bytes, compression_type: typing.Optional[CompressionType] = None) -> None:
		if compression_type is not None:
			self.compression_type = compression_type
		elif len(data) > COMPRESSION_THRESHOLD:
			self.compression_type = CompressionType.zlib
		else:
			self.compression_type = CompressionType.none
		
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
		
		stream.write(NET_MESSAGE_STREAMED_OBJECT_HEADER.pack(self.uncompressed_length, self.compression_type.value, len(self.stream_data)))
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
	
	TRIGGER_DATA = b"\t\x00TrigState\x01\x00\x00\x00\x00\t\xf0\xab\x8d\x96\x98\x98\x9a\x8d\x9a\x9b\x02\x01"
	UNTRIGGER_DATA = b"\t\x00TrigState\x01\x00\x00\x00\x01\t\xf0\xab\x8d\x96\x98\x98\x9a\x8d\x9a\x9b\x02\x00"
	
	async def handle(self, connection: "GameConnection") -> None:
		data = self.decompress_data()
		
		if self.lock_request:
			if data != type(self).TRIGGER_DATA:
				logger_test_and_set.warning("Unexpected stream data for TestAndSet trigger request! Ignoring the stream data and locking as usual.")
			
			try:
				lock_owner = connection.client_state.locks[self.uoid]
			except KeyError:
				logger_test_and_set.debug("Avatar %d locking %s", connection.client_state.ki_number, self.uoid)
				connection.client_state.locks[self.uoid] = connection.client_state.ki_number
				reply_code = ServerReplyMessage.Type.affirm
			else:
				logger_test_and_set.debug("Avatar %d was denied lock of %s - already locked by %d", connection.client_state.ki_number, self.uoid, lock_owner)
				reply_code = ServerReplyMessage.Type.deny
			
			server_reply_message = ServerReplyMessage()
			server_reply_message.receivers.append(self.uoid)
			server_reply_message.type = reply_code
			
			with io.BytesIO() as message_stream:
				PlasmaMessage.creatable_to_stream(server_reply_message, message_stream)
				message_buffer = message_stream.getvalue()
			
			net_game_message = NetMessageGameMessage()
			net_game_message.delivery_time = structs.ZERO_DATETIME
			net_game_message.compress_and_set_data(message_buffer)
			await connection.send_propagate_buffer(net_game_message)
		else:
			if data != type(self).UNTRIGGER_DATA:
				logger_test_and_set.warning("Unexpected stream data for TestAndSet un-trigger request! Ignoring the stream data and unlocking as usual.")
			
			try:
				lock_owner = connection.client_state.locks[self.uoid]
			except KeyError:
				logger_test_and_set.warning("Avatar %d tried to unlock %s even though it's not locked - ignoring", connection.client_state.ki_number, self.uoid)
			else:
				if lock_owner == connection.client_state.ki_number:
					del connection.client_state.locks[self.uoid]
				else:
					logger_test_and_set.warning("Avatar %d tried to unlock %s even though it's locked by %d - ignoring", connection.client_state.ki_number, self.uoid, lock_owner)


def _apply_parsed_change_to_blob(current_blob: bytes, change_header: sdl.SDLStreamHeader, change_record: sdl.GuessedSDLRecord) -> bytes:
	"""Parse the SDL blob ``current_blob``,
	apply the changed values from the already parsed SDL record ``change_record`` onto it,
	and return the SDL blob with the change applied.
	"""
	
	with io.BytesIO(current_blob) as stream:
		current_header = sdl.SDLStreamHeader.from_stream(stream)
		
		if current_header.uoid is not None:
			logger_sdl_change.info("Currently saved SDL blob header contains UOID: %s", current_header.uoid)
		
		if change_header != current_header:
			raise ValueError(f"Mismatched state descriptors when applying change - current SDL blob has header {change_header}, but the change SDL blob has header {current_header})")
		
		current_record = sdl.GuessedSDLRecord()
		current_record.read(stream)
		
		if logger_sdl_change.isEnabledFor(logging.DEBUG):
			logger_sdl_change.debug("Parsed currently saved SDL blob:")
			for line in current_record.as_multiline_str():
				logger_sdl_change.debug("%s", line.replace("\t", "    "))
		
		lookahead = stream.read(16)
	
	if lookahead:
		raise ValueError(f"Currently saved SDL blob has trailing data (probably not parsed correctly): {lookahead!r}")
	
	changed_record = current_record.with_change(change_record)
	
	if logger_sdl_change.isEnabledFor(logging.DEBUG):
		logger_sdl_change.debug("Changed state:")
		for line in changed_record.as_multiline_str():
			logger_sdl_change.debug("%s", line.replace("\t", "    "))
	
	with io.BytesIO() as stream:
		current_header.write(stream)
		changed_record.write(stream)
		changed_blob = stream.getvalue()
	
	# Check that the changed blob can be re-parsed successfully.
	
	with io.BytesIO(changed_blob) as stream:
		roundtripped_header = sdl.SDLStreamHeader.from_stream(stream)
		if roundtripped_header != current_header:
			raise ValueError(f"Re-parsed changed SDL blob header ({change_header}) doesn't match original header ({current_header})")
		
		roundtripped_record = sdl.GuessedSDLRecord()
		roundtripped_record.read(stream)
		if roundtripped_record != changed_record:
			if logger_sdl_change.isEnabledFor(logging.DEBUG):
				logger_sdl_change.debug("Re-parsed changed blob:")
				for line in roundtripped_record.as_multiline_str():
					logger_sdl_change.debug("%s", line.replace("\t", "    "))
			
			raise ValueError("Re-parsed changed SDL blob body doesn't match original body")
		
		lookahead = stream.read(16)
	
	if lookahead:
		raise ValueError(f"Re-parsed changed SDL blob has trailing data (probably not parsed correctly): {lookahead!r}")
	
	return changed_blob


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
	
	async def handle(self, connection: "GameConnection") -> None:
		if logger_sdl.isEnabledFor(logging.DEBUG):
			if self.persist_on_server:
				desc = "persistent"
			else:
				desc = "temporary"
			
			if isinstance(self, NetMessageSDLStateBroadcast):
				desc += ", broadcast"
			
			if NetMessageFlags.new_sdl_state in self.flags:
				desc += ", new"
			
			if self.is_avatar_state:
				desc += ", avatar"
			
			logger_sdl.debug("Received SDL change (%s) for %s", desc, self.uoid)
		
		if self.is_initial_state:
			logger_sdl.warning("SDL state message from client has initial state flag set")
		
		if self.persist_on_server:
			if self.is_avatar_state:
				logger_sdl.warning("Avatar state message has persist on server flag set - it will be saved, but will probably be unusable on future link-ins!")
			if self.uoid.clone_ids is not None:
				logger_sdl.warning("Clone object state message has persist on server flag set - it will be saved, but will probably be unusable on future link-ins!")
		
		if NetMessageFlags.echo_back_to_sender in self.flags:
			await connection.send_propagate_buffer(self)
		
		blob_data = self.decompress_data()
		with io.BytesIO(blob_data) as stream:
			try:
				header = sdl.SDLStreamHeader.from_stream(stream)
			except ValueError:
				logger_sdl.warning("Failed to parse SDL change blob header - this change will not be saved or sent to new clients", exc_info=True)
				return
			
			if header.uoid is not None:
				logger_sdl.info("SDL change blob header contains UOID: %s", header.uoid)
			
			record = sdl.GuessedSDLRecord()
			try:
				record.read(stream)
			except ValueError:
				logger_sdl.error("Failed to parse SDL change blob body for %r v%d - this state will not be saved or sent to new clients", header.descriptor_name, header.descriptor_version, exc_info=True)
				return
			
			if logger_sdl.isEnabledFor(logging.DEBUG):
				logger_sdl.debug("Parsed SDL change for %r v%d:", header.descriptor_name, header.descriptor_version)
				for line in record.as_multiline_str():
					logger_sdl.debug("%s", line.replace("\t", "    "))
			
			lookahead = stream.read(16)
		
		if lookahead:
			logger_sdl.warning("SDL change blob for %r v%d has trailing data (probably not parsed correctly): %r", header.descriptor_name, header.descriptor_version, lookahead)
		else:
			try:
				with io.BytesIO() as stream_out:
					header.write(stream_out)
					record.write(stream_out)
					roundtripped_data = stream_out.getvalue()
			except Exception:
				logger_sdl.warning("Failed to write parsed SDL change for %r v%d back to a blob", header.descriptor_name, header.descriptor_version, exc_info=True)
			else:
				if roundtripped_data != blob_data:
					logger_sdl.warning("Failed to roundtrip SDL change blob for %r v%d", header.descriptor_name, header.descriptor_version)
					logger_sdl.debug("Original change blob data: %r", blob_data)
					logger_sdl.debug("Parsed and rewritten change blob data: %r", roundtripped_data)
		
		if self.uoid.object_name == AGE_SDL_HOOK_NAME:
			# Special treatment for AgeSDLHook:
			# save in the appropriate vault node
			# and not together with all the other per-instance SDL states.
			
			if not self.persist_on_server:
				logger_sdl.warning("AgeSDLHook change doesn't have persist on server flag set - will save anyway")
			if self.is_avatar_state:
				logger_sdl.warning("AgeSDLHook change is marked as an avatar state")
			if self.uoid != connection.client_state.age_sdl_hook_uoid:
				logger_sdl.warning("Received an AgeSDLHook change with UOID %s, which doesn't match the expected UOID %s for this age's AgeSDLHook", self.uoid, connection.client_state.age_sdl_hook_uoid)
			
			try:
				age_sdl_node_id = await connection.find_age_sdl_node()
			except state.VaultNodeNotFound:
				logger_sdl.info("Age instance SDL vault node not found - creating one...")
				age_sdl_node_id = await connection.server_state.create_vault_node(state.VaultNodeData(creator_account_uuid=connection.client_state.account_uuid, creator_id=connection.client_state.ki_number, node_type=state.VaultNodeType.sdl, int32_1=0, string64_1=connection.client_state.age_file_name))
				await connection.server_state.add_vault_node_ref(state.VaultNodeRef(connection.client_state.age_info_node_id, age_sdl_node_id))
			
			age_sdl_node_data = await connection.server_state.fetch_vault_node(age_sdl_node_id)
			age_sdl_blob = age_sdl_node_data.blob_1
			
			if age_sdl_blob:
				try:
					changed_blob = _apply_parsed_change_to_blob(age_sdl_blob, header, record)
				except ValueError:
					logger_sdl.error("Failed to apply change to SDL blob from age instance SDL vault node", exc_info=True)
					return
			else:
				logger_sdl.info("Age instance SDL vault node is empty - will initialize it with the blob sent by the client")
				changed_blob = blob_data
			
			await connection.server_state.update_vault_node(age_sdl_node_id, state.VaultNodeData(blob_1=changed_blob), uuid.uuid4())
		elif self.persist_on_server:
			# Handle all other persistent object states.
			# These currently go directly to the database.
			# TODO Cache parsed object SDL states in memory for easier updating?
			
			try:
				existing_blob = await connection.server_state.fetch_object_sdl_state(connection.client_state.age_node_id, self.uoid, header.descriptor_name)
			except state.ObjectStateNotFound:
				logger_sdl.debug("No existing SDL blob found for object %s - will initialize it with the blob sent by the client", self.uoid)
				if NetMessageFlags.new_sdl_state not in self.flags:
					logger_sdl.info("Client sent a non-new SDL change for object %s, but no SDL blob has been saved yet for that object - will use this SDL blob as the initial state", self.uoid)
				
				changed_blob = blob_data
			else:
				if NetMessageFlags.new_sdl_state in self.flags:
					logger_sdl.info("Client sent a new SDL state for object %s, but there's already a saved SDL blob for that object - will treat the new blob as a change and apply it to the saved one", self.uoid)
				
				try:
					changed_blob = _apply_parsed_change_to_blob(existing_blob, header, record)
				except ValueError:
					logger_sdl.error("Failed to apply change to existing saved SDL blob for object %s", self.uoid, exc_info=True)
					return
			
			await connection.server_state.save_object_sdl_state(connection.client_state.age_node_id, self.uoid, header.descriptor_name, changed_blob)
		else:
			pass # TODO Save in memory for sending to other clients later


class NetMessageSDLStateBroadcast(NetMessageSDLState):
	CLASS_INDEX = 0x0329
	
	async def handle(self, connection: "GameConnection") -> None:
		await super().handle(connection)
		
		# TODO Forward to other clients


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
	
	def inspect_wrapped_message(self, connection: "GameConnection") -> None:
		try:
			message_data = self.decompress_data()
			with io.BytesIO(message_data) as message_stream:
				(class_index,) = structs.stream_unpack(message_stream, structs.CLASS_INDEX)
				try:
					message = PlasmaMessage.from_class_index(class_index)
				except UnknownClassIndexError:
					message = PlasmaMessage()
					message.class_index = class_index
				
				if message is None:
					raise ValueError("plMessage is nullptr, this should never happen!")
				
				message.read(message_stream)
				extra_data = message_stream.read()
		except (EOFError, UnknownClassIndexError, ValueError) as exc:
			logger_pl_message.error("Failed to parse plMessage. Ignoring and forwarding anyway...", exc_info=exc)
		else:
			logger_pl_message.debug("Parsed plMessage: %r", message)
			
			# Check that clone messages are wrapped in the correct network message class.
			if isinstance(self, NetMessageLoadClone):
				# FIXME This really belongs into NetMessageLoadClone.handle, but we don't have the parsed message there...
				if isinstance(message, LoadCloneMessage):
					if isinstance(message, LoadAvatarMessage):
						if message.is_player != self.is_player:
							logger_pl_message.warning("plLoadAvatarMsg %s is_player (%r) doesn't match containing network load clone message's is_player (%r)", message.class_description, message.is_player, self.is_player)
						
						if message.spawn_point is not None:
							connection.client_state.try_find_age_sequence_prefix(message.spawn_point.location)
					elif self.is_player:
						logger_pl_message.warning("plLoadCloneMsg %s isn't an avatar message, but containing network load clone message's is_player is set", message.class_description)
					
					if message.is_loading != self.is_loading:
						logger_pl_message.warning("plLoadCloneMsg %s is_loading (%r) doesn't match containing network load clone message's is_loading (%r)", message.class_description, message.is_loading, self.is_loading)
				else:
					logger_pl_message.warning("plMessage %s isn't a clone message, but is wrapped in a network load clone message", message.class_description)
			elif isinstance(message, LoadCloneMessage):
				logger_pl_message.warning("plLoadCloneMsg %s is wrapped in a non-clone network message %s", message.class_description, self.class_description)
			
			# Double-check the containing network game message's has_game_message_receivers flag
			# and check for nullptr receivers.
			game_message_receiver: typing.Optional[structs.Uoid] = None
			for i, receiver in enumerate(message.receivers):
				if receiver is None:
					logger_pl_message.warning("plMessage %s has nullptr receiver at index %d", message.class_description, i)
				elif game_message_receiver is None and receiver.location.sequence_number != 0 and structs.Location.Flags.reserved not in receiver.location.flags:
					game_message_receiver = receiver
			
			if game_message_receiver is None and NetMessageFlags.has_game_message_receivers in self.flags:
				logger_pl_message.warning("plMessage %s has no (non-virtual, non-reserved) receivers, but the containing network game message has the has_game_message_receivers flag set", message.class_description)
			elif game_message_receiver is not None and NetMessageFlags.has_game_message_receivers not in self.flags:
				logger_pl_message.warning("plMessage %s has at least one (non-virtual, non-reserved) receiver (e. g. %r), but the containing network game message doesn't have the has_game_message_receivers flag set", message.class_description, game_message_receiver)
			
			# Check for unexpected flags,
			# possibly depending on the message class
			# and the containing network message flags.
			unexpected_flags = message.flags & ~PlasmaMessageFlags.all_expected
			if unexpected_flags:
				logger_pl_message.warning("plMessage %s has flags set that we don't expect for net-propagated messages: %r", message.class_description, unexpected_flags)
			if PlasmaMessageFlags.net_propagate not in message.flags:
				logger_pl_message.warning("plMessage %s was sent over the network, but doesn't have the net_propagate flag set", message.class_description)
			if PlasmaMessageFlags.net_sent in message.flags and not (PlasmaMessageFlags.net_force in message.flags or PlasmaMessageFlags.ccr_send_to_all_players in message.flags):
				logger_pl_message.warning("plMessage %s was sent over the network more than once, but doesn't have any force-sending flags set", message.class_description)
			if (PlasmaMessageFlags.net_use_relevance_regions in message.flags) != (NetMessageFlags.use_relevance_regions in self.flags):
				logger_pl_message.warning("plMessage %s net_use_relevance_regions flag (%r) doesn't match containing network game message's use_relevance_regions flag (%r)", message.class_description, PlasmaMessageFlags.net_use_relevance_regions in message.flags, NetMessageFlags.use_relevance_regions in self.flags)
			if (PlasmaMessageFlags.net_allow_inter_age in message.flags) != (NetMessageFlags.inter_age_routing in self.flags):
				logger_pl_message.warning("plMessage %s net_allow_inter_age flag (%r) doesn't match containing network game message's inter_age_routing flag (%r)", message.class_description, PlasmaMessageFlags.net_allow_inter_age in message.flags, NetMessageFlags.inter_age_routing in self.flags)
			if (PlasmaMessageFlags.net_send_unreliable in message.flags) == (NetMessageFlags.needs_reliable_send in self.flags):
				logger_pl_message.warning("plMessage %s net_send_unreliable flag (%r) doesn't match containing network game message's needs_reliable_send flag (%r)", message.class_description, PlasmaMessageFlags.net_send_unreliable in message.flags, NetMessageFlags.needs_reliable_send in self.flags)
			if (PlasmaMessageFlags.ccr_send_to_all_players in message.flags) != (NetMessageFlags.route_to_all_players in self.flags):
				logger_pl_message.warning("plMessage %s ccr_send_to_all_players flag (%r) doesn't match containing network game message's route_to_all_players flag (%r)", message.class_description, PlasmaMessageFlags.ccr_send_to_all_players in message.flags, NetMessageFlags.route_to_all_players in self.flags)
			
			if extra_data:
				logger_pl_message.debug("plMessage %s has extra trailing data: %r", message.class_description, extra_data)
	
	async def handle(self, connection: "GameConnection") -> None:
		# If full plMessage parsing is enabled,
		# decompress and parse the message and run some consistency checks on it.
		# This can never truly fail for now -
		# any parse errors and failed checks are logged,
		# but don't block forwarding/echoing of the message.
		if connection.server_state.config.server_game_parse_pl_messages == configuration.ParsePlMessages.known:
			self.inspect_wrapped_message(connection)
		
		# TODO Set kNetNonLocal flag on the wrapped plMessage before forwarding?
		# TODO Forward to other clients
		
		if NetMessageFlags.echo_back_to_sender in self.flags:
			await connection.send_propagate_buffer(self)
		
		if NetMessageFlags.route_to_all_players in self.flags:
			logger_pl_message.warning("Ignoring route_to_all_players flag - CCR broadcast messages not supported yet")


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
	
	async def handle(self, connection: "GameConnection") -> None:
		logger_pl_message.warning("Directed game messages not supported yet - treating it like a broadcast message for now")
		await super().handle(connection)


class NetMessageLoadClone(NetMessageGameMessage):
	CLASS_INDEX = 0x03b3
	
	uoid: structs.Uoid
	is_player: bool
	is_loading: bool
	is_initial_state: bool
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["uoid"] = str(self.uoid)
		if not self.is_player:
			fields["is_player"] = repr(self.is_player)
		if not self.is_loading:
			fields["is_loading"] = repr(self.is_loading)
		if self.is_initial_state:
			fields["is_initial_state"] = repr(self.is_initial_state)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		self.uoid = structs.Uoid.from_stream(stream)
		self.is_player, self.is_loading, self.is_initial_state = structs.stream_unpack(stream, NET_MESSAGE_LOAD_CLONE_BOOLS)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		self.uoid.write(stream)
		stream.write(NET_MESSAGE_LOAD_CLONE_BOOLS.pack(self.is_player, self.is_loading, self.is_initial_state))
	
	def inspect_player_load_avatar_message(self, connection: "GameConnection") -> None:
		try:
			message_data = self.decompress_data()
			with io.BytesIO(message_data) as message_stream:
				(class_index,) = structs.stream_unpack(message_stream, structs.CLASS_INDEX)
				if class_index != LoadAvatarMessage.CLASS_INDEX:
					logger_pl_message.warning("Player load clone message contains a plMessage of class 0x%04x instead of plLoadAvatarMsg - cannot determine age sequence prefix, but ignoring and forwarding anyway...", class_index)
					return
				
				message = LoadAvatarMessage()
				message.class_index = class_index
				message.read(message_stream)
		except (EOFError, UnknownClassIndexError, ValueError) as exc:
			logger_pl_message.error("Failed to parse player load clone message - cannot determine age sequence prefix, but ignoring and forwarding anyway...", exc_info=exc)
		else:
			logger_pl_message.debug("Parsed player plLoadAvatarMsg: %r", message)
			
			# The client sometimes first sends a plLoadAvatarMsg without a spawn point,
			# followed very soon by another almost identical plLoadAvatarMsg that does have a spawn point.
			if message.spawn_point is not None:
				connection.client_state.try_find_age_sequence_prefix(message.spawn_point.location)
			else:
				logger_pl_message.debug("Player plLoadAvatarMsg spawn point is nullptr - cannot determine age sequence prefix yet")
	
	async def handle(self, connection: "GameConnection") -> None:
		logger_pl_message.debug("Received load clone message for %s, player? %r, loading? %r", self.uoid, self.is_player, self.is_loading)
		if self.is_initial_state:
			logger_pl_message.warning("Load clone message from client has initial state flag set")
		
		# In "parse only if necessary" mode,
		# skip parsing the wrapped plMessage,
		# unless it's a player plLoadAvatarMsg
		# and we still need to determine the age sequence prefix.
		# (If full plMessage parsing is enabled,
		# the age sequence prefix is determined in NetMessageGameMessage.inspect_wrapped_message instead.)
		if (
			connection.server_state.config.server_game_parse_pl_messages == configuration.ParsePlMessages.necessary
			and self.is_player
			and not hasattr(connection.client_state, "age_sequence_prefix")
		):
			self.inspect_player_load_avatar_message(connection)
		
		await super().handle(connection)


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
	uoid: structs.Uoid
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		if self.unload:
			fields["unload"] = repr(self.unload)
		fields["uoid"] = str(self.uoid)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		(unload,) = structs.read_exact(stream, 1)
		self.unload = bool(unload)
		self.uoid = structs.Uoid.from_stream(stream)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		stream.write(bytes([self.unload]))
		self.uoid.write(stream)


class GameClientState(object):
	# TODO A lot of this needs to be moved into some kind of shared state when implementing actual multiplayer.
	mcp_id: int
	age_node_id: int
	age_info_node_id: int
	age_instance_uuid: uuid.UUID
	age_file_name: str
	age_sequence_prefix: int
	account_uuid: uuid.UUID
	ki_number: int
	age_sdl_hook_uoid: structs.Uoid
	locks: typing.Dict[structs.Uoid, int]
	
	def __init__(self) -> None:
		super().__init__()
		
		# Other attributes are intentionally left unset at first.
		# They will be set in the join_age_request handler shortly after the client has connected.
		self.locks = {}
	
	def try_find_age_sequence_prefix(self, location: structs.Location) -> bool:
		"""Try to derive the client's age sequence prefix from the given location.
		
		The client never directly sends the age sequence prefix,
		but the server needs to know it so it can send the AgeSDLHook in reply to the GameStateRequest.
		Normally the server would look up the sequence prefix in the corresponding .age file,
		but I don't want to implement that yet
		(and also would like to avoid depending on age-specific data files as much as possible).
		So as a workaround,
		wait for a message from the client that contains a non-global location
		and extract the sequence prefix from there.
		
		This is currently done based on the plLoadAvatarMsg for the player's avatar,
		because that's been the most reliable solution so far.
		The client always sends at least one such message before requesting the game state,
		and at least one of those messages has its spawn point field set,
		which refers to an object in the age that the player is linking to.
		
		:return: ``True`` if :attr:`age_sequence_prefix` was set successfully from the location,
			or ``False`` if the location didn't contain a usable prefix.
		"""
		
		if location.sequence_number not in range(0x21, 0x80000000) or structs.Location.Flags.reserved in location.flags:
			logger_sdl.debug("Attempted to derive the age's sequence prefix from a global or reserved location: %s", location)
			return False
		
		(self.age_sequence_prefix, _) = structs.split_sequence_number(location.sequence_number)
		logger_sdl.debug("Received message containing a non-global location %r - assuming that this age's sequence prefix is %d", location, self.age_sequence_prefix)
		
		self.age_sdl_hook_uoid = structs.Uoid()
		self.age_sdl_hook_uoid.location = structs.Location(structs.make_sequence_number(self.age_sequence_prefix, -2), structs.Location.Flags.built_in)
		self.age_sdl_hook_uoid.load_mask = 0xff
		self.age_sdl_hook_uoid.class_type = 0x0001 # Scene Object
		self.age_sdl_hook_uoid.object_id = 1
		self.age_sdl_hook_uoid.object_name = AGE_SDL_HOOK_NAME
		self.age_sdl_hook_uoid.clone_ids = None
		
		return True


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
			logger_join.warning("Client connected to game server with non-zero UUIDs: account UUID %s, age instance UUID %s", account_uuid, age_instance_uuid)
	
	@base.message_handler(0)
	async def ping_request(self) -> None:
		(ping_time,) = await self.read_unpack(PING_REQUEST)
		logger_ping.debug("Ping request: time %d", ping_time)
		await self.write_message(0, PING_REPLY.pack(ping_time))
	
	async def join_age_reply(self, trans_id: int, result: base.NetError) -> None:
		logger_join.debug("Sending join age reply: transaction ID %d, result %r", trans_id, result)
		await self.write_message(1, JOIN_AGE_REPLY.pack(trans_id, result))
	
	@base.message_handler(1)
	async def join_age_request(self) -> None:
		trans_id, mcp_id, account_uuid, ki_number = await self.read_unpack(JOIN_AGE_REQUEST)
		account_uuid = uuid.UUID(bytes_le=account_uuid)
		logger_join.debug("Join age request: transaction ID %d, MCP ID %d, account UUID %s, KI number %d", trans_id, mcp_id, account_uuid, ki_number)
		
		try:
			self.client_state.mcp_id
		except AttributeError:
			pass
		else:
			await self.join_age_reply(trans_id, base.NetError.invalid_parameter)
			raise base.ProtocolError(f"Client attempted to join another age instance ({mcp_id}) with an already established game server connection (for age instance {self.client_state.mcp_id})")
		
		# As a shortcut for now,
		# the auth server sends the age node ID as the MCP ID.
		# This might change in the future.
		age_node_id = mcp_id
		
		try:
			age_node_data = await self.server_state.fetch_vault_node(age_node_id)
		except state.VaultNodeNotFound:
			await self.join_age_reply(trans_id, base.NetError.age_not_found)
			raise base.ProtocolError(f"Client attempted to join age instance with nonexistant ID {age_node_id}")
		
		logger_join.debug("Age node: %s", age_node_data)
		
		if age_node_data.node_type != state.VaultNodeType.age:
			await self.join_age_reply(trans_id, base.NetError.age_not_found)
			raise base.ProtocolError(f"Client attempted to join age instance with ID {age_node_id}, which is of type {age_node_data.node_type}, not Age")
		
		age_instance_uuid = age_node_data.uuid_1
		if age_instance_uuid is None:
			await self.join_age_reply(trans_id, base.NetError.internal_error)
			raise base.ProtocolError(f"Age instance with ID {age_node_id} has no age instance UUID")
		
		age_file_name = age_node_data.string64_1
		if age_file_name is None:
			await self.join_age_reply(trans_id, base.NetError.internal_error)
			raise base.ProtocolError(f"Age instance with ID {age_node_id} has no age file name")
		
		try:
			age_info_node_id = await self.server_state.find_unique_vault_node(state.VaultNodeData(node_type=state.VaultNodeType.age_info), parent_id=age_node_id)
		except state.VaultNodeNotFound:
			await self.join_age_reply(trans_id, base.NetError.vault_node_not_found)
			raise base.ProtocolError(f"Age instance with ID {age_node_id} has no Age Info child node")
		
		age_info_node_data = await self.server_state.fetch_vault_node(age_info_node_id)
		logger_join.debug("Age Info node: %s", age_info_node_data)
		
		if age_info_node_data.uint32_1 != age_node_id:
			await self.join_age_reply(trans_id, base.NetError.internal_error)
			raise base.ProtocolError(f"Age Info node {age_info_node_id} has its Age ID field set to {age_info_node_data.uint32_1}, but its parent Age node is actually {age_node_id}")
		
		if age_info_node_data.uuid_1 != age_instance_uuid:
			await self.join_age_reply(trans_id, base.NetError.internal_error)
			raise base.ProtocolError(f"Age Info node {age_info_node_id} has age instance UUID {age_info_node_data.uuid_1}, but its parent Age node {age_node_id} has age instance UUID {age_instance_uuid}")
		
		if age_info_node_data.string64_2 != age_file_name:
			await self.join_age_reply(trans_id, base.NetError.internal_error)
			raise base.ProtocolError(f"Age Info node {age_info_node_id} has age file name {age_info_node_data.string64_2!r}, but its parent Age node {age_node_id} has age file name {age_file_name!r}")
		
		self.client_state.mcp_id = mcp_id
		self.client_state.age_node_id = age_node_id
		self.client_state.age_info_node_id = age_info_node_id
		self.client_state.age_instance_uuid = age_instance_uuid
		self.client_state.age_file_name = age_file_name
		self.client_state.account_uuid = account_uuid
		self.client_state.ki_number = ki_number
		logger_join.info("Account %s, avatar %d joined age instance %d: %r, %r (%d) %r, %s", account_uuid, ki_number, mcp_id, age_file_name, age_info_node_data.string64_4, age_info_node_data.int32_1, age_info_node_data.string64_3, age_instance_uuid)
		
		await self.join_age_reply(trans_id, base.NetError.success)
	
	async def send_propagate_buffer(self, message: NetMessage, *, set_time_sent: bool = True) -> None:
		if set_time_sent:
			message.flags |= NetMessageFlags.has_time_sent
			message.time_sent = datetime.datetime.now(tz=datetime.timezone.utc)
		
		logger_net_message.debug("Sending propagate buffer: %r", message)
		
		with io.BytesIO() as stream:
			message.write(stream)
			buffer = stream.getvalue()
		
		await self.write_message(2, PROPAGATE_BUFFER_HEADER.pack(message.class_index, len(buffer)) + buffer)
	
	async def find_age_sdl_node(self) -> int:
		return await self.server_state.find_unique_vault_node(
			state.VaultNodeData(node_type=state.VaultNodeType.sdl),
			parent_id=self.client_state.age_info_node_id,
		)
	
	async def send_initial_age_sdl(self, age_sdl_blob: bytes) -> None:
		"""Send the given SDL blob to the client as the initial state for the AgeSDLHook.
		
		Can only be called if the :attr:`GameClientState.age_sequence_prefix` has been initialized.
		"""
		
		logger_sdl.debug("Sending initial state for AgeSDLHook %s", self.client_state.age_sdl_hook_uoid)
		age_sdl_hook_state = NetMessageSDLState()
		age_sdl_hook_state.uoid = self.client_state.age_sdl_hook_uoid
		age_sdl_hook_state.compress_and_set_data(age_sdl_blob)
		age_sdl_hook_state.is_initial_state = True
		age_sdl_hook_state.persist_on_server = True
		age_sdl_hook_state.is_avatar_state = False
		await self.send_propagate_buffer(age_sdl_hook_state)
	
	@base.message_handler(2)
	async def receive_propagate_buffer(self) -> None:
		buffer_type, buffer_length = await self.read_unpack(PROPAGATE_BUFFER_HEADER)
		
		with io.BytesIO(await self.read(buffer_length)) as buffer:
			message = NetMessage.from_stream(buffer)
			extra_data = buffer.read()
		
		if buffer_type != message.class_index:
			raise base.ProtocolError(f"PropagateBuffer type 0x{buffer_type:>04x} doesn't match class index in serialized message: 0x{message.class_index:>04x}")
		
		logger_net_message.debug("Received propagate buffer: %r", message)
		
		# Check for unsupported and unexpected flags,
		# possibly depending on the message class.
		unsupported_flags = message.flags & ~NetMessageFlags.all_handled
		if unsupported_flags:
			logger_net_message.warning("PropagateBuffer message %s has flags set that we can't handle yet: %r", message.class_description, unsupported_flags)
		if NetMessageFlags.has_game_message_receivers in message.flags and not isinstance(message, NetMessageGameMessage):
			logger_net_message.warning("PropagateBuffer message %s has has_game_message_receivers flag set even though it's not a game message", message.class_description)
		if NetMessageFlags.echo_back_to_sender in message.flags and not isinstance(message, (NetMessageGameMessage, NetMessageSDLState)):
			logger_net_message.warning("PropagateBuffer message %s has echo_back_to_sender flag set even though it's not a game message or SDL state", message.class_description)
		if NetMessageFlags.new_sdl_state in message.flags and not isinstance(message, NetMessageSDLState):
			logger_net_message.warning("PropagateBuffer message %s has new_sdl_state flag set even though it's not an SDL state message", message.class_description)
		if NetMessageFlags.initial_age_state_request in message.flags and not isinstance(message, NetMessageGameStateRequest):
			logger_net_message.warning("PropagateBuffer message %s has initial_age_state_request flag set even though it's not a game state request message", message.class_description)
		if NetMessageFlags.use_relevance_regions in message.flags and not isinstance(message, (NetMessageSDLState, NetMessageGameMessage)):
			logger_net_message.warning("PropagateBuffer message %s has use_relevance_regions flag set even though it's not an SDL state or game message", message.class_description)
		if NetMessageFlags.inter_age_routing in message.flags and not isinstance(message, NetMessageGameMessageDirected):
			logger_net_message.warning("PropagateBuffer message %s has inter_age_routing flag set even though it's not a directed game message", message.class_description)
		if NetMessageFlags.route_to_all_players in message.flags and type(message) != NetMessageGameMessage:
			logger_net_message.warning("PropagateBuffer message %s has route_to_all_players flag set even though its class is not plNetMsgGameMessage", message.class_description)
		
		if message.protocol_version is not None:
			logger_net_message.warning("PropagateBuffer message %s contains protocol version: %r", message.class_description, message.protocol_version)
		if message.context is not None:
			logger_net_message.warning("PropagateBuffer message %s contains context: %d", message.class_description, message.context)
		if message.trans_id is not None:
			logger_net_message.warning("PropagateBuffer message %s contains transaction ID: %d", message.class_description, message.trans_id)
		if message.account_uuid is not None:
			logger_net_message.warning("PropagateBuffer message %s contains account UUID: %s", message.class_description, message.account_uuid)
		if extra_data:
			logger_net_message.warning("PropagateBuffer message %s has extra trailing data: %r", message.class_description, extra_data)
		
		await message.handle(self)
