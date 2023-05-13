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


"""Parses and stores config settings.

Yes, this is all coded manually.
I'm sure there's a good way to handle this generically,
but this way is easier for now.
"""


import ast
import configparser
import ipaddress
import os
import sys
import typing


class ConfigError(Exception):
	pass


def parse_bool(s: str) -> bool:
	if s == "false":
		return False
	elif s == "true":
		return True
	else:
		raise ConfigError(f"Invalid boolean value: expected true or false, but found {s!r}")


def parse_int(s: str) -> int:
	try:
		return int(s)
	except ValueError as exc:
		raise ConfigError(f"Invalid integer value: {exc!s}")


def parse_ipv4_address(s: str) -> ipaddress.IPv4Address:
	try:
		return ipaddress.IPv4Address(s)
	except ValueError as exc:
		raise ConfigError(f"Invalid IPv4 address: {exc!s}")


class Configuration(object):
	database_path: str
	
	logging_config: dict
	logging_enable_crash_lines: bool
	
	console_enable: bool
	
	server_listen_address: str
	server_address_for_client: typing.Optional[ipaddress.IPv4Address]
	server_port: int
	
	server_status_enable: bool
	server_status_listen_address: str
	server_status_port: int
	server_status_message: str
	server_status_add_version_info: bool
	
	server_auth_send_server_address: bool
	server_auth_address_for_client: typing.Optional[ipaddress.IPv4Address]
	
	server_game_address_for_client: typing.Optional[ipaddress.IPv4Address]
	
	def _set_option_internal(self, option: typing.Tuple[str, ...], value: str) -> None:
		if option == ("database", "path"):
			self.database_path = value
		elif option == ("logging", "config"):
			try:
				obj = ast.literal_eval(value)
			except SyntaxError as e:
				raise ConfigError(e)
			
			if not isinstance(obj, dict):
				raise ConfigError(f"Expected a Python dictionary, not {type(obj).__name__}")
			self.logging_config = obj
		elif option == ("logging", "enable_crash_lines"):
			self.logging_enable_crash_lines = parse_bool(value)
		elif option == ("console", "enable"):
			self.console_enable = parse_bool(value)
		elif option == ("server", "listen_address"):
			self.server_listen_address = value
		elif option == ("server", "port"):
			self.server_port = parse_int(value)
		elif option == ("server", "address_for_client"):
			self.server_address_for_client = parse_ipv4_address(value) if value else None
		elif option == ("server", "status", "enable"):
			self.server_status_enable = parse_bool(value)
		elif option == ("server", "status", "listen_address"):
			self.server_status_listen_address = value
		elif option == ("server", "status", "port"):
			self.server_status_port = parse_int(value)
		elif option == ("server", "status", "message"):
			self.server_status_message = value
		elif option == ("server", "status", "add_version_info"):
			self.server_status_add_version_info = parse_bool(value)
		elif option == ("server", "auth", "send_server_address"):
			self.server_auth_send_server_address = parse_bool(value)
		elif option == ("server", "auth", "address_for_client"):
			self.server_auth_address_for_client = parse_ipv4_address(value) if value else None
		elif option == ("server", "game", "address_for_client"):
			self.server_game_address_for_client = parse_ipv4_address(value) if value else None
		else:
			# Logging might not be set up here yet, so use stderr instead.
			print("Warning: Ignoring unknown config option " + repr(".".join(option)), file=sys.stderr)
	
	def set_option(self, option: typing.Tuple[str, ...], value: str) -> None:
		try:
			self._set_option_internal(tuple(option), value)
		except ConfigError as exc:
			option_name = ".".join(option)
			raise ConfigError(f"In option {option_name!r}: {exc}")
	
	def set_options_from_ini_data(self, ini_data: typing.Mapping[str, typing.Mapping[str, str]]) -> None:
		for section, section_data in ini_data.items():
			section_name_parts = tuple(section.split("."))
			for option_name, value in section_data.items():
				if "." in option_name:
					option_name_parts = option_name.split(".")
					correct_section_name = ".".join([section, *option_name_parts[:-1]])
					correct_option_name = option_name_parts[-1]
					raise ConfigError(f"In section {section!r}: Literal dots are not allowed in INI option name: {option_name!r} (write option {correct_option_name!r} in section {correct_section_name!r} instead)")
				
				self.set_option(section_name_parts + (option_name,), value)
	
	def set_options_from_ini_file(self, ini_path: typing.Union[str, bytes, os.PathLike]) -> None:
		parser = configparser.ConfigParser(
			# Disable alternative syntax characters.
			delimiters=("=",),
			comment_prefixes=("#",),
			# Disable empty lines in multi-line values.
			empty_lines_in_values=False,
			# Disable configparser's "default section" feature.
			default_section="[]do not use this feature[]",
			# Disable variable interpolation in values.
			interpolation=None,
		)
		
		# Read the file manually instead of using ConfigParser.read
		# so that FileNotFoundError isn't swallowed silently.
		with open(ini_path, "r", encoding="utf-8") as f:
			parser.read_file(f)
		
		self.set_options_from_ini_data(parser)
	
	def set_defaults(self) -> None:
		"""Set default values for all options that haven't been explicitly set previously."""
		
		if not hasattr(self, "database_path"):
			self.database_path = "nagus.sqlite"
		if not hasattr(self, "logging_config"):
			self.logging_config = {
				"version": 1,
				"incremental": True,
				"root": {"level": "DEBUG"},
				"loggers": {
					"nagus.auth_server.connect": {"level": "INFO"},
					"nagus.auth_server.login": {"level": "INFO"},
					"nagus.auth_server.ping": {"level": "INFO"},
					"nagus.auth_server.vault.read": {"level": "INFO"},
					"nagus.base": {"level": "INFO"},
					"nagus.console": {"level": "INFO"},
					"nagus.game_server.join": {"level": "INFO"},
					"nagus.game_server.net_message": {"level": "INFO"},
					"nagus.game_server.ping": {"level": "INFO"},
				},
			}
		if not hasattr(self, "logging_enable_crash_lines"):
			self.logging_enable_crash_lines = True
		if not hasattr(self, "console_enable"):
			self.console_enable = True
		if not hasattr(self, "server_listen_address"):
			self.server_listen_address = ""
		if not hasattr(self, "server_port"):
			self.server_port = 14617
		if not hasattr(self, "server_address_for_client"):
			self.server_address_for_client = None
		if not hasattr(self, "server_status_enable"):
			self.server_status_enable = True
		if not hasattr(self, "server_status_listen_address"):
			self.server_status_listen_address = self.server_listen_address
		if not hasattr(self, "server_status_port"):
			self.server_status_port = 8080
		if not hasattr(self, "server_status_message"):
			self.server_status_message = "Welcome to URU"
		if not hasattr(self, "server_status_add_version_info"):
			self.server_status_add_version_info = True
		if not hasattr(self, "server_auth_send_server_address"):
			self.server_auth_send_server_address = True
		if not hasattr(self, "server_auth_address_for_client"):
			self.server_auth_address_for_client = self.server_address_for_client
		if not hasattr(self, "server_game_address_for_client"):
			self.server_game_address_for_client = self.server_address_for_client
