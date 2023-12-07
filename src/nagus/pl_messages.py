# This file is part of NAGUS, an Uru Live server that is not very good.
# Copyright (C) 2023 dgelessus
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


"""Parsed representations of various :cpp:class:`plMessage`\\s that the client may send over the :ref:`game server <game_server>`.

Most of these :cpp:class:`plMessage` types don't need to be parsed or serialized by the server during normal operation.
"""


import abc
import collections
import enum
import struct
import typing

from . import structs


Point3 = typing.Tuple[float, float, float]


PLASMA_MESSAGE_HEADER_END = struct.Struct("<dI")
LOAD_CLONE_MESSAGE_MID = struct.Struct("<II??")
ANIM_COMMAND_MESSAGE_MID = struct.Struct("<fffffff")
AVATAR_SEEK_MESSAGE_TARGET = struct.Struct("<3f3f")
AVATAR_SEEK_MESSAGE_MID_1 = struct.Struct("<f?")
AVATAR_SEEK_MESSAGE_MID_2 = struct.Struct("<H?B")
AVATAR_BRAIN_GENERIC_MESSAGE = struct.Struct("<Ii?f??f")
PICKED_EVENT_FOOTER = struct.Struct("<?3f")
FACING_EVENT_FOOTER = struct.Struct("<f?")
ACTIVATE_EVENT = struct.Struct("<??")
MULTI_STAGE_EVENT_HEADER = struct.Struct("<ii")
COOP_EVENT = struct.Struct("<IH")
OFFER_LINKING_BOOK_EVENT_FOOTER = struct.Struct("<iI")
NOTIFY_MESSAGE_HEADER = struct.Struct("<ifiI")
LINK_EFFECTS_TRIGGER_MESSAGE_HEADER = struct.Struct("<i?")
PARTICLE_KILL_MESSAGE = struct.Struct("<ffB")
INPUT_INTERFACE_MANAGER_MESSAGE_HEADER = struct.Struct("<BI")


class UnknownClassIndexError(Exception):
	pass


class MessageFlags(structs.IntFlag):
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


class Message(object):
	CLASS_INDEX = 0x0202
	
	class_index: int
	sender: typing.Optional[structs.Uoid]
	receivers: typing.List[typing.Optional[structs.Uoid]]
	timestamp: float
	flags: MessageFlags
	
	@classmethod
	def __init_subclass__(cls, **kwargs: typing.Any) -> None:
		super().__init_subclass__(**kwargs)
		
		if cls.CLASS_INDEX in MESSAGE_CLASSES_BY_INDEX:
			raise ValueError(f"Attempted to create PlasmaMessage subclass {cls.__qualname__} with class index 0x{cls.CLASS_INDEX:>04x} which is already used by existing subclass {MESSAGE_CLASSES_BY_INDEX[cls.CLASS_INDEX].__qualname__}")
		
		MESSAGE_CLASSES_BY_INDEX[cls.CLASS_INDEX] = cls
	
	def __init__(self) -> None:
		super().__init__()
		
		self.class_index = type(self).CLASS_INDEX
		self.sender = None
		self.receivers = []
		self.timestamp = 0.0
		self.flags = MessageFlags.local_propagate
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = collections.OrderedDict()
		
		if self.sender is not None:
			fields["sender"] = str(self.sender)
		
		if self.receivers:
			if self.sender is not None and self.receivers[0] == self.sender:
				receivers_rep = "<sender>"
			else:
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
					
					if self.sender is not None and self.receivers[0] == self.sender:
						receivers_rep += ", <sender>"
					else:
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
	def from_class_index(cls, class_index: int) -> "typing.Optional[Message]":
		if class_index == structs.NULL_CLASS_INDEX:
			return None
		
		try:
			clazz = MESSAGE_CLASSES_BY_INDEX[class_index]
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
		self.flags = MessageFlags(flags)
	
	@classmethod
	def creatable_from_stream(cls, stream: typing.BinaryIO) -> "typing.Optional[Message]":
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
	def creatable_to_stream(cls, message: "typing.Optional[Message]", stream: typing.BinaryIO) -> None:
		if message is None:
			stream.write(b"\x00\x80")
		else:
			stream.write(structs.CLASS_INDEX.pack(message.class_index))
			message.write(stream)


MESSAGE_CLASSES_BY_INDEX: typing.Dict[int, typing.Type[Message]] = {
	Message.CLASS_INDEX: Message,
}


