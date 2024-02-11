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


"""Basic infrastructure shared across all server types."""


import abc
import asyncio
import enum
import ipaddress
import logging
import random
import struct
import typing
import uuid

from . import configuration
from . import crypto
from . import state
from . import structs


logger = logging.getLogger(__name__)
logger_connect = logger.getChild("connect")
logger_crypt = logger.getChild("crypt")
logger_message = logger.getChild("message")


CONNECT_HEADER_TAIL = struct.Struct("<III16s")
CONNECT_HEADER_LENGTH = struct.calcsize("<BH") + CONNECT_HEADER_TAIL.size

SETUP_MESSAGE_HEADER = struct.Struct("<BB")


SYSTEM_RANDOM = random.SystemRandom()


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


class NetError(structs.IntEnum):
	"""Python conversion of the :cpp:enum:`ENetError` enum,
	which is used for status codes in various messages.
	"""
	
	# These first two codes are not actually errors:
	pending = -1
	success = 0
	
	internal_error = 1
	timeout = 2
	bad_server_data = 3
	age_not_found = 4
	connect_failed = 5
	disconnected = 6
	file_not_found = 7
	old_build_id = 8
	remote_shutdown = 9
	timeout_odbc = 10
	account_already_exists = 11
	player_already_exists = 12
	account_not_found = 13
	player_not_found = 14
	invalid_parameter = 15
	name_lookup_failed = 16
	logged_in_elsewhere = 17
	vault_node_not_found = 18
	max_players_on_acct = 19
	authentication_failed = 20
	state_object_not_found = 21
	login_denied = 22
	circular_reference = 23
	account_not_activated = 24
	key_already_used = 25
	key_not_found = 26
	activation_code_not_found = 27
	player_name_invalid = 28
	not_supported = 29
	service_forbidden = 30
	auth_token_too_old = 31
	must_use_gametap_client = 32
	too_many_failed_logins = 33
	gametap_connection_failed = 34
	gt_too_many_auth_options = 35
	gt_missing_parameter = 36
	gt_server_error = 37
	account_banned = 38
	kicked_by_ccr = 39
	score_wrong_type = 40
	score_not_enough_points = 41
	score_already_exists = 42
	score_no_data_found = 43
	invite_no_matching_player = 44
	invite_too_many_hoods = 45
	need_to_pay = 46
	server_busy = 47
	vault_node_access_violation = 48
	
	@property
	def message(self) -> typing.Optional[str]:
		return NET_ERROR_MESSAGES.get(self, None)


NET_ERROR_MESSAGES = {
	NetError.success: "Success",
	NetError.internal_error: "Internal Error",
	NetError.timeout: "No Response From Server",
	NetError.bad_server_data: "Invalid Server Data",
	NetError.age_not_found: "Age Not Found",
	NetError.connect_failed: "Network Connection Failed",
	NetError.disconnected: "Disconnected From Server",
	NetError.file_not_found: "File Not Found",
	NetError.old_build_id: "Old Build",
	NetError.remote_shutdown: "Remote Shutdown",
	NetError.timeout_odbc: "Database Timeout",
	NetError.account_already_exists: "Account Already Exists",
	NetError.player_already_exists: "Player Already Exists",
	NetError.account_not_found: "Account Not Found",
	NetError.player_not_found: "Player Not Found",
	NetError.invalid_parameter: "Invalid Parameter",
	NetError.name_lookup_failed: "Name Lookup Failed",
	NetError.logged_in_elsewhere: "Logged In Elsewhere",
	NetError.vault_node_not_found: "Vault Node Not Found",
	NetError.max_players_on_acct: "Max Players On Account",
	NetError.authentication_failed: "Authentication Failed",
	NetError.state_object_not_found: "State Object Not Found",
	NetError.login_denied: "Login Denied",
	NetError.circular_reference: "Circular Reference",
	NetError.account_not_activated: "Account Not Activated",
	NetError.key_already_used: "Key Already Used",
	NetError.key_not_found: "Key Not Found",
	NetError.activation_code_not_found: "Activation Code Not Found",
	NetError.player_name_invalid: "Player Name Invalid",
	NetError.not_supported: "Not Supported",
	NetError.service_forbidden: "Service Forbidden",
	NetError.auth_token_too_old: "Auth Token Too Old",
	NetError.must_use_gametap_client: "Must Use GameTap Client",
	NetError.too_many_failed_logins: "Too Many Failed Logins",
	NetError.gametap_connection_failed: "GameTap: Connection Failed",
	NetError.gt_too_many_auth_options: "GameTap: Too Many Auth Options",
	NetError.gt_missing_parameter: "GameTap: Missing Parameter",
	NetError.gt_server_error: "GameTap: Server Error",
	NetError.account_banned: "Account has been banned",
	NetError.kicked_by_ccr: "Account kicked by CCR",
	NetError.score_wrong_type: "Wrong score type for operation",
	NetError.score_not_enough_points: "Not enough points",
	NetError.score_already_exists: "Non-fixed score already exists",
	NetError.score_no_data_found: "No score data found",
	NetError.invite_no_matching_player: "Invite: Couldn't find player",
	NetError.invite_too_many_hoods: "Invite: Too many hoods",
	NetError.need_to_pay: "Payments not up to date",
	NetError.server_busy: "Server Busy",
	NetError.vault_node_access_violation: "Vault Node Access Violation",
}


