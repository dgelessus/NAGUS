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


"""Handles reading and writing of SDL blobs.

This module contains two variants of SDL de-/serialization:
a normal version that works based on state descriptors
and a "guessed" version that tries to parse blobs *without* knowing the state descriptor.

The "guessed" version is currently more developed,
because I want to use it to get basic SDL functionality working
without having to implement the complexity of the full SDL system yet.
It may also be useful as a debugging tool for inspecting unknown SDL blobs.
The normal version will be finished later.
"""


import collections
import datetime
import io
import struct
import typing

from . import structs


class SDLStreamHeader(object):
	class Flags(structs.IntFlag):
		has_uoid = 1 << 0
		var_length_io = 1 << 15
		
		supported = (
			has_uoid
			| var_length_io
		)
	
	descriptor_name: bytes
	descriptor_version: int
	uoid: typing.Optional[structs.Uoid]
	
	def __init__(
		self,
		descriptor_name: bytes,
		descriptor_version: int,
		uoid: typing.Optional[structs.Uoid] = None,
	) -> None:
		super().__init__()
		
		self.descriptor_name = descriptor_name
		self.descriptor_version = descriptor_version
		self.uoid = uoid
	
	def __eq__(self, other: object) -> bool:
		if not isinstance(other, SDLStreamHeader):
			return NotImplemented
		
		return (
			self.descriptor_name == other.descriptor_name
			and self.descriptor_version == other.descriptor_version
			and self.uoid == other.uoid
		)
	
	def __repr__(self) -> str:
		parts = [
			repr(self.descriptor_name),
			repr(self.descriptor_version),
		]
		
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
		
		return cls(descriptor_name, descriptor_version, uoid)
	
	def write(self, stream: typing.BinaryIO) -> None:
		flags = SDLStreamHeader.Flags.var_length_io
		if self.uoid is not None:
			flags |= SDLStreamHeader.Flags.has_uoid
		stream.write(structs.UINT16.pack(flags))
		
		structs.write_safe_string(stream, self.descriptor_name)
		stream.write(structs.UINT16.pack(self.descriptor_version))
		
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
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		if self.hint is not None:
			fields["hint"] = repr(self.hint)
		return fields
	
	def copy(self) -> "VariableValueBase":
		copy = type(self)()
		copy.hint = self.hint
		return copy
	
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
		
		return self.flags == other.flags and self.timestamp == other.timestamp
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["flags"] = repr(self.flags)
		if self.timestamp is not None:
			fields["timestamp"] = repr(self.timestamp)
		return fields
	
	def copy(self) -> "SimpleVariableValueBase":
		copy = typing.cast(SimpleVariableValueBase, super().copy())
		copy.flags = self.flags
		copy.timestamp = self.timestamp
		return copy
	
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


MIN_REASONABLE_TIMESTAMP = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc).timestamp()


