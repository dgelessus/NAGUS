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
import typing
import uuid

from . import auth_server


class ServerState(object):
	loop: asyncio.AbstractEventLoop
	
	auth_connections: typing.Dict[uuid.UUID, "auth_server.AuthConnection"]
	
	def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
		super().__init__()
		
		self.loop = loop
		
		self.auth_connections = {}
