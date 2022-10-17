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


import struct
import typing
import uuid


ZERO_UUID = uuid.UUID("00000000-0000-0000-0000-000000000000")

# No UINT8 - just do stream.read(1) instead!
UINT16 = struct.Struct("<H")
UINT32 = struct.Struct("<I")
UINT64 = struct.Struct("<Q")


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
