# This file is part of NAGUS, an Uru Live server that is not very good.
# Copyright (C) 2023 dgelessus
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


"""Provides a simple command-line console for interactively managing the server."""


import asyncio
import logging
import shlex
import sys
import typing
import uuid

from . import __version__
from . import auth_server
from . import base
from . import state


logger = logging.getLogger(__name__)


HELP_TEXT = """Available commands:
	exit, shutdown, stop, q, quit - Shut down the server
	help, ? - Display this help text
	version - Display the server's version number
	kick token|address|account|avatar WHO - Forcibly disconnect a client from the server
	list - List all clients connected to the server
	loglevel CATEGORY [LEVEL_NAME] - Display or change the log level for a category of log messages (or category "root" for all)
	status [STATUS_MESSAGE] [MORE_LINES ...] - Display or change the status message (option server.status.message)
"""


class ServerShutdownRequest(Exception):
	pass


class CommandError(Exception):
	pass


class UserError(CommandError):
	pass


async def read_line(prompt: str = "") -> str:
	"""Primitive async wrapper around :func:`input`."""
	
	return await asyncio.get_event_loop().run_in_executor(None, input, prompt)


async def run_command(server_state: state.ServerState, command: str, args: typing.Sequence[str]) -> None:
	def _check_arg_count(count: int) -> None:
		if len(args) != count:
			raise UserError(f"Expected exactly {count} arguments, not {len(args)}")
	
	if command in {"exit", "shutdown", "stop", "q", "quit"}:
		_check_arg_count(0)
		raise ServerShutdownRequest("Server was shut down via console")
	elif command in {"help", "?"}:
		_check_arg_count(0)
		print(HELP_TEXT, end="")
	elif command == "version":
		_check_arg_count(0)
		print(f"This is NAGUS version {__version__}")
	elif command == "kick":
		_check_arg_count(2)
		
		what = args[0]
		who = args[1]
		
		conns: typing.List[auth_server.AuthConnection] = []
		if what == "token":
			try:
				token = uuid.UUID(who)
			except ValueError as exc:
				raise UserError(exc)
			
			try:
				conns.append(server_state.auth_connections[token])
			except KeyError:
				pass
		elif what == "address":
			for conn in server_state.auth_connections.values():
				client_address = conn.writer.get_extra_info("peername")
				if client_address[0] == who:
					conns.append(conn)
		elif what == "account":
			try:
				account_uuid = uuid.UUID(who)
			except ValueError as exc:
				raise UserError(exc)
			
			for conn in server_state.auth_connections.values():
				if getattr(conn.client_state, "account_uuid", None) == account_uuid:
					conns.append(conn)
		elif what == "avatar":
			try:
				ki_number = int(who)
			except ValueError as exc:
				raise UserError(exc)
			
			for conn in server_state.auth_connections.values():
				if conn.client_state.ki_number == ki_number:
					conns.append(conn)
		else:
			raise UserError(f"Don't know how to kick by {what!r} (expected token, address, account, or avatar)")
		
		if not conns:
			raise UserError(f"Couldn't find a connected client with {what} {who}")
		
		for conn in conns:
			kick_task = conn.kick_async(base.NetError.kicked_by_ccr, set_avatar_offline=True)
			if kick_task is not None:
				server_state.add_background_task(kick_task)
		
		if len(conns) == 1:
			print(f"Kicked client with {what} {who}")
		else:
			print(f"Kicked {len(conns)} clients with {what} {who}")
	elif command == "list":
		_check_arg_count(0)
		
		if not server_state.auth_connections:
			print(f"There are no clients currently connected")
			return
		
		print(f"There are {len(server_state.auth_connections)} clients currently connected:")
		for token, conn in server_state.auth_connections.items():
			try:
				account_uuid = conn.client_state.account_uuid
			except AttributeError:
				player_state_desc = "not logged in"
			else:
				player_state_desc = f"account {account_uuid}"
				if conn.client_state.ki_number is not None:
					player_state_desc += f", avatar {conn.client_state.ki_number}"
					# TODO Fetch avatar name and current age from vault
				else:
					player_state_desc += ", not playing"
			
			client_address = conn.writer.get_extra_info("peername")
			desc = f"{token} {client_address!r} - {player_state_desc}"
			if hasattr(conn.client_state, "cleanup_handle"):
				desc += " (recently disconnected)"
			print(desc)
	elif command == "loglevel":
		if len(args) not in {1, 2}:
			raise UserError(f"Expected 1 or 2 arguments, not {len(args)}")
		
		logger_name = args[0]
		logg = logging.getLogger(None if logger_name == "root" else logger_name)
		
		if len(args) == 1:
			level_name = logging.getLevelName(logg.getEffectiveLevel())
			print(f"Current log level for {logger_name!r} is {level_name}")
		else:
			log_level: typing.Union[str, int] = args[1]
			try:
				log_level = int(log_level)
			except ValueError:
				pass
			
			try:
				logg.setLevel(log_level)
			except ValueError as exc:
				raise UserError(str(exc))
			
			if isinstance(log_level, int):
				log_level = logging.getLevelName(log_level)
			
			print(f"Log level for {logger_name!r} now set to {log_level}")
	elif command == "status":
		if not args:
			print("Current status message:")
			print(server_state.status_message)
		else:
			server_state.status_message = "\n".join(args)
			print("Status message changed to:")
			print(server_state.status_message)
	else:
		raise UserError(f"Unknown command - run 'help' for a list of available commands")


async def run_line(server_state: state.ServerState, line: str) -> None:
	try:
		words = shlex.split(line)
	except ValueError as exc:
		print(f"Error: Invalid syntax: {exc}", file=sys.stderr)
		return
	
	if not words:
		# Blank line does nothing.
		return
	
	logger.debug("Executing console command: %r", words)
	
	command, *args = words
	try:
		await run_command(server_state, command, args)
	except ServerShutdownRequest:
		# Let it propagate up to async_main,
		# shutting down the main server task along the way.
		raise
	except CommandError as exc:
		print(f"Error: {command}: {exc}", file=sys.stderr)
	except Exception as exc:
		print(f"Internal error in command {command!r}: {type(exc).__name__}: {exc}", file=sys.stderr)
		logger.error("Internal error in command %r", command, exc_info=exc)


async def run_console(server_state: state.ServerState) -> None:
	while True:
		line = await read_line("nagus> ")
		await run_line(server_state, line)