class GuessedSimpleVariableValue(SimpleVariableValueBase):
	"""A simple variable value whose size was guessed rather than known from a state descriptor.
	
	The variable's contents are not parsed further.
	The data field contains the data for *all* array elements,
	prefixed by the variable array length field
	(if any).
	"""
	
	data: bytes
	
	def __init__(
		self,
		*,
		hint: typing.Optional[bytes] = None,
		flags: SimpleVariableValueBase.Flags = SimpleVariableValueBase.Flags(0),
		timestamp: typing.Optional[datetime.datetime] = None,
		data: bytes = b"",
	) -> None:
		super().__init__(hint=hint, flags=flags, timestamp=timestamp)
		
		self.data = data
	
	def __eq__(self, other: object) -> bool:
		if not isinstance(other, GuessedSimpleVariableValue):
			return NotImplemented
		
		return super().__eq__(other) and self.data == other.data
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["data"] = repr(self.data)
		return fields
	
	def __str__(self) -> str:
		flags = self.flags
		if SimpleVariableValueBase.Flags.same_as_default in flags:
			assert not self.data
			flags &= ~SimpleVariableValueBase.Flags.same_as_default
			res = "<default>"
		else:
			# Try to give a nicer, but still unambiguous representation for easily recognized data types.
			if len(self.data) == 32 and 0x20 <= self.data[0] <= 0x7f:
				# STRING32
				s = self.data.rstrip(b"\x00").decode("latin-1")
				res = repr(s)
			elif (
				len(self.data) >= 17 # minimum possible length for UOID
				and self.data[0] & ~0x3 == 0 # UOID flags valid
				and self.data[5] & ~0x1f == 0 # location flags valid
				and self.data[6] == 0 # location flags MSB unused
			):
				# PLKEY
				with io.BytesIO(self.data) as stream:
					try:
						uoid = structs.Uoid.from_stream(stream)
						ok = not stream.read()
					except (EOFError, ValueError):
						ok = False
				
				res = str(uoid) if ok else repr(self.data)
			elif len(self.data) == 8:
				# TIME
				timestamp, micros = structs.UNIFIED_TIME.unpack(self.data)
				if timestamp >= MIN_REASONABLE_TIMESTAMP and micros in range(1000000):
					try:
						res = structs.unpack_unified_time(self.data).isoformat()
					except (struct.error, OverflowError):
						res = repr(self.data)
				else:
					res = repr(self.data)
			else:
				res = repr(self.data)
		
		if self.timestamp is None:
			assert SimpleVariableValueBase.Flags.has_timestamp not in flags
		else:
			assert SimpleVariableValueBase.Flags.has_timestamp in flags
			flags &= ~SimpleVariableValueBase.Flags.has_timestamp
			res += f" @ {self.timestamp.isoformat()}"
		
		if flags:
			res += f" ({flags})"
		
		if self.hint:
			res += f" # {self.hint!r}"
		
		return res
	
	def copy(self) -> "GuessedSimpleVariableValue":
		copy = typing.cast(GuessedSimpleVariableValue, super().copy())
		copy.data = self.data
		return copy
	
	def write(self, stream: typing.BinaryIO) -> None:
		"""Write the full variable value back.
		
		This will only work correctly if written in place of a variable with a similar enough structure.
		"""
		
		self.base_write(stream)
		stream.write(self.data)


class SimpleVariableValue(SimpleVariableValueBase):
	"""A parsed simple variable value."""
	
	values: typing.List[typing.Any]
	
	def __init__(
		self,
		*,
		hint: typing.Optional[bytes] = None,
		flags: SimpleVariableValueBase.Flags = SimpleVariableValueBase.Flags(0),
		timestamp: typing.Optional[datetime.datetime] = None,
		values: typing.List[typing.Any],
	) -> None:
		super().__init__(hint=hint, flags=flags, timestamp=timestamp)
		
		self.values = values
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["values"] = repr(self.values)
		return fields
	
	def __eq__(self, other: object) -> bool:
		if not isinstance(other, SimpleVariableValue):
			return NotImplemented
		
		return super().__eq__(other) and self.values == other.values
	
	def copy(self) -> "SimpleVariableValue":
		copy = typing.cast(SimpleVariableValue, super().copy())
		copy.values = list(self.values)
		return copy
	
	def read(self, stream: typing.BinaryIO, element_count: typing.Optional[int], element_reader: typing.Callable[[typing.BinaryIO], typing.Any]) -> None:
		"""Read a full variable value from an SDL blob.
		
		To work correctly,
		this method needs to know the declared array element count for the variable.
		Reading the individual elements is delegated to a function passed in by the caller,
		which must read the correct amount of data for each element
		and parse the data as desired.
		"""
		
		self.base_read(stream)
		
		if element_count is None:
			(element_count,) = structs.stream_unpack(stream, structs.UINT32)
		
		self.values = [element_reader(stream) for _ in range(element_count)]
	
	def write(self, stream: typing.BinaryIO, write_element_count: bool, element_writer: typing.Callable[[typing.BinaryIO, typing.Any], None]) -> None:
		"""Write the full variable value to an SDL blob.
		
		To work correctly,
		this method needs to know whether the variable is a variable-length array,
		i. e. whether an explicit element count field needs to be written.
		Writing the individual elements is delegated to a function passed in by the caller.
		"""
		
		self.base_write(stream)
		
		if write_element_count:
			stream.write(structs.UINT32.pack(len(self.values)))
		
		for element in self.values:
			element_writer(stream, element)


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


def _looks_like_start_of_blob_body(data: bytes) -> bool:
	"""Check whether the given data looks like the start of an SDL blob body."""
	
	return data[:3] in {b"\x00\x00\x06", b"\x01\x00\x06"}


def _find_start_of_blob_body(data: bytes) -> int:
	"""Find the first index in the given data that looks like the start of an SDL blob body.
	
	:raises ValueError: If no matching index could be found in the data.
	"""
	
	next_pos = 1
	# If no start of blob body was found,
	# the loop is terminated by the ValueError thrown by bytes.index.
	while True:
		pos = data.index(b"\x00\x06", next_pos)
		if _looks_like_start_of_blob_body(data[pos-1:pos+2]):
			return pos - 1
		next_pos = pos + 2


