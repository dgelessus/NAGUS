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
from . import crash_lines
from . import state
from . import structs


logger = logging.getLogger(__name__)
logger_age = logger.getChild("age")
logger_avatar = logger.getChild("avatar")
logger_client_errors = logger.getChild("client_errors")
logger_connect = logger.getChild("connect")
logger_login = logger.getChild("login")
logger_ping = logger.getChild("ping")
logger_vault = logger.getChild("vault")
logger_vault_read = logger_vault.getChild("read")
logger_vault_notify = logger_vault.getChild("notify")
logger_vault_write = logger_vault.getChild("write")


# Random placeholder UUID that identifies the one and only "account",
# until I implement proper authentication and support for multiple accounts.
PLACEHOLDER_ACCOUNT_UUID = uuid.UUID("192e8ae7-b263-4b44-996e-2b492a30da53")

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
UPGRADE_VISITOR_REQUEST = struct.Struct("<II")
UPGRADE_VISITOR_REPLY = struct.Struct("<II")
KICKED_OFF = struct.Struct("<I")
VAULT_NODE_CREATE_HEADER = struct.Struct("<II")
VAULT_NODE_CREATED = struct.Struct("<III")
VAULT_NODE_FETCH = struct.Struct("<II")
VAULT_NODE_FETCHED_HEADER = struct.Struct("<III")
VAULT_NODE_CHANGED = struct.Struct("<I16s")
VAULT_NODE_SAVE_HEADER = struct.Struct("<II16sI")
VAULT_SAVE_NODE_REPLY = struct.Struct("<II")
VAULT_NODE_DELETED = struct.Struct("<I")
VAULT_NODE_ADDED = struct.Struct("<III")
VAULT_NODE_ADD = struct.Struct("<IIII")
VAULT_ADD_NODE_REPLY = struct.Struct("<II")
VAULT_NODE_REMOVED = struct.Struct("<II")
VAULT_NODE_REMOVE = struct.Struct("<III")
VAULT_REMOVE_NODE_REPLY = struct.Struct("<II")
VAULT_FETCH_NODE_REFS = struct.Struct("<II")
VAULT_NODE_REFS_FETCHED_HEADER = struct.Struct("<III")
VAULT_INIT_AGE_REQUEST_HEADER = struct.Struct("<I16s16s")
VAULT_INIT_AGE_REQUEST_FOOTER = struct.Struct("<ii")
VAULT_INIT_AGE_REPLY = struct.Struct("<IIII")
VAULT_NODE_FIND_HEADER = struct.Struct("<II")
VAULT_NODE_FIND_REPLY_HEADER = struct.Struct("<III")
AGE_REQUEST_HEADER = struct.Struct("<I")
AGE_REPLY = struct.Struct("<III16sII")
LOG_CLIENT_DEBUGGER_CONNECT = struct.Struct("<I")


SYSTEM_RANDOM = random.SystemRandom()


class AccountFlags(structs.IntFlag):
	disabled = 0
	admin = 1 << 0
	developer = 1 << 1
	beta_tester = 1 << 2
	user = 1 << 3
	special_event = 1 << 4
	banned = 1 << 16


class AccountBillingType(structs.IntFlag):
	free = 0
	paid_subscriber = 1 << 0
	gametap = 1 << 1


class AuthClientState(object):
	cleanup_handle: asyncio.TimerHandle
	token: uuid.UUID
	server_challenge: int
	account_uuid: uuid.UUID
	ki_number: int