class LoadCloneMessage(Message):
	CLASS_INDEX = 0x0253
	
	clone: typing.Optional[structs.Uoid]
	requestor: typing.Optional[structs.Uoid]
	originating_ki_number: int
	user_data: int
	is_valid: bool
	is_loading: bool
	trigger_message: typing.Optional[Message]
	
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
		
		self.trigger_message = Message.creatable_from_stream(stream)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		
		structs.Uoid.key_to_stream(self.clone, stream)
		structs.Uoid.key_to_stream(self.requestor, stream)
		stream.write(LOAD_CLONE_MESSAGE_MID.pack(self.originating_ki_number, self.user_data, self.is_valid, self.is_loading))
		Message.creatable_to_stream(self.trigger_message, stream)


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


class EnableMessage(Message):
	class Commands(structs.IntFlag):
		disable = 1 << 0
		enable = 1 << 1
		drawable = 1 << 2
		physical = 1 << 3
		audible = 1 << 4
		all = 1 << 5
		by_type = 1 << 6
	
	CLASS_INDEX = 0x0254
	
	commands: "EnableMessage.Commands"
	types: int
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["commands"] = repr(self.commands)
		if self.types:
			fields["types"] = "{" + ", ".join(f"0x{x:>04x}" for x in structs.bit_numbers_from_int(self.types)) + "}"
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		self.commands = EnableMessage.Commands(structs.read_bit_vector(stream))
		self.types = structs.read_bit_vector(stream)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		structs.write_bit_vector(stream, self.commands)
		structs.write_bit_vector(stream, self.types)


class ServerReplyMessage(Message):
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


class MessageWithCallbacks(Message):
	CLASS_INDEX = 0x0283
	
	callbacks: typing.List[typing.Optional[Message]]
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		if self.callbacks:
			fields["callbacks"] = repr(self.callbacks)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		(callback_count,) = structs.stream_unpack(stream, structs.UINT32)
		self.callbacks = []
		for _ in range(callback_count):
			self.callbacks.append(Message.creatable_from_stream(stream))
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		stream.write(structs.UINT32.pack(len(self.callbacks)))
		for callback in self.callbacks:
			Message.creatable_to_stream(callback, stream)


class AnimationCommandMessage(MessageWithCallbacks):
	class Commands(structs.IntFlag):
		continue_ = 1 << 0
		stop = 1 << 1
		set_looping = 1 << 2
		unset_looping = 1 << 3
		set_begin = 1 << 4
		set_end = 1 << 5
		set_loop_end = 1 << 6
		set_loop_begin = 1 << 7
		set_speed = 1 << 8
		go_to_time = 1 << 9
		set_backwards = 1 << 10
		set_forwards = 1 << 11
		toggle_state = 1 << 12
		add_callbacks = 1 << 13
		remove_callbacks = 1 << 14
		go_to_begin = 1 << 15
		go_to_end = 1 << 16
		go_to_loop_begin = 1 << 17
		go_to_loop_end = 1 << 18
		increment_forward = 1 << 19
		increment_backward = 1 << 20
		run_forward = 1 << 21
		run_backward = 1 << 22
		play_to_time = 1 << 23
		play_to_percentage = 1 << 24
		fast_forward = 1 << 25
		go_to_percent = 1 << 26
	
	CLASS_INDEX = 0x0206
	
	commands: "AnimationCommandMessage.Commands"
	begin: float
	end: float
	loop_begin: float
	loop_end: float
	speed: float
	speed_change_rate: float
	time: float
	animation_name: bytes
	loop_name: bytes
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["commands"] = repr(self.commands)
		if self.begin != 0.0:
			fields["begin"] = repr(self.begin)
		if self.end != 0.0:
			fields["end"] = repr(self.end)
		if self.loop_begin != 0.0:
			fields["loop_begin"] = repr(self.loop_begin)
		if self.loop_end != 0.0:
			fields["loop_end"] = repr(self.loop_end)
		if self.speed != 0.0:
			fields["speed"] = repr(self.speed)
		if self.speed_change_rate != 0.0:
			fields["speed_change_rate"] = repr(self.speed_change_rate)
		if self.time != 0.0:
			fields["time"] = repr(self.time)
		if self.animation_name:
			fields["animation_name"] = repr(self.animation_name)
		if self.loop_name:
			fields["loop_name"] = repr(self.loop_name)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		self.commands = AnimationCommandMessage.Commands(structs.read_bit_vector(stream))
		(
			self.begin,
			self.end,
			self.loop_begin,
			self.loop_end,
			self.speed,
			self.speed_change_rate,
			self.time,
		) = structs.stream_unpack(stream, ANIM_COMMAND_MESSAGE_MID)
		self.animation_name = structs.read_safe_string(stream)
		self.loop_name = structs.read_safe_string(stream)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		structs.write_bit_vector(stream, self.commands)
		stream.write(ANIM_COMMAND_MESSAGE_MID.pack(
			self.begin,
			self.end,
			self.loop_begin,
			self.loop_end,
			self.speed,
			self.speed_change_rate,
			self.time,
		))
		structs.write_safe_string(stream, self.animation_name)
		structs.write_safe_string(stream, self.loop_name)


