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
import concurrent.futures
import datetime
import enum
import logging
import sqlite3
import struct
import types
import typing
import uuid

from . import auth_server


logger = logging.getLogger(__name__)

_T = typing.TypeVar("_T")

ZERO_UUID = uuid.UUID("00000000-0000-0000-0000-000000000000")

VAULT_NODE_DATA_HEADER = struct.Struct("<Q")
VAULT_NODE_DATA_INT32 = struct.Struct("<i")
VAULT_NODE_DATA_UINT32 = struct.Struct("<I")
VAULT_NODE_REF = struct.Struct("<III?")


class VaultNodeType(enum.IntEnum):
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


class VaultNodeFieldFlags(enum.IntFlag):
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


class VaultNodeData(object):
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
	
	@classmethod
	def unpack(cls, data: bytes) -> "VaultNodeData":
		(flags,) = VAULT_NODE_DATA_HEADER.unpack_from(data)
		data = data[VAULT_NODE_DATA_HEADER.size:]
		if flags >= 1 << 32:
			raise ValueError(f"Unsupported vault node data flags set: 0x{flags:>016x}")
		
		flags = VaultNodeFieldFlags(flags)
		self = cls()
		
		def _unpack_uint32() -> int:
			nonlocal data
			(x,) = VAULT_NODE_DATA_UINT32.unpack_from(data)
			data = data[VAULT_NODE_DATA_UINT32.size:]
			return x
		
		def _unpack_int32() -> int:
			nonlocal data
			(x,) = VAULT_NODE_DATA_UINT32.unpack_from(data)
			data = data[VAULT_NODE_DATA_INT32.size:]
			return x
		
		def _unpack_uuid() -> uuid.UUID:
			nonlocal data
			uu = uuid.UUID(bytes_le=data[:16])
			data = data[16:]
			return uu
		
		def _unpack_blob() -> bytes:
			nonlocal data
			length = _unpack_uint32()
			blob = data[:length]
			if len(blob) != length:
				raise ValueError(f"Truncated vault node string or blob: expected {length} bytes, but there are only {len(blob)} bytes of data remaining")
			data = data[length:]
			return blob
		
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
		
		if data:
			raise ValueError(f"Extra data at end of packed vault node data: {data!r}")
		
		return self
	
	def pack(self) -> bytes:
		flags = VaultNodeFieldFlags(0)
		data = bytearray()
		
		def _pack_uint32(x: int) -> None:
			data.extend(VAULT_NODE_DATA_UINT32.pack(x))
		
		def _pack_int32(x: int) -> None:
			data.extend(VAULT_NODE_DATA_INT32.pack(x))
		
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
	
	def __init__(self, parent_id: int, child_id: int, owner_id: int = 0, seen: bool = True) -> None:
		super().__init__()
		
		self.parent_id = parent_id
		self.child_id = child_id
		self.owner_id = owner_id
		self.seen = seen
	
	def pack(self) -> bytes:
		return VAULT_NODE_REF.pack(self.parent_id, self.child_id, self.owner_id, self.seen)


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
		logger.info("Loaded NAGUS database at %s %r", "URI" if uri else "path", database)
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


