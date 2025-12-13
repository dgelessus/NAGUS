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

"""Parses the general structure of .prp files."""

import collections
import hashlib
import io
import struct
import sys
import typing

from .. import structs


MOUL_PRP_VERSION_MAGIC = b"\x06\x00\x00\x00"

MOUL_PAGE_INFO_MID = struct.Struct("<HIIIH")
CLASS_VERSION = struct.Struct("<HH")
KEY_LIST_HEADER = struct.Struct("<IBI")
KEY_FOOTER = struct.Struct("<II")


class PRPHeader(structs.FieldBasedRepr):
	location: structs.Location
	age_name: bytes
	page_name: bytes
	plasma_major_version: int
	body_length: int # "checksum"
	data_offset: int
	index_offset: int
	class_versions: typing.List[typing.Tuple[int, int]]
	
	def __init__(
		self,
		location: structs.Location,
		age_name: bytes,
		page_name: bytes,
		plasma_major_version: int,
		body_length: int,
		data_offset: int,
		index_offset: int,
		class_versions: typing.List[typing.Tuple[int, int]],
	) -> None:
		super().__init__()
		
		self.location = location
		self.age_name = age_name
		self.page_name = page_name
		self.plasma_major_version = plasma_major_version
		self.body_length = body_length
		self.data_offset = data_offset
		self.index_offset = index_offset
		self.class_versions = class_versions
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["location"] = str(self.location)
		fields["age_name"] = repr(self.age_name)
		fields["page_name"] = repr(self.page_name)
		fields["plasma_major_version"] = repr(self.plasma_major_version)
		fields["body_length"] = hex(self.body_length)
		fields["data_offset"] = hex(self.data_offset)
		fields["index_offset"] = hex(self.index_offset)
		fields["class_versions"] = "[" + ", ".join(f"(0x{class_index:>04x}, {version})" for class_index, version in self.class_versions) + "]"
		return fields
	
	def as_multiline_str(self) -> typing.Iterable[str]:
		yield f"location: sequence number {self.location.sequence_number:#x}, flags 0x{self.location.flags.value:04x}"
		try:
			yield f"\tdecoded location: {self.location}"
		except Exception as exc:
			yield f"\tdecoded location: error: {type(exc).__module__}.{type(exc).__qualname__}: {exc}"
		
		yield f"age name: {self.age_name!r}"
		yield f"page name: {self.page_name!r}"
		yield f"Plasma 2.0 major version: {self.plasma_major_version}"
		yield f'PRP body length ("checksum"): {self.body_length:#x}'
		yield f"start of data at offset {self.data_offset:#x}"
		yield f"start of index at offset {self.index_offset:#x}"
		
		yield f"{len(self.class_versions)} class versions:"
		for class_index, version in self.class_versions:
			yield f"\tclass 0x{class_index:>04x}: version {version}"
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "PRPHeader":
		prp_version_magic = structs.read_exact(stream, 4)
		if prp_version_magic != MOUL_PRP_VERSION_MAGIC:
			raise ValueError(f"Not a valid MOUL(a) PRP: expected version/magic number {MOUL_PRP_VERSION_MAGIC.hex()}, but found {prp_version_magic.hex()}")
		
		location = structs.Location.from_stream(stream)
		age_name = structs.read_safe_string(stream)
		page_name = structs.read_safe_string(stream)
		plasma_major_version, body_length, data_offset, index_offset, class_versions_count = structs.stream_unpack(stream, MOUL_PAGE_INFO_MID)
		
		class_versions = []
		for _ in range(class_versions_count):
			class_versions.append(structs.stream_unpack(stream, CLASS_VERSION))
		
		return cls(location, age_name, page_name, plasma_major_version, body_length, data_offset, index_offset, class_versions)


class PRPKey(structs.FieldBasedRepr):
	uoid: structs.Uoid
	data_offset: int
	data_length: int
	
	def __init__(
		self,
		uoid: structs.Uoid,
		data_offset: int,
		data_length: int,
	) -> None:
		super().__init__()
		
		self.uoid = uoid
		self.data_offset = data_offset
		self.data_length = data_length
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["uoid"] = str(self.uoid)
		fields["data_offset"] = hex(self.data_offset)
		fields["data_length"] = hex(self.data_length)
		return fields
	
	def __str__(self) -> str:
		return f"{self.uoid}, offset {self.data_offset:#x}, length {self.data_length:#x}"
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "PRPKey":
		uoid = structs.Uoid.from_stream(stream)
		data_offset, data_length = structs.stream_unpack(stream, KEY_FOOTER)
		return cls(uoid, data_offset, data_length)


