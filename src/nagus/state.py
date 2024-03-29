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


"""Global state shared between all components of the server."""


import asyncio
import collections
import concurrent.futures
import datetime
import io
import logging
import sqlite3
import struct
import types
import typing
import uuid

from . import configuration
from . import structs


if typing.TYPE_CHECKING:
	# Avoid circular import
	from . import auth_server


logger = logging.getLogger(__name__)
logger_db = logger.getChild("db")
logger_states = logger.getChild("states")
logger_vault = logger.getChild("vault")

_T = typing.TypeVar("_T")

# This is the instance UUID for the public Ae'gura from DIRTSAND's default static_ages.ini.
# It seems that nothing actually depends on this specific UUID,
# and in fact MOSS uses a random UUID instead.
# I'm only using a fixed UUID for now
# so I don't have to implement any special logic for finding public age instances yet.
PUBLIC_AEGURA_UUID = uuid.UUID("7e0facea-dae1-4aec-a4ca-e76c05fdcfcf")
# There's only a single neighborhood for now -
# no need for dynamic DRC Hood creation if there can't be multiple accounts...
# This UUID is hardcoded in the client scripts (psnlBookshelf.py)
# as the only neighborhood to which visitors have access,
# so it seems convenient to use that for the default neighborhood.
DEFAULT_NEIGHBORHOOD_UUID = uuid.UUID("366f9aa1-c4c9-4c4c-a23a-cbe6896cc3b9")

VAULT_NODE_DATA_HEADER = struct.Struct("<Q")
VAULT_NODE_REF = struct.Struct("<III?")
PUBLIC_AGE_INSTANCE = struct.Struct("<16s128s128s128s2048siiII")


class VaultNodeType(structs.IntEnum):
	invalid = 0
	vnodemgr_low = 1
	player = 2
	age = 3
	vnodemgr_unused00 = 4
	vnodemgr_unused01 = 5
	vnodemgr_unused02 = 6
	vnodemgr_unused03 = 7
	vnodemgr_high = 21
	folder = 22
	player_info = 23
	system = 24
	image = 25
	text_note = 26
	sdl = 27
	age_link = 28
	chronicle = 29
	player_info_list = 30
	unused00 = 31
	unused01 = 32
	age_info = 33
	age_info_list = 34
	marker_game = 35


class VaultNodeFieldFlags(structs.IntFlag):
	node_id = 1 << 0
	create_time = 1 << 1
	modify_time = 1 << 2
	create_age_name = 1 << 3
	create_age_uuid = 1 << 4
	creator_account_uuid = 1 << 5
	creator_id = 1 << 6
	node_type = 1 << 7
	int32_1 = 1 << 8
	int32_2 = 1 << 9
	int32_3 = 1 << 10
	int32_4 = 1 << 11
	uint32_1 = 1 << 12
	uint32_2 = 1 << 13
	uint32_3 = 1 << 14
	uint32_4 = 1 << 15
	uuid_1 = 1 << 16
	uuid_2 = 1 << 17
	uuid_3 = 1 << 18
	uuid_4 = 1 << 19
	string64_1 = 1 << 20
	string64_2 = 1 << 21
	string64_3 = 1 << 22
	string64_4 = 1 << 23
	string64_5 = 1 << 24
	string64_6 = 1 << 25
	istring64_1 = 1 << 26
	istring64_2 = 1 << 27
	text_1 = 1 << 28
	text_2 = 1 << 29
	blob_1 = 1 << 30
	blob_2 = 1 << 31


def _uuid_from_db(uu: typing.Optional[bytes]) -> typing.Optional[uuid.UUID]:
	if uu is None:
		return None
	else:
		return uuid.UUID(bytes_le=uu)


def _uuid_to_db(uu: typing.Optional[uuid.UUID]) -> typing.Optional[bytes]:
	if uu is None:
		return None
	else:
		return uu.bytes_le


