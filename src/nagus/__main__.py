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


class NagusRequestHandler(socketserver.BaseRequestHandler):
	def handle(self) -> None:
		logger.info("Connection from %s", self.client_address)
		
		data = self.request.recv(ASYNC_SOCKET_CONNECT_PACKET.size)
		conn_type, hdr_bytes, build_id, build_type, branch_id, product_id = ASYNC_SOCKET_CONNECT_PACKET.unpack(data)
		conn_type = ConnectionType(conn_type)
		build_type = BuildType(build_type)
		product_id = uuid.UUID(bytes_le=product_id)
		logger.debug("Received connect packet: connection type %s, %d bytes, build ID %d, build type %s, branch ID %d, product ID %s", conn_type, hdr_bytes, build_id, build_type, branch_id, product_id)


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
