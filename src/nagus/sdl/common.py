# This file is part of NAGUS, an Uru Live server that is not very good.
# Copyright (C) 2025 dgelessus
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


"""Common SDL-related code that works regardless of which de-/serialization method is used.

Defines some basic data types
and implements those parts of SDL de-/serialization that don't depend on a state descriptor.
"""


import abc
import collections
import datetime
import typing

from .. import structs


class StateDescriptorId(object):
	name: bytes
	version: int
	
	def __init__(self, name: bytes, version: int) -> None:
		super().__init__()
		
		self.name = name
		self.version = version
	
	def __eq__(self, other: object) -> bool:
		if not isinstance(other, StateDescriptorId):
			return NotImplemented
		
		return self.name == other.name and self.version == other.version
	
	def __repr__(self) -> str:
		return f"{type(self).__qualname__}({self.name!r}, {self.version!r})"
	
	def __str__(self) -> str:
		return f"{self.name!r} v{self.version}"


class SDLStreamHeader(object):
	class Flags(structs.IntFlag):
		has_uoid = 1 << 0
		var_length_io = 1 << 15
		
		supported = (
			has_uoid
			| var_length_io
		)
	
	descriptor_id: StateDescriptorId
	uoid: typing.Optional[structs.Uoid]
	
	def __init__(
		self,
		descriptor_id: StateDescriptorId,
		uoid: typing.Optional[structs.Uoid] = None,
	) -> None:
		super().__init__()
		
		self.descriptor_id = descriptor_id
		self.uoid = uoid
	
	def __eq__(self, other: object) -> bool:
		if not isinstance(other, SDLStreamHeader):
			return NotImplemented
		
		return (
			self.descriptor_id == other.descriptor_id
			and self.uoid == other.uoid
		)
	
	def __repr__(self) -> str:
		parts = [repr(self.descriptor_id)]
		
		if self.uoid is not None:
			parts.append(f"uoid={self.uoid!r}")
		
		joined_parts = ", ".join(parts)
		return f"{type(self).__qualname__}({joined_parts})"
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "SDLStreamHeader":
		(flags,) = structs.stream_unpack(stream, structs.UINT16)
		flags = SDLStreamHeader.Flags(flags)
		if SDLStreamHeader.Flags.var_length_io not in flags:
			raise ValueError(f"SDL stream header does not have required flag var_length_io set: {flags!r}")
		elif flags & ~SDLStreamHeader.Flags.supported:
			raise ValueError(f"SDL stream header has unsupported flags set: {flags!r}")
		
		descriptor_name = structs.read_safe_string(stream)
		(descriptor_version,) = structs.stream_unpack(stream, structs.UINT16)
		
		uoid: typing.Optional[structs.Uoid]
		if SDLStreamHeader.Flags.has_uoid in flags:
			uoid = structs.Uoid.from_stream(stream)
		else:
			uoid = None
		
		return cls(StateDescriptorId(descriptor_name, descriptor_version), uoid)
	
	def write(self, stream: typing.BinaryIO) -> None:
		flags = SDLStreamHeader.Flags.var_length_io
		if self.uoid is not None:
			flags |= SDLStreamHeader.Flags.has_uoid
		stream.write(structs.UINT16.pack(flags))
		
		structs.write_safe_string(stream, self.descriptor_id.name)
		stream.write(structs.UINT16.pack(self.descriptor_id.version))
		
		if self.uoid is not None:
			self.uoid.write(stream)


class VariableValueBase(structs.FieldBasedRepr):
	"""Base class for all SDL variable values (simple and nested SDL).
	
	Parses and writes the header structure common to all variables,
	i. e. the notification info.
	"""
	
	class Flags(structs.IntFlag):
		has_notification_info = 1 << 1
		
		supported = has_notification_info
	
	hint: typing.Optional[bytes]
	
	def __init__(self, *, hint: typing.Optional[bytes] = None) -> None:
		super().__init__()
		
		self.hint = hint
	
	def __eq__(self, other: object) -> bool:
		if not isinstance(other, VariableValueBase):
			return NotImplemented
		
		return self.hint == other.hint
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		if self.hint is not None:
			fields["hint"] = repr(self.hint)
		return fields
	
	@abc.abstractmethod
	def copy(self) -> "VariableValueBase":
		raise NotImplementedError()
	
	def base_read(self, stream: typing.BinaryIO) -> None:
		"""Read the part of the variable value structure that does *not* vary depending on the state descriptor."""
		
		(flags,) = structs.read_exact(stream, 1)
		flags = VariableValueBase.Flags(flags)
		if flags & ~VariableValueBase.Flags.supported:
			raise ValueError(f"SDL variable value header has unsupported flags set: {flags!r}")
		
		if flags & VariableValueBase.Flags.has_notification_info:
			(notification_info_flags,) = structs.read_exact(stream, 1)
			if notification_info_flags != 0:
				raise ValueError(f"SDL variable notification info has unsupported flags set: 0x{notification_info_flags:>02x}")
			
			self.hint = structs.read_safe_string(stream)
		else:
			self.hint = None
	
	def base_write(self, stream: typing.BinaryIO) -> None:
		"""Write the part of the variable value structure that does *not* vary depending on the state descriptor."""
		
		flags = VariableValueBase.Flags(0)
		if self.hint is not None:
			flags |= VariableValueBase.Flags.has_notification_info
		stream.write(bytes([flags]))
		
		if self.hint is not None:
			stream.write(b"\x00")
			structs.write_safe_string(stream, self.hint)


