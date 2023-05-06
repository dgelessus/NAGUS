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


class NotificationInfo(object):
	flags: int
	hint: bytes
	
	def __init__(self, flags: int = 0, hint: bytes = b"") -> None:
		super().__init__()
		
		self.flags = flags
		self.hint = hint
	
	def __repr__(self) -> str:
		parts = []
		
		if self.flags != 0:
			parts.append(f"flags=0x{self.flags:>#04x}")
		if self.hint:
			parts.append(f"hint={self.hint!r}")
		
		joined_parts = ", ".join(parts)
		return f"{type(self).__qualname__}({joined_parts})"
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "NotificationInfo":
		(flags,) = structs.read_exact(stream, 1)
		if flags != 0:
			raise ValueError(f"SDL variable notification info has unsupported flags set: 0x{flags:>02x}")
		
		hint = structs.read_safe_string(stream)
		return cls(flags, hint)
	
	def write(self, stream: typing.BinaryIO) -> None:
		stream.write(bytes([self.flags]))
		structs.write_safe_string(stream, self.hint)


class VariableValueBase(object):
	"""Base class for all SDL variable values (simple and nested SDL).
	
	Parses and writes the header structure common to all variables,
	i. e. the notification info.
	"""
	
	class Flags(structs.IntFlag):
		has_notification_info = 1 << 1
		
		supported = has_notification_info
	
	notification_info: typing.Optional[NotificationInfo]
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = collections.OrderedDict()
		if self.notification_info is None or self.notification_info.flags != 0 or self.notification_info.hint:
			fields["notification_info"] = repr(self.notification_info)
		return fields
	
	def __repr__(self) -> str:
		joined_fields = ", ".join(name + "=" + value for name, value in self.repr_fields().items())
		return f"{type(self).__qualname__}({joined_fields})"
	
	def base_read(self, stream: typing.BinaryIO) -> None:
		"""Read the part of the variable value structure that does *not* vary depending on the state descriptor."""
		
		(flags,) = structs.read_exact(stream, 1)
		flags = VariableValueBase.Flags(flags)
		if flags & ~VariableValueBase.Flags.supported:
			raise ValueError(f"SDL variable value header has unsupported flags set: {flags!r}")
		
		if flags & VariableValueBase.Flags.has_notification_info:
			self.notification_info = NotificationInfo.from_stream(stream)
		else:
			self.notification_info = None
	
	def base_write(self, stream: typing.BinaryIO) -> None:
		"""Write the part of the variable value structure that does *not* vary depending on the state descriptor."""
		
		flags = VariableValueBase.Flags(0)
		if self.notification_info is not None:
			flags |= VariableValueBase.Flags.has_notification_info
		stream.write(bytes([flags]))
		
		if self.notification_info is not None:
			self.notification_info.write(stream)


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
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["flags"] = repr(self.flags)
		if self.timestamp is not None:
			fields["timestamp"] = repr(self.timestamp)
		return fields
	
	def base_read(self, stream: typing.BinaryIO) -> None:
		super().base_read(stream)
		
		(flags,) = structs.read_exact(stream, 1)
		self.flags = SimpleVariableValueBase.Flags(flags)
		if self.flags & ~VariableValueBase.Flags.supported:
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


class GuessedSimpleVariableValue(SimpleVariableValueBase):
	"""A simple variable value whose size was guessed rather than known from a state descriptor.
	
	The variable's contents are not parsed further.
	The data field contains the data for *all* array elements,
	prefixed by the variable array length field
	(if any).
	"""
	
	data: bytes
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["data"] = repr(self.data)
		return fields
	
	def write(self, stream: typing.BinaryIO) -> None:
		"""Write the full variable value back.
		
		This will only work correctly if written in place of a variable with a similar enough structure.
		"""
		
		self.base_write(stream)
		stream.write(self.data)


class SimpleVariableValue(SimpleVariableValueBase):
	"""A parsed simple variable value."""
	
	values: typing.List[typing.Any]
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["values"] = repr(self.values)
		return fields
	
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


class GuessedNestedSDLVariableValue(NestedSDLVariableValueBase):
	variable_array_length: typing.Optional[int]
	values: "typing.Dict[int, GuessedSDLRecord]"
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		if self.variable_array_length is not None:
			fields["variable_array_length"] = repr(self.variable_array_length)
		fields["values"] = repr(self.values)
		return fields
	
	# TODO write


class NestedSDLVariableValue(NestedSDLVariableValueBase):
	variable_array_length: typing.Optional[int]
	values: "typing.Dict[int, SDLRecordBase]" # TODO Use SDLRecord class once it exists
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		if self.variable_array_length is not None:
			fields["variable_array_length"] = repr(self.variable_array_length)
		fields["values"] = repr(self.values)
		return fields
	
	# TODO read, write