class AvatarMessage(Message):
	CLASS_INDEX = 0x0297


class AvatarTaskMessage(AvatarMessage):
	CLASS_INDEX = 0x0298
	
	task: typing.Any # TODO
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		if self.task is not None:
			fields["task"] = repr(self.task)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		(task_present,) = stream.read(1)
		if task_present:
			raise NotImplementedError("Cannot parse plAvTask yet") # TODO
		else:
			self.task = None
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		if self.task is None:
			stream.write(b"\x00")
		else:
			stream.write(b"\x01")
			raise NotImplementedError("Cannot write plAvTask yet") # TODO


class AvatarSeekMessage(AvatarTaskMessage):
	class AlignmentType(structs.IntEnum):
		handle = 0
		handle_at_animation_end = 1
		handle_with_world_origin = 2
		bone = 3
		bone_at_animation_end = 4
	
	class SeekFlags(structs.IntFlag):
		unforce_3rd_person_on_finish = 1 << 0
		force_3rd_person_on_start = 1 << 1
		no_warp_on_timeout = 1 << 2
		rotation_only = 1 << 3
	
	CLASS_INDEX = 0x0299
	
	seek_point: typing.Union[structs.Uoid, typing.Tuple[Point3, Point3]]
	duration: float
	smart_seek: bool
	animation_name: bytes
	alignment_type: "AvatarSeekMessage.AlignmentType"
	no_seek: bool
	seek_flags: "AvatarSeekMessage.SeekFlags"
	finish_key: typing.Optional[structs.Uoid]
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["seek_point"] = str(self.seek_point)
		fields["duration"] = repr(self.duration)
		fields["smart_seek"] = repr(self.smart_seek)
		if self.animation_name:
			fields["animation_name"] = repr(self.animation_name)
		if self.alignment_type != AvatarSeekMessage.AlignmentType.handle:
			fields["alignment_type"] = repr(self.alignment_type)
		if self.no_seek:
			fields["no_seek"] = repr(self.no_seek)
		if self.seek_flags:
			fields["seek_flags"] = repr(self.seek_flags)
		if self.finish_key is not None:
			fields["finish_key"] = str(self.finish_key)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		
		seek_point = structs.Uoid.key_from_stream(stream)
		if seek_point is None:
			pos_x, pos_y, pos_z, look_x, look_y, look_z = structs.stream_unpack(stream, AVATAR_SEEK_MESSAGE_TARGET)
			self.seek_point = (pos_x, pos_y, pos_z), (look_x, look_y, look_z)
		else:
			self.seek_point = seek_point
		
		self.duration, self.smart_seek = structs.stream_unpack(stream, AVATAR_SEEK_MESSAGE_MID_1)
		self.animation_name = structs.read_safe_string(stream)
		alignment_type, self.no_seek, seek_flags = structs.stream_unpack(stream, AVATAR_SEEK_MESSAGE_MID_2)
		self.alignment_type = AvatarSeekMessage.AlignmentType(alignment_type)
		self.seek_flags = AvatarSeekMessage.SeekFlags(seek_flags)
		self.finish_key = structs.Uoid.key_from_stream(stream)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		
		if isinstance(self.seek_point, structs.Uoid):
			structs.Uoid.key_to_stream(self.seek_point, stream)
		else:
			pos, look = self.seek_point
			structs.Uoid.key_to_stream(None, stream)
			stream.write(AVATAR_SEEK_MESSAGE_TARGET.pack(*pos, *look))
		
		stream.write(AVATAR_SEEK_MESSAGE_MID_1.pack(self.duration, self.smart_seek))
		structs.write_safe_string(stream, self.animation_name)
		stream.write(AVATAR_SEEK_MESSAGE_MID_2.pack(self.alignment_type, self.no_seek, self.seek_flags))
		structs.Uoid.key_to_stream(self.finish_key, stream)


