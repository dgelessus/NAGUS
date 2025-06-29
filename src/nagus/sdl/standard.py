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


"""A "standard" implementation of the SDl system.

Currently very incomplete.
Once finished,
it will work based on .sdl files,
like the client and other servers do.
"""


import collections
import datetime
import typing

from .. import structs
from . import common


class SimpleVariableValue(common.SimpleVariableValueBase):
	"""A parsed simple variable value."""
	
	values: typing.List[typing.Any]
	
	def __init__(
		self,
		*,
		hint: typing.Optional[bytes] = None,
		flags: common.SimpleVariableValueBase.Flags = common.SimpleVariableValueBase.Flags(0),
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
		return SimpleVariableValue(
			hint=self.hint,
			flags=self.flags,
			timestamp=self.timestamp,
			values=list(self.values),
		)
	
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


class NestedSDLVariableValue(common.NestedSDLVariableValueBase):
	variable_array_length: typing.Optional[int]
	values: "typing.Dict[int, common.SDLRecordBase]" # TODO Use SDLRecord class once it exists
	
	def __init__(
		self,
		*,
		hint: typing.Optional[bytes] = None,
		variable_array_length: typing.Optional[int] = None,
		values: "typing.Dict[int, common.SDLRecordBase]",
	) -> None:
		super().__init__(hint=hint)
		
		self.variable_array_length = variable_array_length
		self.values = values
	
	def __eq__(self, other: object) -> bool:
		if not isinstance(other, NestedSDLVariableValue):
			return NotImplemented
		
		return (
			super().__eq__(other)
			and self.variable_array_length == other.variable_array_length
			and self.values == other.values
		)
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		if self.variable_array_length is not None:
			fields["variable_array_length"] = repr(self.variable_array_length)
		fields["values"] = repr(self.values)
		return fields
	
	def copy(self) -> "NestedSDLVariableValue":
		return NestedSDLVariableValue(
			hint=self.hint,
			variable_array_length=self.variable_array_length,
			values=dict(self.values),
		)
	
	# TODO read, write