class VaultNodeData(structs.FieldBasedRepr):
	__slots__ = (
		"node_id",
		"create_time", "modify_time",
		"create_age_name", "create_age_uuid",
		"creator_account_uuid", "creator_id",
		"node_type",
		"int32_1", "int32_2", "int32_3", "int32_4",
		"uint32_1", "uint32_2", "uint32_3", "uint32_4",
		"uuid_1", "uuid_2", "uuid_3", "uuid_4",
		"string64_1", "string64_2", "string64_3", "string64_4", "string64_5", "string64_6",
		"istring64_1", "istring64_2",
		"text_1", "text_2",
		"blob_1", "blob_2",
	)
	
	node_id: typing.Optional[int]
	create_time: typing.Optional[int]
	modify_time: typing.Optional[int]
	create_age_name: typing.Optional[str]
	create_age_uuid: typing.Optional[uuid.UUID]
	creator_account_uuid: typing.Optional[uuid.UUID]
	creator_id: typing.Optional[int]
	node_type: typing.Optional[VaultNodeType]
	int32_1: typing.Optional[int]
	int32_2: typing.Optional[int]
	int32_3: typing.Optional[int]
	int32_4: typing.Optional[int]
	uint32_1: typing.Optional[int]
	uint32_2: typing.Optional[int]
	uint32_3: typing.Optional[int]
	uint32_4: typing.Optional[int]
	uuid_1: typing.Optional[uuid.UUID]
	uuid_2: typing.Optional[uuid.UUID]
	uuid_3: typing.Optional[uuid.UUID]
	uuid_4: typing.Optional[uuid.UUID]
	string64_1: typing.Optional[str]
	string64_2: typing.Optional[str]
	string64_3: typing.Optional[str]
	string64_4: typing.Optional[str]
	string64_5: typing.Optional[str]
	string64_6: typing.Optional[str]
	istring64_1: typing.Optional[str]
	istring64_2: typing.Optional[str]
	text_1: typing.Optional[str]
	text_2: typing.Optional[str]
	blob_1: typing.Optional[bytes]
	blob_2: typing.Optional[bytes]
	
	def __init__(
		self,
		node_id: typing.Optional[int] = None,
		create_time: typing.Optional[int] = None,
		modify_time: typing.Optional[int] = None,
		create_age_name: typing.Optional[str] = None,
		create_age_uuid: typing.Optional[uuid.UUID] = None,
		creator_account_uuid: typing.Optional[uuid.UUID] = None,
		creator_id: typing.Optional[int] = None,
		node_type: typing.Optional[VaultNodeType] = None,
		int32_1: typing.Optional[int] = None,
		int32_2: typing.Optional[int] = None,
		int32_3: typing.Optional[int] = None,
		int32_4: typing.Optional[int] = None,
		uint32_1: typing.Optional[int] = None,
		uint32_2: typing.Optional[int] = None,
		uint32_3: typing.Optional[int] = None,
		uint32_4: typing.Optional[int] = None,
		uuid_1: typing.Optional[uuid.UUID] = None,
		uuid_2: typing.Optional[uuid.UUID] = None,
		uuid_3: typing.Optional[uuid.UUID] = None,
		uuid_4: typing.Optional[uuid.UUID] = None,
		string64_1: typing.Optional[str] = None,
		string64_2: typing.Optional[str] = None,
		string64_3: typing.Optional[str] = None,
		string64_4: typing.Optional[str] = None,
		string64_5: typing.Optional[str] = None,
		string64_6: typing.Optional[str] = None,
		istring64_1: typing.Optional[str] = None,
		istring64_2: typing.Optional[str] = None,
		text_1: typing.Optional[str] = None,
		text_2: typing.Optional[str] = None,
		blob_1: typing.Optional[bytes] = None,
		blob_2: typing.Optional[bytes] = None,
	) -> None:
		super().__init__()
		
		self.node_id = node_id
		self.create_time = create_time
		self.modify_time = modify_time
		self.create_age_name = create_age_name
		self.create_age_uuid = create_age_uuid
		self.creator_account_uuid = creator_account_uuid
		self.creator_id = creator_id
		self.node_type = node_type
		self.int32_1 = int32_1
		self.int32_2 = int32_2
		self.int32_3 = int32_3
		self.int32_4 = int32_4
		self.uint32_1 = uint32_1
		self.uint32_2 = uint32_2
		self.uint32_3 = uint32_3
		self.uint32_4 = uint32_4
		self.uuid_1 = uuid_1
		self.uuid_2 = uuid_2
		self.uuid_3 = uuid_3
		self.uuid_4 = uuid_4
		self.string64_1 = string64_1
		self.string64_2 = string64_2
		self.string64_3 = string64_3
		self.string64_4 = string64_4
		self.string64_5 = string64_5
		self.string64_6 = string64_6
		self.istring64_1 = istring64_1
		self.istring64_2 = istring64_2
		self.text_1 = text_1
		self.text_2 = text_2
		self.blob_1 = blob_1
		self.blob_2 = blob_2
	
	def read(self, stream: typing.BinaryIO) -> None:
		(flags,) = structs.stream_unpack(stream, VAULT_NODE_DATA_HEADER)
		if flags >= 1 << 32:
			raise ValueError(f"Unsupported vault node data flags set: 0x{flags:>016x}")
		
		flags = VaultNodeFieldFlags(flags)
		
		def _unpack_uint32() -> int:
			(x,) = structs.stream_unpack(stream, structs.UINT32)
			return x
		
		def _unpack_int32() -> int:
			(x,) = structs.stream_unpack(stream, structs.INT32)
			return x
		
		def _unpack_uuid() -> uuid.UUID:
			return uuid.UUID(bytes_le=structs.read_exact(stream, 16))
		
		def _unpack_blob() -> bytes:
			length = _unpack_uint32()
			return structs.read_exact(stream, length)
		
		def _unpack_string() -> str:
			string = _unpack_blob().decode("utf-16-le")
			if not string.endswith("\x00"):
				raise ValueError(f"Missing zero terminator in vault node string: {string!r}")
			return string[:-1]
		
		if VaultNodeFieldFlags.node_id in flags:
			self.node_id = _unpack_uint32()
		
		if VaultNodeFieldFlags.create_time in flags:
			self.create_time = _unpack_uint32()
		
		if VaultNodeFieldFlags.modify_time in flags:
			self.modify_time = _unpack_uint32()
		
		if VaultNodeFieldFlags.create_age_name in flags:
			self.create_age_name = _unpack_string()
		
		if VaultNodeFieldFlags.create_age_uuid in flags:
			self.create_age_uuid = _unpack_uuid()
		
		if VaultNodeFieldFlags.creator_account_uuid in flags:
			self.creator_account_uuid = _unpack_uuid()
		
		if VaultNodeFieldFlags.creator_id in flags:
			self.creator_id = _unpack_uint32()
		
		if VaultNodeFieldFlags.node_type in flags:
			self.node_type = VaultNodeType(_unpack_uint32())
		
		if VaultNodeFieldFlags.int32_1 in flags:
			self.int32_1 = _unpack_int32()
		
		if VaultNodeFieldFlags.int32_2 in flags:
			self.int32_2 = _unpack_int32()
		
		if VaultNodeFieldFlags.int32_3 in flags:
			self.int32_3 = _unpack_int32()
		
		if VaultNodeFieldFlags.int32_4 in flags:
			self.int32_4 = _unpack_int32()
		
		if VaultNodeFieldFlags.uint32_1 in flags:
			self.uint32_1 = _unpack_uint32()
		
		if VaultNodeFieldFlags.uint32_2 in flags:
			self.uint32_2 = _unpack_uint32()
		
		if VaultNodeFieldFlags.uint32_3 in flags:
			self.uint32_3 = _unpack_uint32()
		
		if VaultNodeFieldFlags.uint32_4 in flags:
			self.uint32_4 = _unpack_uint32()
		
		if VaultNodeFieldFlags.uuid_1 in flags:
			self.uuid_1 = _unpack_uuid()
		
		if VaultNodeFieldFlags.uuid_2 in flags:
			self.uuid_2 = _unpack_uuid()
		
		if VaultNodeFieldFlags.uuid_3 in flags:
			self.uuid_3 = _unpack_uuid()
		
		if VaultNodeFieldFlags.uuid_4 in flags:
			self.uuid_4 = _unpack_uuid()
		
		if VaultNodeFieldFlags.string64_1 in flags:
			self.string64_1 = _unpack_string()
		
		if VaultNodeFieldFlags.string64_2 in flags:
			self.string64_2 = _unpack_string()
		
		if VaultNodeFieldFlags.string64_3 in flags:
			self.string64_3 = _unpack_string()
		
		if VaultNodeFieldFlags.string64_4 in flags:
			self.string64_4 = _unpack_string()
		
		if VaultNodeFieldFlags.string64_5 in flags:
			self.string64_5 = _unpack_string()
		
		if VaultNodeFieldFlags.string64_6 in flags:
			self.string64_6 = _unpack_string()
		
		if VaultNodeFieldFlags.istring64_1 in flags:
			self.istring64_1 = _unpack_string()
		
		if VaultNodeFieldFlags.istring64_2 in flags:
			self.istring64_2 = _unpack_string()
		
		if VaultNodeFieldFlags.text_1 in flags:
			self.text_1 = _unpack_string()
		
		if VaultNodeFieldFlags.text_2 in flags:
			self.text_2 = _unpack_string()
		
		if VaultNodeFieldFlags.blob_1 in flags:
			self.blob_1 = _unpack_blob()
		
		if VaultNodeFieldFlags.blob_2 in flags:
			self.blob_2 = _unpack_blob()
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "VaultNodeData":
		self = cls()
		self.read(stream)
		return self
	
	@classmethod
	def unpack(cls, data: bytes) -> "VaultNodeData":
		with io.BytesIO(data) as stream:
			self = cls.from_stream(stream)
			extra_data = stream.read()
			if extra_data:
				raise ValueError(f"Extra data at end of packed vault node data: {extra_data!r}")
			return self
	
	def pack(self) -> bytes:
		flags = VaultNodeFieldFlags(0)
		data = bytearray()
		
		def _pack_uint32(x: int) -> None:
			data.extend(structs.UINT32.pack(x))
		
		def _pack_int32(x: int) -> None:
			data.extend(structs.INT32.pack(x))
		
		def _pack_uuid(uu: uuid.UUID) -> None:
			data.extend(uu.bytes_le)
		
		def _pack_blob(blob: bytes) -> None:
			_pack_uint32(len(blob))
			data.extend(blob)
		
		def _pack_string(string: str) -> None:
			_pack_blob((string + "\x00").encode("utf-16-le"))
		
		if self.node_id is not None:
			flags |= VaultNodeFieldFlags.node_id
			_pack_uint32(self.node_id)
		
		if self.create_time is not None:
			flags |= VaultNodeFieldFlags.create_time
			_pack_uint32(self.create_time)
		
		if self.modify_time is not None:
			flags |= VaultNodeFieldFlags.modify_time
			_pack_uint32(self.modify_time)
		
		if self.create_age_name is not None:
			flags |= VaultNodeFieldFlags.create_age_name
			_pack_string(self.create_age_name)
		
		if self.create_age_uuid is not None:
			flags |= VaultNodeFieldFlags.create_age_uuid
			_pack_uuid(self.create_age_uuid)
		
		if self.creator_account_uuid is not None:
			flags |= VaultNodeFieldFlags.creator_account_uuid
			_pack_uuid(self.creator_account_uuid)
		
		if self.creator_id is not None:
			flags |= VaultNodeFieldFlags.creator_id
			_pack_uint32(self.creator_id)
		
		if self.node_type is not None:
			flags |= VaultNodeFieldFlags.node_type
			_pack_uint32(self.node_type)
		
		if self.int32_1 is not None:
			flags |= VaultNodeFieldFlags.int32_1
			_pack_int32(self.int32_1)
		
		if self.int32_2 is not None:
			flags |= VaultNodeFieldFlags.int32_2
			_pack_int32(self.int32_2)
		
		if self.int32_3 is not None:
			flags |= VaultNodeFieldFlags.int32_3
			_pack_int32(self.int32_3)
		
		if self.int32_4 is not None:
			flags |= VaultNodeFieldFlags.int32_4
			_pack_int32(self.int32_4)
		
		if self.uint32_1 is not None:
			flags |= VaultNodeFieldFlags.uint32_1
			_pack_uint32(self.uint32_1)
		
		if self.uint32_2 is not None:
			flags |= VaultNodeFieldFlags.uint32_2
			_pack_uint32(self.uint32_2)
		
		if self.uint32_3 is not None:
			flags |= VaultNodeFieldFlags.uint32_3
			_pack_uint32(self.uint32_3)
		
		if self.uint32_4 is not None:
			flags |= VaultNodeFieldFlags.uint32_4
			_pack_uint32(self.uint32_4)
		
		if self.uuid_1 is not None:
			flags |= VaultNodeFieldFlags.uuid_1
			_pack_uuid(self.uuid_1)
		
		if self.uuid_2 is not None:
			flags |= VaultNodeFieldFlags.uuid_2
			_pack_uuid(self.uuid_2)
		
		if self.uuid_3 is not None:
			flags |= VaultNodeFieldFlags.uuid_3
			_pack_uuid(self.uuid_3)
		
		if self.uuid_4 is not None:
			flags |= VaultNodeFieldFlags.uuid_4
			_pack_uuid(self.uuid_4)
		
		if self.string64_1 is not None:
			flags |= VaultNodeFieldFlags.string64_1
			_pack_string(self.string64_1)
		
		if self.string64_2 is not None:
			flags |= VaultNodeFieldFlags.string64_2
			_pack_string(self.string64_2)
		
		if self.string64_3 is not None:
			flags |= VaultNodeFieldFlags.string64_3
			_pack_string(self.string64_3)
		
		if self.string64_4 is not None:
			flags |= VaultNodeFieldFlags.string64_4
			_pack_string(self.string64_4)
		
		if self.string64_5 is not None:
			flags |= VaultNodeFieldFlags.string64_5
			_pack_string(self.string64_5)
		
		if self.string64_6 is not None:
			flags |= VaultNodeFieldFlags.string64_6
			_pack_string(self.string64_6)
		
		if self.istring64_1 is not None:
			flags |= VaultNodeFieldFlags.istring64_1
			_pack_string(self.istring64_1)
		
		if self.istring64_2 is not None:
			flags |= VaultNodeFieldFlags.istring64_2
			_pack_string(self.istring64_2)
		
		if self.text_1 is not None:
			flags |= VaultNodeFieldFlags.text_1
			_pack_string(self.text_1)
		
		if self.text_2 is not None:
			flags |= VaultNodeFieldFlags.text_2
			_pack_string(self.text_2)
		
		if self.blob_1 is not None:
			flags |= VaultNodeFieldFlags.blob_1
			_pack_blob(self.blob_1)
		
		if self.blob_2 is not None:
			flags |= VaultNodeFieldFlags.blob_2
			_pack_blob(self.blob_2)
		
		return VAULT_NODE_DATA_HEADER.pack(flags) + data
	
	@classmethod
	def from_db_row(cls, row: typing.Iterable[typing.Any]) -> "VaultNodeData":
		(
			node_id,
			create_time, modify_time,
			create_age_name, create_age_uuid,
			creator_account_uuid, creator_id,
			node_type,
			int32_1, int32_2, int32_3, int32_4,
			uint32_1, uint32_2, uint32_3, uint32_4,
			uuid_1, uuid_2, uuid_3, uuid_4,
			string64_1, string64_2, string64_3, string64_4, string64_5, string64_6,
			istring64_1, istring64_2,
			text_1, text_2,
			blob_1, blob_2,
		) = row
		
		return cls(
			node_id,
			create_time, modify_time,
			create_age_name, _uuid_from_db(create_age_uuid),
			_uuid_from_db(creator_account_uuid), creator_id,
			VaultNodeType(node_type),
			int32_1, int32_2, int32_3, int32_4,
			uint32_1, uint32_2, uint32_3, uint32_4,
			_uuid_from_db(uuid_1), _uuid_from_db(uuid_2), _uuid_from_db(uuid_3), _uuid_from_db(uuid_4),
			string64_1, string64_2, string64_3, string64_4, string64_5, string64_6,
			istring64_1, istring64_2,
			text_1, text_2,
			blob_1, blob_2,
		)
	
	def to_db_row(self) -> typing.Tuple[typing.Any, ...]:
		return (
			self.node_id,
			self.create_time, self.modify_time,
			self.create_age_name, _uuid_to_db(self.create_age_uuid),
			_uuid_to_db(self.creator_account_uuid), self.creator_id,
			self.node_type,
			self.int32_1, self.int32_2, self.int32_3, self.int32_4,
			self.uint32_1, self.uint32_2, self.uint32_3, self.uint32_4,
			_uuid_to_db(self.uuid_1), _uuid_to_db(self.uuid_2), _uuid_to_db(self.uuid_3), _uuid_to_db(self.uuid_4),
			self.string64_1, self.string64_2, self.string64_3, self.string64_4, self.string64_5, self.string64_6,
			self.istring64_1, self.istring64_2,
			self.text_1, self.text_2,
			self.blob_1, self.blob_2,
		)
	
	def to_db_named_values(self) -> typing.Mapping[str, typing.Any]:
		columns: typing.Dict[str, typing.Any] = {}
		
		if self.node_id is not None:
			columns["NodeId"] = self.node_id
		
		if self.create_time is not None:
			columns["CreateTime"] = self.create_time
		
		if self.modify_time is not None:
			columns["ModifyTime"] = self.modify_time
		
		if self.create_age_name is not None:
			columns["CreateAgeName"] = self.create_age_name
		
		if self.create_age_uuid is not None:
			columns["CreateAgeUuid"] = _uuid_to_db(self.create_age_uuid)
		
		if self.creator_account_uuid is not None:
			columns["CreatorAcct"] = _uuid_to_db(self.creator_account_uuid)
		
		if self.creator_id is not None:
			columns["CreatorId"] = self.creator_id
		
		if self.node_type is not None:
			columns["NodeType"] = self.node_type
		
		if self.int32_1 is not None:
			columns["Int32_1"] = self.int32_1
		
		if self.int32_2 is not None:
			columns["Int32_2"] = self.int32_2
		
		if self.int32_3 is not None:
			columns["Int32_3"] = self.int32_3
		
		if self.int32_4 is not None:
			columns["Int32_4"] = self.int32_4
		
		if self.uint32_1 is not None:
			columns["UInt32_1"] = self.uint32_1
		
		if self.uint32_2 is not None:
			columns["UInt32_2"] = self.uint32_2
		
		if self.uint32_3 is not None:
			columns["UInt32_3"] = self.uint32_3
		
		if self.uint32_4 is not None:
			columns["UInt32_4"] = self.uint32_4
		
		if self.uuid_1 is not None:
			columns["Uuid_1"] = _uuid_to_db(self.uuid_1)
		
		if self.uuid_2 is not None:
			columns["Uuid_2"] = _uuid_to_db(self.uuid_2)
		
		if self.uuid_3 is not None:
			columns["Uuid_3"] = _uuid_to_db(self.uuid_3)
		
		if self.uuid_4 is not None:
			columns["Uuid_4"] = _uuid_to_db(self.uuid_4)
		
		if self.string64_1 is not None:
			columns["String64_1"] = self.string64_1
		
		if self.string64_2 is not None:
			columns["String64_2"] = self.string64_2
		
		if self.string64_3 is not None:
			columns["String64_3"] = self.string64_3
		
		if self.string64_4 is not None:
			columns["String64_4"] = self.string64_4
		
		if self.string64_5 is not None:
			columns["String64_5"] = self.string64_5
		
		if self.string64_6 is not None:
			columns["String64_6"] = self.string64_6
		
		if self.istring64_1 is not None:
			columns["IString64_1"] = self.istring64_1
		
		if self.istring64_2 is not None:
			columns["IString64_2"] = self.istring64_2
		
		if self.text_1 is not None:
			columns["Text_1"] = self.text_1
		
		if self.text_2 is not None:
			columns["Text_2"] = self.text_2
		
		if self.blob_1 is not None:
			columns["Blob_1"] = self.blob_1
		
		if self.blob_2 is not None:
			columns["Blob_2"] = self.blob_2
		
		return columns
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		
		for attr in type(self).__slots__:
			value = getattr(self, attr)
			if value is not None:
				if isinstance(value, str):
					rep = repr(value)
				else:
					rep = str(value)
				
				fields[attr] = rep
		
		return fields