class AvatarBrainGenericMessage(AvatarMessage):
	class Type(structs.IntEnum):
		next_stage = 0
		previous_stage = 1
		go_to_stage = 2
		set_loop_count = 3
	
	CLASS_INDEX = 0x038f
	
	type: "AvatarBrainGenericMessage.Type"
	stage: int
	set_time: bool
	time: float
	set_direction: bool
	direction: bool
	transition_time: float
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["type"] = repr(self.type)
		fields["stage"] = repr(self.stage)
		fields["set_time"] = repr(self.set_time)
		fields["time"] = repr(self.time)
		fields["set_direction"] = repr(self.set_direction)
		fields["direction"] = repr(self.direction)
		fields["transition_time"] = repr(self.transition_time)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		(
			message_type,
			self.stage,
			self.set_time,
			self.time,
			self.set_direction,
			self.direction,
			self.transition_time,
		) = structs.stream_unpack(stream, AVATAR_BRAIN_GENERIC_MESSAGE)
		self.type = AvatarBrainGenericMessage.Type(message_type)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		stream.write(AVATAR_BRAIN_GENERIC_MESSAGE.pack(
			self.type,
			self.stage,
			self.set_time,
			self.time,
			self.set_direction,
			self.direction,
			self.transition_time,
		))


class NotifyEvent(abc.ABC):
	TYPE: typing.ClassVar[int]
	
	@abc.abstractmethod
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		return collections.OrderedDict()
	
	def __repr__(self) -> str:
		joined_fields = ", ".join(name + "=" + value for name, value in self.repr_fields().items())
		return f"{type(self).__name__}({joined_fields})"
	
	@classmethod
	@abc.abstractmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "NotifyEvent":
		raise NotImplementedError()
	
	@classmethod
	def from_stream_with_type(cls, stream: typing.BinaryIO) -> "NotifyEvent":
		(typenum,) = structs.stream_unpack(stream, structs.INT32)
		if typenum == CollisionEvent.TYPE:
			return CollisionEvent.from_stream(stream)
		elif typenum == PickedEvent.TYPE:
			return PickedEvent.from_stream(stream)
		elif typenum == VariableEvent.TYPE:
			return VariableEvent.from_stream(stream)
		elif typenum == FacingEvent.TYPE:
			return FacingEvent.from_stream(stream)
		elif typenum == ContainedEvent.TYPE:
			return ContainedEvent.from_stream(stream)
		elif typenum == ActivateEvent.TYPE:
			return ActivateEvent.from_stream(stream)
		elif typenum == CallbackEvent.TYPE:
			return CallbackEvent.from_stream(stream)
		elif typenum == ResponderStateEvent.TYPE:
			return ResponderStateEvent.from_stream(stream)
		elif typenum == MultiStageEvent.TYPE:
			return MultiStageEvent.from_stream(stream)
		elif typenum == SpawnedEvent.TYPE:
			return SpawnedEvent.from_stream(stream)
		elif typenum == CoopEvent.TYPE:
			return CoopEvent.from_stream(stream)
		elif typenum == OfferLinkingBookEvent.TYPE:
			return OfferLinkingBookEvent.from_stream(typenum)
		else:
			raise NotImplementedError(f"Unsupported proEventData type: {typenum}")
	
	@abc.abstractmethod
	def write(self, stream: typing.BinaryIO) -> None:
		raise NotImplementedError()
	
	def write_with_type(self, stream: typing.BinaryIO) -> None:
		stream.write(structs.INT32.pack(type(self).TYPE))
		self.write(stream)


class CollisionEvent(NotifyEvent):
	TYPE = 1
	
	enter: bool
	hitter: typing.Optional[structs.Uoid]
	hittee: typing.Optional[structs.Uoid]
	
	def __init__(self, enter: bool, hitter: typing.Optional[structs.Uoid], hittee: typing.Optional[structs.Uoid]) -> None:
		super().__init__()
		
		self.enter = enter
		self.hitter = hitter
		self.hittee = hittee
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["enter"] = repr(self.enter)
		if self.hitter is not None:
			fields["hitter"] = str(self.hitter)
		if self.hittee is not None:
			fields["hittee"] = str(self.hittee)
		return fields
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "CollisionEvent":
		(enter,) = structs.read_exact(stream, 1)
		hitter = structs.Uoid.key_from_stream(stream)
		hittee = structs.Uoid.key_from_stream(stream)
		return cls(bool(enter), hitter, hittee)
	
	def write(self, stream: typing.BinaryIO) -> None:
		stream.write(bytes([self.enter]))
		structs.Uoid.key_to_stream(self.hitter, stream)
		structs.Uoid.key_to_stream(self.hittee, stream)


