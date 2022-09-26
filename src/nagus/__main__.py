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


"""This is NAGUS, an Uru Live server that is not very good.

This module implements the main entry point for the server.
There's almost no actual logic in this module ---
the code here just dispatches incoming connections to other modules that do the actual work.
"""


import asyncio
import logging
import socket
import sys
import typing

from . import auth_server
from . import base
from . import state
from . import status_server


logger = logging.getLogger(__name__)


CONNECTION_CLASSES: typing.Dict[base.ConnectionType, typing.Type[base.BaseMOULConnection]] = {}

for cls in [
	# TODO Add all the other server types here once implemented
	auth_server.AuthConnection,
]:
	CONNECTION_CLASSES[cls.CONNECTION_TYPE] = cls


async def client_connected_inner(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, server_state: state.ServerState) -> None:
	client_address = writer.get_extra_info("peername")
	
	sock = writer.transport.get_extra_info("socket")
	if sock is not None:
		# Disable Nagle's algorithm
		# (if this is a TCP-based transport, which it should always be)
		# to try to ensure that every write call goes out as an actual TCP packet right away.
		sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
	
	(conn_type_num,) = await reader.readexactly(1)
	try:
		conn_type = base.ConnectionType(conn_type_num)
	except ValueError:
		raise base.ProtocolError(f"Unknown connection type {conn_type_num}")
	
	logger.info("Client %s requests connection type %s", client_address, conn_type)
	
	try:
		conn_class = CONNECTION_CLASSES[conn_type]
	except KeyError:
		raise base.ProtocolError(f"Unsupported connection type {conn_type}")
	
	conn = conn_class(reader, writer, server_state)
	await conn.handle()


async def client_connected(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, server_state: state.ServerState) -> None:
	# Avoid UnboundLocalError in case get_extra_info throws an exception somehow
	client_address = None
	
	try:
		try:
			client_address = writer.get_extra_info("peername")
			logger.info("Connection from %s", client_address)
			await client_connected_inner(reader, writer, server_state)
		finally:
			writer.close()
			logger.info("Closing connection with %s", client_address)
			# No need to await writer.wait_closed(),
			# because we don't do anything else with the writer anymore.
	except (ConnectionResetError, asyncio.IncompleteReadError) as exc:
		logger.error("Client %s disconnected: %s.%s: %s", client_address, type(exc).__module__, type(exc).__qualname__, exc)
	except base.ProtocolError as exc:
		logger.error("Error in data sent by %s: %s", client_address, exc)
	except Exception as exc:
		logger.error("Uncaught exception while handling request from %s:", client_address, exc_info=exc)
	except BaseException as exc:
		logger.error("Uncaught BaseException while handling request from %s - something has gone quite wrong:", client_address, exc_info=exc)
		raise


async def moul_server_main(host: str, port: int, server_state: state.ServerState) -> None:
	async def _client_connected(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
		await client_connected(reader, writer, server_state)
	
	async with await asyncio.start_server(_client_connected, host, port) as server:
		logger.info("NAGUS listening on address %r:%d...", host, port)
		await server.serve_forever()


async def async_main() -> None:
	async with state.Database("nagus.sqlite") as db:
		await db.setup()
		
		server_state = state.ServerState(asyncio.get_event_loop(), db)
		moul_task = asyncio.create_task(moul_server_main("", 14617, server_state))
		status_task = asyncio.create_task(status_server.run_status_server("", 8080))
		await asyncio.gather(moul_task, status_task)


def main() -> typing.NoReturn:
	logging.basicConfig(
		format="[%(levelname)s] %(name)s: %(message)s",
		level=logging.DEBUG,
		stream=sys.stdout,
	)
	
	try:
		asyncio.run(async_main())
	except KeyboardInterrupt:
		logger.info("KeyboardInterrupt received, stopping server.")
	
	sys.exit(0)


if __name__ == "__main__":
	sys.exit(main())
