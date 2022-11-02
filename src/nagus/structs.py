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


import datetime
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

UNIFIED_TIME = struct.Struct("<II")


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


def unpack_unified_time(data: bytes) -> datetime.datetime:
	timestamp, micros = UNIFIED_TIME.unpack(data)
	return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc) + datetime.timedelta(microseconds=micros)


def read_unified_time(stream: typing.BinaryIO) -> datetime.datetime:
	return unpack_unified_time(read_exact(stream, UNIFIED_TIME.size))


def pack_unified_time(dt: datetime.datetime) -> bytes:
	return UNIFIED_TIME.pack(int(dt.timestamp()), dt.microsecond)


def write_unified_time(stream: typing.BinaryIO, dt: datetime.datetime) -> None:
	stream.write(pack_unified_time(dt))