class PickedEvent(NotifyEvent):
	TYPE = 2
	
	picker: typing.Optional[structs.Uoid]
	picked: typing.Optional[structs.Uoid]
	enabled: bool
	hit_point: Point3
	
	def __init__(self, picker: typing.Optional[structs.Uoid], picked: typing.Optional[structs.Uoid], enabled: bool, hit_point: Point3) -> None:
		super().__init__()
		
		self.picker = picker
		self.picked = picked
		self.enabled = enabled
		self.hit_point = hit_point
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		if self.picker is not None:
			fields["picker"] = str(self.picker)
		if self.picked is not None:
			fields["picked"] = str(self.picked)
		fields["enabled"] = repr(self.enabled)
		if any(self.hit_point):
			fields["hit_point"] = repr(self.hit_point)
		return fields
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "PickedEvent":
		picker = structs.Uoid.key_from_stream(stream)
		picked = structs.Uoid.key_from_stream(stream)
		enabled, hit_x, hit_y, hit_z = structs.stream_unpack(stream, PICKED_EVENT_FOOTER)
		return cls(picker, picked, bool(enabled), (hit_x, hit_y, hit_z))
	
	def write(self, stream: typing.BinaryIO) -> None:
		structs.Uoid.key_to_stream(self.picker, stream)
		structs.Uoid.key_to_stream(self.picked, stream)
		stream.write(PICKED_EVENT_FOOTER.pack(self.enabled, *self.hit_point))


class VariableEvent(NotifyEvent):
	class DataType(enum.Enum):
		float = 1
		key = 2
		int = 3
		null = 4
	
	TYPE = 4
	
	name: bytes
	data_type: "VariableEvent.DataType"
	value: typing.Union[int, float, structs.Uoid, None]
	key: typing.Optional[structs.Uoid]
	
	def __init__(self, name: bytes, data_type: "VariableEvent.DataType", value: typing.Union[int, float, structs.Uoid, None]) -> None:
		super().__init__()
		
		self.name = name
		self.data_type = data_type
		self.value = value
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["name"] = repr(self.name)
		fields["data_type"] = repr(self.data_type)
		fields["value"] = str(self.value)
		return fields
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "VariableEvent":
		name = structs.read_safe_string(stream)
		(data_type_int,) = structs.stream_unpack(stream, structs.INT32)
		data_type = VariableEvent.DataType(data_type_int)
		(number,) = structs.stream_unpack(
			stream,
			structs.FLOAT32 if data_type == VariableEvent.DataType.float else structs.INT32,
		)
		key = structs.Uoid.key_from_stream(stream)
		
		if data_type not in {VariableEvent.DataType.float, VariableEvent.DataType.int} and number != 0:
			raise ValueError(f"proVariableEventData has non-number type {data_type.name}, but its number value isn't zero: {number}")
		elif data_type != VariableEvent.DataType.key and key is not None:
			raise ValueError(f"proVariableEventData has non-key type {data_type.name}, but its key isn't nullptr: {key}")
		
		value: typing.Union[int, float, structs.Uoid, None]
		if data_type in {VariableEvent.DataType.float, VariableEvent.DataType.int}:
			value = number
		elif data_type == VariableEvent.DataType.key:
			value = key
		elif data_type == VariableEvent.DataType.null:
			value = None
		else:
			raise AssertionError(f"Unhandled proVariableEventData type: {data_type.name}")
		
		return cls(name, data_type, value)
	
	def write(self, stream: typing.BinaryIO) -> None:
		structs.write_safe_string(stream, self.name)
		stream.write(structs.INT32.pack(self.data_type.value))
		
		if self.data_type == VariableEvent.DataType.float:
			if not isinstance(self.value, (int, float)):
				raise ValueError(f"VariableEvent has type float, but its value isn't a number: {self.value}")
			stream.write(structs.FLOAT32.pack(self.value))
		elif self.data_type == VariableEvent.DataType.int:
			if not isinstance(self.value, int):
				raise ValueError(f"VariableEvent has type int, but its value isn't an int: {self.value}")
			stream.write(structs.INT32.pack(self.value))
		else:
			if isinstance(self.value, (int, float)):
				raise ValueError(f"VariableEvent has non-number type {self.data_type.name}, but its value is a number: {self.value}")
			stream.write(b"\x00\x00\x00\x00")
		
		key: typing.Optional[structs.Uoid]
		if self.data_type == VariableEvent.DataType.key:
			if self.value is not None and not isinstance(self.value, structs.Uoid):
				raise ValueError(f"VariableEvent has type key, but its value isn't a key or None: {self.value}")
			key = self.value
		else:
			if isinstance(self.value, structs.Uoid):
				raise ValueError(f"VariableEvent has non-key type {self.data_type.name}, but its value is an UOID: {self.value}")
			key = None
		structs.Uoid.key_to_stream(self.key, stream)


