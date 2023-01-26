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

from . import __version__
from . import state


logger = logging.getLogger(__name__)


HELP_TEXT = """Available commands:
	exit, shutdown, stop, q, quit - Shut down the server
	help, ? - Display this help text
	loglevel [LEVEL_NAME] - Display or change the server log level (option logging.level)
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
		print()
	elif command == "version":
		_check_arg_count(0)
		print(f"This is NAGUS version {__version__}")
	elif command == "loglevel":
		if not args:
			current_level = logging.root.getEffectiveLevel()
			print("Current log level: " + logging.getLevelName(current_level))
		elif len(args) == 1:
			log_level: typing.Union[str, int]
			(log_level,) = args
			
			try:
				log_level = int(log_level)
			except ValueError:
				pass
			
			try:
				logging.root.setLevel(log_level)
			except ValueError as exc:
				raise UserError(str(exc))
			
			if isinstance(log_level, int):
				log_level = logging.getLevelName(log_level)
			
			print(f"Log level now set to {log_level}")
		else:
			raise UserError(f"Expected at most 1 argument, not {len(args)}")
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
	if not server_state.config.console_enable:
		return
	
	while True:
		line = await read_line("nagus> ")
		await run_line(server_state, line)