class GuessedNestedSDLVariableValue(NestedSDLVariableValueBase):
	variable_array_length: typing.Optional[int]
	values_indices: bool
	values: "typing.Dict[int, GuessedSDLRecord]"
	
	def __init__(
		self,
		*,
		hint: typing.Optional[bytes] = None,
		variable_array_length: typing.Optional[int] = None,
		values_indices: bool = False,
		values: "typing.Dict[int, GuessedSDLRecord]",
	) -> None:
		super().__init__(hint=hint)
		
		self.variable_array_length = variable_array_length
		self.values_indices = values_indices
		self.values = values
	
	def __eq__(self, other: object) -> bool:
		if not isinstance(other, GuessedNestedSDLVariableValue):
			return NotImplemented
		
		return (
			self.variable_array_length == other.variable_array_length
			and self.values_indices == other.values_indices
			and self.values == other.values
		)
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		if self.variable_array_length is not None:
			fields["variable_array_length"] = repr(self.variable_array_length)
		if self.values_indices:
			fields["values_indices"] = repr(self.values_indices)
		fields["values"] = repr(self.values)
		return fields
	
	def as_multiline_str(self) -> typing.Iterable[str]:
		if self.variable_array_length is None:
			desc = f"{len(self.values)} elements"
		else:
			desc = f"{len(self.values)} of {self.variable_array_length} elements"
		
		if not self.values_indices:
			desc += " (complete)"
		
		if self.hint:
			desc += f" # {self.hint!r}"
		
		if self.values:
			yield f"{desc}:"
		else:
			yield desc
		
		for index, value in self.values.items():
			it = iter(value.as_multiline_str())
			first = next(it, "")
			yield f"\t[{index}] = {first}"
			for line in it:
				yield "\t\t" + line
	
	def copy(self) -> "GuessedNestedSDLVariableValue":
		copy = typing.cast(GuessedNestedSDLVariableValue, super().copy())
		copy.variable_array_length = self.variable_array_length
		copy.values_indices = self.values_indices
		copy.values = dict(self.values)
		return copy
	
	def read(self, stream: typing.BinaryIO) -> None:
		self.base_read(stream)
		
		# Assume that a single nested SDL variable doesn't have more than 255 elements.
		
		pos = stream.tell()
		lookahead = stream.read(9)
		stream.seek(pos)
		
		if lookahead.startswith(b"\x00\x00\x00\x00\x00"):
			(self.variable_array_length,) = structs.stream_unpack(stream, structs.UINT32)
			assert self.variable_array_length == 0
			self.values_indices = True
		elif _looks_like_start_of_blob_body(lookahead[6:]):
			(self.variable_array_length,) = structs.stream_unpack(stream, structs.UINT32)
			self.values_indices = True
		elif _looks_like_start_of_blob_body(lookahead[5:]):
			(self.variable_array_length,) = structs.stream_unpack(stream, structs.UINT32)
			self.values_indices = False
		elif _looks_like_start_of_blob_body(lookahead[2:]):
			self.variable_array_length = None
			self.values_indices = True
		elif _looks_like_start_of_blob_body(lookahead[1:]):
			self.variable_array_length = None
			self.values_indices = False
		else:
			raise ValueError(f"Unable to guess whether or not this nested SDL variable has indices before its element values. Lookahead is {lookahead!r}")
		
		# Assume (again) that there are no more than 255 elements.
		(value_count,) = structs.read_exact(stream, 1)
		self.values = {}
		for i in range(value_count):
			if self.values_indices:
				# Assume (again) that there are no more than 255 elements.
				(index,) = structs.read_exact(stream, 1)
			else:
				index = i
			
			value = self.values[index] = GuessedSDLRecord(simple_values={}, nested_sdl_values={})
			value.read(stream)
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "GuessedNestedSDLVariableValue":
		self = GuessedNestedSDLVariableValue(values={})
		self.read(stream)
		return self
	
	def write(self, stream: typing.BinaryIO) -> None:
		self.base_write(stream)
		
		if self.variable_array_length is not None:
			stream.write(structs.UINT32.pack(self.variable_array_length))
		
		stream.write(bytes([len(self.values)]))
		
		for index, value in self.values.items():
			if self.values_indices:
				stream.write(bytes([index]))
			
			value.write(stream)


