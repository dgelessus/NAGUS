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


"""Common data types and utilities for binary data (de)serialization."""


import abc
import collections
import datetime
import enum
import struct
import typing
import uuid


ZERO_DATETIME = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
ZERO_UUID = uuid.UUID("00000000-0000-0000-0000-000000000000")

INT8 = struct.Struct("<b")
INT16 = struct.Struct("<h")
INT32 = struct.Struct("<i")
INT64 = struct.Struct("<q")
# No UINT8 - just do stream.read(1) instead!
UINT16 = struct.Struct("<H")
UINT32 = struct.Struct("<I")
UINT64 = struct.Struct("<Q")

FLOAT32 = struct.Struct("<f")
FLOAT64 = struct.Struct("<d")

UNIFIED_TIME = struct.Struct("<II")

LOCATION = struct.Struct("<IH")
UOID_MID_PART = struct.Struct("<HI")
UOID_CLONE_IDS = struct.Struct("<HHI")

CLASS_INDEX = UINT16
NULL_CLASS_INDEX = 0x8000


class _TestEnum(enum.IntEnum):
	thing = 1


# mypy gets really confused by our custom IntEnum and IntFlag replacements.
if not typing.TYPE_CHECKING and str(_TestEnum.thing) == "1":
	# Starting with Python 3.11,
	# the __str__ of enum.IntEnum and enum.IntFlag subclasses always uses the plain integer value,
	# rather than using the enum constant name if possible
	# (as in Python 3.10 and earlier).
	# The old behavior was quite useful for debug logging,
	# so we define replacement IntEnum and IntFlag base classes if necessary to restore that behavior.
	# We can't just define these unconditionally,
	# because the IntFlag definition requires the boundary kwarg to the metaclass,
	# which was only added in Python 3.11.
	
	class IntEnum(int, enum.Enum):
		pass
	
	class IntFlag(int, enum.Flag, boundary=enum.FlagBoundary.KEEP):
		pass
else:
	IntEnum = enum.IntEnum
	IntFlag = enum.IntFlag


class FieldBasedRepr(abc.ABC):
	@abc.abstractmethod
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		return collections.OrderedDict()
	
	def __repr__(self) -> str:
		joined_fields = ", ".join(name + "=" + value for name, value in self.repr_fields().items())
		return f"{type(self).__name__}({joined_fields})"


def read_exact(stream: typing.BinaryIO, byte_count: int) -> bytes:
	"""Read byte_count bytes from the stream and raise an exception if too few bytes are read
	(i. e. if EOF was hit prematurely).
	"""
	
	data = stream.read(byte_count)
	if len(data) != byte_count:
		raise EOFError(f"Attempted to read {byte_count} bytes of data, but only got {len(data)} bytes")
	return data


def stream_unpack(stream: typing.BinaryIO, st: struct.Struct) -> tuple:
	"""Unpack data from the stream according to the struct st.
	
	The number of bytes to read is determined using st.size,
	so variable-sized structs cannot be used with this method.
	"""
	
	return st.unpack(read_exact(stream, st.size))


def unpack_fixed_utf_16_string(data: bytes) -> str:
	"""Decode a string from a fixed-length zero-terminated UTF-16 array."""
	
	return data.decode("utf-16-le").rstrip("\x00")


def pack_fixed_utf_16_string(string: str, wchar_count: int) -> bytes:
	"""Encode a string as a fixed-length zero-terminated UTF-16 array.
	
	The packed string is always zero-terminated.
	If ``string`` encoded as UTF-16 is ``wchar_count`` or more code units long,
	the last code unit in the array is set to U+0000
	and all further code units are truncated.
	"""
	
	dat = string.encode("utf-16-le")
	return dat[:2*(wchar_count-1)].ljust(2*wchar_count, b"\x00")


def _bit_flip(data: bytes) -> bytes:
	return bytes(~b & 0xff for b in data)


def read_safe_string(stream: typing.BinaryIO) -> bytes:
	(count,) = stream_unpack(stream, UINT16)
	if count & 0xf000:
		count &= ~0xf000
	else:
		# Cyan's open-sourced client code says:
		# "Backward compat hack - remove in a week or so (from 6/30/03)"
		# So we prrrobably don't need this anymore in the year of our Lord 2022.
		##read_exact(stream, 2)
		raise ValueError(f"SafeString byte count ({count:#x}) doesn't have high 4 bits set!")
	
	string = read_exact(stream, count)
	if string and string[0] & 0x80:
		string = _bit_flip(string)
	return string