class PRPKeyList(structs.FieldBasedRepr):
	length: int
	flags: int
	keys: typing.List[PRPKey]
	
	def __init__(
		self,
		length: int,
		flags: int,
		keys: typing.List[PRPKey],
	) -> None:
		super().__init__()
		
		self.length = length
		self.flags = flags
		self.keys = keys
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["length"] = hex(self.length)
		fields["flags"] = f"0x{self.flags:>02x}"
		fields["keys"] = repr(self.keys)
		return fields
	
	def as_multiline_str(self) -> typing.Iterable[str]:
		yield f"length: {self.length:#x} bytes"
		yield f"flags: 0x{self.flags:>02x}"
		yield f"{len(self.keys)} keys:"
		for key in self.keys:
			yield "\t" + str(key)
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "PRPKeyList":
		length, flags, key_count = structs.stream_unpack(stream, KEY_LIST_HEADER)
		
		keys = []
		for _ in range(key_count):
			keys.append(PRPKey.from_stream(stream))
		
		return cls(length, flags, keys)


class PRPIndex(object):
	keys_by_class_index: typing.List[typing.Tuple[int, PRPKeyList]]
	
	def __init__(self, keys_by_class_index: typing.List[typing.Tuple[int, PRPKeyList]]) -> None:
		super().__init__()
		
		self.keys_by_class_index = keys_by_class_index
	
	def __repr__(self) -> str:
		return f"{type(self).__qualname__}({self.keys_by_class_index!r})"
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "PRPIndex":
		(class_count,) = structs.stream_unpack(stream, structs.UINT32)
		
		keys_by_class_index = []
		for _ in range(class_count):
			(class_index,) = structs.stream_unpack(stream, structs.UINT16)
			key_list = PRPKeyList.from_stream(stream)
			keys_by_class_index.append((class_index, key_list))
		
		return cls(keys_by_class_index)


def _uoid_sort_key(uoid: structs.Uoid) -> object:
	return uoid.location.sequence_number, uoid.location.flags, uoid.class_index, uoid.name, uoid.load_mask, uoid.id, uoid.clone_ids


def main() -> typing.NoReturn:
	_, prp_path = sys.argv
	
	with open(prp_path, "rb") as stream:
		header = PRPHeader.from_stream(stream)
		
		print("page info (PRP header):")
		for line in header.as_multiline_str():
			print("\t" + line)
		
		stream_length = stream.seek(0, io.SEEK_END)
		body_length = stream_length - header.data_offset
		if body_length != header.body_length:
			print(f'\tWARNING: "Checksum" mismatch! Page info declares body length {header.body_length:#x}, but actual body length is {body_length:#x} ({stream_length:#x} - {header.data_offset:#x}).')
			print("\tWARNING: Will try to continue reading anyway. Expect errors!")
		
		print()
		
		stream.seek(header.index_offset)
		index = PRPIndex.from_stream(stream)
		all_keys = []
		print(f"index: {len(index.keys_by_class_index)} classes:")
		for class_index, key_list in index.keys_by_class_index:
			all_keys.extend(key_list.keys)
			print(f"\tkey list for class 0x{class_index:>04x}:")
			for line in key_list.as_multiline_str():
				print("\t\t" + line)
		
		print()
		
		all_keys.sort(key=lambda pk: _uoid_sort_key(pk.uoid))
		
		print(f"hashes of object data for all {len(all_keys)} keys, sorted:")
		for prp_key in all_keys:
			stream.seek(prp_key.data_offset)
			data = structs.read_exact(stream, prp_key.data_length)
			hexdigest = hashlib.sha256(data).hexdigest()
			print(f"\t{prp_key.uoid}:")
			print(f"\t\t{len(data):#x} bytes, sha256:{hexdigest}")
	
	sys.exit(0)


if __name__ == "__main__":
	sys.exit(main())
