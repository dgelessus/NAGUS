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


"""Implements the :ref:`auth server <auth_server>`."""


import asyncio
import enum
import ipaddress
import logging
import random
import struct
import typing
import uuid

from . import base
from . import state


logger = logging.getLogger(__name__)


CONNECT_DATA = struct.Struct("<I16s")

PING_HEADER = struct.Struct("<III")
SERVER_ADDRESS = struct.Struct("<I16s")
NOTIFY_NEW_BUILD = struct.Struct("<I")
CLIENT_REGISTER_REPLY = struct.Struct("<I")
CLIENT_REGISTER_REQUEST = struct.Struct("<I")
CLIENT_SET_CCR_LEVEL = struct.Struct("<I")
ACCOUNT_PLAYER_INFO_HEADER = struct.Struct("<II")
ACCOUNT_LOGIN_REPLY = struct.Struct("<II16sII4I")
ACCOUNT_LOGIN_REQUEST_HEADER = struct.Struct("<II")
ACCOUNT_SET_PLAYER_REPLY = struct.Struct("<II")
ACCOUNT_SET_PLAYER_REQUEST = struct.Struct("<II")
PLAYER_DELETE_REPLY = struct.Struct("<II")
PLAYER_DELETE_REQUEST = struct.Struct("<II")
PLAYER_CREATE_REPLY_HEADER = struct.Struct("<IIII")
PLAYER_CREATE_REQUEST_HEADER = struct.Struct("<I")


ZERO_UUID = uuid.UUID("00000000-0000-0000-0000-000000000000")


SYSTEM_RANDOM = random.SystemRandom()


class AccountFlags(enum.IntFlag):
	disabled = 0
	admin = 1 << 0
	developer = 1 << 1
	beta_tester = 1 << 2
	user = 1 << 3
	special_event = 1 << 4
	banned = 1 << 16


class AccountBillingType(enum.IntFlag):
	free = 0
	paid_subscriber = 1 << 0
	gametap = 1 << 1


class AuthClientState(object):
	cleanup_handle: asyncio.TimerHandle
	token: uuid.UUID
	server_challenge: int
	ki_number: int