class SDLRecordBase(object):
	"""Base class for the normal and guessing implementations of SDL records."""
	
	class Flags(structs.IntFlag):
		volatile = 1 << 0
		
		supported = volatile
	
	IO_VERSION: int = 6
	
	flags: "SDLRecordBase.Flags"
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = collections.OrderedDict()
		if self.flags:
			fields["flags"] = repr(self.flags)
		return fields
	
	def __repr__(self) -> str:
		joined_fields = ", ".join(name + "=" + value for name, value in self.repr_fields().items())
		return f"{type(self).__qualname__}({joined_fields})"
	
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


class GuessedSDLRecord(SDLRecordBase):
	"""An SDL record parsed by guessing the structure of an SDL blob rather than knowing it from a state descriptor.
	
	SDL blobs aren't meant to be parsed on their own -
	it's expected that the correct structure and data types are known from the corresponding state descriptor.
	In practice,
	it's usually possible to guess the basic structure from the SDL blob alone.
	
	This implementation works for many simple cases,
	but still breaks on some things encountered in practice.
	Nested SDL variables are currently ignored completely.
	"""
	
	# This is a variable header with the following contents:
	# 1 byte: flags with only has_notification_info set (always the case)
	# 1 byte: notification info flags set to 0 (always the case)
	# 2 bytes: empty SafeString (it's empty most of the time, but not always)
	VARIABLE_SIGNATURE = b"\x02\x00\x00\xf0"
	
	simple_values: typing.Dict[int, GuessedSimpleVariableValue]
	nested_sdl_values: typing.Dict[int, NestedSDLVariableValue]
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		if self.simple_values:
			fields["simple_values"] = repr(self.simple_values)
		if self.nested_sdl_values:
			fields["nested_sdl_values"] = repr(self.nested_sdl_values)
		return fields
	
	def read(self, stream: typing.BinaryIO) -> None:
		self.base_read(stream)
		
		# Assume that a single state descriptor doesn't contain more than 255 simple variables.
		# This seems to be a safe assumption currently -
		# for reference: STATEDESC city VERSION 43 has 151 variables.
		(simple_variable_count,) = structs.read_exact(stream, 1)
		
		self.simple_values = {}
		# Skip this entire thing if there are no simple variables in this blob.
		if simple_variable_count:
			pos = stream.tell()
			lookahead = stream.read(5)
			stream.seek(pos)
			
			if lookahead.startswith(GuessedSDLRecord.VARIABLE_SIGNATURE):
				simple_variables_have_indices = False
			elif lookahead[1:5] == GuessedSDLRecord.VARIABLE_SIGNATURE:
				simple_variables_have_indices = True
			else:
				raise ValueError(f"Unable to guess whether or not this SDL blob has indices before its simple variables. Simple variable count is {simple_variable_count}, lookahead afterwards is {lookahead!r}")
			
			# Last variable needs special treatment,
			# because it's followed by the nested SDL variable stuff and not another simple variable.
			rang = range(simple_variable_count)
			for i in rang:
				if simple_variables_have_indices:
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
				
				# Find end of data for this variable by looking for the start of the next variable.
				try:
					data_len = lookahead.index(GuessedSDLRecord.VARIABLE_SIGNATURE)
				except ValueError:
					# If there are no nested SDL variables,
					# the SDL blob will end shortly after the last simple variable
					# and there will be no next variable.
					# The last byte in the SDL blob will be the nested SDL variable count,
					# which will be 0.
					# (This assumes that a single state descriptor doesn't contain more than 255 nested SDL variables - see below.)
					# All data before that byte will be part of the last simple variable's data.
					if i == rang[-1] and len(lookahead) < 128 and lookahead.endswith(b"\x00"):
						data_len = len(lookahead) - 1
					else:
						raise ValueError(f"Unable to find end of data for variable {index} (index {i} in the blob). Lookahead is {lookahead!r}")
				else:
					if simple_variables_have_indices:
						# Exclude the next variable's index from this variable's data.
						assert data_len > 0
						data_len -= 1
				
				value.data = structs.read_exact(stream, data_len)
		
		# Assume that a single state descriptor doesn't contain more than 255 nested SDL variables.
		# This is an even safer assumption,
		# because nested SDL variables aren't used very often.
		(nested_sdl_variable_count,) = structs.read_exact(stream, 1)
		self.nested_sdl_values = {}
		# TODO Read nested SDL variable values
