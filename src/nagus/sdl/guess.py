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


"""The "guessed" implementation of SDL de-/serialization.

Tries to parse SDL blobs *without* knowing their state descriptor.
Almost all SDL blobs that a client will produce can be parsed this way.
However,
SDL blobs produced by some other software (DIRTSAND in particular) won't work,
because the "guess-parser" relies on some not strictly necessary fields being present,
which are always written by Cyan's SDL implementation,
but not necessarily by other implementations.

This implementation also can't support migrating an SDL blob to a different version of the state descriptor.

Despite these limitations,
it's enough to run a server with no .sdl files at all on the server side.
It may also be useful as a debugging tool for inspecting unknown SDL blobs.
"""


import collections
import datetime
import io
import struct
import typing

from .. import structs
from . import common


MIN_REASONABLE_TIMESTAMP = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc).timestamp()


def format_simple_variable_data(data: bytes) -> str:
	"""Try to render the given simple variable data
	in a way that is more human-readable,
	but still unambiguous.
	
	This function tries to recognize certain data types
	by the length of the data
	and whether it matches some simple patterns:
	
	* STRING32 values are recognized if they start with a printable ASCII character.
		They are rendered as quoted Latin-1 strings.
	* PLKEY values are recognized if they don't use any reserved fields.
		They are rendered in the usual format used by NAGUS for UOIDs/keys.
	* TIME values are recognized if they have a valid microseconds field and aren't too far in the past.
		They are rendered using :func:`datetime.datetime.isoformat`.
	
	Unrecognized values are rendered using the standard bytes repr.
	"""
	
	if len(data) == 32 and 0x20 <= data[0] <= 0x7f:
		# STRING32
		s = data.rstrip(b"\x00").decode("latin-1")
		return repr(s)
	elif (
		len(data) >= 17 # minimum possible length for UOID
		and data[0] & ~0x3 == 0 # UOID flags valid
		and data[5] & ~0x1f == 0 # location flags valid
		and data[6] == 0 # location flags MSB unused
	):
		# PLKEY
		with io.BytesIO(data) as stream:
			try:
				uoid = structs.Uoid.from_stream(stream)
				tail_data = stream.read()
				if not tail_data:
					return str(uoid)
			except (EOFError, ValueError):
				pass
	elif len(data) == 8:
		# TIME
		timestamp, micros = structs.UNIFIED_TIME.unpack(data)
		if timestamp >= MIN_REASONABLE_TIMESTAMP and micros in range(1000000):
			try:
				return structs.unpack_unified_time(data).isoformat()
			except (struct.error, OverflowError):
				pass
	
	return repr(data)


class GuessedSimpleVariableValue(common.SimpleVariableValueBase):
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
		flags: common.SimpleVariableValueBase.Flags = common.SimpleVariableValueBase.Flags(0),
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
		if common.SimpleVariableValueBase.Flags.same_as_default in flags:
			assert not self.data
			flags &= ~common.SimpleVariableValueBase.Flags.same_as_default
			res = "<default>"
		else:
			res = format_simple_variable_data(self.data)
		
		if self.timestamp is None:
			assert common.SimpleVariableValueBase.Flags.has_timestamp not in flags
		else:
			assert common.SimpleVariableValueBase.Flags.has_timestamp in flags
			flags &= ~common.SimpleVariableValueBase.Flags.has_timestamp
			res += f" @ {self.timestamp.isoformat()}"
		
		if flags:
			res += f" ({flags})"
		
		if self.hint:
			res += f" # {self.hint!r}"
		
		return res
	
	def copy(self) -> "GuessedSimpleVariableValue":
		return GuessedSimpleVariableValue(
			hint=self.hint,
			flags=self.flags,
			timestamp=self.timestamp,
			data=self.data,
		)
	
	def write(self, stream: typing.BinaryIO) -> None:
		"""Write the full variable value back.
		
		This will only work correctly if written in place of a variable with a similar enough structure.
		"""
		
		self.base_write(stream)
		stream.write(self.data)


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


class GuessedNestedSDLVariableValue(common.NestedSDLVariableValueBase):
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
			super().__eq__(other)
			and self.variable_array_length == other.variable_array_length
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
		return GuessedNestedSDLVariableValue(
			hint=self.hint,
			variable_array_length=self.variable_array_length,
			values_indices=self.values_indices,
			values=dict(self.values),
		)
	
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


class GuessedSDLRecord(common.SDLRecordBase):
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
		flags: common.SDLRecordBase.Flags = common.SDLRecordBase.Flags(0),
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
		if common.SDLRecordBase.Flags.volatile in self.flags:
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
		return GuessedSDLRecord(
			flags=self.flags,
			simple_values_indices=self.simple_values_indices,
			simple_values=dict(self.simple_values),
			nested_sdl_values_indices=self.nested_sdl_values_indices,
			nested_sdl_values=dict(self.nested_sdl_values),
		)
	
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
			
			if lookahead == b"\x00":
				# No nested SDL variables either -
				# this is an empty blob.
				self.nested_sdl_values_indices = True
			elif _looks_like_start_of_variable(lookahead[1:]):
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


def guess_parse_sdl_blob(stream: typing.BinaryIO) -> typing.Tuple[common.SDLStreamHeader, GuessedSDLRecord]:
	header = common.SDLStreamHeader.from_stream(stream)
	
	try:
		record = GuessedSDLRecord.from_stream(stream)
	except ValueError as exc:
		raise ValueError(f"Failed to parse SDL blob of type {header.descriptor_id}: {exc}")
	
	lookahead = stream.read(16)
	
	if lookahead:
		lookahead_desc = repr(lookahead)
		if len(lookahead) >= 16:
			lookahead_desc += "..."
		raise ValueError(f"SDL blob wasn't fully parsed and has trailing data: {lookahead_desc}")
	
	return header, record
