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


import argparse
import asyncio
import logging
import logging.config
import random
import socket
import sys
import typing

from . import __version__
from . import auth_server
from . import base
from . import configuration
from . import console
from . import crash_lines
from . import game_server
from . import gatekeeper_server
from . import state


logger = logging.getLogger(__name__)
logger_client = logger.getChild("client")


DEFAULT_CONFIG_FILE_NAME = "nagus_config.ini"

CONNECTION_CLASSES: typing.Sequence[typing.Type[base.BaseMOULConnection]] = [
	gatekeeper_server.GatekeeperConnection,
	# TODO Add file server once implemented
	auth_server.AuthConnection,
	game_server.GameConnection,
]
CONNECTION_CLASSES_BY_TYPE: typing.Dict[base.ConnectionType, typing.Type[base.BaseMOULConnection]] = {
	cls.CONNECTION_TYPE: cls for cls in CONNECTION_CLASSES
}


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
	
	logger_client.info("Client %s requests connection type %s", client_address, conn_type)
	
	try:
		conn_class = CONNECTION_CLASSES_BY_TYPE[conn_type]
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
			await client_connected_inner(reader, writer, server_state)
		finally:
			writer.close()
			# No need to await writer.wait_closed(),
			# because we don't do anything else with the writer anymore.
	except (ConnectionResetError, asyncio.IncompleteReadError) as exc:
		logger_client.error("Client %s disconnected: %s.%s: %s", client_address, type(exc).__module__, type(exc).__qualname__, exc)
	except base.ProtocolError as exc:
		logger_client.error("Error in data sent by %s: %s", client_address, exc)
	except Exception as exc:
		if server_state.config.logging_enable_crash_lines:
			try:
				quip = random.choice(crash_lines.client_crash_lines)
			except IndexError:
				quip = "missingno"
		else:
			quip = "Server error"
		logger_client.error("%s (uncaught exception while handling request from %s)", quip, client_address, exc_info=exc)
	except asyncio.CancelledError:
		logger_client.info("Connection handler for %s was cancelled - most likely the server is shutting down", client_address)
		raise
	except BaseException as exc:
		logger_client.error("Uncaught BaseException while handling request from %s - something has gone quite wrong:", client_address, exc_info=exc)
		raise
	else:
		logger_client.info("Cleanly disconnected from client %s", client_address)


async def moul_server_main(server_state: state.ServerState) -> None:
	host = server_state.config.server_listen_address
	port = server_state.config.server_port
	
	async def _client_connected(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
		await client_connected(reader, writer, server_state)
	
	async with await asyncio.start_server(_client_connected, host, port) as server:
		logger.info("NAGUS listening on address %r:%d...", host, port)
		await server.serve_forever()


async def async_main(config: configuration.Configuration) -> None:
	db = await state.Database.connect(config.database_path)
	try:
		server_state = state.ServerState(config, asyncio.get_event_loop(), db)
		await server_state.setup_database()
		try:
			tasks = [
				asyncio.create_task(moul_server_main(server_state)),
			]
			
			if config.console_enable:
				tasks.append(asyncio.create_task(console.run_console(server_state)))
			
			if config.server_status_enable:
				from . import status_server
				tasks.append(asyncio.create_task(status_server.run_status_server(server_state)))
			
			await asyncio.gather(*tasks)
		finally:
			count = await server_state.set_all_avatars_offline()
			if count != 0:
				logger.debug("Set %d avatars to offline while shutting down server", count)
	finally:
		await db.close()


def main() -> typing.NoReturn:
	ap = argparse.ArgumentParser(
		formatter_class=argparse.RawDescriptionHelpFormatter,
		description="""
NAGUS is an experimental work-in-progress Uru Live/Myst Online server
written in pure Python. It is currently not very good.
""",
		add_help=False,
		allow_abbrev=False,
	)
	
	ap.add_argument("--help", action="help", help="Display this help message and exit.")
	ap.add_argument("--version", action="version", version=__version__, help="Display version information and exit.")
	
	config_file_group = ap.add_mutually_exclusive_group()
	config_file_group.add_argument("--config-file", help=f"Read server configuration from the given file instead of the default location ({DEFAULT_CONFIG_FILE_NAME}).")
	config_file_group.add_argument("--no-config-file", action="store_true", help="Don't read any config file - only use command-line and default configuration.")
	
	ap.add_argument("-c", "--config", action="append", help="Set a configuration setting (format: section.name=value), overriding the default and any previous setting from the config file.")
	
	ns = ap.parse_args()
	
	config = configuration.Configuration()
	
	if ns.no_config_file:
		print("Info: Server config file disabled - using only command-line and default configuration.", file=sys.stderr)
	else:
		if ns.config_file is None:
			config_file = DEFAULT_CONFIG_FILE_NAME
		else:
			config_file = ns.config_file
		
		try:
			config.set_options_from_ini_file(config_file)
		except FileNotFoundError as exc:
			if ns.config_file is None:
				print(f"Warning: Server config file not found at default location: {exc}", file=sys.stderr)
				print("Warning: See nagus_config.defaults.ini for a list of supported config settings.", file=sys.stderr)
				print("Warning: Or pass --no-config-file to suppress this warning.", file=sys.stderr)
			else:
				print(f"Error: Server config file does not exist: {exc}", file=sys.stderr)
				sys.exit(1)
		except configuration.ConfigError as exc:
			print(f"Error: In config file {config_file!r}: {exc}", file=sys.stderr)
			sys.exit(1)
	
	if ns.config is None:
		ns.config = []
	
	for setting in ns.config:
		option, sep, value = setting.partition("=")
		if not sep:
			print(f"Error: In -c/--config option: Invalid argument - expected format section.name=value, but got {setting!r}", file=sys.stderr)
			sys.exit(2)
		
		try:
			config.set_option(option.split("."), value)
		except configuration.ConfigError as exc:
			print(f"Error: In -c/--config option: {exc}", file=sys.stderr)
			sys.exit(2)
	
	try:
		config.set_defaults()
	except configuration.ConfigError as exc:
		print(f"Error: In server configuration: {exc}", file=sys.stderr)
		sys.exit(1)
	
	logging.basicConfig(
		format="[%(levelname)s] %(name)s: %(message)s",
		stream=sys.stdout,
	)
	logging.config.dictConfig(config.logging_config)
	
	try:
		config.read_external_files()
	except configuration.ConfigError as exc:
		print(f"Error: While processing external configuration files: {exc}", file=sys.stderr)
		sys.exit(1)
	
	try:
		asyncio.run(async_main(config))
	except KeyboardInterrupt:
		logger.info("KeyboardInterrupt received, stopping server.")
	except console.ServerShutdownRequest:
		logger.info("Shutdown requested via console, stopping server.")
	
	sys.exit(0)


if __name__ == "__main__":
	sys.exit(main())
