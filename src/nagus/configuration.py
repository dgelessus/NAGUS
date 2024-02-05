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
import collections
import configparser
import enum
import ipaddress
import logging
import os
import pathlib
import sys
import typing
import uuid

from . import structs


# Be careful:
# this logger must not be used inside the Configuration class
# or any other code that might run while parsing the main config file,
# because the logging system is only configured *after* the main config file has been parsed!
logger = logging.getLogger(__name__)


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


class WhichStaticAgeInstance(enum.Enum):
	static = "static"
	none = "none"


class SendServerCaps(enum.Enum):
	always = "always"
	compatible = "compatible"
	never = "never"


class ParsePlMessages(enum.Enum):
	necessary = "necessary"
	known = "known"


class StaticAgeInstanceDefinition(object):
	age_file_name: str
	instance_uuid: typing.Optional[uuid.UUID]
	instance_name: typing.Optional[str]
	user_defined_name: typing.Optional[str]
	
	def __init__(
		self,
		age_file_name: str,
		instance_uuid: typing.Optional[uuid.UUID] = None,
		instance_name: typing.Optional[str] = None,
		user_defined_name: typing.Optional[str] = None,
	) -> None:
		super().__init__()
		
		self.age_file_name = age_file_name
		self.instance_uuid = instance_uuid
		self.instance_name = instance_name
		self.user_defined_name = user_defined_name
	
	def __repr__(self) -> str:
		return f"{type(self).__qualname__}(age_file_name={self.age_file_name!r}, instance_uuid={self.instance_uuid!r}, instance_name={self.instance_name!r}, user_defined_name={self.user_defined_name!r})"


def parse_static_ages_ini(ini_path: typing.Union[str, bytes, os.PathLike[str], os.PathLike[bytes]]) -> typing.Iterable[StaticAgeInstanceDefinition]:
	# Can't use configparser here,
	# because static_ages.ini may contain multiple sections with the same name:
	# an age instance that should receive a random instance UUID uses the section name [auto]
	# and a single static_ages.ini can contain multiple such instances.
	# configparser doesn't support this -
	# it considers duplicate section names an error by default,
	# and even if this check is disabled,
	# it merges/overwrites the identically named sections instead of keeping them both.
	# So we have to parse static_ages.ini manually instead
	# (thankfully the format used by DIRTSAND is very simple).
	with open(ini_path, "r", encoding="utf-8") as f:
		section_name: typing.Optional[str] = None
		instance_uuid: typing.Optional[uuid.UUID] = None
		age_file_name: typing.Optional[str] = None
		instance_name: typing.Optional[str] = None
		user_defined_name: typing.Optional[str] = None
		
		def _build_result() -> StaticAgeInstanceDefinition:
			assert section_name is not None
			if age_file_name is None:
				raise ConfigError(f"In section {section_name!r}: Missing required option 'Filename'")
			
			return StaticAgeInstanceDefinition(
				age_file_name=age_file_name,
				instance_uuid=instance_uuid,
				instance_name=instance_name,
				user_defined_name=user_defined_name,
			)
		
		for lineno, line in enumerate(f, 1):
			line = line.strip()
			if not line or line.startswith("#"):
				# Ignore comments and empty lines.
				continue
			
			if line.startswith("[") and line.endswith("]"):
				if section_name is not None:
					yield _build_result()
				
				section_name = line[1:-1]
				if section_name == "auto":
					instance_uuid = None
				else:
					try:
						instance_uuid = uuid.UUID(section_name)
					except ValueError as exc:
						raise ConfigError(f"Line {lineno}: Section name {section_name!r} is not 'auto' or a UUID: {exc}")
				
				age_file_name = None
				instance_name = None
				user_defined_name = None
			elif section_name is None:
				raise ConfigError(f"Line {lineno}: Missing section name")
			else:
				option, sep, value = line.partition("=")
				if not sep:
					raise ConfigError(f"Line {lineno}, in section {section_name!r}: Invalid syntax - expected a section header, option assignment, comment, or blank line")
				
				option = option.rstrip()
				value = value.lstrip()
				
				if option == "Filename":
					age_file_name = value
				elif option == "Instance":
					instance_name = value
				elif option == "UserName":
					user_defined_name = value
				else:
					logger.warning("In static age instance configuration, line %d, in section %r: Ignoring unknown option %r", lineno, section_name, option)
		
		if section_name is not None:
			yield _build_result()