class FacingEvent(NotifyEvent):
	TYPE = 5
	
	facer: typing.Optional[structs.Uoid]
	facee: typing.Optional[structs.Uoid]
	dot_product: float
	enabled: bool
	
	def __init__(self, facer: typing.Optional[structs.Uoid], facee: typing.Optional[structs.Uoid], dot_product: float, enabled: bool) -> None:
		super().__init__()
		
		self.facer = facer
		self.facee = facee
		self.dot_product = dot_product
		self.enabled = enabled
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		if self.facer is not None:
			fields["facer"] = str(self.facer)
		if self.facee is not None:
			fields["facee"] = str(self.facee)
		fields["dot_product"] = repr(self.dot_product)
		fields["enabled"] = repr(self.enabled)
		return fields
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "FacingEvent":
		facer = structs.Uoid.key_from_stream(stream)
		facee = structs.Uoid.key_from_stream(stream)
		dot_product, enabled = structs.stream_unpack(stream, FACING_EVENT_FOOTER)
		return cls(facer, facee, dot_product, enabled)
	
	def write(self, stream: typing.BinaryIO) -> None:
		structs.Uoid.key_to_stream(self.facer, stream)
		structs.Uoid.key_to_stream(self.facee, stream)
		stream.write(FACING_EVENT_FOOTER.pack(self.dot_product, self.enabled))


class ContainedEvent(NotifyEvent):
	TYPE = 6
	
	contained: typing.Optional[structs.Uoid]
	container: typing.Optional[structs.Uoid]
	entering: bool
	
	def __init__(self, contained: typing.Optional[structs.Uoid], container: typing.Optional[structs.Uoid], entering: bool) -> None:
		super().__init__()
		
		self.contained = contained
		self.container = container
		self.entering = entering
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		if self.contained is not None:
			fields["contained"] = str(self.contained)
		if self.container is not None:
			fields["container"] = str(self.container)
		fields["entering"] = repr(self.entering)
		return fields
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "ContainedEvent":
		contained = structs.Uoid.key_from_stream(stream)
		container = structs.Uoid.key_from_stream(stream)
		(entering,) = structs.read_exact(stream, 1)
		return cls(contained, container, bool(entering))
	
	def write(self, stream: typing.BinaryIO) -> None:
		structs.Uoid.key_to_stream(self.contained, stream)
		structs.Uoid.key_to_stream(self.container, stream)
		stream.write(bytes([self.entering]))


class ActivateEvent(NotifyEvent):
	TYPE = 7
	
	activate: bool
	
	def __init__(self, activate: bool) -> None:
		super().__init__()
		
		self.activate = activate
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["activate"] = repr(self.activate)
		return fields
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "ActivateEvent":
		active, activate = structs.stream_unpack(stream, ACTIVATE_EVENT)
		if not active:
			raise ValueError(f"proActivateEventData has its active field set to false")
		return cls(activate)
	
	def write(self, stream: typing.BinaryIO) -> None:
		stream.write(ACTIVATE_EVENT.pack(True, self.activate))


class CallbackEvent(NotifyEvent):
	TYPE = 8
	
	callback_type: int
	
	def __init__(self, callback_type: int) -> None:
		super().__init__()
		
		self.callback_type = callback_type
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["callback_type"] = repr(self.callback_type)
		return fields
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "CallbackEvent":
		(callback_type,) = structs.stream_unpack(stream, structs.INT32)
		return cls(callback_type)
	
	def write(self, stream: typing.BinaryIO) -> None:
		stream.write(structs.INT32.pack(self.callback_type))


class ResponderStateEvent(NotifyEvent):
	TYPE = 9
	
	state: int
	
	def __init__(self, state: int) -> None:
		super().__init__()
		
		self.state = state
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["state"] = repr(self.state)
		return fields
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "ResponderStateEvent":
		(responder_state,) = structs.stream_unpack(stream, structs.INT32)
		return cls(responder_state)
	
	def write(self, stream: typing.BinaryIO) -> None:
		stream.write(structs.INT32.pack(self.state))


class MultiStageEvent(NotifyEvent):
	class Event(structs.IntEnum):
		enter_stage = 1
		beginning_of_loop = 2
		advance_next_stage = 3
		regress_previous_stage = 4
	
	TYPE = 10
	
	stage: int
	event: "MultiStageEvent.Event"
	avatar: typing.Optional[structs.Uoid]
	
	def __init__(self, stage: int, event: "MultiStageEvent.Event", avatar: typing.Optional[structs.Uoid]) -> None:
		super().__init__()
		
		self.stage = stage
		self.event = event
		self.avatar = avatar
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["stage"] = repr(self.stage)
		fields["event"] = repr(self.event)
		if self.avatar is not None:
			fields["avatar"] = str(self.avatar)
		return fields
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "MultiStageEvent":
		stage, event = structs.stream_unpack(stream, MULTI_STAGE_EVENT_HEADER)
		avatar = structs.Uoid.key_from_stream(stream)
		return cls(stage, MultiStageEvent.Event(event), avatar)
	
	def write(self, stream: typing.BinaryIO) -> None:
		stream.write(MULTI_STAGE_EVENT_HEADER.pack(self.stage, self.event))
		structs.Uoid.key_to_stream(self.avatar, stream)


