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
import logging
import sqlite3
import types
import typing
import uuid

from . import auth_server


logger = logging.getLogger(__name__)


class Database(typing.AsyncContextManager["Database"]):
	location: typing.Tuple[typing.Union[str, bytes], bool]
	conn: sqlite3.Connection
	
	def __init__(self, database: typing.Union[str, bytes], *, uri: bool = False) -> None:
		super().__init__()
		
		self.location = (database, uri)
	
	async def __aenter__(self) -> "Database":
		def _do_connect() -> None:
			database, uri = self.location
			self.conn = sqlite3.connect(database, uri=uri)
			self.conn.__enter__()
			logger.info("Loaded NAGUS database at %s %r", "URI" if uri else "path", database)
		
		await asyncio.to_thread(_do_connect)
		return self
	
	async def __aexit__(
		self,
		exc_type: typing.Optional[typing.Type[BaseException]],
		exc_val: typing.Optional[BaseException],
		exc_tb: typing.Optional[types.TracebackType],
	) -> typing.Optional[bool]:
		def _do_disconnect() -> typing.Optional[bool]:
			res = self.conn.__exit__(exc_type, exc_val, exc_tb)
			del self.conn
			return res
		
		return await asyncio.to_thread(_do_disconnect)
	
	async def setup(self) -> None:
		def _do_setup() -> None:
			self.conn.executescript("""
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
		
		await asyncio.to_thread(_do_setup)
		logger.debug("Finished setting up the NAGUS database")


class ServerState(object):
	loop: asyncio.AbstractEventLoop
	db: Database
	
	auth_connections: typing.Dict[uuid.UUID, "auth_server.AuthConnection"]
	
	def __init__(self, loop: asyncio.AbstractEventLoop, db: Database) -> None:
		super().__init__()
		
		self.loop = loop
		self.db = db
		
		self.auth_connections = {}