class VaultNodeRef(object):
	__slots__ = (
		"parent_id",
		"child_id",
		"owner_id",
		"seen",
	)
	
	parent_id: int
	child_id: int
	owner_id: int
	seen: bool
	
	def __init__(self, parent_id: int, child_id: int, owner_id: int = 0, seen: bool = False) -> None:
		super().__init__()
		
		self.parent_id = parent_id
		self.child_id = child_id
		self.owner_id = owner_id
		self.seen = seen
	
	def pack(self) -> bytes:
		return VAULT_NODE_REF.pack(self.parent_id, self.child_id, self.owner_id, self.seen)
	
	def __str__(self) -> str:
		desc = f"{self.parent_id} -> {self.child_id}"
		if self.owner_id:
			desc += f", owner: {self.owner_id}"
		if self.seen:
			desc += f", seen: {self.seen}"
		
		return f"<ref {desc}>"
	
	def __repr__(self) -> str:
		rep = f"{type(self).__qualname__}({self.parent_id}, {self.child_id}"
		if self.owner_id:
			rep += f", owner_id={self.owner_id}"
		if self.seen:
			rep += f", seen={self.seen}"
		rep += ")"
		return rep


class VaultNodeFolderType(structs.IntEnum):
	user_defined = 0
	inbox = 1
	buddy_list = 2
	ignore_list = 3
	people_i_know_about = 4
	vault_mgr_global_data = 5
	chronicle = 6
	avatar_outfit = 7
	age_type_journal = 8
	sub_ages = 9
	device_inbox = 10
	hood_members = 11
	all_players = 12
	age_members = 13
	age_journals = 14
	age_devices = 15
	age_instance_sdl = 16
	age_global_sdl = 17
	can_visit = 18
	age_owners = 19
	all_age_global_sdl_nodes = 20
	player_info = 21
	public_ages = 22
	ages_i_own = 23
	ages_i_can_visit = 24
	avatar_closet = 25
	age_info = 26
	system = 27
	player_invite = 28
	ccr_players = 29
	global_inbox = 30
	child_ages = 31
	game_scores = 32


class PublicAgeInstance(structs.FieldBasedRepr):
	instance_uuid: uuid.UUID
	file_name: str
	instance_name: str
	user_defined_name: str
	description: str
	sequence_number: int
	language: int
	owner_count: int
	current_population: int
	
	def __init__(
		self,
		instance_uuid: uuid.UUID,
		file_name: str,
		instance_name: str,
		user_defined_name: str,
		description: str,
		sequence_number: int,
		language: int,
		owner_count: int,
		current_population: int,
	) -> None:
		super().__init__()
		
		self.instance_uuid = instance_uuid
		self.file_name = file_name
		self.instance_name = instance_name
		self.user_defined_name = user_defined_name
		self.description = description
		self.sequence_number = sequence_number
		self.language = language
		self.owner_count = owner_count
		self.current_population = current_population
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["instance_uuid"] = str(self.instance_uuid)
		fields["file_name"] = repr(self.file_name)
		fields["instance_name"] = repr(self.instance_name)
		fields["user_defined_name"] = repr(self.user_defined_name)
		fields["description"] = repr(self.description)
		fields["sequence_number"] = repr(self.sequence_number)
		fields["language"] = repr(self.language)
		fields["owner_count"] = repr(self.owner_count)
		fields["current_population"] = repr(self.current_population)
		return fields
	
	@classmethod
	def unpack(cls, data: bytes) -> "PublicAgeInstance":
		(
			instance_uuid,
			file_name,
			instance_name,
			user_defined_name,
			description,
			sequence_number,
			language,
			owner_count,
			current_population,
		) = PUBLIC_AGE_INSTANCE.unpack(data)
		return cls(
			instance_uuid=uuid.UUID(bytes_le=instance_uuid),
			file_name=structs.unpack_fixed_utf_16_string(file_name),
			instance_name=structs.unpack_fixed_utf_16_string(instance_name),
			user_defined_name=structs.unpack_fixed_utf_16_string(user_defined_name),
			description=structs.unpack_fixed_utf_16_string(description),
			sequence_number=sequence_number,
			language=language,
			owner_count=owner_count,
			current_population=current_population,
		)
	
	def pack(self) -> bytes:
		return PUBLIC_AGE_INSTANCE.pack(
			self.instance_uuid.bytes_le,
			structs.pack_fixed_utf_16_string(self.file_name, 64),
			structs.pack_fixed_utf_16_string(self.instance_name, 64),
			structs.pack_fixed_utf_16_string(self.user_defined_name, 64),
			structs.pack_fixed_utf_16_string(self.description, 1024),
			self.sequence_number,
			self.language,
			self.owner_count,
			self.current_population,
		)