class SpawnedEvent(NotifyEvent):
	TYPE = 11
	
	spawner: typing.Optional[structs.Uoid]
	spawnee: typing.Optional[structs.Uoid]
	
	def __init__(self, spawner: typing.Optional[structs.Uoid], spawnee: typing.Optional[structs.Uoid]) -> None:
		super().__init__()
		
		self.spawner = spawner
		self.spawnee = spawnee
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		if self.spawner is not None:
			fields["spawner"] = str(self.spawner)
		if self.spawnee is not None:
			fields["spawnee"] = str(self.spawnee)
		return fields
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "SpawnedEvent":
		spawner = structs.Uoid.key_from_stream(stream)
		spawnee = structs.Uoid.key_from_stream(stream)
		return cls(spawner, spawnee)
	
	def write(self, stream: typing.BinaryIO) -> None:
		structs.Uoid.key_to_stream(self.spawner, stream)
		structs.Uoid.key_to_stream(self.spawnee, stream)


class CoopEvent(NotifyEvent):
	TYPE = 13
	
	initiator_ki_number: int
	serial_number: int
	
	def __init__(self, initiator_ki_number: int, serial_number: int) -> None:
		super().__init__()
		
		self.initiator_ki_number = initiator_ki_number
		self.serial_number = serial_number
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["initiator_ki_number"] = repr(self.initiator_ki_number)
		fields["serial_number"] = repr(self.serial_number)
		return fields
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "CoopEvent":
		initiator_ki_number, serial_number = structs.stream_unpack(stream, COOP_EVENT)
		return cls(initiator_ki_number, serial_number)
	
	def write(self, stream: typing.BinaryIO) -> None:
		stream.write(COOP_EVENT.pack(self.initiator_ki_number, self.serial_number))


class OfferLinkingBookEvent(NotifyEvent):
	class Event(structs.IntEnum):
		finish = 0
		offer = 999
		rescind = -999
	
	TYPE = 14
	
	offerer: typing.Optional[structs.Uoid]
	event: "OfferLinkingBookEvent.Event"
	offeree_ki_number: int
	
	def __init__(self, offerer: typing.Optional[structs.Uoid], event: "OfferLinkingBookEvent.Event", offeree_ki_number: int) -> None:
		super().__init__()
		
		self.offerer = offerer
		self.event = event
		self.offeree_ki_number = offeree_ki_number
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		if self.offerer is not None:
			fields["offerer"] = str(self.offerer)
		fields["event"] = repr(self.event)
		fields["offeree_ki_number"] = repr(self.offeree_ki_number)
		return fields
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "OfferLinkingBookEvent":
		offerer = structs.Uoid.key_from_stream(stream)
		event, offeree_ki_number = structs.stream_unpack(stream, OFFER_LINKING_BOOK_EVENT_FOOTER)
		return cls(offerer, OfferLinkingBookEvent.Event(event), offeree_ki_number)
	
	def write(self, stream: typing.BinaryIO) -> None:
		structs.Uoid.key_to_stream(self.offerer, stream)
		stream.write(OFFER_LINKING_BOOK_EVENT_FOOTER.pack(self.event, self.offeree_ki_number))


class NotifyMessage(Message):
	class Type(structs.IntEnum):
		activator = 0
		var_notification = 1
		notify_self = 2
		responder_fast_forward = 3
		responder_change_state = 4
	
	CLASS_INDEX = 0x02ed
	
	type: "NotifyMessage.Type"
	state: float
	id: int
	events: typing.List[NotifyEvent]
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		if self.type != NotifyMessage.Type.activator:
			fields["type"] = repr(self.type)
		fields["state"] = repr(self.state)
		if self.id != 0:
			fields["id"] = repr(self.id)
		if self.events:
			fields["events"] = repr(self.events)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		
		notification_type, notify_state, notify_id, event_count = structs.stream_unpack(stream, NOTIFY_MESSAGE_HEADER)
		self.type = NotifyMessage.Type(notification_type)
		self.state = notify_state
		self.id = notify_id
		
		self.events = []
		for _ in range(event_count):
			self.events.append(NotifyEvent.from_stream_with_type(stream))
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		
		stream.write(NOTIFY_MESSAGE_HEADER.pack(self.type, self.state, self.id, len(self.events)))
		
		for event in self.events:
			event.write_with_type(stream)