class AuthConnection(base.BaseMOULConnection):
	CONNECTION_TYPE = base.ConnectionType.cli2auth
	DISCONNECTED_CLIENT_TIMEOUT = 30
	
	client_state: AuthClientState
	
	def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, server_state: state.ServerState) -> None:
		super().__init__(reader, writer, server_state)
		
		self.client_state = AuthClientState()
	
	async def handle_disconnect(self) -> None:
		try:
			token = self.client_state.token
		except AttributeError:
			# Client disconnected very early
			# or never received a token for some other reason,
			# so there's nothing that needs to be cleaned up.
			return
		
		def _remove_disconnected_connection_callback() -> None:
			logger.info("Client with token %s didn't reconnect within %d seconds - discarding its state", token, type(self).DISCONNECTED_CLIENT_TIMEOUT)
			if token not in self.server_state.auth_connections:
				raise AssertionError(f"Cleanup callback for token {token} fired even though the corresponding state has already been discarded")
			elif self.server_state.auth_connections[token] != self:
				raise AssertionError(f"Cleanup callback for token {token} fired even though the client has reconnected")
			else:
				del self.server_state.auth_connections[token]
		
		self.client_state.cleanup_handle = self.server_state.loop.call_later(
			type(self).DISCONNECTED_CLIENT_TIMEOUT,
			_remove_disconnected_connection_callback,
		)
	
	async def read_connect_packet_data(self) -> None:
		"""Read and unpack the client's token.
		
		If a previously connected client reconnects using its token,
		restore the corresponding client-specific state.
		"""
		
		data_length, token = await self.read_unpack(CONNECT_DATA)
		if data_length != CONNECT_DATA.size:
			raise base.ProtocolError(f"Client sent client-to-auth connect data with unexpected length {data_length} (should be {CONNECT_DATA.size})")
		
		token = uuid.UUID(bytes_le=token)
		if token != ZERO_UUID:
			logger.info("Client reconnected using token %s", token)
			try:
				# When client reconnects with a token,
				# restore the corresponding server-side state,
				# assuming it still exists.
				self.client_state = self.server_state.auth_connections[token].client_state
				self.client_state.cleanup_handle.cancel()
				self.server_state.auth_connections[token] = self
			except KeyError:
				raise base.ProtocolError(f"Client attempted to reconnect using an unknown token: {token}")
		else:
			# Client doesn't have a token yet (probably a new connection) - assign it one.
			self.client_state.token = uuid.uuid4()
			while self.client_state.token in self.server_state.auth_connections:
				logger.warning("Random UUID collision!? %s is already taken, trying again...", self.client_state.token)
				self.client_state.token = uuid.uuid4()
			
			logger.info("New client connection, assigning token %s", self.client_state.token)
			self.server_state.auth_connections[self.client_state.token] = self
	
	@base.message_handler(0)
	async def ping_request(self) -> None:
		"""Reply to ping request."""
		
		header_data = await self.read(PING_HEADER.size)
		ping_time, trans_id, payload_length = PING_HEADER.unpack(header_data)
		logger.debug("Ping request: time %d", ping_time)
		if trans_id != 0:
			logger.info("Ping request with non-zero transaction ID: %d", trans_id)
		if payload_length != 0:
			logger.info("Ping request with non-empty payload: %d bytes", payload_length)
		payload = await self.read(payload_length)
		# Send everything back unmodified
		await self.write_message(0, header_data + payload)
	
	async def server_address(self, server_ip: ipaddress.IPv4Address, token: uuid.UUID) -> None:
		logger.debug("Sending server address message: server IP %s, token %s", server_ip, token)
		await self.write_message(1, SERVER_ADDRESS.pack(int(server_ip), token.bytes_le))
	
	async def notify_new_build(self, foo: int) -> None:
		logger.debug("Sending new build notification: %d", foo)
		await self.write_message(2, NOTIFY_NEW_BUILD.pack(foo))
	
	async def client_register_reply(self, server_challenge: int) -> None:
		logger.debug("Sending client register reply with server challenge: 0x%08x", server_challenge)
		await self.write_message(3, CLIENT_REGISTER_REPLY.pack(server_challenge))
	
	@base.message_handler(1)
	async def client_register_request(self) -> None:
		(build_id,) = await self.read_unpack(CLIENT_REGISTER_REQUEST)
		logger.debug("Build ID: %d", build_id)
		if build_id != self.build_id:
			raise base.ProtocolError(f"Client register request build ID ({build_id}) differs from connect packet ({self.build_id})")
		
		# Send ServerCaps message for H'uru clients in a way that doesn't break OpenUru clients.
		# This is barely tested and does some wacky stuff,
		# so I'm commenting it out for now.
		# H'uru clients generally work fine without the ServerCaps message.
		r"""
		await self.write(
			# ServerCaps message type number - recognized by H'uru, but ignored by OpenUru.
			b"\x02\x10"
			# ServerCaps message data for H'uru.
			# OpenUru parses this as the start of a FileDownloadChunk message,
			# which will be ignored,
			# because no file download transaction is active.
			# H'uru sees: 0x25 bytes of data, bit vector is 1 dword long, value is 0
			# OpenUru sees: message type 0x25 (FileDownloadChunk), transaction ID 0x10000, error code 0, file size 0 (continued below)
			b"\x25\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00"
			# ServerCaps message extra data,
			# which is ignored by H'uru,
			# because the bit vector doesn't have this many dwords.
			# OpenUru parses this as the rest of FileDownloadChunk message:
			b"\x00\x00" # file size 0 (continued)
			b"\x00\x00\x00\x00\x13\x00\x00\x00" # chunk offset 0, chunk size 0x13
			b"[ServerCaps compat]" # 0x13 bytes of chunk data
		)
		#"""
		
		# Reply to client register request
		if hasattr(self, "server_challenge"):
			logger.warning("Already registered client sent another client register request - generating new server challenge...")
		self.client_state.server_challenge = SYSTEM_RANDOM.randrange(0x100000000)
		await self.client_register_reply(self.client_state.server_challenge)
		
		sockname = self.writer.get_extra_info("sockname")
		if sockname is None:
			logger.warning("Unable to send a ServerAddr message to client - couldn't determine own IP address")
		elif len(sockname) != 2:
			logger.warning("Unable to send a ServerAddr message to client - own address has unexpected format (probably IPv6): %r", sockname)
		else:
			(addr, port) = sockname
			ip_addr = ipaddress.IPv4Address(addr)
			await self.server_address(ip_addr, self.client_state.token)
	
	@base.message_handler(2)
	async def client_set_ccr_level(self) -> None:
		(ccr_level,) = await self.read_unpack(CLIENT_SET_CCR_LEVEL)
		logger.warning("Client changed its CCR level to %d", ccr_level)
		raise base.ProtocolError(f"Client attempted to change its CCR level (to {ccr_level}), we don't allow this")
	
	async def account_player_info(
		self,
		trans_id: int,
		player_vault_node_id: int,
		player_name: str,
		avatar_shape: str,
		explorer: int,
	) -> None:
		logger.debug("Sending player info: transaction ID %d, KI number %d, player name %r, avatar shape %r, explorer? %d", trans_id, player_vault_node_id, player_name, avatar_shape, explorer)
		await self.write_message(6, (
			ACCOUNT_PLAYER_INFO_HEADER.pack(trans_id, player_vault_node_id)
			+ base.pack_string_field(player_name, 40)
			+ base.pack_string_field(avatar_shape, 64)
			+ base.DWORD.pack(explorer)
		))
	
	async def account_login_reply(
		self,
		trans_id: int,
		result: base.NetError,
		account_id: uuid.UUID,
		account_flags: AccountFlags,
		billing_type: AccountBillingType,
		ntd_encryption_key: typing.Tuple[int, int, int, int],
	) -> None:
		logger.debug(
			"Sending account login reply: transaction ID %d, result %r, account ID %s, account flags %r, billing type %r, NTD encryption key [0x%08x, 0x%08x, 0x%08x, 0x%08x]",
			trans_id, result, account_id, account_flags, billing_type, *ntd_encryption_key,
		)
		await self.write_message(4, ACCOUNT_LOGIN_REPLY.pack(trans_id, result, account_id.bytes_le, account_flags, billing_type, *ntd_encryption_key))
	
	@base.message_handler(3)
	async def account_login_request(self) -> None:
		trans_id, client_challenge = await self.read_unpack(ACCOUNT_LOGIN_REQUEST_HEADER)
		account_name = await self.read_string_field(64)
		challenge_hash = await self.read(20)
		auth_token = await self.read_string_field(64)
		os_name = await self.read_string_field(8)
		
		logger.debug("Login request: transaction ID: %d, client challenge 0x%08x, account %r, challenge hash %s", trans_id, client_challenge, account_name, challenge_hash.hex())
		if auth_token:
			logger.warning("Login request with auth token %r by account %r", auth_token, account_name)
		if os_name != "win":
			logger.info("Login request with non-Windows OS name %r by account %r", os_name, account_name)
		
		if not hasattr(self.client_state, "server_challenge"):
			raise base.ProtocolError("Client attempted to log in without sending a client register request first")
		
		# TODO Implement actual authentication
		await self.account_login_reply(trans_id, base.NetError.success, ZERO_UUID, AccountFlags.user, AccountBillingType.paid_subscriber, (0, 0, 0, 0))
	
	async def account_set_player_reply(self, trans_id: int, result: base.NetError) -> None:
		logger.debug("Sending set player reply: transaction ID %d, result %r", trans_id, result)
		await self.write_message(7, ACCOUNT_SET_PLAYER_REPLY.pack(trans_id, result))
	
	@base.message_handler(6)
	async def account_set_player_request(self) -> None:
		trans_id, ki_number = await self.read_unpack(ACCOUNT_SET_PLAYER_REQUEST)
		logger.debug("Set player request: transaction ID %d, KI number %d", trans_id, ki_number)
		# TODO Check that the KI number actually belongs to the player's account
		self.client_state.ki_number = ki_number
		await self.account_set_player_reply(trans_id, base.NetError.success)
	
	async def player_delete_reply(self, trans_id: int, result: base.NetError) -> None:
		logger.debug("Sending player delete reply: transaction ID %d, result %r", trans_id, result)
		await self.write_message(17, PLAYER_DELETE_REPLY.pack(trans_id, result))
	
	@base.message_handler(13)
	async def player_delete_request(self) -> None:
		trans_id, ki_number = await self.read_unpack(PLAYER_DELETE_REQUEST)
		logger.debug("Player delete request: transaction ID %d, KI number %d", trans_id, ki_number)
		if ki_number == getattr(self.client_state, "ki_number", None):
			# Can't delete current avatar
			await self.player_delete_reply(trans_id, base.NetError.invalid_parameter)
			return
		# TODO Actually implement this
		await self.player_delete_reply(trans_id, base.NetError.success)
	
	async def player_create_reply(
		self,
		trans_id: int,
		result: base.NetError,
		ki_number: int,
		explorer: int,
		avatar_name: str,
		avatar_shape: str,
	) -> None:
		await self.write_message(16, (
			PLAYER_CREATE_REPLY_HEADER.pack(trans_id, result, ki_number, explorer)
			+ base.pack_string_field(avatar_name, 40)
			+ base.pack_string_field(avatar_shape, 64)
		))
	
	@base.message_handler(17)
	async def player_create_request(self) -> None:
		(trans_id,) = await self.read_unpack(PLAYER_CREATE_REQUEST_HEADER)
		avatar_name = await self.read_string_field(40)
		avatar_shape = await self.read_string_field(260)
		friend_invite_code = await self.read_string_field(260)
		logger.debug("Player create request: transaction ID %d, avatar name %r, avatar shape %r", trans_id, avatar_name, avatar_shape)
		if avatar_shape not in {"female", "male"}:
			logger.error("Unsupported avatar shape %r")
			# More correct would be invalid_parameter,
			# but the client assumes that means an invalid invite code.
			await self.player_create_reply(trans_id, base.NetError.not_supported, 0, 0, "", "")
			return
		if friend_invite_code:
			logger.error("Player create request with friend invite code, we don't support this: %r", friend_invite_code)
			await self.player_create_reply(trans_id, base.NetError.invalid_parameter, 0, 0, "", "")
			return
		# TODO Actually implement this
		await self.player_create_reply(trans_id, base.NetError.success, 1337, 1, avatar_name, avatar_shape)
