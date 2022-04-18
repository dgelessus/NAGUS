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
import socketserver
import struct
import sys
import typing
import uuid


logger = logging.getLogger(__name__)


ASYNC_SOCKET_CONNECT_PACKET = struct.Struct("<BHIII16s")
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


class NagusRequestHandler(socketserver.StreamRequestHandler):
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
	
	def handle(self) -> None:
		logger.info("Connection from %s", self.client_address)
		
		data = self._read(ASYNC_SOCKET_CONNECT_PACKET.size)
		conn_type, hdr_bytes, build_id, build_type, branch_id, product_id = ASYNC_SOCKET_CONNECT_PACKET.unpack(data)
		conn_type = ConnectionType(conn_type)
		build_type = BuildType(build_type)
		product_id = uuid.UUID(bytes_le=product_id)
		logger.debug("Received connect packet: connection type %s, %d bytes, build ID %d, build type %s, branch ID %d, product ID %s", conn_type, hdr_bytes, build_id, build_type, branch_id, product_id)
		
		if conn_type == ConnectionType.cli2auth:
			data = self._read(CLI2AUTH_CONNECT_DATA.size)
			data_bytes, token = CLI2AUTH_CONNECT_DATA.unpack(data)
			token = uuid.UUID(bytes_le=token)
			logger.debug("Received client-to-auth connect data: %d bytes, token %s", data_bytes, token)
			
			data = self._read(SETUP_MESSAGE_HEADER.size)
			message_type, length = SETUP_MESSAGE_HEADER.unpack(data)
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
			
			if message_type == 1:
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


def main() -> typing.NoReturn:
	logging.basicConfig(level=logging.DEBUG)
	
	address = ("", 14617)
	
	try:
		with socketserver.TCPServer(address, NagusRequestHandler) as server:
			logger.info("NAGUS running and listening on address %s...", address)
			server.serve_forever()
	except KeyboardInterrupt:
		logger.info("KeyboardInterrupt received, stopping server.")
	
	sys.exit(0)


if __name__ == "__main__":
	sys.exit(main())