def write_safe_string(stream: typing.BinaryIO, s: bytes) -> None:
	if len(s) > 0xfff:
		raise ValueError(f"String of length {len(s)} is too long to be packed into a SafeString")
	stream.write(UINT16.pack(len(s) | 0xf000))
	stream.write(_bit_flip(s))


def read_safe_wide_string(stream: typing.BinaryIO) -> str:
	(count,) = stream_unpack(stream, UINT16)
	count &= ~0xf000
	string = _bit_flip(read_exact(stream, 2*count)).decode("utf-16-le")
	(terminator,) = stream_unpack(stream, UINT16)
	if terminator != 0:
		raise ValueError(f"SafeWString terminator is non-zero: {terminator:#x}")
	return string


def write_safe_wide_string(stream: typing.BinaryIO, string: str) -> None:
	encoded = string.encode("utf-16-le")
	# Can't use len(string) - it will give the wrong result if the string contains code points above U+FFFF!
	utf_16_length = len(encoded) // 2
	if utf_16_length > 0xfff:
		raise ValueError(f"String of length {utf_16_length} is too long to be packed into a SafeWString")
	stream.write(UINT16.pack(utf_16_length | 0xf000))
	stream.write(_bit_flip(encoded))
	stream.write(b"\x00\x00")


def read_bit_vector(stream: typing.BinaryIO) -> int:
	(count,) = stream_unpack(stream, UINT32)
	bits = 0
	for i in range(count):
		(v,) = stream_unpack(stream, UINT32)
		bits |= v << 32*i
	return bits


def write_bit_vector(stream: typing.BinaryIO, bits: int) -> None:
	count = (bits.bit_length() + 31) // 32
	stream.write(UINT32.pack(count))
	for _ in range(count):
		stream.write(UINT32.pack(bits & 0xffffffff))
		bits >>= 32


def bit_numbers_from_int(bits: int) -> typing.Iterable[int]:
	if bits < 0:
		raise ValueError("Cannot convert negative integer to bit set")
	
	i = 0
	while bits:
		if bits & 1:
			yield i
		bits >>= 1
		i += 1


def unpack_unified_time(data: bytes) -> datetime.datetime:
	timestamp, micros = UNIFIED_TIME.unpack(data)
	return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc) + datetime.timedelta(microseconds=micros)


def read_unified_time(stream: typing.BinaryIO) -> datetime.datetime:
	return unpack_unified_time(read_exact(stream, UNIFIED_TIME.size))


def pack_unified_time(dt: datetime.datetime) -> bytes:
	return UNIFIED_TIME.pack(int(dt.timestamp()), dt.microsecond)


def write_unified_time(stream: typing.BinaryIO, dt: datetime.datetime) -> None:
	stream.write(pack_unified_time(dt))


# The original open-sourced client code had a debug assertion that only allowed age prefix numbers from -0xfe to 0xfe (inclusive).
# H'uru extended the range to -0xff to 0xfeff (inclusive).
# OpenUru later separately extended the range to -0x7ffe to 0x7ffe (inclusive).
# libHSPlasma parses sequence numbers incorrectly if the age prefix is 0x8000 or higher
# (and also the last few pages of age prefix 0x7fff).
# Going by the enum constants in plLocation in the open-sourced client code,
# age prefix numbers from -0xff to 0xfeff (inclusive) are possible,
# although age prefixes -0xff and 0xfeff have a few pages that conflict with reserved/special sequence numbers after encoding.
# The implementations below try to check for all of these weird corner cases
# without disallowing any legitimate and safe combinations.


def can_split_sequence_number(sequence_number: int) -> bool:
	"""Check whether the given sequence number can be safely split using :func:`split_sequence_number`."""
	
	# Sequence numbers up to and including 32 (0x20) are local-only or otherwise special.
	# Sequence number 0xff000000 is reserved for the server.
	# Sequence numbers 0xff000001 through 0xff010000 (inclusive) are in the reserved/global range,
	# but cannot be parsed meaningfully
	# (the age prefix number comes out as 0,
	# which is non-global and so should be encoded differently).
	# Sequence number 0xffffffff is invalid.
	return sequence_number in range(0x21, 0xffffffff) and sequence_number not in range(0xff000000, 0xff010001)