class NestedSDLVariableValue(NestedSDLVariableValueBase):
	variable_array_length: typing.Optional[int]
	values: "typing.Dict[int, SDLRecordBase]" # TODO Use SDLRecord class once it exists
	
	def __init__(
		self,
		*,
		hint: typing.Optional[bytes] = None,
		variable_array_length: typing.Optional[int] = None,
		values: "typing.Dict[int, SDLRecordBase]",
	) -> None:
		super().__init__(hint=hint)
		
		self.variable_array_length = variable_array_length
		self.values = values
	
	def __eq__(self, other: object) -> bool:
		if not isinstance(other, NestedSDLVariableValue):
			return NotImplemented
		
		return (
			self.variable_array_length == other.variable_array_length
			and self.values == other.values
		)
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		if self.variable_array_length is not None:
			fields["variable_array_length"] = repr(self.variable_array_length)
		fields["values"] = repr(self.values)
		return fields
	
	def copy(self) -> "NestedSDLVariableValue":
		copy = typing.cast(NestedSDLVariableValue, super().copy())
		copy.variable_array_length = self.variable_array_length
		copy.values = dict(self.values)
		return copy
	
	# TODO read, write


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
	
	def copy(self) -> "SDLRecordBase":
		copy = type(self)()
		copy.flags = self.flags
		return copy
	
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


def _looks_like_start_of_variable(data: bytes) -> bool:
	"""Check whether the given data looks like the start of an SDL variable."""
	
	return (
		len(data) >= 4
		# 1 byte: flags with only has_notification_info set (always the case)
		# 1 byte: notification info flags set to 0 (always the case)
		and data.startswith(b"\x02\x00")
		# 2 bytes: SafeString header with a relatively short length (almost always the case)
		and data[2] < 0x80
		and data[3:4] == b"\xf0"
	)


def _find_start_of_variable(data: bytes) -> int:
	"""Find the first index in the given data that looks like the start of an SDL variable.
	
	:raises ValueError: If no matching index could be found in the data.
	"""
	
	next_pos = 0
	# If no start of variable was found,
	# the loop is terminated by the ValueError thrown by bytes.index.
	while True:
		pos = data.index(b"\x02\x00", next_pos)
		if _looks_like_start_of_variable(data[pos:pos+4]):
			return pos
		next_pos = pos + 2