class AuthConnection(base.BaseMOULConnection):
	CONNECTION_TYPE = base.ConnectionType.cli2auth
	DISCONNECTED_CLIENT_TIMEOUT = 30
	
	client_state: AuthClientState
	
	def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, server_state: state.ServerState) -> None:
		super().__init__(reader, writer, server_state)
		
		self.client_state = AuthClientState()
	
	def _get_own_ipv4_address(self) -> ipaddress.IPv4Address:
		sockname = self.writer.get_extra_info("sockname")
		if sockname is None:
			raise ValueError("Couldn't determine own IP address")
		elif len(sockname) != 2:
			raise ValueError(f"Own address has unexpected format (probably IPv6): {sockname!r}")
		else:
			(addr, port) = sockname
			return ipaddress.IPv4Address(addr)
	
	async def handle_disconnect(self) -> None:
		try:
			token = self.client_state.token
		except AttributeError:
			# Client disconnected very early
			# or never received a token for some other reason,
			# so there's nothing that needs to be cleaned up.
			return
		
		def _remove_disconnected_connection_callback() -> None:
			logger_connect.info("Client with token %s didn't reconnect within %d seconds - discarding its state", token, type(self).DISCONNECTED_CLIENT_TIMEOUT)
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
		if token != structs.ZERO_UUID:
			logger_connect.info("Client reconnected using token %s", token)
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
				logger_connect.warning("Random UUID collision!? %s is already taken, trying again...", self.client_state.token)
				self.client_state.token = uuid.uuid4()
			
			logger_connect.info("New client connection, assigning token %s", self.client_state.token)
			self.server_state.auth_connections[self.client_state.token] = self
	
	async def kicked_off(self, reason: base.NetError) -> None:
		await self.write_message(39, KICKED_OFF.pack(reason))
	
	async def disconnect_with_reason(self, client_reason: base.NetError, server_log_message: str) -> typing.NoReturn:
		"""Send the client a reason why it's being disconnected before actually disconnecting it.
		
		This must only be used after the connection has been fully set up!
		Otherwise the client won't recognize the Auth2Cli_KickedOff message.
		"""
		
		await self.kicked_off(client_reason)
		raise base.ProtocolError(server_log_message)
	
	@base.message_handler(0)
	async def ping_request(self) -> None:
		"""Reply to ping request."""
		
		header_data = await self.read(PING_HEADER.size)
		ping_time, trans_id, payload_length = PING_HEADER.unpack(header_data)
		logger_ping.debug("Ping request: time %d", ping_time)
		if trans_id != 0:
			logger_ping.info("Ping request with non-zero transaction ID: %d", trans_id)
		if payload_length != 0:
			logger_ping.info("Ping request with non-empty payload: %d bytes", payload_length)
		payload = await self.read(payload_length)
		# Send everything back unmodified
		await self.write_message(0, header_data + payload)
	
	async def server_address(self, server_ip: ipaddress.IPv4Address, token: uuid.UUID) -> None:
		logger_connect.debug("Sending server address message: server IP %s, token %s", server_ip, token)
		await self.write_message(1, SERVER_ADDRESS.pack(int(server_ip), token.bytes_le))
	
	async def notify_new_build(self, foo: int) -> None:
		logger.debug("Sending new build notification: %d", foo)
		await self.write_message(2, NOTIFY_NEW_BUILD.pack(foo))
	
	async def client_register_reply(self, server_challenge: int) -> None:
		logger_connect.debug("Sending client register reply with server challenge: 0x%08x", server_challenge)
		await self.write_message(3, CLIENT_REGISTER_REPLY.pack(server_challenge))
	
	@base.message_handler(1)
	async def client_register_request(self) -> None:
		(build_id,) = await self.read_unpack(CLIENT_REGISTER_REQUEST)
		logger_connect.debug("Build ID: %d", build_id)
		if build_id != self.build_id:
			await self.disconnect_with_reason(base.NetError.invalid_parameter, f"Client register request build ID ({build_id}) differs from connect packet ({self.build_id})")
		
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
			logger_connect.warning("Already registered client sent another client register request - generating new server challenge...")
		self.client_state.server_challenge = SYSTEM_RANDOM.randrange(0x100000000)
		await self.client_register_reply(self.client_state.server_challenge)
		
		if self.server_state.config.server_auth_send_server_address:
			try:
				ip_addr = self.server_state.config.server_auth_address_for_client
				if ip_addr is None:
					ip_addr = self._get_own_ipv4_address()
			except ValueError:
				logger_connect.warning("Unable to get own IPv4 address - won't send a ServerAddr message to the client", exc_info=True)
			else:
				await self.server_address(ip_addr, self.client_state.token)
	
	@base.message_handler(2)
	async def client_set_ccr_level(self) -> None:
		(ccr_level,) = await self.read_unpack(CLIENT_SET_CCR_LEVEL)
		logger.warning("Client changed its CCR level to %d", ccr_level)
		await self.disconnect_with_reason(base.NetError.service_forbidden, f"Client attempted to change its CCR level (to {ccr_level}), we don't allow this")
	
	async def account_player_info(
		self,
		trans_id: int,
		player_vault_node_id: int,
		player_name: str,
		avatar_shape: str,
		explorer: int,
	) -> None:
		logger_login.debug("Sending player info: transaction ID %d, KI number %d, player name %r, avatar shape %r, explorer? %d", trans_id, player_vault_node_id, player_name, avatar_shape, explorer)
		await self.write_message(6, (
			ACCOUNT_PLAYER_INFO_HEADER.pack(trans_id, player_vault_node_id)
			+ base.pack_string_field(player_name, 40)
			+ base.pack_string_field(avatar_shape, 64)
			+ structs.UINT32.pack(explorer)
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
		logger_login.debug(
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
		
		logger_login.debug("Login request: transaction ID: %d, client challenge 0x%08x, account %r, challenge hash %s", trans_id, client_challenge, account_name, challenge_hash.hex())
		if auth_token:
			logger_login.warning("Login request with auth token %r by account %r", auth_token, account_name)
		if os_name != "win":
			logger_login.info("Login request with non-Windows OS name %r by account %r", os_name, account_name)
		
		if not hasattr(self.client_state, "server_challenge"):
			await self.disconnect_with_reason(base.NetError.service_forbidden, "Client attempted to log in without sending a client register request first")
		
		# TODO Implement actual authentication
		self.client_state.account_uuid = PLACEHOLDER_ACCOUNT_UUID
		logger_login.info("Account %r logged in (UUID %s)", account_name, self.client_state.account_uuid)
		
		async for avatar in self.server_state.find_avatars(self.client_state.account_uuid):
			await self.account_player_info(trans_id, avatar.player_node_id, avatar.name, avatar.shape, avatar.explorer)
		
		await self.account_login_reply(trans_id, base.NetError.success, self.client_state.account_uuid, AccountFlags.user, AccountBillingType.paid_subscriber, (0, 0, 0, 0))
	
	async def account_set_player_reply(self, trans_id: int, result: base.NetError) -> None:
		logger_login.debug("Sending set player reply: transaction ID %d, result %r", trans_id, result)
		await self.write_message(7, ACCOUNT_SET_PLAYER_REPLY.pack(trans_id, result))
	
	@base.message_handler(6)
	async def account_set_player_request(self) -> None:
		trans_id, ki_number = await self.read_unpack(ACCOUNT_SET_PLAYER_REQUEST)
		logger_login.debug("Set player request: transaction ID %d, KI number %d", trans_id, ki_number)
		# TODO Check that the KI number actually belongs to the player's account
		self.client_state.ki_number = ki_number
		logger_login.info("Account %s now playing as avatar %r", self.client_state.account_uuid, ki_number)
		await self.account_set_player_reply(trans_id, base.NetError.success)
	
	async def player_delete_reply(self, trans_id: int, result: base.NetError) -> None:
		logger_avatar.debug("Sending player delete reply: transaction ID %d, result %r", trans_id, result)
		await self.write_message(17, PLAYER_DELETE_REPLY.pack(trans_id, result))
	
	@base.message_handler(13)
	async def player_delete_request(self) -> None:
		trans_id, ki_number = await self.read_unpack(PLAYER_DELETE_REQUEST)
		logger_avatar.debug("Player delete request: transaction ID %d, KI number %d", trans_id, ki_number)
		if ki_number == getattr(self.client_state, "ki_number", None):
			# Can't delete current avatar
			await self.player_delete_reply(trans_id, base.NetError.invalid_parameter)
			return
		
		try:
			await self.server_state.delete_avatar(ki_number, self.client_state.account_uuid)
		except state.AvatarNotFound:
			await self.player_delete_reply(trans_id, base.NetError.player_not_found)
		except Exception:
			logger_avatar.error("Unhandled exception while deleting avatar", exc_info=True)
			await self.player_delete_reply(trans_id, base.NetError.internal_error)
		else:
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
		logger_avatar.debug("Sending player create reply: transaction ID %d, result %r, KI number %d, explorer? %d, name %r, avatar shape %r", trans_id, result, ki_number, explorer, avatar_name, avatar_shape)
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
		logger_avatar.debug("Player create request: transaction ID %d, avatar name %r, avatar shape %r", trans_id, avatar_name, avatar_shape)
		
		if friend_invite_code:
			logger_avatar.error("Player create request with friend invite code, we don't support this: %r", friend_invite_code)
			await self.player_create_reply(trans_id, base.NetError.invalid_parameter, 0, 0, "", "")
			return
		
		try:
			ki_number, _ = await self.server_state.create_avatar(avatar_name, avatar_shape, 1, self.client_state.account_uuid)
		except ValueError:
			# More correct would be invalid_parameter,
			# but the client assumes that means an invalid invite code.
			await self.player_create_reply(trans_id, base.NetError.not_supported, 0, 0, "", "")
		except state.AvatarAlreadyExists:
			await self.player_create_reply(trans_id, base.NetError.player_already_exists, 0, 0, "", "")
		except state.VaultNodeNotFound:
			logger_avatar.error("Vault node not found while creating avatar", exc_info=True)
			await self.player_create_reply(trans_id, base.NetError.vault_node_not_found, 0, 0, "", "")
		except Exception:
			logger_avatar.error("Unhandled exception while creating avatar", exc_info=True)
			await self.player_create_reply(trans_id, base.NetError.internal_error, 0, 0, "", "")
		else:
			await self.player_create_reply(trans_id, base.NetError.success, ki_number, 1, avatar_name, avatar_shape)
	
	async def upgrade_visitor_reply(self, trans_id: int, result: base.NetError) -> None:
		logger_avatar.debug("Sending upgrade visitor reply: transaction ID %d, result %r", trans_id, result)
		await self.write_message(18, UPGRADE_VISITOR_REPLY.pack(trans_id, result))
	
	@base.message_handler(20)
	async def upgrade_visitor_request(self) -> None:
		(trans_id, ki_number) = await self.read_unpack(UPGRADE_VISITOR_REQUEST)
		# TODO Actually implement this
		await self.upgrade_visitor_reply(trans_id, base.NetError.success)
	
	async def vault_node_created(self, trans_id: int, result: base.NetError, node_id: int) -> None:
		logger_vault_write.debug("Sending vault node created: transaction ID %d, result %r, node ID %d", trans_id, result, node_id)
		await self.write_message(23, VAULT_NODE_CREATED.pack(trans_id, result, node_id))
	
	@base.message_handler(25)
	async def vault_node_create(self) -> None:
		trans_id, packed_node_data_length = await self.read_unpack(VAULT_NODE_CREATE_HEADER)
		packed_node_data = await self.read(packed_node_data_length)
		node_data = state.VaultNodeData.unpack(packed_node_data)
		logger_vault_write.debug("Vault node create: transaction ID %d, node data %s", trans_id, node_data)
		
		node_data.creator_account_uuid = self.client_state.account_uuid
		node_data.creator_id = self.client_state.ki_number
		
		try:
			node_id = await self.server_state.create_vault_node(node_data)
		except Exception:
			logger_vault_write.error("Unhandled exception while creating vault node", exc_info=True)
			await self.vault_node_created(trans_id, base.NetError.internal_error, 0)
		else:
			await self.vault_node_created(trans_id, base.NetError.success, node_id)
	
	async def vault_node_fetched(self, trans_id: int, result: base.NetError, node_data: typing.Optional[state.VaultNodeData]) -> None:
		logger_vault_read.debug("Sending fetched vault node: transaction ID %d, result %r, node data %s", trans_id, result, node_data)
		packed_node_data = b"" if node_data is None else node_data.pack()
		await self.write_message(24, VAULT_NODE_FETCHED_HEADER.pack(trans_id, result, len(packed_node_data)) + packed_node_data)
	
	@base.message_handler(26)
	async def vault_node_fetch(self) -> None:
		(trans_id, node_id) = await self.read_unpack(VAULT_NODE_FETCH)
		logger_vault_read.debug("Vault node fetch: transaction ID %d, node ID %d", trans_id, node_id)
		
		try:
			node_data = await self.server_state.fetch_vault_node(node_id)
		except state.VaultNodeNotFound:
			await self.vault_node_fetched(trans_id, base.NetError.vault_node_not_found, None)
		except Exception:
			logger_vault_read.error("Unhandled exception while fetching vault node", exc_info=True)
			await self.vault_node_fetched(trans_id, base.NetError.internal_error, None)
		else:
			await self.vault_node_fetched(trans_id, base.NetError.success, node_data)
	
	async def vault_node_changed(self, node_id: int, revision_id: uuid.UUID) -> None:
		logger_vault_notify.debug("Sending vault node changed: node ID %d, revision ID %s", node_id, revision_id)
		await self.write_message(25, VAULT_NODE_CHANGED.pack(node_id, revision_id.bytes_le))
	
	async def vault_save_node_reply(self, trans_id: int, result: base.NetError) -> None:
		logger_vault_write.debug("Sending vault save node reply: transaction ID %d, result %r", trans_id, result)
		await self.write_message(32, VAULT_SAVE_NODE_REPLY.pack(trans_id, result))
	
	@base.message_handler(27)
	async def vault_node_save(self) -> None:
		trans_id, node_id, revision_id, packed_node_data_length = await self.read_unpack(VAULT_NODE_SAVE_HEADER)
		revision_id = uuid.UUID(bytes_le=revision_id)
		packed_node_data = await self.read(packed_node_data_length)
		node_data = state.VaultNodeData.unpack(packed_node_data)
		logger_vault_write.debug("Vault node save: transaction ID %d, node ID %d, revision ID %s, node data %s", trans_id, node_id, revision_id, node_data)
		try:
			await self.server_state.update_vault_node(node_id, node_data)
		except state.VaultNodeNotFound:
			await self.vault_save_node_reply(trans_id, base.NetError.vault_node_not_found)
		except Exception:
			logger_vault_write.error("Unhandled exception while creating vault node", exc_info=True)
			await self.vault_save_node_reply(trans_id, base.NetError.internal_error)
		else:
			await self.vault_node_changed(node_id, revision_id)
			await self.vault_save_node_reply(trans_id, base.NetError.success)
	
	async def vault_node_deleted(self, node_id: int) -> None:
		logger_vault_notify.debug("Sending vault node deleted: node ID %d", node_id)
		await self.write_message(26, VAULT_NODE_DELETED.pack(node_id))
	
	async def vault_node_added(self, parent_id: int, child_id: int, owner_id: int) -> None:
		logger_vault_notify.debug("Sending vault node added: parent ID %d, child ID %d, owner ID %d", parent_id, child_id, owner_id)
		await self.write_message(27, VAULT_NODE_ADDED.pack(parent_id, child_id, owner_id))
	
	async def vault_add_node_reply(self, trans_id: int, result: base.NetError) -> None:
		logger_vault_write.debug("Sending vault add node reply: transaction ID %d, result %r", trans_id, result)
		await self.write_message(33, VAULT_ADD_NODE_REPLY.pack(trans_id, result))
	
	@base.message_handler(29)
	async def vault_node_add(self) -> None:
		trans_id, parent_id, child_id, owner_id = await self.read_unpack(VAULT_NODE_ADD)
		logger_vault_write.debug("Vault node add: transaction ID %d, parent ID %d, child ID %d, owner ID %d", trans_id, parent_id, child_id, owner_id)
		try:
			await self.server_state.add_vault_node_ref(state.VaultNodeRef(parent_id, child_id, owner_id))
		except state.VaultNodeNotFound:
			await self.vault_add_node_reply(trans_id, base.NetError.vault_node_not_found)
		except state.VaultNodeAlreadyExists:
			await self.vault_add_node_reply(trans_id, base.NetError.invalid_parameter)
		except Exception:
			logger_vault_write.error("Unhandled exception while adding vault node", exc_info=True)
			await self.vault_add_node_reply(trans_id, base.NetError.internal_error)
		else:
			await self.vault_node_added(parent_id, child_id, owner_id)
			await self.vault_add_node_reply(trans_id, base.NetError.success)
	
	async def vault_node_removed(self, parent_id: int, child_id: int) -> None:
		logger_vault_notify.debug("Sending vault node removed: parent ID %d, child ID %d", parent_id, child_id)
		await self.write_message(28, VAULT_NODE_REMOVED.pack(parent_id, child_id))
	
	async def vault_remove_node_reply(self, trans_id: int, result: base.NetError) -> None:
		logger_vault_write.debug("Sending vault remove node reply: transaction ID %d, result %r", trans_id, result)
		await self.write_message(34, VAULT_REMOVE_NODE_REPLY.pack(trans_id, result))
	
	@base.message_handler(30)
	async def vault_node_remove(self) -> None:
		trans_id, parent_id, child_id = await self.read_unpack(VAULT_NODE_REMOVE)
		logger_vault_write.debug("Vault node remove: transaction ID %d, parent ID %d, child ID %d", trans_id, parent_id, child_id)
		try:
			await self.server_state.remove_vault_node_ref(parent_id, child_id)
		except state.VaultNodeNotFound:
			await self.vault_remove_node_reply(trans_id, base.NetError.vault_node_not_found)
		except Exception:
			logger_vault_write.error("Unhandled exception while removing vault node", exc_info=True)
			await self.vault_remove_node_reply(trans_id, base.NetError.internal_error)
		else:
			await self.vault_node_removed(parent_id, child_id)
			await self.vault_remove_node_reply(trans_id, base.NetError.success)
	
	async def vault_node_refs_fetched(self, trans_id: int, result: base.NetError, refs: typing.Sequence[state.VaultNodeRef]) -> None:
		logger_vault_read.debug("Sending fetched vault node refs: transaction ID %d, result %r, refs %r", trans_id, result, refs)
		if len(refs) > 1048576:
			raise ValueError(f"Attempted to reply with {len(refs)} vault node refs - that's too many for the client")
		
		message = bytearray(VAULT_NODE_REFS_FETCHED_HEADER.pack(trans_id, result, len(refs)))
		for ref in refs:
			message.extend(ref.pack())
		
		await self.write_message(29, message)
	
	@base.message_handler(31)
	async def vault_fetch_node_refs(self) -> None:
		(trans_id, node_id) = await self.read_unpack(VAULT_FETCH_NODE_REFS)
		logger_vault_read.debug("Vault node refs fetch: transaction ID %d, node ID %d", trans_id, node_id)
		
		try:
			refs = []
			async for ref in self.server_state.fetch_vault_node_refs_recursive(node_id):
				refs.append(ref)
				if len(refs) > 1048576:
					raise ValueError(f"There are more than 1048576 node refs under node ID {node_id} - that's too many for the client")
		except state.VaultNodeNotFound:
			await self.vault_node_refs_fetched(trans_id, base.NetError.vault_node_not_found, [])
		except Exception:
			logger_vault_read.error("Unhandled exception while fetching vault node refs", exc_info=True)
			await self.vault_node_refs_fetched(trans_id, base.NetError.internal_error, [])
		else:
			await self.vault_node_refs_fetched(trans_id, base.NetError.success, refs)
	
	async def vault_init_age_reply(self, trans_id: int, result: base.NetError, age_node_id: int, age_info_node_id: int) -> None:
		logger_age.debug("Sending vault init age reply: transaction ID %d, result %r, Age node ID %d, Age Info node ID %d", trans_id, result, age_node_id, age_info_node_id)
		await self.write_message(30, VAULT_INIT_AGE_REPLY.pack(trans_id, result, age_node_id, age_info_node_id))
	
	@base.message_handler(32)
	async def vault_init_age_request(self) -> None:
		trans_id, instance_uuid, parent_instance_uuid = await self.read_unpack(VAULT_INIT_AGE_REQUEST_HEADER)
		instance_uuid = uuid.UUID(bytes_le=instance_uuid)
		parent_instance_uuid = uuid.UUID(bytes_le=parent_instance_uuid)
		age_file_name = await self.read_string_field(260)
		instance_name: typing.Optional[str] = await self.read_string_field(260)
		user_defined_name: typing.Optional[str] = await self.read_string_field(260)
		description: typing.Optional[str] = await self.read_string_field(1024)
		sequence_number, language = await self.read_unpack(VAULT_INIT_AGE_REQUEST_FOOTER)
		logger_age.debug("Vault init age request: transaction ID %d, instance UUID %s, parent instance UUID %s, age %r, instance name %r, user-defined name %r, description %r", trans_id, instance_uuid, parent_instance_uuid, age_file_name, instance_name, user_defined_name, description)
		
		if instance_uuid == structs.ZERO_UUID:
			instance_uuid = uuid.uuid4()
			logger_age.debug("Received init age request with zero UUID - generated random age instance UUID %s", instance_uuid)
		if parent_instance_uuid == structs.ZERO_UUID:
			parent_instance_uuid = None
		if not age_file_name:
			logger_age.error("Received init age request with empty age file name, this isn't supposed to happen!")
			await self.vault_init_age_reply(trans_id, base.NetError.invalid_parameter, 0, 0)
			return
		if not instance_name:
			instance_name = None
		if not user_defined_name:
			user_defined_name = None
		if not description:
			description = None
		if sequence_number != 0:
			logger_age.warning("Received init age request with sequence number %d instead of 0", sequence_number)
		if language != -1:
			logger_age.warning("Received init age request with language %d instead of -1", language)
		
		try:
			age_node_id, age_info_node_id = await self.server_state.create_age_instance(
				age_file_name,
				instance_uuid,
				parent_instance_uuid,
				instance_name,
				user_defined_name,
				description,
				sequence_number,
				language,
				allow_existing=True,
			)
		except state.VaultNodeNotFound:
			await self.vault_init_age_reply(trans_id, base.NetError.vault_node_not_found, 0, 0)
		except (state.VaultNodeAlreadyExists, state.AgeInstanceAlreadyExists):
			await self.vault_init_age_reply(trans_id, base.NetError.invalid_parameter, 0, 0)
		except Exception:
			logger_age.error("Unhandled exception while finding/creating age instance", exc_info=True)
			await self.vault_init_age_reply(trans_id, base.NetError.internal_error, 0, 0)
		else:
			await self.vault_init_age_reply(trans_id, base.NetError.success, age_node_id, age_info_node_id)
	
	async def vault_node_find_reply(self, trans_id: int, result: base.NetError, found_node_ids: typing.Sequence[int]) -> None:
		logger_vault_read.debug("Sending vault node find reply: transaction ID %d, result %r, found node IDs %r", trans_id, result, found_node_ids)
		message = bytearray(VAULT_NODE_FIND_REPLY_HEADER.pack(trans_id, result, len(found_node_ids)))
		
		for node_id in found_node_ids:
			message.extend(structs.UINT32.pack(node_id))
		
		await self.write_message(31, message)
	
	@base.message_handler(33)
	async def vault_node_find(self) -> None:
		trans_id, packed_template_length = await self.read_unpack(VAULT_NODE_FIND_HEADER)
		packed_template = await self.read(packed_template_length)
		template = state.VaultNodeData.unpack(packed_template)
		logger_vault_read.debug("Vault node find: transaction ID %d, template %s", trans_id, template)
		try:
			found_node_ids = []
			async for node_id in self.server_state.find_vault_nodes(template):
				found_node_ids.append(node_id)
		except Exception:
			logger_vault_read.error("Unhandled exception while finding vault node", exc_info=True)
			await self.vault_node_find_reply(trans_id, base.NetError.internal_error, [])
		else:
			await self.vault_node_find_reply(trans_id, base.NetError.success if found_node_ids else base.NetError.vault_node_not_found, found_node_ids)
	
	async def age_reply(self, trans_id: int, result: base.NetError, mcp_id: int, instance_uuid: uuid.UUID, age_node_id: int, server_ip: ipaddress.IPv4Address) -> None:
		logger_age.debug("Sending age reply: transaction ID %d, result %r, MCP ID %d, instance UUID %s, Age node ID %d, server IP %s", trans_id, result, mcp_id, instance_uuid, age_node_id, server_ip)
		await self.write_message(35, AGE_REPLY.pack(trans_id, result, mcp_id, instance_uuid.bytes_le, age_node_id, int(server_ip)))
	
	@base.message_handler(36)
	async def age_request(self) -> None:
		(trans_id,) = await self.read_unpack(AGE_REQUEST_HEADER)
		age_file_name = await self.read_string_field(64)
		instance_uuid = uuid.UUID(bytes_le=await self.read(16))
		logger_age.debug("Age request: transaction ID %d, age %r, instance UUID %s", trans_id, age_file_name, instance_uuid)
		
		try:
			age_node_id, _ = await self.server_state.find_age_instance(age_file_name, instance_uuid)
		except state.AgeInstanceNotFound:
			await self.age_reply(trans_id, base.NetError.age_not_found, 0, structs.ZERO_UUID, 0, ipaddress.IPv4Address(0))
		except Exception:
			logger_age.error("Unhandled exception while finding age instance for age request", exc_info=True)
			await self.age_reply(trans_id, base.NetError.internal_error, 0, structs.ZERO_UUID, 0, ipaddress.IPv4Address(0))
		else:
			ip_addr = self.server_state.config.server_game_address_for_client
			if ip_addr is None:
				ip_addr = self._get_own_ipv4_address()
			await self.age_reply(trans_id, base.NetError.success, age_node_id, instance_uuid, age_node_id, ip_addr)
	
	def get_client_error_quip(self) -> str:
		if self.server_state.config.logging_enable_crash_lines:
			try:
				return random.choice(crash_lines.client_crash_lines)
			except IndexError:
				return "missingno"
		else:
			return "Received client error"
	
	@base.message_handler(43)
	async def log_python_traceback(self) -> None:
		traceback_text = await self.read_string_field(1024)
		logger_client_errors.error("%s (client Python traceback)", self.get_client_error_quip())
		for line in traceback_text.splitlines():
			logger_client_errors.error("[traceback] %s", line)
	
	@base.message_handler(44)
	async def log_stack_dump(self) -> None:
		stack_dump_text = await self.read_string_field(1024)
		logger_client_errors.error("%s (client stack dump)", self.get_client_error_quip())
		for line in stack_dump_text.splitlines():
			logger_client_errors.error("[stack dump] %s", line)
	
	@base.message_handler(45)
	async def log_client_debugger_connect(self) -> None:
		(nothing,) = await self.read_unpack(LOG_CLIENT_DEBUGGER_CONNECT)
		logger_client_errors.warning("Client debugger connect: nothing %d", nothing)