def split_sequence_number(sequence_number: int) -> typing.Tuple[int, int]:
	"""Split a sequence number (from a location) into its prefix (age) and suffix (page) parts.
	
	:raises ValueError: If the sequence number is out of range, ambiguous, or has a known special meaning.
	"""
	
	if sequence_number not in range(0x100000000):
		raise ValueError(f"Sequence number out of range: {sequence_number:#x}")
	elif not can_split_sequence_number(sequence_number):
		raise ValueError(f"Sequence number has special meaning and shouldn't be split: {sequence_number:#x}")
	
	if sequence_number in range(0xff010001, 0xffffffff):
		sequence_number -= 0xff000001
		age = -(sequence_number >> 16)
	else:
		if not (
			sequence_number in range(0x80000000)
			# Special case for VeeTsah (prefix number 40004, in the problematic range that libHSPlasma parses incorrectly).
			or sequence_number in range(0x9c440021, 0x9c450021)
		):
			raise ValueError(f"Potentially problematic sequence number: {sequence_number:#x}")
		
		sequence_number -= 33
		age = sequence_number >> 16
	
	page = sequence_number & 0xffff
	
	return age, page


def make_sequence_number(age: int, page: int) -> int:
	"""Combine a prefix (age) number and suffix (page) number into a single sequence number.
	
	:raises ValueError: If the inputs are out of range or the result would be ambiguous or conflict with known special seqeuence numbers.
	"""
	
	# Any age prefix numbers outside this range are definitely invalid.
	if age not in range(-0xff, 0xff00):
		raise ValueError(f"Age prefix number out of range: {age}")
	
	# Disallow age prefix numbers that might cause issues for OpenUru clients and libHSPlasma,
	# with an exception for VeeTsah,
	# because that's already widely deployed.
	# I might remove this check in the future.
	if not (
		age in range(-0xff, 0x7fff)
		# Special case for VeeTsah (in the problematic range that libHSPlasma parses incorrectly).
		or age == 40004
	):
		raise ValueError(f"Potentially problematic age prefix number: {age}")
	
	# Any page suffix numbers outside this range are definitely invalid.
	if page not in range(0x10000):
		raise ValueError(f"Page number out of range: {page}")
	
	# Prevent any combinations that would conflict with special/reserved locations after encoding.
	if (
		age == 0xfeff and page in range(0xffdf, 0x10000)
		or age == -0xff and page in {0xfffe, 0xffff}
	):
		raise ValueError(f"Page number out of range: {page}")
	
	if age < 0:
		sequence_number = (-age << 16) + page + 0xff000001
		assert sequence_number in range(0xff010001, 0xffffffff)
		return sequence_number
	else:
		sequence_number = (age << 16) + page + 33
		assert sequence_number in range(0x21, 0xff000000)
		return sequence_number


class Location(object):
	class Flags(IntFlag):
		local_only = 1 << 0
		volatile = 1 << 1
		reserved = 1 << 2
		built_in = 1 << 3
		itinerant = 1 << 4
	
	sequence_number: int
	flags: "Location.Flags"
	
	def __init__(self, sequence_number: int, flags: "Location.Flags" = Flags(0)) -> None:
		super().__init__()
		
		self.sequence_number = sequence_number
		self.flags = flags
	
	def __eq__(self, other: object) -> bool:
		if not isinstance(other, Location):
			return NotImplemented
		
		return self.sequence_number == other.sequence_number and self.flags == other.flags
	
	def __hash__(self) -> int:
		return hash((self.sequence_number, self.flags))
	
	def __repr__(self) -> str:
		parts = [hex(self.sequence_number)]
		if self.flags:
			parts.append(str(self.flags))
		joined_parts = ", ".join(parts)
		return f"{type(self).__qualname__}({joined_parts})"
	
	def __str__(self) -> str:
		if self.sequence_number == 0:
			seqnum_str = "fixed" # libHSPlasma calls this "virtual"
		else:
			try:
				age, page = split_sequence_number(self.sequence_number)
			except ValueError:
				seqnum_str = f"0x{self.sequence_number:>08x}"
			else:
				seqnum_str = f"{age}, {page}"
		
		if self.flags:
			return f"<loc: {seqnum_str}, {self.flags!s}>"
		else:
			return f"<loc: {seqnum_str}>"
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "Location":
		sequence_number, flags = stream_unpack(stream, LOCATION)
		return cls(sequence_number, Location.Flags(flags))
	
	def write(self, stream: typing.BinaryIO) -> None:
		stream.write(LOCATION.pack(self.sequence_number, self.flags))