class ProtocolError(Exception):
	pass


def pack_string_field(string: str, max_length: int = 0xffff) -> bytes:
	encoded = string.encode("utf-16-le")
	# Can't use len(string) - it will give the wrong result if the string contains code points above U+FFFF!
	utf_16_length = len(encoded) // 2
	if utf_16_length >= max_length:
		raise ValueError(f"Attempted to send string of length {utf_16_length} in string field with maximum length {max_length} - this would break the client")
	return structs.UINT16.pack(utf_16_length) + encoded


ConnT = typing.TypeVar("ConnT", bound="BaseMOULConnection")
MessageHandler = typing.Callable[[ConnT], typing.Awaitable[None]]
MessageHandlerT = typing.TypeVar("MessageHandlerT", bound=MessageHandler[typing.Any])


def message_handler(message_type: int) -> typing.Callable[[MessageHandlerT], MessageHandlerT]:
	"""Register the decorated method as a handler for the given message type.
	
	When the message handler method is called,
	the message type has already been read,
	but nothing else.
	The message handler is responsible for reading the message body.
	This can't be done generically,
	because messages don't have an overall byte length field.
	
	This decorator should only be used inside :class:`BaseMOULConnection` and subclasses.
	The decorated method must be ``async``,
	should take no arguments,
	and should return nothing.
	The name of the message handler method should be the name of the message type
	(adjusted for Python's naming conventions) ---
	this is displayed in debug log messages.
	"""
	
	if callable(message_type):
		raise TypeError("@message_handler() decorator must be called with parentheses")
	
	def _message_handler_decorator(method: MessageHandlerT) -> MessageHandlerT:
		# We store the message type number on the function/method object.
		# There's no way to make mypy happy here.
		method.message_type = message_type # type: ignore
		return method
	
	return _message_handler_decorator


