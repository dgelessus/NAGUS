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
import logging
import struct
import typing
import uuid


logger = logging.getLogger(__name__)


WORD = struct.Struct("<H")
DWORD = struct.Struct("<I")
QWORD = struct.Struct("<Q")
# No BYTE - just do await self.read(1) instead!

CONNECT_HEADER_TAIL = struct.Struct("<III16s")
CONNECT_HEADER_LENGTH = struct.calcsize("<BH") + CONNECT_HEADER_TAIL.size

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


class ProtocolError(Exception):
	pass


def truncate_utf_16_string(string: str, max_length: int) -> str:
	"""Truncate a string to the given number of UTF-16 code units.
	
	This simulates truncation of wide strings (``wchar_t *``) on Windows.
	"""
	
	# Decrement max_length by 1 to account for the U+0000 terminator.
	return string.encode("utf-16-le")[:(max_length-1)*2].decode("utf-16-le", "surrogatepass")


def pack_string_field(string: str, max_length: int = 0xffff) -> bytes:
	encoded = string.encode("utf-16-le")
	# Can't use len(string) - it will give the wrong result if the string contains code points above U+FFFF!
	utf_16_length = len(encoded) // 2
	if utf_16_length >= max_length:
		raise ValueError(f"Attempted to send string of length {utf_16_length} in string field with maximum length {max_length} - this would break the client")
	return WORD.pack(utf_16_length) + encoded


ConnT = typing.TypeVar("ConnT", bound="BaseMOULConnection")
MessageHandler = typing.Callable[[ConnT], typing.Awaitable[None]]
MessageHandlerT = typing.TypeVar("MessageHandlerT", bound=MessageHandler)


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
	
	MESSAGE_HANDLERS: typing.ClassVar[typing.Dict[int, MessageHandler]]
	CONNECTION_TYPE: ConnectionType # to be set in each subclass
	
	reader: asyncio.StreamReader
	writer: asyncio.StreamWriter
	
	build_id: int
	build_type: BuildType
	branch_id: int
	product_id: uuid.UUID
	
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
				
				cls.MESSAGE_HANDLERS[message_type] = typing.cast(MessageHandler, attr)
	
	def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
		super().__init__()
		
		self.reader = reader
		self.writer = writer
	
	async def read(self, byte_count: int) -> bytes:
		"""Read ``byte_count`` bytes from the socket and raise :class:`~asyncio.IncompleteReadError` if too few bytes are read (i. e. the connection was disconnected prematurely)."""
		
		return await self.reader.readexactly(byte_count)
	
	async def write(self, data: bytes) -> None:
		"""Write ``data`` to the socket.
		
		The exact implementation might change in the future ---
		it seems that Uru expects certain data to arrive as a single packet,
		even though TCP doesn't guarantee that packet boundaries are preserved in transmission.
		"""
		
		self.writer.write(data)
		await self.writer.drain()
	
	async def read_unpack(self, st: struct.Struct) -> tuple:
		"""Read and unpack data from the socket according to the struct ``st``.
		
		The number of bytes to read is determined using :field:`struct.Struct.size`,
		so variable-sized structs cannot be used with this method.
		"""
		
		return st.unpack(await self.read(st.size))
	
	async def read_string_field(self, max_length: int = 0xffff) -> str:
		(length,) = await self.read_unpack(WORD)
		if length >= max_length:
			raise ProtocolError(f"Client sent string of length {length} in string field with maximum length {max_length}")
		return (await self.read(2 * length)).decode("utf-16-le")
	
	async def write_message(self, message_type: int, data: bytes) -> None:
		await self.write(WORD.pack(message_type) + data)
	
	async def read_connect_packet_header(self) -> None:
		"""Read and unpack the remaining connect packet header and store the unpacked information.
		
		When this method is called,
		the connection type has already been read ---
		it was used to select the subclass of :class:`BaseMOULConnection` to be used.
		"""
		
		(header_length,) = await self.read_unpack(WORD)
		if header_length != CONNECT_HEADER_LENGTH:
			raise ProtocolError(f"Client sent connect header with unexpected length {header_length} (should be {CONNECT_HEADER_LENGTH})")
		
		build_id, build_type, branch_id, product_id = await self.read_unpack(CONNECT_HEADER_TAIL)
		self.build_id = build_id
		self.build_type = BuildType(build_type)
		self.branch_id = branch_id
		self.product_id = uuid.UUID(bytes_le=product_id)
		logger.debug("Received rest of connect packet header: build ID %d, build type %s, branch ID %d, product ID %s", self.build_id, self.build_type, self.branch_id, self.product_id)
	
	@abc.abstractmethod
	async def read_connect_packet_data(self) -> None:
		"""Read and unpack the type-specific connect packet data."""
		
		raise NotImplementedError()
	
	async def setup_encryption(self) -> None:
		"""Handle an encryption setup packet from the client and set up encryption accordingly.
		
		Currently doesn't actually support encryption yet!
		Unencrypted H'uru connections are accepted.
		Anything that looks like an encrypted connection is assumed to be an OpenUru client with encryption disabled.
		"""
		
		message_type, length = await self.read_unpack(SETUP_MESSAGE_HEADER)
		message_type = SetupMessageType(message_type)
		logger.debug("Received setup message: type %s, %d bytes", message_type, length)
		
		data = await self.read(length - SETUP_MESSAGE_HEADER.size)
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
			await self.write(SETUP_MESSAGE_HEADER.pack(SetupMessageType.srv2cli_encrypt.value, 9) + b"noCrypt")
		else:
			# H'uru internal client sent an empty server seed to explicitly request no encryption.
			# We have to reply with an empty client seed,
			# or else the client will abort the connection.
			logger.debug("Received empty server seed - setting up unencrypted connection.")
			await self.write(SETUP_MESSAGE_HEADER.pack(SetupMessageType.srv2cli_encrypt.value, 2))
		
		logger.debug("Done setting up encryption")
	
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
			logger.debug("Received message of unsupported type %d", message_type)
			await self.handle_unknown_message(message_type)
		else:
			logger.debug("Received message of type %d (%s)", message_type, getattr(handler, "__name__", "name missing"))
			await handler(self)
	
	async def handle(self) -> None:
		await self.read_connect_packet_header()
		await self.read_connect_packet_data()
		await self.setup_encryption()
		
		# TODO Is there any way for clients to disconnect cleanly without unceremoniously closing the socket?
		while True:
			(message_type,) = await self.read_unpack(WORD)
			await self.handle_message(message_type)