class Uoid(FieldBasedRepr):
	class Flags(IntFlag):
		has_clone_ids = 1 << 0
		has_load_mask = 1 << 1
		
		supported = (
			has_clone_ids
			| has_load_mask
		)
	
	location: Location
	load_mask: int
	class_index: int
	id: int
	name: bytes
	clone_ids: typing.Optional[typing.Tuple[int, int]]
	
	def __init__(
		self,
		location: Location,
		class_index: int,
		id: int,
		name: bytes,
		clone_ids: typing.Optional[typing.Tuple[int, int]] = None,
		load_mask: int = 0xff,
	) -> None:
		super().__init__()
		
		self.location = location
		self.class_index = class_index
		self.id = id
		self.name = name
		self.clone_ids = clone_ids
		self.load_mask = load_mask
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["location"] = repr(self.location)
		if self.load_mask != 0xff:
			fields["load_mask"] = hex(self.load_mask)
		fields["class_index"] = f"0x{self.class_index:>04x}"
		fields["id"] = repr(self.id)
		fields["name"] = repr(self.name)
		if self.clone_ids is not None:
			fields["clone_ids"] = repr(self.clone_ids)
		return fields
	
	def __eq__(self, other: object) -> bool:
		if not isinstance(other, Uoid):
			return NotImplemented
		
		return (
			self.location == other.location
			and self.load_mask == other.load_mask
			and self.class_index == other.class_index
			and self.id == other.id
			and self.name == other.name
			and self.clone_ids == other.clone_ids
		)
	
	def __hash__(self) -> int:
		return hash((
			self.location,
			self.load_mask,
			self.class_index,
			self.id,
			self.name,
			self.clone_ids,
		))
	
	def __str__(self) -> str:
		if (
			self.location.sequence_number == 0
			and not self.location.flags
			and self.load_mask == 0xff
			and self.id == 0
			and self.clone_ids is None
		):
			# Compact form for global fixed key UOIDs.
			ret = f"fixed {self.name!r}, class=0x{self.class_index:>04x}"
		else:
			# For all other UOIDs,
			# display all fields that are present.
			ret = str(self.location)
			if self.load_mask != 0xff:
				ret += f", mask=0x{self.load_mask:>02x}"
			ret += f", class=0x{self.class_index:>04x}"
			ret += f", id={self.id}"
			ret += f", name={self.name!r}"
			if self.clone_ids is not None:
				clone_id, cloner_ki_number = self.clone_ids
				ret += f", clone #{clone_id} by avatar {cloner_ki_number}"
		
		return f"<{type(self).__qualname__}: {ret}>"
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "Uoid":
		(flags,) = read_exact(stream, 1)
		flags = Uoid.Flags(flags)
		if flags & ~Uoid.Flags.supported:
			raise ValueError(f"Uoid has unsupported flags set: {flags!r}")
		
		location = Location.from_stream(stream)
		
		if Uoid.Flags.has_load_mask in flags:
			(load_mask,) = read_exact(stream, 1)
			if load_mask == 0xff:
				raise ValueError(f"Uoid has explicit load mask, but it's the same as the implicit default 0xff")
		else:
			load_mask = 0xff
		
		class_index, object_id = stream_unpack(stream, UOID_MID_PART)
		name = read_safe_string(stream)
		
		if Uoid.Flags.has_clone_ids in flags:
			clone_id, ignored, cloner_ki_number = stream_unpack(stream, UOID_CLONE_IDS)
			if clone_id == 0:
				raise ValueError(f"Uoid has clone IDs, but the clone ID is 0")
			if ignored != 0:
				raise ValueError(f"Uoid has non-zero ignored field in the clone IDs: {ignored:#x}")
			if cloner_ki_number == 0:
				raise ValueError(f"Uoid has clone IDs, but the cloner KI number is 0")
			clone_ids = clone_id, cloner_ki_number
		else:
			clone_ids = None
		
		return cls(location, class_index, object_id, name, clone_ids, load_mask)
	
	@classmethod
	def key_from_stream(cls, stream: typing.BinaryIO) -> "typing.Optional[Uoid]":
		(non_null,) = read_exact(stream, 1)
		if non_null:
			return cls.from_stream(stream)
		else:
			return None
	
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
		
		stream.write(UOID_MID_PART.pack(self.class_index, self.id))
		write_safe_string(stream, self.name)
		
		if self.clone_ids is not None:
			clone_id, clone_player_id = self.clone_ids
			stream.write(UOID_CLONE_IDS.pack(clone_id, 0, clone_player_id))
	
	@classmethod
	def key_to_stream(cls, key: "typing.Optional[Uoid]", stream: typing.BinaryIO) -> None:
		if key is None:
			stream.write(b"\x00")
		else:
			stream.write(b"\x01")
			key.write(stream)
