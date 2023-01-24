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


"""Implements the :ref:`status server <status_server>`.

This uses the regular non-async :mod:`http.server`,
because there is no :mod:`asyncio`-based HTTP server in the Python standard library.
"""


import asyncio
import datetime
import http.server
import json
import logging
import threading
import typing

from . import __version__
from . import state


logger = logging.getLogger(__name__)


class StatusServerRequestHandler(http.server.BaseHTTPRequestHandler):
	server_state: state.ServerState
	
	def __init__(self, *args: typing.Any, server_state: state.ServerState) -> None:
		self.server_state = server_state
		super().__init__(*args)
	
	def log_message(self, format: str, *args: typing.Any) -> None:
		if logger.isEnabledFor(logging.INFO):
			logger.info("[%s] %s", self.address_string(), format % args)
	
	def format_status_text(self) -> str:
		text = self.server_state.config.server_status_message
		if self.server_state.config.server_status_add_version_info:
			timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
			text += f"\nNAGUS {__version__} @ {timestamp}"
		return text
	
	def respond(self, content_type: str, data: bytes) -> None:
		self.send_response(http.HTTPStatus.OK)
		self.send_header("Content-Type", content_type)
		self.send_header("Content-Length", str(len(data)))
		self.send_header("Last-Modified", self.date_time_string())
		self.end_headers()
		if self.command != "HEAD":
			self.wfile.write(data)
	
	def doit(self) -> None:
		if self.path in {"/serverstatus/moulbeta.php", "/serverstatus/moullive.php", "/welcome"}:
			self.respond("text/plain", self.format_status_text().encode("ascii"))
		elif self.path == "/status":
			status_obj = {
				"online": True,
				"welcome": self.format_status_text(),
			}
			self.respond("application/json", json.dumps(status_obj).encode("utf-8"))
		else:
			self.send_error(http.HTTPStatus.NOT_FOUND)
			return
	
	def do_HEAD(self) -> None:
		self.doit()
	
	def do_GET(self) -> None:
		self.doit()
	
	def do_POST(self) -> None:
		if self.path == "/serverstatus/moulbeta.php":
			# OpenUru plUruLauncher with build type BETA uses POST instead of GET here.
			self.doit()
		else:
			self.send_error(http.HTTPStatus.NOT_IMPLEMENTED)


def _run_server(server_state: state.ServerState, future: asyncio.Future[None]) -> None:
	host = server_state.config.server_status_listen_address
	port = server_state.config.server_status_port
	loop = server_state.loop
	
	def _request_handler(*args: typing.Any) -> "StatusServerRequestHandler":
		return StatusServerRequestHandler(*args, server_state=server_state)

	with http.server.ThreadingHTTPServer((host, port), _request_handler) as server:
		try:
			@loop.call_soon_threadsafe
			def _add_callback_callback() -> None:
				@future.add_done_callback
				def _shutdown_callback(_future: asyncio.Future[None]) -> None:
					threading.Thread(target=server.shutdown, name="NAGUS status server shutdown thread", daemon=True).start()
		except RuntimeError:
			# Event loop is already closed
			return
		
		try:
			logger.info("NAGUS status server listening on address %r:%d...", host, port)
			server.serve_forever()
		except BaseException as e:
			try:
				@loop.call_soon_threadsafe
				def _exception_callback() -> None:
					if not future.cancelled():
						future.set_exception(e)
			except RuntimeError:
				pass # Event loop is already closed
		else:
			try:
				@loop.call_soon_threadsafe
				def _success_callback() -> None:
					if not future.cancelled():
						future.set_result(None)
			except RuntimeError:
				pass # Event loop is already closed


async def run_status_server(server_state: state.ServerState) -> None:
	"""Run a status server at the given address and port.
	
	The status server continues running until this coroutine is cancelled.
	"""
	
	if not server_state.config.server_status_enable:
		return
	
	# We can't use the usual functions like asyncio.to_thread or asyncio.AbstractEventLoop.run_in_executor,
	# because the futures they return can't be cancelled properly
	# (cancelling the future does nothing once the function has started executing).
	# In addition,
	# those APIs run the given function on a shared executor,
	# which is a bad idea for long-running threads.
	# So instead we create our own thread and set up a custom future that can be cancelled properly.
	future = server_state.loop.create_future()
	threading.Thread(target=lambda: _run_server(server_state, future), name="NAGUS status server").start()
	await future