class Configuration(object):
	database_path: str
	database_journal_mode: str
	
	logging_config: typing.Dict[str, typing.Any]
	logging_enable_crash_lines: bool
	
	console_enable: bool
	
	ages_static_ages_config_file: typing.Optional[pathlib.Path]
	ages_public_aegura_instance: typing.Union[uuid.UUID, WhichStaticAgeInstance]
	ages_default_neighborhood_instance: typing.Union[uuid.UUID, WhichStaticAgeInstance]
	
	server_listen_address: str
	server_address_for_client: typing.Optional[ipaddress.IPv4Address]
	server_port: int
	
	server_status_enable: bool
	server_status_listen_address: str
	server_status_port: int
	server_status_message: str
	server_status_add_version_info: bool
	
	server_gatekeeper_file_server_address: typing.Optional[str]
	server_gatekeeper_auth_server_address: typing.Optional[str]
	
	server_auth_send_server_caps: SendServerCaps
	server_auth_send_server_address: bool
	server_auth_address_for_client: typing.Optional[ipaddress.IPv4Address]
	server_auth_disconnected_client_timeout: int
	
	server_game_address_for_client: typing.Optional[ipaddress.IPv4Address]
	server_game_parse_pl_messages: ParsePlMessages
	
	# The following variables aren't set directly from configuration options,
	# but instead derived from external files referenced in the options.
	ages_static_ages_config: typing.Sequence[StaticAgeInstanceDefinition]
	
	def _set_option_internal(self, option: typing.Tuple[str, ...], value: str) -> None:
		if option == ("database", "path"):
			self.database_path = value
		elif option == ("database", "journal_mode"):
			self.database_journal_mode = value
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
		elif option == ("ages", "static_ages_config_file"):
			self.ages_static_ages_config_file = pathlib.Path(value) if value else None
		elif option == ("ages", "public_aegura_instance"):
			try:
				self.ages_public_aegura_instance = WhichStaticAgeInstance(value)
			except ValueError as exc1:
				try:
					self.ages_public_aegura_instance = uuid.UUID(value)
				except ValueError as exc2:
					raise ConfigError(f"Invalid value for option: {exc1}, {exc2}")
		elif option == ("ages", "default_neighborhood_instance"):
			try:
				self.ages_default_neighborhood_instance = WhichStaticAgeInstance(value)
			except ValueError as exc1:
				try:
					self.ages_default_neighborhood_instance = uuid.UUID(value)
				except ValueError as exc2:
					raise ConfigError(f"Invalid value for option: {exc1}, {exc2}")
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
		elif option == ("server", "gatekeeper", "file_server_address"):
			self.server_gatekeeper_file_server_address = value if value else None
		elif option == ("server", "gatekeeper", "auth_server_address"):
			self.server_gatekeeper_auth_server_address = value if value else None
		elif option == ("server", "auth", "send_server_caps"):
			try:
				self.server_auth_send_server_caps = SendServerCaps(value)
			except ValueError as exc:
				raise ConfigError(f"Invalid value for option: {exc}")
		elif option == ("server", "auth", "send_server_address"):
			self.server_auth_send_server_address = parse_bool(value)
		elif option == ("server", "auth", "address_for_client"):
			self.server_auth_address_for_client = parse_ipv4_address(value) if value else None
		elif option == ("server", "auth", "disconnected_client_timeout"):
			self.server_auth_disconnected_client_timeout = parse_int(value)
			if self.server_auth_disconnected_client_timeout < 0:
				raise ConfigError(f"Timeout must not be negative: {self.server_auth_disconnected_client_timeout}")
		elif option == ("server", "game", "address_for_client"):
			self.server_game_address_for_client = parse_ipv4_address(value) if value else None
		elif option == ("server", "game", "parse_pl_messages"):
			try:
				self.server_game_parse_pl_messages = ParsePlMessages(value)
			except ValueError as exc:
				raise ConfigError(f"Invalid value for option: {exc}")
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
	
	def set_options_from_ini_file(self, ini_path: typing.Union[str, bytes, os.PathLike[str], os.PathLike[bytes]]) -> None:
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
		if not hasattr(self, "database_journal_mode"):
			self.database_journal_mode = "wal"
		if not hasattr(self, "logging_config"):
			self.logging_config = {
				"version": 1,
				"incremental": True,
				"root": {"level": "DEBUG"},
				"loggers": {
					"asyncio": {"level": "INFO"},
					"nagus.auth_server.connect": {"level": "INFO"},
					"nagus.auth_server.login": {"level": "INFO"},
					"nagus.auth_server.ping": {"level": "INFO"},
					"nagus.auth_server.vault.read": {"level": "INFO"},
					"nagus.auth_server.vault.notify": {"level": "INFO"},
					"nagus.base": {"level": "INFO"},
					"nagus.console": {"level": "INFO"},
					"nagus.game_server.join": {"level": "INFO"},
					"nagus.game_server.net_message": {"level": "INFO"},
					"nagus.game_server.paging": {"level": "INFO"},
					"nagus.game_server.ping": {"level": "INFO"},
					"nagus.game_server.pl_message": {"level": "INFO"},
					"nagus.game_server.sdl": {"level": "INFO"},
					"nagus.game_server.test_and_set": {"level": "INFO"},
					"nagus.game_server.voice": {"level": "INFO"},
					"nagus.gatekeeper_server": {"level": "INFO"},
				},
			}
		if not hasattr(self, "logging_enable_crash_lines"):
			self.logging_enable_crash_lines = True
		if not hasattr(self, "console_enable"):
			self.console_enable = True
		if not hasattr(self, "ages_static_ages_config_file"):
			self.ages_static_ages_config_file = pathlib.Path("static_ages.ini")
		if not hasattr(self, "ages_public_aegura_instance"):
			self.ages_public_aegura_instance = WhichStaticAgeInstance.static
		if not hasattr(self, "ages_default_neighborhood_instance"):
			self.ages_default_neighborhood_instance = WhichStaticAgeInstance.static
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
		if not hasattr(self, "server_gatekeeper_file_server_address"):
			self.server_gatekeeper_file_server_address = None
		if not hasattr(self, "server_auth_send_server_caps"):
			self.server_auth_send_server_caps = SendServerCaps.compatible
		if not hasattr(self, "server_auth_send_server_address"):
			self.server_auth_send_server_address = True
		if not hasattr(self, "server_auth_address_for_client"):
			self.server_auth_address_for_client = self.server_address_for_client
		if not hasattr(self, "server_gatekeeper_auth_server_address"):
			if self.server_auth_address_for_client is None:
				self.server_gatekeeper_auth_server_address = None
			else:
				self.server_gatekeeper_auth_server_address = str(self.server_auth_address_for_client)
		if not hasattr(self, "server_auth_disconnected_client_timeout"):
			self.server_auth_disconnected_client_timeout = 30 if self.server_auth_send_server_address else 0
		if not hasattr(self, "server_game_address_for_client"):
			self.server_game_address_for_client = self.server_address_for_client
		if not hasattr(self, "server_game_parse_pl_messages"):
			self.server_game_parse_pl_messages = ParsePlMessages.necessary
	
	def read_external_files(self) -> None:
		"""Read configuration variables that are stored in or derived from other files.
		
		Should only be called after all configuration options have been set,
		because some of the options determine if/which other files need to be read.
		"""
		
		if self.ages_static_ages_config_file is not None:
			try:
				self.ages_static_ages_config = list(parse_static_ages_ini(self.ages_static_ages_config_file))
			except FileNotFoundError as exc:
				raise ConfigError(f"Static ages configuration file (ages.static_ages_config_file) does not exist: {exc}")
			
			# Implementing [auto] correctly for multiple static instances of the same age gets a bit complex.
			# Having multiple static instances of the same age at all is rare enough,
			# so it's not worth the effort to support [auto] for this edge case.
			age_file_names = collections.Counter(age.age_file_name for age in self.ages_static_ages_config)
			for age in self.ages_static_ages_config:
				if age.instance_uuid is None and age_file_names[age.age_file_name] > 1:
					raise ConfigError(f"Cannot use [auto] instance UUIDs when defining more than one instance of age {age.age_file_name!r}")
			
			# Check that the static ages config defines the necessary ages for these options.
			# This gives nicer error reporting
			# and ensures that the configuration is consistent
			# before the server starts creating any of the static age instances.
			
			if self.ages_public_aegura_instance == WhichStaticAgeInstance.static:
				static_aeguras = [age for age in self.ages_static_ages_config if age.age_file_name == structs.AEGURA_AGE_NAME]
				if not static_aeguras:
					raise ConfigError("Static ages configuration doesn't define an instance of city (Ae'gura) - please define one")
				elif len(static_aeguras) > 1:
					raise ConfigError("Static ages configuration defines multiple instances of city (Ae'gura) - please set ages.public_aegura_instance to select which one should be the public Ae'gura instance")
			
			if self.ages_default_neighborhood_instance == WhichStaticAgeInstance.static:
				static_hoods = [age for age in self.ages_static_ages_config if age.age_file_name == structs.NEIGHBORHOOD_AGE_NAME]
				if not static_hoods:
					raise ConfigError("Static ages configuration doesn't define a Neighborhood instance - please define one to act as the default neighborhood for new avatars")
				elif len(static_hoods) > 1:
					raise ConfigError("Static ages configuration defines multiple Neighborhood instances - please set ages.default_neighborhood_instance to select which one should be the default neighborhood for new avatars")