class AvatarInfo(object):
	player_node_id: int
	name: str
	shape: str
	explorer: int
	
	def __init__(self, player_node_id: int, name: str, shape: str, explorer: int) -> None:
		super().__init__()
		
		self.player_node_id = player_node_id
		self.name = name
		self.shape = shape
		self.explorer = explorer


class Cursor(typing.AsyncContextManager["Cursor"], typing.AsyncIterable[sqlite3.Row]):
	"""Basic async wrapper around the synchronous :class:`sqlite3.Cursor` API."""
	
	db: "Database"
	cursor: sqlite3.Cursor
	
	def __init__(self, db: "Database", cursor: sqlite3.Cursor) -> None:
		super().__init__()
		
		self.db = db
		self.cursor = cursor
	
	async def __aenter__(self) -> "Cursor":
		return self
	
	async def __aexit__(
		self,
		exc_type: typing.Optional[typing.Type[BaseException]],
		exc_val: typing.Optional[BaseException],
		exc_tb: typing.Optional[types.TracebackType],
	) -> typing.Optional[bool]:
		await self.close()
		return False
	
	async def __aiter__(self) -> typing.AsyncIterator[sqlite3.Row]:
		row = await self.fetchone()
		while row is not None:
			yield row
			row = await self.fetchone()
	
	async def close(self) -> None:
		await self.db._run(self.cursor.close)
	
	async def execute(self, sql: str, parameters: typing.Iterable[typing.Any] = ()) -> "Cursor":
		await self.db._run(self.cursor.execute, sql, parameters)
		return self
	
	async def executemany(self, sql: str, seq_of_parameters: typing.Iterable[typing.Iterable[typing.Any]]) -> "Cursor":
		await self.db._run(self.cursor.executemany, sql, seq_of_parameters)
		return self
	
	async def executescript(self, sql: str) -> "Cursor":
		await self.db._run(self.cursor.executescript, sql)
		return self
	
	async def fetchone(self) -> typing.Optional[sqlite3.Row]:
		return await self.db._run(self.cursor.fetchone)
	
	async def fetchmany(self, size: typing.Optional[int]) -> typing.List[sqlite3.Row]:
		return await self.db._run(self.cursor.fetchmany, size)
	
	async def fetchall(self) -> typing.List[sqlite3.Row]:
		return await self.db._run(self.cursor.fetchall)
	
	@property
	def lastrowid(self) -> typing.Any:
		return self.cursor.lastrowid
	
	@property
	def rowcount(self) -> typing.Any:
		return self.cursor.rowcount


class Database(typing.AsyncContextManager[None]):
	conn: sqlite3.Connection
	executor: concurrent.futures.Executor
	
	def __init__(self, connection: sqlite3.Connection, executor: concurrent.futures.Executor) -> None:
		super().__init__()
		
		self.conn = connection
		self.executor = executor
	
	@classmethod
	async def connect(cls, database: typing.Union[str, bytes], *, uri: bool = False) -> "Database":
		executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
		conn = await asyncio.get_event_loop().run_in_executor(executor, lambda: sqlite3.connect(database, uri=uri))
		logger_db.info("Loaded NAGUS database at %s %r", "URI" if uri else "path", database)
		return cls(conn, executor)
	
	def _run(self, func: typing.Callable[..., _T], *args: typing.Any) -> asyncio.Future[_T]:
		return asyncio.get_event_loop().run_in_executor(self.executor, func, *args)
	
	async def __aenter__(self) -> None:
		await self._run(self.conn.__enter__)
	
	async def __aexit__(
		self,
		exc_type: typing.Optional[typing.Type[BaseException]],
		exc_val: typing.Optional[BaseException],
		exc_tb: typing.Optional[types.TracebackType],
	) -> typing.Optional[bool]:
		return await self._run(self.conn.__exit__, exc_type, exc_val, exc_tb)
	
	async def close(self) -> None:
		await self._run(self.conn.close)
	
	async def cursor(self) -> Cursor:
		return Cursor(self, await self._run(self.conn.cursor))


class VaultNodeNotFound(Exception):
	pass


class VaultNodeAlreadyExists(Exception):
	pass


class VaultSemanticError(Exception):
	pass


class AgeInstanceNotFound(Exception):
	pass


class AgeInstanceAlreadyExists(Exception):
	pass


class AvatarNotFound(Exception):
	pass


class AvatarAlreadyExists(Exception):
	pass


class ObjectStateNotFound(Exception):
	pass