class LinkEffectsTriggerMessage(Message):
	class Flags(structs.IntFlag):
		mute_link_sfx = 1 << 0
	
	CLASS_INDEX = 0x0300
	
	ccr_level: int
	linking_out: bool
	linker: typing.Optional[structs.Uoid]
	link_effects_flags: "LinkEffectsTriggerMessage.Flags"
	link_in_animation: typing.Optional[structs.Uoid]
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		if self.ccr_level != 0:
			fields["ccr_level"] = repr(self.ccr_level)
		fields["linking_out"] = repr(self.linking_out)
		if self.linker is not None:
			fields["linker"] = str(self.linker)
		if self.link_effects_flags:
			fields["link_effects_flags"] = repr(self.link_effects_flags)
		if self.link_in_animation is not None:
			fields["link_in_animation"] = str(self.link_in_animation)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		self.ccr_level, self.linking_out = structs.stream_unpack(stream, LINK_EFFECTS_TRIGGER_MESSAGE_HEADER)
		self.linker = structs.Uoid.key_from_stream(stream)
		(link_effects_flags,) = structs.stream_unpack(stream, structs.UINT32)
		self.link_effects_flags = LinkEffectsTriggerMessage.Flags(link_effects_flags)
		self.link_in_animation = structs.Uoid.key_from_stream(stream)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		stream.write(LINK_EFFECTS_TRIGGER_MESSAGE_HEADER.pack(self.ccr_level, self.linking_out))
		structs.Uoid.key_to_stream(self.linker, stream)
		stream.write(structs.UINT32.pack(self.link_effects_flags))
		structs.Uoid.key_to_stream(self.link_in_animation, stream)


class ParticleTransferMessage(Message):
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


class ParticleKillMessage(Message):
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


class AvatarInputStateMessage(Message):
	class State(structs.IntFlag):
		forward = 1 << 0
		backward = 1 << 1
		rotate_left = 1 << 2
		rotate_right = 1 << 3
		strafe_left = 1 << 4
		strafe_right = 1 << 5
		always_run = 1 << 6
		jump = 1 << 7
		consumable_jump = 1 << 8
		modifier_run = 1 << 9
		modifier_strafe = 1 << 10
		ladder_inverted = 1 << 11
	
	CLASS_INDEX = 0x0347
	
	state: "AvatarInputStateMessage.State"
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["state"] = repr(self.state)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		(state,) = structs.stream_unpack(stream, structs.UINT16)
		self.state = AvatarInputStateMessage.State(state)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		stream.write(structs.UINT16.pack(self.state))


class InputInterfaceManagerMessage(Message):
	class Command(structs.IntEnum):
		add_interface = 0
		remove_interface = 1
		enable_clickables = 2
		disable_clickables = 3
		set_offer_book_mode = 4
		clear_offer_book_mode = 5
		notify_offer_accepted = 6
		notify_offer_rejected = 7
		notify_offer_completed = 8
		disable_avatar_clickable = 9
		enable_avatar_clickable = 10
		gui_disable_avatar_clickable = 11
		gui_enable_avatar_clickable = 12
		set_share_spawn_point = 13
		set_share_age_instance_guid = 14
	
	CLASS_INDEX = 0x0363
	
	command: "InputInterfaceManagerMessage.Command"
	offeree_ki_number: int
	age_name: bytes
	age_file_name: bytes
	spawn_point: bytes
	avatar: typing.Optional[structs.Uoid]
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["command"] = repr(self.command)
		fields["offeree_ki_number"] = repr(self.offeree_ki_number)
		if self.age_name:
			fields["age_name"] = repr(self.age_name)
		if self.age_file_name:
			fields["age_file_name"] = repr(self.age_file_name)
		if self.spawn_point:
			fields["spawn_point"] = repr(self.spawn_point)
		if self.avatar is not None:
			fields["avatar"] = str(self.avatar)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		super().read(stream)
		command, self.offeree_ki_number = structs.stream_unpack(stream, INPUT_INTERFACE_MANAGER_MESSAGE_HEADER)
		self.command = InputInterfaceManagerMessage.Command(command)
		self.age_name = structs.read_safe_string(stream)
		self.age_file_name = structs.read_safe_string(stream)
		self.spawn_point = structs.read_safe_string(stream)
		self.avatar = structs.Uoid.key_from_stream(stream)
	
	def write(self, stream: typing.BinaryIO) -> None:
		super().write(stream)
		stream.write(INPUT_INTERFACE_MANAGER_MESSAGE_HEADER.pack(self.command, self.offeree_ki_number))
		structs.write_safe_string(stream, self.age_name)
		structs.write_safe_string(stream, self.age_file_name)
		structs.write_safe_string(stream, self.spawn_point)
		structs.Uoid.key_to_stream(self.avatar, stream)
