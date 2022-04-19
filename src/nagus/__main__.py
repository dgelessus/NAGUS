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


import enum
import logging
import socket
import socketserver
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


class NAGUSConnection(socketserver.StreamRequestHandler):
	# Try to ensure that every send call goes out as an actual TCP packet right away - see docstring of _write below.
	disable_nagle_algorithm = True
	
	type: ConnectionType
	build_id: int
	build_type: BuildType
	branch_id: int
	product_id: uuid.UUID
	
	def _read(self, byte_count: int) -> bytes:
		"""Read ``byte_count`` bytes from the socket and raise :class:`EOFError` if too few bytes are read (i. e. the connection was disconnected prematurely)."""
		
		data = self.rfile.read(byte_count)
		if len(data) != byte_count:
			raise EOFError(f"Attempted to read {byte_count} bytes of data, but only got {len(data)} bytes")
		return data
	
	def _write(self, data: bytes) -> None:
		"""Write ``data`` to the socket.
		
		Currently this uses :func:`socket.socket.sendall`,
		but this might change in the future ---
		it seems that Uru expects certain data to arrive as a single packet,
		even though TCP doesn't guarantee that packet boundaries are preserved in transmission.
		"""
		
		self.request.sendall(data)
	
	def _read_unpack(self, st: struct.Struct) -> tuple:
		"""Read and unpack data from the socket according to the struct ``st``.
		
		The number of bytes to read is determined using :field:`struct.Struct.size`,
		so variable-sized structs cannot be used with this method.
		"""
		
		return st.unpack(self._read(st.size))
	
	def handle(self) -> None:
		logger.info("Connection from %s", self.client_address)
		
		conn_type, header_length = self._read_unpack(CONNECT_HEADER_1)
		if header_length != CONNECT_HEADER_LENGTH:
			logger.error("Client sent connect header with unexpected length %d (should be %d)", header_length, CONNECT_HEADER_LENGTH)
			return
		
		self.type = ConnectionType(conn_type)
		build_id, build_type, branch_id, product_id = self._read_unpack(CONNECT_HEADER_2)
		self.build_id = build_id
		self.build_type = BuildType(build_type)
		self.branch_id = branch_id
		self.product_id = uuid.UUID(bytes_le=product_id)
		logger.debug("Received connect packet header: connection type %s, build ID %d, build type %s, branch ID %d, product ID %s", self.type, self.build_id, self.build_type, self.branch_id, self.product_id)
		
		if self.type == ConnectionType.cli2auth:
			data_bytes, token = self._read_unpack(CLI2AUTH_CONNECT_DATA)
			token = uuid.UUID(bytes_le=token)
			logger.debug("Received client-to-auth connect data: %d bytes, token %s", data_bytes, token)
		else:
			logger.error("Unsupported connection type: %s", self.type)
			return
		
		message_type, length = self._read_unpack(SETUP_MESSAGE_HEADER)
		message_type = SetupMessageType(message_type)
		logger.debug("Received setup message: type %s, %d bytes", message_type, length)
		
		data = self._read(length - SETUP_MESSAGE_HEADER.size)
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
			self._write(SETUP_MESSAGE_HEADER.pack(SetupMessageType.srv2cli_encrypt.value, 9) + b"noCrypt")
		else:
			# H'uru internal client sent an empty server seed to explicitly request no encryption.
			# We have to reply with an empty client seed,
			# or else the client will abort the connection.
			logger.debug("Received empty server seed - setting up unencrypted connection.")
			self._write(SETUP_MESSAGE_HEADER.pack(SetupMessageType.srv2cli_encrypt.value, 2))
		
		logger.debug("Auth server connection set up")
		
		message_type = int.from_bytes(self._read(2), "little")
		logger.debug("Received message: type %d", message_type)
		
		if self.type == ConnectionType.cli2auth and message_type == 1:
			build_id = int.from_bytes(self._read(4), "little")
			logger.debug("Build ID: %d", build_id)
			
			# Reply to client register request
			self._write(b"\x03\x00\xde\xad\xbe\xef")
			
			data = self._read(14)
			logger.debug("Received stuff: %s", data)
			if data[:2] == "\x00\x00":
				# Reply to ping
				self._write(data)
			
			logger.debug("Received stuff: %s", self._read(50))
	
	def finish(self) -> None:
		super().finish()
		logger.info("Disconnecting %s", self.client_address)


class NAGUS(socketserver.TCPServer):
	def __init__(self, server_address: typing.Tuple[str, int]) -> None:
		super().__init__(server_address, NAGUSConnection)
		logger.info("NAGUS listening on address %s...", server_address)
	
	def handle_error(self, request: socket.socket, client_address: typing.Tuple[str, int]) -> None:
		logger.error("Uncaught exception while handling request from %s:", client_address, exc_info=True)


def main() -> typing.NoReturn:
	logging.basicConfig(level=logging.DEBUG)
	
	address = ("", 14617)
	
	try:
		with NAGUS(address) as server:
			server.serve_forever()
	except KeyboardInterrupt:
		logger.info("KeyboardInterrupt received, stopping server.")
	
	sys.exit(0)


if __name__ == "__main__":
	sys.exit(main())