class BaseMOULConnection(object):
	"""Base implementation of the MOUL network protocol (spoken over port 14617).
	
	Subclasses are expected to implement :meth:`read_connect_packet_data`
	as well as message handlers for all supported message types
	(see :func:`message_handler`).
	"""
	
	MESSAGE_HANDLERS: "typing.ClassVar[typing.Dict[int, MessageHandler[BaseMOULConnection]]]"
	CONNECTION_TYPE: ConnectionType # to be set in each subclass
	
	reader: asyncio.StreamReader
	writer: asyncio.StreamWriter
	server_state: state.ServerState
	dh_keys: typing.Optional[configuration.DHKeys]
	
	build_id: int
	build_type: BuildType
	branch_id: int
	product_id: uuid.UUID
	encryption_state_read: typing.Optional[crypto.Rc4State]
	encryption_state_write: typing.Optional[crypto.Rc4State]
	
	@classmethod
	def __init_subclass__(cls) -> None:
		"""Register a new connection class and its message handlers.
		
		Every subclass of :class:`BaseMOULConnection` must set the class attribute :attr:`CONNECTION_TYPE`.
		This information is used by the top-level :func:`nagus.__main__.client_connected` handler to dispatch incoming connections to the correct classes.
		
		All message handler methods
		(decorated with :func:`message_handler`)
		inside the subclass are collected into the :attr:`MESSAGE_HANDLERS` dictionary,
		which is used by :meth:`handle_message` to efficiently dispatch messages by type.
		"""
		
		cls.MESSAGE_HANDLERS = {}
		
		for name in dir(cls):
			try:
				attr = getattr(cls, name)
			except AttributeError:
				continue
			
			if callable(attr):
				try:
					message_type = attr.message_type
				except AttributeError:
					continue
				
				cls.MESSAGE_HANDLERS[message_type] = typing.cast(MessageHandler[BaseMOULConnection], attr)
	
	def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, server_state: state.ServerState) -> None:
		super().__init__()
		
		self.reader = reader
		self.writer = writer
		self.server_state = server_state
		
		self.encryption_state_read = None
		self.encryption_state_write = None
	
	def get_own_ipv4_address(self) -> ipaddress.IPv4Address:
		sockname = self.writer.get_extra_info("sockname")
		if sockname is None:
			raise ValueError("Couldn't determine own IP address")
		elif len(sockname) != 2:
			raise ValueError(f"Own address has unexpected format (probably IPv6): {sockname!r}")
		else:
			addr, port = sockname
			return ipaddress.IPv4Address(addr)
	
	def get_own_address_string(self) -> str:
		# TODO Do we care about supporting more than just IPv4 here?
		return str(self.get_own_ipv4_address())
	
	async def read(self, byte_count: int) -> bytes:
		"""Read ``byte_count`` bytes from the socket and raise :class:`~asyncio.IncompleteReadError` if too few bytes are read (i. e. the connection was disconnected prematurely).
		
		If encryption has been set up for this connection,
		the data is automatically decrypted after reading.
		"""
		
		data = await self.reader.readexactly(byte_count)
		if self.encryption_state_read is not None:
			data = self.encryption_state_read.crypt(data)
		return data
	
	async def write(self, data: bytes) -> None:
		"""Write ``data`` to the socket.
		
		If encryption has been set up for this connection,
		the data is automatically encrypted before writing.
		
		The exact implementation might change in the future ---
		it seems that Uru expects certain data to arrive as a single packet,
		even though TCP doesn't guarantee that packet boundaries are preserved in transmission.
		"""
		
		if self.encryption_state_write is not None:
			data = self.encryption_state_write.crypt(data)
		self.writer.write(data)
		await self.writer.drain()
	
	async def read_unpack(self, st: struct.Struct) -> typing.Tuple[typing.Any, ...]:
		"""Read and unpack data from the socket according to the struct ``st``.
		
		The number of bytes to read is determined using :field:`struct.Struct.size`,
		so variable-sized structs cannot be used with this method.
		"""
		
		return st.unpack(await self.read(st.size))
	
	async def read_string_field(self, max_length: int = 0xffff) -> str:
		(length,) = await self.read_unpack(structs.UINT16)
		if length >= max_length:
			raise ProtocolError(f"Client sent string of length {length} in string field with maximum length {max_length}")
		return (await self.read(2 * length)).decode("utf-16-le")
	
	async def write_message(self, message_type: int, data: bytes) -> None:
		await self.write(structs.UINT16.pack(message_type) + data)
	
	async def read_connect_packet_header(self) -> None:
		"""Read and unpack the remaining connect packet header and store the unpacked information.
		
		When this method is called,
		the connection type has already been read ---
		it was used to select the subclass of :class:`BaseMOULConnection` to be used.
		"""
		
		(header_length,) = await self.read_unpack(structs.UINT16)
		if header_length != CONNECT_HEADER_LENGTH:
			raise ProtocolError(f"Client sent connect header with unexpected length {header_length} (should be {CONNECT_HEADER_LENGTH})")
		
		build_id, build_type, branch_id, product_id = await self.read_unpack(CONNECT_HEADER_TAIL)
		self.build_id = build_id
		self.build_type = BuildType(build_type)
		self.branch_id = branch_id
		self.product_id = uuid.UUID(bytes_le=product_id)
		logger_connect.debug("Received rest of connect packet header: build ID %d, build type %s, branch ID %d, product ID %s", self.build_id, self.build_type, self.branch_id, self.product_id)
	
	@abc.abstractmethod
	async def read_connect_packet_data(self) -> None:
		"""Read and unpack the type-specific connect packet data."""
		
		raise NotImplementedError()
	
	async def setup_encryption(self) -> None:
		"""Handle an encryption setup packet from the client and set up encryption accordingly."""
		
		message_type, length = await self.read_unpack(SETUP_MESSAGE_HEADER)
		message_type = SetupMessageType(message_type)
		logger_crypt.debug("Received setup message: type %s, %d bytes", message_type, length)
		if message_type != SetupMessageType.cli2srv_connect:
			raise ProtocolError(f"Client sent unexpected setup message type: {message_type!r}")
		
		data = await self.read(length - SETUP_MESSAGE_HEADER.size)
		logger_crypt.debug("Setup message data: %s", data)
		
		if data:
			# Received the Diffie-Hellman y value from the client.
			if self.dh_keys is None:
				# The server has encryption completely disabled
				# (usually because no keys are configured),
				# so assume the connection is from a CWE/OpenUru client built with NO_ENCRYPTION.
				# In this case,
				# we have to send back a seed of the correct length,
				# but the client will not use it and the connection will be unencrypted.
				logger_crypt.debug("Client sent a non-empty Diffie-Hellman y value, but this server has encryption disabled - assuming NO_ENCRYPTION and replying with a dummy seed")
				await self.write(SETUP_MESSAGE_HEADER.pack(SetupMessageType.srv2cli_encrypt.value, 9) + b"noCrypt")
				self.encryption_state_read = None
				self.encryption_state_write = None
			else:
				# Encryption is enabled,
				# so do the key exchange.
				if len(data) != 64:
					raise ProtocolError(f"Expected Diffie-Hellman y value to be 64 bytes long, but client sent {len(data)} bytes")
				
				dh_y = int.from_bytes(data, "little")
				logger_crypt.debug("Received y from client: %#x", dh_y)
				
				seed = random.randrange(2**56)
				seed_data = seed.to_bytes(7, "little")
				await self.write(SETUP_MESSAGE_HEADER.pack(SetupMessageType.srv2cli_encrypt.value, 9) + seed_data)
				if logger_crypt.isEnabledFor(logging.DEBUG):
					logger_crypt.debug("Sent generated seed to client: %s", seed_data.hex())
				
				session_key_data = (seed ^ (pow(dh_y, self.dh_keys.a, self.dh_keys.n) & (2**56 - 1))).to_bytes(7, "little")
				if logger_crypt.isEnabledFor(logging.DEBUG):
					logger_crypt.debug("Agreed on RC4 session key: %s", session_key_data.hex())
				self.encryption_state_read = crypto.Rc4State(session_key_data)
				self.encryption_state_write = crypto.Rc4State(session_key_data)
		else:
			# H'uru internal client sent an empty y value to explicitly request no encryption.
			if self.server_state.config.server_encryption == configuration.Encryption.force:
				raise ProtocolError(f"Client tried request no encryption, but the server is configured to require encryption")
			
			# We have to reply with an empty seed,
			# or else the client will abort the connection.
			logger_crypt.debug("Received empty Diffie-Hellman y value - setting up unencrypted connection")
			await self.write(SETUP_MESSAGE_HEADER.pack(SetupMessageType.srv2cli_encrypt.value, 2))
			self.encryption_state_read = None
			self.encryption_state_write = None
		
		logger_crypt.debug("Done setting up encryption")
	
	async def handle_unknown_message(self, message_type: int) -> None:
		"""Read and handle an unknown message of the given type.
		
		Because the message protocol doesn't have a generic length field,
		it's impossible to continue reading correctly after an unknown message,
		so we have to abort the connection.
		"""
		
		try:
			# For debugging,
			# try to read a bit of data after it without waiting too long.
			data = await asyncio.wait_for(self.reader.read(64), 0.1)
		except asyncio.TimeoutError as exc:
			raise ProtocolError(f"Client sent unsupported message type {message_type} and no data quickly following it")
		else:
			raise ProtocolError(f"Client sent unsupported message type {message_type} - next few bytes: {data!r}")
	
	async def handle_message(self, message_type: int) -> None:
		"""Dispatch a message to the appropriate handler based on its type."""
		
		try:
			handler = type(self).MESSAGE_HANDLERS[message_type]
		except KeyError:
			logger_message.debug("Received message of unsupported type %d", message_type)
			await self.handle_unknown_message(message_type)
		else:
			logger_message.debug("Received message of type %d (%s)", message_type, getattr(handler, "__name__", "name missing"))
			await handler(self)
	
	async def handle_disconnect(self) -> None:
		"""May be overridden to perform custom cleanup when the client disconnects."""
	
	async def handle(self) -> None:
		try:
			await self.read_connect_packet_header()
			await self.read_connect_packet_data()
			await self.setup_encryption()
			
			# TODO Is there any way for clients to disconnect cleanly without unceremoniously closing the socket?
			while True:
				(message_type,) = await self.read_unpack(structs.UINT16)
				await self.handle_message(message_type)
		finally:
			await self.handle_disconnect()