class ServerState(object):
	config: configuration.Configuration
	loop: asyncio.AbstractEventLoop
	db: Database
	
	background_tasks: typing.Set[asyncio.Task[typing.Any]]
	status_message: str
	# All auth server connections that are currently considered "usable".
	# These are all connections that are either connected or recently disconnected and not timed out yet,
	# excluding ones that disconnected so early that they have no state that could be preserved
	# and ones that were forcibly kicked by the server and can never reconnect.
	# The key is the connection's token UUID.
	auth_connections: typing.Dict[uuid.UUID, "auth_server.AuthConnection"]
	# The subset of auth server connections that are currently active as an avatar.
	# The key is the active avatar's KI number.
	auth_connections_by_ki_number: typing.Dict[int, "auth_server.AuthConnection"]
	
	# The following attributes are only initialized in setup_database,
	# because they are sometimes derived from the database and not just the configs.
	public_aegura_instance_uuid: typing.Optional[uuid.UUID]
	default_neighborhood_instance_uuid: typing.Optional[uuid.UUID]
	
	def __init__(self, config: configuration.Configuration, loop: asyncio.AbstractEventLoop, db: Database) -> None:
		super().__init__()
		
		self.config = config
		self.loop = loop
		self.db = db
		
		self.background_tasks = set()
		self.status_message = config.server_status_message
		self.auth_connections = {}
		self.auth_connections_by_ki_number = {}
	
	def add_background_task(self, task: asyncio.Task[typing.Any]) -> None:
		"""Keep a reference to a background task while it's running.
		
		The reference to the task is dropped once it's done running.
		If the task is already done,
		this method does nothing.
		
		This is based on the recommendation in the docs for :func:`asyncio.create_task`,
		which says that a background task may not run reliably if the task object is garbage collected while running.
		"""
		
		if task.done():
			return
		
		task.add_done_callback(self.background_tasks.discard)
		self.background_tasks.add(task)
	
	def create_background_task(self, coro: typing.Coroutine[typing.Any, typing.Any, typing.Any]) -> None:
		self.add_background_task(self.loop.create_task(coro))
	
	async def setup_database(self) -> None:
		async with self.db, await self.db.cursor() as cursor:
			try:
				await cursor.executescript(f"pragma journal_mode = {self.config.database_journal_mode};")
			except sqlite3.Error as exc:
				raise ValueError(f"Invalid SQLite journal mode: {self.config.database_journal_mode!r}: {exc}")
			
			await cursor.executescript("""
			pragma foreign_keys = on;
			
			create table if not exists VaultNodes (
				NodeId integer primary key not null,
				CreateTime integer not null,
				ModifyTime integer not null,
				CreateAgeName text,
				CreateAgeUuid blob,
				CreatorAcct blob not null,
				CreatorId integer not null,
				NodeType integer not null,
				Int32_1 integer,
				Int32_2 integer,
				Int32_3 integer,
				Int32_4 integer,
				UInt32_1 integer,
				UInt32_2 integer,
				UInt32_3 integer,
				UInt32_4 integer,
				Uuid_1 blob,
				Uuid_2 blob,
				Uuid_3 blob,
				Uuid_4 blob,
				String64_1 text,
				String64_2 text,
				String64_3 text,
				String64_4 text,
				String64_5 text,
				String64_6 text,
				IString64_1 text collate nocase,
				IString64_2 text collate nocase,
				Text_1 text,
				Text_2 text,
				Blob_1 blob,
				Blob_2 blob
			);
			
			create table if not exists VaultNodeRefs (
				ParentId integer not null,
				ChildId integer not null,
				OwnerId integer not null default 0,
				Seen integer not null default true,
				
				primary key (ParentId, ChildId),
				foreign key (ParentId) references VaultNodes(NodeId),
				foreign key (ChildId) references VaultNodes(NodeId)
				-- No foreign key constraint for OwnerId
				-- because it may be 0 instead of an actual node ID.
				-- foreign key (OwnerId) references VaultNodes(NodeId)
			);
			
			create table if not exists AgeInstanceObjectStates (
				AgeVaultNodeId integer not null,
				Uoid blob not null,
				StateDescName text not null,
				SdlBlob blob not null,
				
				primary key (AgeVaultNodeId, Uoid, StateDescName),
				foreign key (AgeVaultNodeId) references VaultNodes(NodeId)
			);
			""")
		
		try:
			system = await self.find_system_vault_node()
		except VaultNodeNotFound:
			logger_vault.info("No system node found in vault! Assuming this is a fresh database, so creating a new one.")
			system = await self.create_vault_node(VaultNodeData(creator_account_uuid=structs.ZERO_UUID, creator_id=0, node_type=VaultNodeType.system))
			global_inbox_folder = await self.create_vault_node(VaultNodeData(creator_account_uuid=structs.ZERO_UUID, creator_id=0, node_type=VaultNodeType.folder, int32_1=VaultNodeFolderType.global_inbox))
			await self.add_vault_node_ref(VaultNodeRef(system, global_inbox_folder))
		
		logger_vault.debug("System node: %d", system)
		
		try:
			all_players_id = await self.find_all_players_vault_node()
		except VaultNodeNotFound:
			logger_vault.info("No All Players list node found in vault! Creating a new one.")
			all_players_id = await self.create_vault_node(VaultNodeData(creator_account_uuid=structs.ZERO_UUID, creator_id=0, node_type=VaultNodeType.player_info_list, int32_1=VaultNodeFolderType.all_players))
		
		logger_vault.debug("All Players list node: %d", all_players_id)
		
		for static_age in self.config.ages_static_ages_config:
			instance_uuid = await self.setup_static_age_instance(
				age_file_name=static_age.age_file_name,
				instance_uuid=static_age.instance_uuid,
				instance_name=static_age.instance_name,
				user_defined_name=static_age.user_defined_name,
			)
			
			if self.config.ages_public_aegura_instance == configuration.WhichStaticAgeInstance.static and static_age.age_file_name == structs.AEGURA_AGE_NAME:
				assert not hasattr(self, "public_aegura_instance_uuid")
				self.public_aegura_instance_uuid = instance_uuid
			elif self.config.ages_default_neighborhood_instance == configuration.WhichStaticAgeInstance.static and static_age.age_file_name == structs.NEIGHBORHOOD_AGE_NAME:
				assert not hasattr(self, "default_neighborhood_instance_uuid")
				self.default_neighborhood_instance_uuid = instance_uuid
		
		if isinstance(self.config.ages_public_aegura_instance, uuid.UUID):
			self.public_aegura_instance_uuid = self.config.ages_public_aegura_instance
		elif self.config.ages_public_aegura_instance == configuration.WhichStaticAgeInstance.static:
			assert hasattr(self, "public_aegura_instance_uuid")
		elif self.config.ages_public_aegura_instance == configuration.WhichStaticAgeInstance.none:
			self.public_aegura_instance_uuid = None
		else:
			raise AssertionError(f"Unhandled value for config option ages.public_aegura_instance: {self.config.ages_public_aegura_instance!r}")
		
		logger_vault.debug("Public Ae'gura instance: %s", self.public_aegura_instance_uuid)
		
		if isinstance(self.config.ages_default_neighborhood_instance, uuid.UUID):
			self.default_neighborhood_instance_uuid = self.config.ages_default_neighborhood_instance
		elif self.config.ages_default_neighborhood_instance == configuration.WhichStaticAgeInstance.static:
			assert hasattr(self, "default_neighborhood_instance_uuid")
		elif self.config.ages_default_neighborhood_instance == configuration.WhichStaticAgeInstance.none:
			self.default_neighborhood_instance_uuid = None
		else:
			raise AssertionError(f"Unhandled value for config option ages.default_neighborhood_instance: {self.config.ages_default_neighborhood_instance!r}")
		
		logger_vault.debug("Default neighborhood instance: %s", self.default_neighborhood_instance_uuid)
		
		logger_db.debug("Finished setting up the NAGUS database")
	
	async def fetch_vault_node(self, node_id: int) -> VaultNodeData:
		async with await self.db.cursor() as cursor:
			await cursor.execute("select * from VaultNodes where NodeId = ?", (node_id,))
			row = await cursor.fetchone()
			if row is None:
				raise VaultNodeNotFound(f"Couldn't find vault node with ID {node_id}")
			else:
				return VaultNodeData.from_db_row(row)
	
	async def find_vault_nodes(self, template: VaultNodeData, *, parent_id: typing.Optional[int] = None) -> typing.AsyncIterable[int]:
		fields = template.to_db_named_values()
		cond_parts = []
		values = []
		for name, value in fields.items():
			cond_parts.append(f"{name} = ?")
			values.append(value)
		
		if cond_parts:
			cond = " and ".join(cond_parts)
		else:
			cond = "1=1"
		
		async with await self.db.cursor() as cursor:
			if parent_id is None:
				await cursor.execute(f"select NodeId from VaultNodes where {cond}", values)
			else:
				await cursor.execute(
					f"""
					select NodeId
					from VaultNodes
					join VaultNodeRefs on NodeId = ChildId
					where ParentId = ? and {cond}
					""",
					[parent_id] + values,
				)
			
			async for (node_id,) in cursor:
				yield node_id
	
	async def find_unique_vault_node(self, template: VaultNodeData, *, parent_id: typing.Optional[int] = None) -> int:
		found_node_id: typing.Optional[int] = None
		async for node_id in self.find_vault_nodes(template, parent_id=parent_id):
			if found_node_id is not None:
				logger_vault.warning(
					"Found multiple vault nodes matching the template %r with parent %r: %d and %d (and possibly more)! Ignoring all except the first one.",
					template, parent_id, found_node_id, node_id,
				)
				break
			
			found_node_id = node_id
		
		if found_node_id is None:
			raise VaultNodeNotFound(f"Found no vault node matching the template {template!r} with parent {parent_id}")
		else:
			return found_node_id
	
	async def find_system_vault_node(self) -> int:
		return await self.find_unique_vault_node(VaultNodeData(node_type=VaultNodeType.system))
	
	async def find_all_players_vault_node(self) -> int:
		return await self.find_unique_vault_node(VaultNodeData(node_type=VaultNodeType.player_info_list, int32_1=VaultNodeFolderType.all_players))
	
	async def create_vault_node(self, data: VaultNodeData) -> int:
		data.create_time = data.modify_time = int(datetime.datetime.now().timestamp())
		
		logger_vault.debug("Creating vault node: %r", data)
		
		fields = data.to_db_named_values()
		names = ", ".join(fields.keys())
		placeholders = ", ".join("?" * len(fields))
		values = list(fields.values())
		
		async with self.db, await self.db.cursor() as cursor:
			await cursor.execute(f"insert into VaultNodes ({names}) values ({placeholders}) returning NodeId", values)
			row = await cursor.fetchone()
			assert row is not None
			(node_id,) = row
			return node_id
	
	async def update_vault_node(self, node_id: int, data: VaultNodeData, revision_id: uuid.UUID) -> None:
		data.modify_time = int(datetime.datetime.now().timestamp())
		
		logger_vault.debug("Updating vault node %d, revision %s: %s", node_id, revision_id, data)
		
		fields = data.to_db_named_values()
		assignment_parts = []
		values = []
		for name, value in fields.items():
			assignment_parts.append(f"{name} = ?")
			values.append(value)
		
		assert assignment_parts
		assignment = ", ".join(assignment_parts)
		
		async with self.db, await self.db.cursor() as cursor:
			await cursor.execute(f"update VaultNodes set {assignment} where NodeId = ?", values + [node_id])
			if cursor.rowcount == 0:
				raise VaultNodeNotFound(f"Couldn't update vault node with ID {node_id} as it doesn't exist")
		
		for conn in self.auth_connections.values():
			# TODO Send notifications asynchronously
			if conn.cares_about_vault_node(node_id):
				await conn.vault_node_changed(node_id, revision_id)
	
	async def delete_vault_node(self, node_id: int) -> None:
		logger_vault.debug("Deleting vault node %d", node_id)
		
		async with self.db, await self.db.cursor() as cursor:
			await cursor.execute("delete from VaultNodes where NodeId = ?", (node_id,))
			if cursor.rowcount == 0:
				raise VaultNodeNotFound(f"Couldn't delete vault node with ID {node_id} as it doesn't exist")
		
		for conn in self.auth_connections.values():
			# TODO Send notifications asynchronously
			if conn.cares_about_vault_node(node_id):
				await conn.vault_node_deleted(node_id)
				conn.stop_caring_about_vault_nodes({node_id})
	
	async def fetch_vault_node_child_refs(self, parent_id: int) -> typing.AsyncIterable[VaultNodeRef]:
		async with await self.db.cursor() as cursor:
			await cursor.execute("select NodeId from VaultNodes where NodeId = ?", (parent_id,))
			if await cursor.fetchone() is None:
				raise VaultNodeNotFound(f"Couldn't fetch refs for vault node ID {parent_id} as it doesn't exist")
			
			await cursor.execute("select ChildId, OwnerId, Seen from VaultNodeRefs where ParentId = ?", (parent_id,))
			async for child_id, owner_id, seen in cursor:
				yield VaultNodeRef(parent_id, child_id, owner_id, seen)
	
	async def fetch_vault_node_refs_recursive(self, top_id: int) -> typing.AsyncIterable[VaultNodeRef]:
		async with await self.db.cursor() as cursor:
			await cursor.execute("select NodeId from VaultNodes where NodeId = ?", (top_id,))
			if await cursor.fetchone() is None:
				raise VaultNodeNotFound(f"Couldn't fetch refs for vault node ID {top_id} as it doesn't exist")
			
			await cursor.execute(
				"""
				with recursive
					VaultNodeRefsRecursive(ParentId, ChildId, OwnerId, Seen) as (
						select ParentId, ChildId, OwnerId, Seen
						from VaultNodeRefs
						where ParentId = ?
						union
						select ref.ParentId, ref.ChildId, ref.OwnerId, ref.Seen
						from VaultNodeRefs ref
						join VaultNodeRefsRecursive rec
						on ref.ParentId = rec.ChildId
					)
				select ParentId, ChildId, OwnerId, Seen
				from VaultNodeRefsRecursive
				""",
				(top_id,),
			)
			async for parent_id, child_id, owner_id, seen in cursor:
				yield VaultNodeRef(parent_id, child_id, owner_id, seen)
	
	async def add_vault_node_ref(self, ref: VaultNodeRef) -> None:
		logger_vault.debug("Adding vault node ref: %r", ref)
		
		async with self.db, await self.db.cursor() as cursor:
			try:
				await cursor.execute(
					"insert into VaultNodeRefs (ParentId, ChildId, OwnerId, Seen) values (?, ?, ?, ?)",
					(ref.parent_id, ref.child_id, ref.owner_id, ref.seen),
				)
			except sqlite3.IntegrityError as e:
				message = str(e)
				if "UNIQUE" in message:
					raise VaultNodeAlreadyExists(f"A vault node ref {ref.parent_id} -> {ref.child_id} already exists")
				elif "FOREIGN KEY" in message:
					raise VaultNodeNotFound(f"Couldn't add vault node ref {ref.parent_id} -> {ref.child_id} as either the parent or child doesn't exist")
				else:
					raise e
		
		for conn in self.auth_connections.values():
			# TODO Send notifications asynchronously
			if conn.cares_about_vault_node(ref.parent_id):
				await conn.vault_node_added(ref.parent_id, ref.child_id, ref.owner_id)
	
	async def remove_vault_node_ref(self, parent_id: int, child_id: int) -> None:
		logger_vault.debug("Removing vault node ref: %d -> %d", parent_id, child_id)
		
		async with self.db, await self.db.cursor() as cursor:
			await cursor.execute(
				"delete from VaultNodeRefs where ParentId = ? and ChildId = ?",
				(parent_id, child_id),
			)
			if cursor.rowcount == 0:
				raise VaultNodeNotFound(f"Couldn't remove vault node ref {parent_id} -> {child_id} as id doesn't exist")
		
		for conn in self.auth_connections.values():
			# TODO Send notifications asynchronously
			if conn.cares_about_vault_node(parent_id):
				await conn.vault_node_removed(parent_id, child_id)
	
	async def send_vault_node(self, node_id: int, receiver_id: int, sender_id: int) -> None:
		receiver_inbox_id = await self.find_unique_vault_node(VaultNodeData(node_type=VaultNodeType.folder, int32_1=1), parent_id=receiver_id)
		await self.add_vault_node_ref(VaultNodeRef(receiver_inbox_id, node_id, sender_id))
	
	async def find_age_instance(self, age_file_name: str, instance_uuid: uuid.UUID) -> typing.Tuple[int, int]:
		try:
			age_info_id = await self.find_unique_vault_node(VaultNodeData(node_type=VaultNodeType.age_info, uuid_1=instance_uuid, string64_2=age_file_name))
			age_info = await self.fetch_vault_node(age_info_id)
		except VaultNodeNotFound:
			raise AgeInstanceNotFound(f"There is no instance of age {age_file_name!r} with UUID {instance_uuid}")
		
		if age_info.uint32_1 is None:
			raise VaultSemanticError(f"Age Info node {age_info_id} doesn't have its AgeId (UInt32_1) set")
		return age_info.uint32_1, age_info_id
	
	async def create_age_instance(
		self,
		age_file_name: str,
		instance_uuid: uuid.UUID,
		parent_instance_uuid: typing.Optional[uuid.UUID] = None,
		instance_name: typing.Optional[str] = None,
		user_defined_name: typing.Optional[str] = None,
		description: typing.Optional[str] = None,
		sequence_number: int = 0,
		language: int = -1,
		*,
		public: bool = False,
		allow_existing: bool = False,
	) -> typing.Tuple[int, int]:
		try:
			age_id, age_info_id = await self.find_age_instance(age_file_name, instance_uuid)
		except AgeInstanceNotFound:
			logger.info("Creating new age instance of age %r with instance UUID %s", age_file_name, instance_uuid)
		else:
			if allow_existing:
				return age_id, age_info_id
			else:
				raise AgeInstanceAlreadyExists(f"There is already an instance of age {age_file_name!r} with UUID {instance_uuid}")
		
		system_id = await self.find_system_vault_node()
		
		age_id = await self.create_vault_node(VaultNodeData(creator_account_uuid=instance_uuid, creator_id=0, node_type=VaultNodeType.age, uuid_1=instance_uuid, uuid_2=parent_instance_uuid, string64_1=age_file_name))
		age_info_id = await self.create_vault_node(VaultNodeData(
			creator_account_uuid=instance_uuid,
			creator_id=age_id,
			node_type=VaultNodeType.age_info,
			int32_1=sequence_number, # TODO Auto-increment sequence number where necessary?
			int32_2=1 if public else None,
			int32_3=language,
			uint32_1=age_id,
			uint32_2=0,
			uint32_3=0,
			uuid_1=instance_uuid,
			uuid_2=parent_instance_uuid,
			string64_2=age_file_name,
			string64_3=instance_name,
			string64_4=user_defined_name,
			text_1=description,
		))
		
		await self.add_vault_node_ref(VaultNodeRef(age_id, system_id))
		await self.add_vault_node_ref(VaultNodeRef(age_id, age_info_id))
		
		await self.add_vault_node_ref(VaultNodeRef(
			age_id,
			await self.create_vault_node(VaultNodeData(creator_account_uuid=instance_uuid, creator_id=age_id, node_type=VaultNodeType.player_info_list, int32_1=VaultNodeFolderType.people_i_know_about)),
		))
		
		await self.add_vault_node_ref(VaultNodeRef(
			age_id,
			await self.create_vault_node(VaultNodeData(creator_account_uuid=instance_uuid, creator_id=age_id, node_type=VaultNodeType.folder, int32_1=VaultNodeFolderType.chronicle)),
		))
		
		await self.add_vault_node_ref(VaultNodeRef(
			age_id,
			await self.create_vault_node(VaultNodeData(creator_account_uuid=instance_uuid, creator_id=age_id, node_type=VaultNodeType.age_info_list, int32_1=VaultNodeFolderType.sub_ages)),
		))
		
		await self.add_vault_node_ref(VaultNodeRef(
			age_id,
			await self.create_vault_node(VaultNodeData(creator_account_uuid=instance_uuid, creator_id=age_id, node_type=VaultNodeType.folder, int32_1=VaultNodeFolderType.age_devices)),
		))
		
		await self.add_vault_node_ref(VaultNodeRef(
			age_info_id,
			await self.create_vault_node(VaultNodeData(creator_account_uuid=instance_uuid, creator_id=age_id, node_type=VaultNodeType.sdl, int32_1=0, string64_1=age_file_name)),
		))
		
		await self.add_vault_node_ref(VaultNodeRef(
			age_info_id,
			await self.create_vault_node(VaultNodeData(creator_account_uuid=instance_uuid, creator_id=age_id, node_type=VaultNodeType.player_info_list, int32_1=VaultNodeFolderType.age_owners)),
		))
		
		await self.add_vault_node_ref(VaultNodeRef(
			age_info_id,
			await self.create_vault_node(VaultNodeData(creator_account_uuid=instance_uuid, creator_id=age_id, node_type=VaultNodeType.player_info_list, int32_1=VaultNodeFolderType.can_visit)),
		))
		
		await self.add_vault_node_ref(VaultNodeRef(
			age_info_id,
			await self.create_vault_node(VaultNodeData(creator_account_uuid=instance_uuid, creator_id=age_id, node_type=VaultNodeType.age_info_list, int32_1=VaultNodeFolderType.child_ages)),
		))
		
		return age_id, age_info_id
	
	async def setup_static_age_instance(
		self,
		age_file_name: str,
		instance_uuid: typing.Optional[uuid.UUID],
		instance_name: typing.Optional[str],
		user_defined_name: typing.Optional[str],
	) -> uuid.UUID:
		"""Ensure that a public static instance of the given age exists,
		by finding an existing matching instance if possible,
		or creating a new one if necessary.
		"""
		
		if instance_uuid is None:
			# This static age instance is declared with an [auto] instance UUID,
			# so we need to figure out what instance UUID to use.
			async with await self.db.cursor() as cursor:
				# Look for any existing public instances of the age in question.
				# If an [auto] static instance is declared for an age,
				# there should never be more than one public instance of that age -
				# but for better predictability and robustness,
				# in case multiple instances exist somehow,
				# we always prefer the oldest one.
				
				await cursor.execute(
					"""
					select Uuid_1
					from VaultNodes
					where NodeType = ? and Int32_2 = 1 and Uuid_1 is not null and String64_2 = ?
					order by CreateTime
					limit 2
					""",
					(VaultNodeType.age_info, age_file_name),
				)
				
				row = await cursor.fetchone()
				if row is None:
					# No existing public instance found,
					# so create a new one with a random UUID.
					# The next time the server is restarted,
					# this instance will be found and not re-created.
					instance_uuid = uuid.uuid4()
					logger.debug("Couldn't find any existing public instance of %r - choosing a new random instance UUID: %s", age_file_name, instance_uuid)
					_, age_info_id = await self.create_age_instance(
						age_file_name=age_file_name,
						instance_uuid=instance_uuid,
						instance_name=instance_name,
						user_defined_name=user_defined_name,
						public=True,
					)
				else:
					# Found an existing public instance of the age in question.
					# (If there are multiple instances for some reason,
					# this will be the oldest one.)
					(existing_instance_uuid_bytes,) = row
					existing_instance_uuid = uuid.UUID(bytes_le=existing_instance_uuid_bytes)
					logger.debug("Found existing public instance of %r with UUID %s - using it as the static instance", age_file_name, existing_instance_uuid)
					
					if await cursor.fetchone() is not None:
						logger.warning("Found multiple existing public instances of %r - using the oldest instance as the static instance: %s", age_file_name, existing_instance_uuid)
					
					# When an [auto] static instance declaration is fulfilled using an existing public instance,
					# then *don't* update the existing instance's display names to match the declaration.
					# This reduces the potential mess if the wrong public instance is selected for some reason.
					
					return existing_instance_uuid
		else:
			# This static age instance is declared with a hardcoded UUID,
			# so we can use the regular logic for finding/creating an age instance by UUID.
			logger.debug("Finding/creating a static instance of %r with UUID %s...", age_file_name, instance_uuid)
			_, age_info_id = await self.create_age_instance(
				age_file_name=age_file_name,
				instance_uuid=instance_uuid,
				instance_name=instance_name,
				user_defined_name=user_defined_name,
				public=True,
				allow_existing=True,
			)
		
		# Now that we have the instance,
		# check that its Age Info node has all the metadata set to what the config says it should be.
		# This is really only relevant when reusing an existing instance,
		# but as an extra correctness check,
		# just run the same logic on newly created instances as well.
		
		age_info_data = await self.fetch_vault_node(age_info_id)
		age_info_needs_updating = False
		
		if age_info_data.int32_2 != 1:
			logger.warning("Existing static instance of %r with UUID %s (Age Info node %d) isn't public - fixing that...", age_file_name, instance_uuid, age_info_id)
			age_info_needs_updating = True
		if age_info_data.string64_3 != instance_name:
			logger.warning("Existing static instance of %r with UUID %s (Age Info node %d) has instance name %r - renaming to %r as declared in the config...", age_file_name, instance_uuid, age_info_id, age_info_data.string64_3, instance_name)
			age_info_needs_updating = True
		if age_info_data.string64_4 != user_defined_name:
			logger.warning("Existing static instance of %r with UUID %s (Age Info node %d) has user-defined name %r - renaming to %r as declared in the config...", age_file_name, instance_uuid, age_info_id, age_info_data.string64_4, user_defined_name)
			age_info_needs_updating = True
		
		if age_info_needs_updating:
			# To reduce log spam about vault node updates,
			# only actually update the node if anything is mismatched.
			await self.update_vault_node(age_info_id, VaultNodeData(int32_2=1, string64_3=instance_name, string64_4=user_defined_name), uuid.uuid4())
		
		return instance_uuid
	
	async def find_public_age_instances(self, age_file_name: str) -> typing.AsyncIterable[PublicAgeInstance]:
		async with await self.db.cursor() as cursor:
			await cursor.execute(
				"""
				select
					age.Uuid_1 as instance_uuid,
					age.String64_3 as instance_name,
					age.String64_4 as user_defined_name,
					age.Text_1 as description,
					age.Int32_1 as sequence_number,
					age.Int32_3 as language,
					(
						select count(*)
						from VaultNodeRefs age_children
						join VaultNodes owners_folder on owners_folder.NodeId = age_children.ChildId and owners_folder.NodeType = ? and owners_folder.Int32_1 = ?
						join VaultNodeRefs owners on owners.ParentId = owners_folder.NodeId
						where age.NodeId = age_children.ParentId
					) as owner_count
				from VaultNodes age
				where age.NodeType = ? and age.Int32_2 = 1 and age.Uuid_1 is not null and age.String64_2 = ?
				order by age.ModifyTime desc
				limit 50
				""",
				(VaultNodeType.player_info_list, VaultNodeFolderType.age_owners, VaultNodeType.age_info, age_file_name),
			)
			
			async for instance_uuid, instance_name, user_defined_name, description, sequence_number, language, owner_count in cursor:
				yield PublicAgeInstance(
					instance_uuid=uuid.UUID(bytes_le=instance_uuid),
					file_name=age_file_name,
					instance_name=instance_name or "",
					user_defined_name=user_defined_name or "",
					description=description or "",
					sequence_number=sequence_number or 0,
					language=language if language is not None else -1,
					owner_count=owner_count,
					current_population=0, # TODO Get population from corresponding game server (if any)
				)
	
	async def find_avatars(self, account_id: uuid.UUID) -> typing.AsyncIterable[AvatarInfo]:
		async for player_id in self.find_vault_nodes(VaultNodeData(node_type=VaultNodeType.player, uuid_1=account_id)):
			player_node = await self.fetch_vault_node(player_id)
			name = player_node.istring64_1
			if name is None:
				raise VaultSemanticError(f"Avatar with KI number {player_id} has no name")
			shape = player_node.string64_1
			if shape is None:
				raise VaultSemanticError(f"Avatar with KI number {player_id} has no shape")
			explorer = player_node.int32_2
			if explorer is None:
				raise VaultSemanticError(f"Avatar with KI number {player_id} has no explorer flag")
			yield AvatarInfo(player_id, name, shape, explorer)
	
	async def create_avatar(self, name: str, shape: str, explorer: int, account_id: uuid.UUID) -> typing.Tuple[int, int]:
		if shape not in {"female", "male"}:
			raise ValueError(f"Unsupported avatar shape {shape!r}")
		
		async for _ in self.find_vault_nodes(VaultNodeData(node_type=VaultNodeType.player, istring64_1=name)):
			raise AvatarAlreadyExists(f"An avatar named {name!r} already exists")
		
		logger.info("Creating avatar %r, avatar shape %r, explorer? %d, account UUID %s", name, shape, explorer, account_id)
		
		system_id = await self.find_system_vault_node()
		all_players_id = await self.find_all_players_vault_node()
		
		# TODO Automatically create new hoods as needed
		if self.default_neighborhood_instance_uuid is None:
			hood_info_id = None
		else:
			_, hood_info_id = await self.find_age_instance(structs.NEIGHBORHOOD_AGE_NAME, self.default_neighborhood_instance_uuid)
		
		if self.public_aegura_instance_uuid is None:
			aegura_info_id = None
		else:
			_, aegura_info_id = await self.find_age_instance(structs.AEGURA_AGE_NAME, self.public_aegura_instance_uuid)
		
		player_id = await self.create_vault_node(VaultNodeData(creator_account_uuid=account_id, creator_id=0, node_type=VaultNodeType.player, int32_1=0, int32_2=explorer, uuid_1=account_id, string64_1=shape, istring64_1=name))
		player_info_id = await self.create_vault_node(VaultNodeData(creator_account_uuid=account_id, creator_id=player_id, node_type=VaultNodeType.player_info, uint32_1=player_id, istring64_1=name))
		
		await self.add_vault_node_ref(VaultNodeRef(player_id, system_id))
		await self.add_vault_node_ref(VaultNodeRef(player_id, player_info_id))
		
		await self.add_vault_node_ref(VaultNodeRef(
			player_id,
			await self.create_vault_node(VaultNodeData(creator_account_uuid=account_id, creator_id=player_id, node_type=VaultNodeType.folder, int32_1=VaultNodeFolderType.inbox)),
		))
		
		await self.add_vault_node_ref(VaultNodeRef(
			player_id,
			await self.create_vault_node(VaultNodeData(creator_account_uuid=account_id, creator_id=player_id, node_type=VaultNodeType.folder, int32_1=VaultNodeFolderType.age_journals)),
		))
		
		await self.add_vault_node_ref(VaultNodeRef(
			player_id,
			await self.create_vault_node(VaultNodeData(creator_account_uuid=account_id, creator_id=player_id, node_type=VaultNodeType.player_info_list, int32_1=VaultNodeFolderType.buddy_list)),
		))
		
		await self.add_vault_node_ref(VaultNodeRef(
			player_id,
			await self.create_vault_node(VaultNodeData(creator_account_uuid=account_id, creator_id=player_id, node_type=VaultNodeType.player_info_list, int32_1=VaultNodeFolderType.ignore_list)),
		))
		
		await self.add_vault_node_ref(VaultNodeRef(
			player_id,
			await self.create_vault_node(VaultNodeData(creator_account_uuid=account_id, creator_id=player_id, node_type=VaultNodeType.player_info_list, int32_1=VaultNodeFolderType.people_i_know_about)),
		))
		
		await self.add_vault_node_ref(VaultNodeRef(
			player_id,
			await self.create_vault_node(VaultNodeData(creator_account_uuid=account_id, creator_id=player_id, node_type=VaultNodeType.folder, int32_1=VaultNodeFolderType.chronicle)),
		))
		
		await self.add_vault_node_ref(VaultNodeRef(
			player_id,
			await self.create_vault_node(VaultNodeData(creator_account_uuid=account_id, creator_id=player_id, node_type=VaultNodeType.folder, int32_1=VaultNodeFolderType.avatar_outfit)),
		))
		
		await self.add_vault_node_ref(VaultNodeRef(
			player_id,
			await self.create_vault_node(VaultNodeData(creator_account_uuid=account_id, creator_id=player_id, node_type=VaultNodeType.folder, int32_1=VaultNodeFolderType.avatar_closet)),
		))
		
		await self.add_vault_node_ref(VaultNodeRef(
			player_id,
			await self.create_vault_node(VaultNodeData(creator_account_uuid=account_id, creator_id=player_id, node_type=VaultNodeType.folder, int32_1=VaultNodeFolderType.player_invite)),
		))
		
		ages_i_own_id = await self.create_vault_node(VaultNodeData(creator_account_uuid=account_id, creator_id=player_id, node_type=VaultNodeType.age_info_list, int32_1=VaultNodeFolderType.ages_i_own))
		await self.add_vault_node_ref(VaultNodeRef(player_id, ages_i_own_id))
		
		# Create the avatar's Relto.
		relto_id, relto_info_id = await self.create_age_instance(
			age_file_name="Personal",
			instance_uuid=uuid.uuid4(),
			instance_name="Relto",
			user_defined_name=f"{name}'s",
			description=f"{name}'s Relto",
		)
		
		# Make the avatar the owner of its Relto.
		relto_owners_id = await self.find_unique_vault_node(VaultNodeData(node_type=VaultNodeType.player_info_list, int32_1=VaultNodeFolderType.age_owners), parent_id=relto_info_id)
		await self.add_vault_node_ref(VaultNodeRef(relto_owners_id, player_info_id))
		
		# Add the avatar's Ages I Own list to its Relto Age node.
		# This is a special case that applies only for Relto instances.
		await self.add_vault_node_ref(VaultNodeRef(relto_id, ages_i_own_id))
		
		# Add a link to the avatar's Relto to its Ages I Own list.
		relto_link_id = await self.create_vault_node(VaultNodeData(creator_account_uuid=account_id, creator_id=player_id, node_type=VaultNodeType.age_link, blob_1=b"Default:LinkInPointDefault:;"))
		await self.add_vault_node_ref(VaultNodeRef(relto_link_id, relto_info_id))
		await self.add_vault_node_ref(VaultNodeRef(ages_i_own_id, relto_link_id))
		
		if hood_info_id is not None:
			# Make the avatar an owner of its neighborhood.
			hood_owners_id = await self.find_unique_vault_node(VaultNodeData(node_type=VaultNodeType.player_info_list, int32_1=VaultNodeFolderType.age_owners), parent_id=hood_info_id)
			await self.add_vault_node_ref(VaultNodeRef(hood_owners_id, player_info_id))
			
			# Add a link to the neighborhood to the avatar's Ages I Own list.
			hood_link_id = await self.create_vault_node(VaultNodeData(creator_account_uuid=account_id, creator_id=player_id, node_type=VaultNodeType.age_link, blob_1=b"Default:LinkInPointDefault:;"))
			await self.add_vault_node_ref(VaultNodeRef(hood_link_id, hood_info_id))
			await self.add_vault_node_ref(VaultNodeRef(ages_i_own_id, hood_link_id))
		
		if aegura_info_id is not None:
			# Add a link to the public Ae'gura to the avatar's Ages I Own list.
			aegura_link_id = await self.create_vault_node(VaultNodeData(creator_account_uuid=account_id, creator_id=player_id, node_type=VaultNodeType.age_link, blob_1=b"Ferry Terminal:LinkInPointFerry:;"))
			await self.add_vault_node_ref(VaultNodeRef(aegura_link_id, aegura_info_id))
			await self.add_vault_node_ref(VaultNodeRef(ages_i_own_id, aegura_link_id))
		
		await self.add_vault_node_ref(VaultNodeRef(
			player_id,
			await self.create_vault_node(VaultNodeData(creator_account_uuid=account_id, creator_id=player_id, node_type=VaultNodeType.age_info_list, int32_1=VaultNodeFolderType.ages_i_can_visit)),
		))
		
		await self.add_vault_node_ref(VaultNodeRef(all_players_id, player_info_id))
		
		return player_id, player_info_id
	
	async def delete_avatar(self, ki_number: int, account_id: uuid.UUID) -> None:
		# Check that the KI number is indeed a Player node belonging to the expected account.
		try:
			player_data = await self.fetch_vault_node(ki_number)
		except VaultNodeNotFound:
			raise AvatarNotFound(f"Cannot delete avatar with KI number {ki_number} as it doesn't exist")
		
		if player_data.node_type != VaultNodeType.player:
			raise AvatarNotFound(f"Cannot delete avatar with KI number {ki_number} as it's not a Player node (actual type {player_data.node_type})")
		
		if player_data.uuid_1 != account_id:
			raise AvatarNotFound(f"Cannot delete avatar with KI number {ki_number} as it doesn't belong to the expected account {account_id}")
		
		logger.info("Deleting avatar %d, avatar shape %r, explorer? %r, account UUID %s", ki_number, player_data.string64_1, player_data.int32_2, account_id)
		
		# Kick any connection that's currently using this avatar.
		try:
			conn = self.auth_connections_by_ki_number[ki_number]
		except KeyError:
			pass
		else:
			from . import base # Avoid circular import problems
			kick_task = conn.kick_async(base.NetError.logged_in_elsewhere, set_avatar_offline=True)
			if kick_task is not None:
				await kick_task
		
		# Remove all direct child refs of the Player node.
		async for ref in self.fetch_vault_node_child_refs(ki_number):
			await self.remove_vault_node_ref(ki_number, ref.child_id)
		
		# Delete the Player node itself.
		await self.delete_vault_node(ki_number)
	
	async def set_avatar_online_state(self, ki_number: int, online: bool, age_name: str, age_instance_uuid: uuid.UUID) -> None:
		player_info_id = await self.find_unique_vault_node(VaultNodeData(node_type=VaultNodeType.player_info), parent_id=ki_number)
		await self.update_vault_node(player_info_id, VaultNodeData(int32_1=online, uuid_1=age_instance_uuid, string64_1=age_name), uuid.uuid4())
	
	async def set_avatar_offline(self, ki_number: int) -> None:
		await self.set_avatar_online_state(ki_number, False, "", structs.ZERO_UUID)
	
	async def set_all_avatars_offline(self) -> int:
		async with self.db, await self.db.cursor() as cursor:
			await cursor.execute(
				"""
				update VaultNodes
				set Int32_1 = 0, Uuid_1 = ?, String64_1 = ''
				where NodeType = ? and Int32_1 != 0
				""",
				(structs.ZERO_UUID.bytes_le, VaultNodeType.player_info),
			)
			return cursor.rowcount
	
	async def fetch_object_sdl_state(self, age_vault_node_id: int, uoid: structs.Uoid, state_desc_name: bytes) -> bytes:
		with io.BytesIO() as stream:
			uoid.write(stream)
			uoid_data = stream.getvalue()
		
		async with await self.db.cursor() as cursor:
			await cursor.execute(
				"""
				select SdlBlob
				from AgeInstanceObjectStates
				where AgeVaultNodeId = ? and Uoid = ? and StateDescName = ?
				""",
				(age_vault_node_id, uoid_data, state_desc_name.decode("ascii")),
			)
			row = await cursor.fetchone()
			if row is None:
				raise ObjectStateNotFound(f"Couldn't find SDL state {state_desc_name!r} for object {uoid!r} in age instance {age_vault_node_id}")
			else:
				(sdl_blob,) = row
				return sdl_blob
	
	async def find_object_sdl_states(self, age_vault_node_id: int) -> typing.AsyncIterable[typing.Tuple[structs.Uoid, bytes, bytes]]:
		async with await self.db.cursor() as cursor:
			await cursor.execute(
				"""
				select Uoid, StateDescName, SdlBlob
				from AgeInstanceObjectStates
				where AgeVaultNodeId = ?
				""",
				(age_vault_node_id,),
			)
			
			async for uoid_data, state_desc_name, sdl_blob in cursor:
				with io.BytesIO(uoid_data) as stream:
					uoid = structs.Uoid.from_stream(stream)
				
				yield uoid, state_desc_name.encode("ascii"), sdl_blob
	
	async def save_object_sdl_state(self, age_vault_node_id: int, uoid: structs.Uoid, state_desc_name: bytes, sdl_blob: bytes) -> None:
		with io.BytesIO() as stream:
			uoid.write(stream)
			uoid_data = stream.getvalue()
		
		async with self.db, await self.db.cursor() as cursor:
			await cursor.execute(
				"""
				insert into AgeInstanceObjectStates (AgeVaultNodeId, Uoid, StateDescName, SdlBlob)
				values (?, ?, ?, ?)
				on conflict do update set SdlBlob = ?
				""",
				(age_vault_node_id, uoid_data, state_desc_name.decode("ascii"), sdl_blob, sdl_blob),
			)