class SimpleVariableValueBase(VariableValueBase):
	"""Base class for the normal and guessing implementations of simple SDL variable values.
	
	Parses and writes the flags and timestamp fields,
	which are structured identically for all simple SDL variable values,
	regardless of the state descriptor.
	"""
	
	class Flags(structs.IntFlag):
		has_timestamp = 1 << 2
		same_as_default = 1 << 3
		dirty = 1 << 4
		want_timestamp = 1 << 5
		
		supported = (
			has_timestamp
			| same_as_default
			| dirty
			| want_timestamp
		)
	
	flags: "SimpleVariableValueBase.Flags"
	timestamp: typing.Optional[datetime.datetime]
	
	def __init__(
		self,
		*,
		hint: typing.Optional[bytes] = None,
		flags: "SimpleVariableValueBase.Flags" = Flags(0),
		timestamp: typing.Optional[datetime.datetime] = None,
	) -> None:
		super().__init__(hint=hint)
		
		self.flags = flags
		self.timestamp = timestamp
	
	def __eq__(self, other: object) -> bool:
		if not isinstance(other, SimpleVariableValueBase):
			return NotImplemented
		
		return (
			super().__eq__(other)
			and self.flags == other.flags
			and self.timestamp == other.timestamp
		)
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["flags"] = repr(self.flags)
		if self.timestamp is not None:
			fields["timestamp"] = repr(self.timestamp)
		return fields
	
	@abc.abstractmethod
	def copy(self) -> "SimpleVariableValueBase":
		raise NotImplementedError()
	
	def base_read(self, stream: typing.BinaryIO) -> None:
		super().base_read(stream)
		
		(flags,) = structs.read_exact(stream, 1)
		self.flags = SimpleVariableValueBase.Flags(flags)
		if self.flags & ~SimpleVariableValueBase.Flags.supported:
			raise ValueError(f"Simple SDL variable value has unsupported flags set: {self.flags!r}")
		
		if self.flags & SimpleVariableValueBase.Flags.has_timestamp:
			self.timestamp = structs.read_unified_time(stream)
		else:
			self.timestamp = None
	
	def base_write(self, stream: typing.BinaryIO) -> None:
		super().base_write(stream)
		
		stream.write(bytes([self.flags]))
		
		if self.flags & SimpleVariableValueBase.Flags.has_timestamp:
			assert self.timestamp is not None
			structs.write_unified_time(stream, self.timestamp)
		else:
			assert self.timestamp is None


class NestedSDLVariableValueBase(VariableValueBase):
	"""Base class for the normal and guessing implementations of nested SDL variable values."""
	
	def base_read(self, stream: typing.BinaryIO) -> None:
		super().base_read(stream)
		
		(flags,) = structs.read_exact(stream, 1)
		if flags:
			raise ValueError(f"Nested SDL variable value has unsupported flags set: {flags!r}")
	
	def base_write(self, stream: typing.BinaryIO) -> None:
		super().base_write(stream)
		
		stream.write(b"\x00")


class SDLRecordBase(structs.FieldBasedRepr):
	"""Base class for the normal and guessing implementations of SDL records."""
	
	class Flags(structs.IntFlag):
		volatile = 1 << 0
		
		supported = volatile
	
	IO_VERSION: int = 6
	
	flags: "SDLRecordBase.Flags"
	
	def __init__(self, *, flags: "SDLRecordBase.Flags" = Flags(0)) -> None:
		super().__init__()
		
		self.flags = flags
	
	def __eq__(self, other: object) -> bool:
		if not isinstance(other, SDLRecordBase):
			return NotImplemented
		
		return self.flags == other.flags
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		if self.flags:
			fields["flags"] = repr(self.flags)
		return fields
	
	@abc.abstractmethod
	def copy(self) -> "SDLRecordBase":
		raise NotImplementedError()
	
	def base_read(self, stream: typing.BinaryIO) -> None:
		(flags,) = structs.stream_unpack(stream, structs.UINT16)
		self.flags = SDLRecordBase.Flags(flags)
		if self.flags & ~SDLRecordBase.Flags.supported:
			raise ValueError(f"SDL blob has unsupported flags set: {self.flags!r}")
		
		(io_version,) = structs.read_exact(stream, 1)
		if io_version != SDLRecordBase.IO_VERSION:
			raise ValueError(f"SDL blob has unsupported IO version: {io_version}")
	
	def base_write(self, stream: typing.BinaryIO) -> None:
		stream.write(structs.UINT16.pack(self.flags))
		stream.write(bytes([SDLRecordBase.IO_VERSION]))