class GuessedSDLRecord(SDLRecordBase):
	"""An SDL record parsed by guessing the structure of an SDL blob rather than knowing it from a state descriptor.
	
	SDL blobs aren't meant to be parsed on their own -
	it's expected that the correct structure and data types are known from the corresponding state descriptor.
	In practice,
	it's usually possible to guess the basic structure from the SDL blob alone.
	
	This implementation works for most blobs produced by Cyan's code,
	but usually not for ones written by DIRTSAND,
	because the latter often omits the notification info fields,
	which this code uses to guess variable boundaries.
	
	Nested SDL variables are currently ignored completely.
	"""
	
	simple_values_indices: bool
	simple_values: typing.Dict[int, GuessedSimpleVariableValue]
	nested_sdl_values_indices: bool
	nested_sdl_values: typing.Dict[int, GuessedNestedSDLVariableValue]
	
	def __init__(
		self,
		*,
		flags: SDLRecordBase.Flags = SDLRecordBase.Flags(0),
		simple_values_indices: bool = False,
		simple_values: typing.Dict[int, GuessedSimpleVariableValue],
		nested_sdl_values_indices: bool = False,
		nested_sdl_values: typing.Dict[int, GuessedNestedSDLVariableValue],
	) -> None:
		super().__init__(flags=flags)
		
		self.simple_values_indices = simple_values_indices
		self.simple_values = simple_values
		self.nested_sdl_values_indices = nested_sdl_values_indices
		self.nested_sdl_values = nested_sdl_values
	
	def __eq__(self, other: object) -> bool:
		if not isinstance(other, GuessedSDLRecord):
			return NotImplemented
		
		return (
			super().__eq__(other)
			and self.simple_values_indices == other.simple_values_indices
			and self.simple_values == other.simple_values
			and self.nested_sdl_values_indices == other.nested_sdl_values_indices
			and self.nested_sdl_values == other.nested_sdl_values
		)
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		if self.simple_values_indices:
			fields["simple_values_indices"] = repr(self.simple_values_indices)
		if self.simple_values:
			fields["simple_values"] = repr(self.simple_values)
		if self.nested_sdl_values_indices:
			fields["nested_sdl_values_indices"] = repr(self.nested_sdl_values_indices)
		if self.nested_sdl_values:
			fields["nested_sdl_values"] = repr(self.nested_sdl_values)
		return fields
	
	def as_multiline_str(self) -> typing.Iterable[str]:
		if SDLRecordBase.Flags.volatile in self.flags:
			prefix = "volatile, "
		else:
			prefix = ""
		
		if not self.simple_values and not self.nested_sdl_values:
			yield prefix + "empty blob"
		
		if self.simple_values:
			desc = f"{prefix}{len(self.simple_values)} simple values"
			prefix = ""
			
			if not self.simple_values_indices:
				desc += " (complete)"
			
			yield f"{desc}:"
			
			for index, value in self.simple_values.items():
				yield f"({index}) = {value}"
		
		if self.nested_sdl_values:
			desc = f"{prefix}{len(self.nested_sdl_values)} nested SDL values"
			prefix = ""
			
			if not self.nested_sdl_values_indices:
				desc += " (complete)"
			
			yield f"{desc}:"
			
			for index, sdl_value in self.nested_sdl_values.items():
				it = iter(sdl_value.as_multiline_str())
				first = next(it, "")
				yield f"({index}) = {first}"
				yield from it
	
	def copy(self) -> "GuessedSDLRecord":
		copy = typing.cast(GuessedSDLRecord, super().copy())
		copy.simple_values_indices = self.simple_values_indices
		copy.simple_values = dict(self.simple_values)
		copy.nested_sdl_values_indices = self.nested_sdl_values_indices
		copy.nested_sdl_values = dict(self.nested_sdl_values)
		return copy
	
	def read(self, stream: typing.BinaryIO) -> None:
		self.base_read(stream)
		
		# Assume that a single state descriptor doesn't contain more than 255 simple variables.
		# This seems to be a safe assumption currently -
		# for reference: STATEDESC city VERSION 43 has 151 variables.
		(simple_variable_count,) = structs.read_exact(stream, 1)
		
		self.simple_values = {}
		# If there are no simple variables in this blob,
		# start right away with the nested SDL variables.
		if simple_variable_count == 0:
			self.simple_values_indices = True
			
			pos = stream.tell()
			lookahead = stream.read(6)
			stream.seek(pos)
			
			if _looks_like_start_of_variable(lookahead[1:]):
				self.nested_sdl_values_indices = False
			elif _looks_like_start_of_variable(lookahead[2:]):
				self.nested_sdl_values_indices = True
			else:
				raise ValueError(f"Unable to guess whether or not this SDL blob has indices before its nested SDL variables. Lookahead (including count) is {lookahead!r}")
		else:
			pos = stream.tell()
			lookahead = stream.read(5)
			stream.seek(pos)
			
			if _looks_like_start_of_variable(lookahead):
				self.simple_values_indices = False
			elif _looks_like_start_of_variable(lookahead[1:]):
				self.simple_values_indices = True
			else:
				raise ValueError(f"Unable to guess whether or not this SDL blob has indices before its simple variables. Simple variable count is {simple_variable_count}, lookahead afterwards is {lookahead!r}")
			
			# Last variable needs special treatment,
			# because it's followed by the nested SDL variable stuff and not another simple variable.
			rang = range(simple_variable_count)
			for i in rang:
				if self.simple_values_indices:
					# Assume (again) that there are no more than 255 simple variables.
					(index,) = structs.read_exact(stream, 1)
				else:
					index = i
				
				value = self.simple_values[index] = GuessedSimpleVariableValue()
				value.base_read(stream)
				
				# Assume that the start of the next variable is found within the next 128 bytes.
				pos = stream.tell()
				lookahead = stream.read(128)
				stream.seek(pos)
				
				# Find end of data for this variable by looking for the start of the next variable or blob body.
				try:
					next_var_pos = _find_start_of_variable(lookahead)
				except ValueError:
					next_var_pos = None
				
				try:
					next_blob_pos = _find_start_of_blob_body(lookahead)
				except ValueError:
					next_blob_pos = None
				
				assert next_var_pos is None or next_blob_pos is None or next_var_pos != next_blob_pos
				
				if next_var_pos is None and next_blob_pos is None:
					# If there are no nested SDL variables,
					# the SDL blob will end shortly after the last simple variable
					# and there will be no next variable or blob.
					# The last byte in the SDL blob will be the nested SDL variable count,
					# which will be 0.
					# (This assumes that a single state descriptor doesn't contain more than 255 nested SDL variables - see below.)
					# All data before that byte will be part of the last simple variable's data.
					if i == rang[-1] and len(lookahead) < 128 and lookahead.endswith(b"\x00"):
						data_len = len(lookahead) - 1
						self.nested_sdl_values_indices = True
					else:
						raise ValueError(f"Unable to find end of data for variable {index} (index {i} in the blob). Lookahead is {lookahead!r}")
				elif i == rang[-1]:
					if next_blob_pos is not None and (next_var_pos is None or next_blob_pos < next_var_pos):
						# Found start of a blob before start of a variable -
						# this means that we're inside a nested SDL variable array containing more than one value
						# and this blob has no nested SDL variables of its own.
						data_len = next_blob_pos
						assert data_len > 0
						assert lookahead[data_len - 1] == 0
						# FIXME This assumes that nested SDL variable array elements never have indices!
						# (If there are indices, this has to go back 2 bytes, not just 1.)
						data_len -= 1
						self.nested_sdl_values_indices = True
					else:
						assert next_var_pos is not None
						data_len = next_var_pos
						assert data_len > 0
						# FIXME This assumes that nested SDL values never have indices!
						# (If there are indices, this has to go back 2 bytes, not just 1.)
						data_len -= 1
						self.nested_sdl_values_indices = False
				else:
					if next_var_pos is None:
						raise ValueError(f"Unable to find end of data for variable {index} (index {i} in the blob). Lookahead is {lookahead!r}")
					
					data_len = next_var_pos
					if self.simple_values_indices:
						# Exclude the next variable's index from this variable's data.
						assert data_len > 0
						data_len -= 1
				
				value.data = structs.read_exact(stream, data_len)
		
		# Assume that a single state descriptor doesn't contain more than 255 nested SDL variables.
		# This is an even safer assumption,
		# because nested SDL variables aren't used very often.
		(nested_sdl_variable_count,) = structs.read_exact(stream, 1)
		self.nested_sdl_values = {}
		for i in range(nested_sdl_variable_count):
			if self.nested_sdl_values_indices:
				# Assume (again) that there are no more than 255 nested SDL variables.
				(index,) = structs.read_exact(stream, 1)
			else:
				index = i
			
			sdl_value = self.nested_sdl_values[index] = GuessedNestedSDLVariableValue(values={})
			sdl_value.read(stream)
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "GuessedSDLRecord":
		self = cls(simple_values={}, nested_sdl_values={})
		self.read(stream)
		return self
	
	def write(self, stream: typing.BinaryIO) -> None:
		self.base_write(stream)
		
		stream.write(bytes([len(self.simple_values)]))
		for index, value in self.simple_values.items():
			if self.simple_values_indices:
				stream.write(bytes([index]))
			
			value.write(stream)
		
		stream.write(bytes([len(self.nested_sdl_values)]))
		for index, sdl_value in self.nested_sdl_values.items():
			if self.nested_sdl_values_indices:
				stream.write(bytes([index]))
			
			sdl_value.write(stream)
	
	def with_change(self, change: "GuessedSDLRecord") -> "GuessedSDLRecord":
		changed = self.copy()
		
		for i, change_value in change.simple_values.items():
			# TODO Set timestamp if requested (may be better done as its own method)
			# TODO Does this need to check the dirty flag?
			changed.simple_values[i] = change_value.copy()
		
		for i, change_sdl_value in change.nested_sdl_values.items():
			# TODO Call with_change recursively?
			# (MOSS and DIRTSAND don't, so it might not be necessary.)
			changed.nested_sdl_values[i] = change_sdl_value.copy()
		
		return changed


def guess_parse_sdl_blob(stream: typing.BinaryIO) -> typing.Tuple[SDLStreamHeader, GuessedSDLRecord]:
	header = SDLStreamHeader.from_stream(stream)
	
	try:
		record = GuessedSDLRecord.from_stream(stream)
	except ValueError as exc:
		raise ValueError(f"Failed to parse SDL blob of type {header.descriptor_name!r} v{header.descriptor_version}: {exc}")
	
	lookahead = stream.read(16)
	
	if lookahead:
		lookahead_desc = repr(lookahead)
		if len(lookahead) >= 16:
			lookahead_desc += "..."
		raise ValueError(f"SDL blob wasn't fully parsed and has trailing data: {lookahead_desc}")
	
	return header, record
