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

This file currently implements the entire server,
until I refactor this properly.

See the docs directory for some general documentation about Uru's network protocol.
"""


import asyncio
import enum
import logging
import socket
import struct
import sys
import typing
import uuid


logger = logging.getLogger(__name__)


CONNECT_HEADER_1 = struct.Struct("<BH")
CONNECT_HEADER_2 = struct.Struct("<III16s") 
CONNECT_HEADER_LENGTH = CONNECT_HEADER_1.size + CONNECT_HEADER_2.size

CLI2AUTH_CONNECT_DATA = struct.Struct("<I16s")

SETUP_MESSAGE_HEADER = struct.Struct("<BB")


ZERO_UUID = uuid.UUID("00000000-0000-0000-0000-000000000000")


class BuildType(enum.Enum):
	dev = 10
	qa = 20
	test = 30
	beta = 40
	live = 50


class ConnectionType(enum.Enum):
	nil = 0
	debug = 1
	
	cli2auth = 10
	cli2game = 11
	srv2agent = 12
	srv2mcp = 13
	srv2vault = 14
	srv2db = 15
	cli2file = 16
	srv2state = 17
	srv2log = 18
	srv2score = 19
	cli2csr = 20
	simple_net = 21
	cli2gatekeeper = 22
	
	admin_interface = ord("a")


class SetupMessageType(enum.Enum):
	cli2srv_connect = 0
	srv2cli_encrypt = 1
	srv2cli_error = 2


class ProtocolError(Exception):
	pass


class NAGUSConnection(object):
	reader: asyncio.StreamReader
	writer: asyncio.StreamWriter
	client_address: typing.Tuple[str, int]
	
	type: ConnectionType
	build_id: int
	build_type: BuildType
	branch_id: int
	product_id: uuid.UUID
	
	def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
		super().__init__()
		
		self.reader = reader
		self.writer = writer
		self.client_address = self.writer.get_extra_info("peername")
	
	async def _read(self, byte_count: int) -> bytes:
		"""Read ``byte_count`` bytes from the socket and raise :class:`~asyncio.IncompleteReadError` if too few bytes are read (i. e. the connection was disconnected prematurely)."""
		
		return await self.reader.readexactly(byte_count)
	
	async def _write(self, data: bytes) -> None:
		"""Write ``data`` to the socket.
		
		The exact implementation might change in the future ---
		it seems that Uru expects certain data to arrive as a single packet,
		even though TCP doesn't guarantee that packet boundaries are preserved in transmission.
		"""
		
		self.writer.write(data)
		await self.writer.drain()
	
	async def _read_unpack(self, st: struct.Struct) -> tuple:
		"""Read and unpack data from the socket according to the struct ``st``.
		
		The number of bytes to read is determined using :field:`struct.Struct.size`,
		so variable-sized structs cannot be used with this method.
		"""
		
		return st.unpack(await self._read(st.size))
	
	async def handle(self) -> None:
		logger.info("Connection from %s", self.client_address)
		
		conn_type, header_length = await self._read_unpack(CONNECT_HEADER_1)
		if header_length != CONNECT_HEADER_LENGTH:
			raise ProtocolError(f"Client sent connect header with unexpected length {header_length} (should be {CONNECT_HEADER_LENGTH})")
		
		self.type = ConnectionType(conn_type)
		build_id, build_type, branch_id, product_id = await self._read_unpack(CONNECT_HEADER_2)
		self.build_id = build_id
		self.build_type = BuildType(build_type)
		self.branch_id = branch_id
		self.product_id = uuid.UUID(bytes_le=product_id)
		logger.debug("Received connect packet header: connection type %s, build ID %d, build type %s, branch ID %d, product ID %s", self.type, self.build_id, self.build_type, self.branch_id, self.product_id)
		
		if self.type == ConnectionType.cli2auth:
			data_length, token = await self._read_unpack(CLI2AUTH_CONNECT_DATA)
			if data_length != CLI2AUTH_CONNECT_DATA.size:
				raise ProtocolError(f"Client sent client-to-auth connect data with unexpected length {data_length} (should be {CLI2AUTH_CONNECT_DATA.size})")
			
			token = uuid.UUID(bytes_le=token)
			if token != ZERO_UUID:
				raise ProtocolError(f"Client sent client-to-auth connect data with unexpected token {token} (should be {ZERO_UUID})")
		else:
			raise ProtocolError(f"Unsupported connection type {self.type}")
		
		message_type, length = await self._read_unpack(SETUP_MESSAGE_HEADER)
		message_type = SetupMessageType(message_type)
		logger.debug("Received setup message: type %s, %d bytes", message_type, length)
		
		data = await self._read(length - SETUP_MESSAGE_HEADER.size)
		logger.debug("Setup message data: %s", data)
		
		if data:
			# Received a server seed from client.
			# We don't support encryption yet,
			# so for now,
			# assume it's a CWE/OpenUru client built with NO_ENCRYPTION.
			# In this case,
			# we have to send back a seed of the correct length,
			# but the client will not use it and the connection will be unencrypted.
			logger.debug("Received a server seed, but encryption not supported yet! Assuming NO_ENCRYPTION and replying with a dummy client seed.")
			await self._write(SETUP_MESSAGE_HEADER.pack(SetupMessageType.srv2cli_encrypt.value, 9) + b"noCrypt")
		else:
			# H'uru internal client sent an empty server seed to explicitly request no encryption.
			# We have to reply with an empty client seed,
			# or else the client will abort the connection.
			logger.debug("Received empty server seed - setting up unencrypted connection.")
			await self._write(SETUP_MESSAGE_HEADER.pack(SetupMessageType.srv2cli_encrypt.value, 2))
		
		logger.debug("Auth server connection set up")
		
		message_type = int.from_bytes(await self._read(2), "little")
		logger.debug("Received message: type %d", message_type)
		
		if self.type == ConnectionType.cli2auth and message_type == 1:
			build_id = int.from_bytes(await self._read(4), "little")
			logger.debug("Build ID: %d", build_id)
			
			# Reply to client register request
			await self._write(b"\x03\x00\xde\xad\xbe\xef")
			
			data = await self._read(14)
			logger.debug("Received stuff: %s", data)
			if data[:2] == "\x00\x00":
				# Reply to ping
				await self._write(data)
			
			logger.debug("Received stuff: %s", await self._read(50))
		
		logger.debug("Haven't implemented anything beyond this point yet - closing connection.")
		self.writer.close()
		await self.writer.wait_closed()
		logger.info("Connection with %s closed.", self.client_address)


async def client_connected(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
	sock = writer.transport.get_extra_info("socket")
	if sock is not None:
		# Disable Nagle's algorithm
		# (if this is a TCP-based transport, which it should always be)
		# to try to ensure that every write call goes out as an actual TCP packet right away.
		sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
	
	conn = NAGUSConnection(reader, writer)
	try:
		await conn.handle()
	except (ConnectionResetError, asyncio.IncompleteReadError) as exc:
		logger.error("Client %s disconnected: %s.%s: %s", conn.client_address, type(exc).__module__, type(exc).__qualname__, exc)
	except ProtocolError as exc:
		logger.error("Error in data sent by %s: %s", conn.client_address, exc)
	except Exception as exc:
		logger.error("Uncaught exception while handling request from %s:", conn.client_address, exc_info=exc)
	except BaseException as exc:
		logger.error("Uncaught BaseException while handling request from %s - something has gone quite wrong:", conn.client_address, exc_info=exc)
		raise


async def server_main(host: str, port: int) -> None:
	async with await asyncio.start_server(client_connected, host, port) as server:
		logger.info("NAGUS listening on address %r:%d...", host, port)
		await server.serve_forever()


def main() -> typing.NoReturn:
	logging.basicConfig(level=logging.DEBUG)
	
	try:
		asyncio.run(server_main("", 14617))
	except KeyboardInterrupt:
		logger.info("KeyboardInterrupt received, stopping server.")
	
	sys.exit(0)


if __name__ == "__main__":
	sys.exit(main())