class ServerState(object):
	loop: asyncio.AbstractEventLoop
	db: Database
	
	auth_connections: typing.Dict[uuid.UUID, "auth_server.AuthConnection"]
	
	def __init__(self, loop: asyncio.AbstractEventLoop, db: Database) -> None:
		super().__init__()
		
		self.loop = loop
		self.db = db
		
		self.auth_connections = {}
	
	async def setup_database(self) -> None:
		async with self.db, await self.db.cursor() as cursor:
			await cursor.executescript("""
			pragma foreign_keys = on;
			
			create table if not exists VaultNodes (
				NodeId integer primary key not null,
				CreateTime integer not null,
				ModifyTime integer not null,
				CreateAgeName text,
				CreateAgeUuid blob,
				CreatorAcct blob not null default x'00000000000000000000000000000000',
				CreatorId integer not null default 0,
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
			""")
		
		try:
			system = await self.find_system_vault_node()
		except VaultNodeNotFound:
			logger.info("No system node found in vault! Assuming this is a fresh database, so creating a new one.")
			system = await self.create_vault_node(VaultNodeData(node_type=VaultNodeType.system))
			global_inbox_folder = await self.create_vault_node(VaultNodeData(node_type=VaultNodeType.folder, int32_1=30))
			await self.add_vault_node_ref(VaultNodeRef(system, global_inbox_folder))
		
		logger.debug("Finished setting up the NAGUS database. System vault node ID is %d", system)
	
	async def fetch_vault_node(self, node_id: int) -> VaultNodeData:
		async with await self.db.cursor() as cursor:
			await cursor.execute("select * from VaultNodes where NodeId = ?", (node_id,))
			row = await cursor.fetchone()
			if row is None:
				raise VaultNodeNotFound(f"Couldn't find vault node with ID {node_id}")
			else:
				return VaultNodeData.from_db_row(row)
	
	async def find_vault_nodes(self, template: VaultNodeData) -> typing.AsyncIterable[int]:
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
			await cursor.execute(f"select NodeId from VaultNodes where {cond}", values)
			
			async for (node_id,) in cursor:
				yield node_id
	
	async def find_system_vault_node(self) -> int:
		it = aiter(self.find_vault_nodes(VaultNodeData(node_type=VaultNodeType.system)))
		try:
			node_id = await anext(it)
		except StopAsyncIteration:
			raise VaultNodeNotFound("Couldn't find the system vault node!")
		
		try:
			node_id_2 = await anext(it)
		except StopAsyncIteration:
			pass
		else:
			logger.warning("Found multiple system nodes in vault: %d and %d (and possibly more)! Ignoring all except the first one.", node_id, node_id_2)
		
		return node_id
	
	async def create_vault_node(self, data: VaultNodeData) -> int:
		data.create_time = data.modify_time = int(datetime.datetime.now().timestamp())
		
		fields = data.to_db_named_values()
		names = ", ".join(fields.keys())
		placeholders = ", ".join("?" * len(fields))
		values = list(fields.values())
		
		async with self.db, await self.db.cursor() as cursor:
			await cursor.execute(f"insert into VaultNodes ({names}) values ({placeholders}) returning NodeId", values)
			(node_id,) = await cursor.fetchone()
			return node_id
	
	async def update_vault_node(self, data: VaultNodeData) -> None:
		if data.node_id is None:
			raise ValueError("Node ID field is required when updating a vault node")
		
		data.modify_time = int(datetime.datetime.now().timestamp())
		
		fields = data.to_db_named_values()
		assignment_parts = []
		values = []
		for name, value in fields.items():
			assignment_parts.append(f"{name} = ?")
			values.append(value)
		
		assert assignment_parts
		assignment = ", ".join(assignment_parts)
		
		async with self.db, await self.db.cursor() as cursor:
			await cursor.execute(f"update VaultNodes set {assignment} where NodeId = ?", values + [data.node_id])
			if cursor.rowcount == 0:
				raise VaultNodeNotFound(f"Couldn't update vault node with ID {data.node_id} as it doesn't exist")
		
		# TODO Notify all relevant clients
	
	async def delete_vault_node(self, node_id: int) -> None:
		async with self.db, await self.db.cursor() as cursor:
			await cursor.execute("delete from VaultNodes where NodeId = ?", (node_id,))
			if cursor.rowcount == 0:
				raise VaultNodeNotFound(f"Couldn't delete vault node with ID {node_id} as it doesn't exist")
		
		# TODO Notify all relevant clients
	
	async def fetch_vault_node_child_refs(self, parent_id: int) -> typing.AsyncIterable[VaultNodeRef]:
		async with await self.db.cursor() as cursor:
			await cursor.execute("select NodeId from VaultNodes where NodeId = ?", (parent_id,))
			if await cursor.fetchone() is None:
				raise VaultNodeNotFound(f"Couldn't fetch refs for vault node ID {parent_id} as it doesn't exist")
			
			await cursor.execute("select (ChildId, OwnerId, Seen) from VaultNodeRefs where ParentId = ?", (parent_id,))
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
		
		# TODO Notify all relevant clients
	
	async def remove_vault_node_ref(self, parent_id: int, child_id: int) -> None:
		async with self.db, await self.db.cursor() as cursor:
			await cursor.execute(
				"delete from VaultNodeRefs where ParentId = ? and ChildId = ?",
				(parent_id, child_id),
			)
			if cursor.rowcount == 0:
				raise VaultNodeNotFound(f"Couldn't remove vault node ref {parent_id} -> {child_id} as id doesn't exist")
		
		# TODO Notify all relevant clients
