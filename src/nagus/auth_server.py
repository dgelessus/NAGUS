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
import datetime
import enum
import io
import ipaddress
import logging
import random
import struct
import typing
import uuid

from . import base
from . import configuration
from . import crash_lines
from . import state
from . import structs


logger = logging.getLogger(__name__)
logger_age = logger.getChild("age")
logger_avatar = logger.getChild("avatar")
logger_client_errors = logger.getChild("client_errors")
logger_connect = logger.getChild("connect")
logger_file = logger.getChild("file")
logger_login = logger.getChild("login")
logger_ping = logger.getChild("ping")
logger_score = logger.getChild("score")
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
VAULT_SEND_NODE = struct.Struct("<II")
AGE_REQUEST_HEADER = struct.Struct("<I")
AGE_REPLY = struct.Struct("<III16sII")
FILE_LIST_REQUEST_HEADER = struct.Struct("<I")
FILE_LIST_REPLY_HEADER = struct.Struct("<III")
FILE_DOWNLOAD_REQUEST_HEADER = struct.Struct("<I")
FILE_DOWNLOAD_CHUNK_HEADER = struct.Struct("<IIIII")
FILE_DOWNLOAD_CHUNK_ACK = struct.Struct("<I")
GET_PUBLIC_AGE_LIST_HEADER = struct.Struct("<I")
PUBLIC_AGE_LIST_HEADER = struct.Struct("<III")
SET_AGE_PUBLIC = struct.Struct("<I?")
LOG_CLIENT_DEBUGGER_CONNECT = struct.Struct("<I")
SCORE_CREATE_HEADER = struct.Struct("<II")
SCORE_CREATE_FOOTER = struct.Struct("<Ii")
SCORE_CREATE_REPLY = struct.Struct("<IIII")
SCORE_DELETE = struct.Struct("<II")
SCORE_DELETE_REPLY = struct.Struct("<II")
SCORE_GET_SCORES_HEADER = struct.Struct("<II")
SCORE_GET_SCORES_REPLY_HEADER = struct.Struct("<IIII")
SCORE_ADD_POINTS = struct.Struct("<IIi")
SCORE_ADD_POINTS_REPLY = struct.Struct("<II")
SCORE_TRANSFER_POINTS = struct.Struct("<IIIi")
SCORE_TRANSFER_POINTS_REPLY = struct.Struct("<II")
SCORE_SET_POINTS = struct.Struct("<IIi")
SCORE_SET_POINTS_REPLY = struct.Struct("<II")
SCORE_GET_RANKS_HEADER = struct.Struct("<IIII")
SCORE_GET_RANKS_FOOTER = struct.Struct("<IIII")
SCORE_GET_RANKS_REPLY_HEADER = struct.Struct("<IIII")


SYSTEM_RANDOM = random.SystemRandom()


class ServerCapsFlags(enum.Flag):
	score_leaderboards = 1 << 0
	game_mgr_blue_spiral = 1 << 1
	game_mgr_climbing_wall = 1 << 2
	game_mgr_heek = 1 << 3
	game_mgr_marker = 1 << 4
	game_mgr_tic_tac_toe = 1 << 5
	game_mgr_var_sync = 1 << 6


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
	usable: bool
	cleanup_handle: asyncio.TimerHandle
	messages_while_disconnected: typing.List[bytes]
	token: uuid.UUID
	server_challenge: int
	account_uuid: uuid.UUID
	ki_number: typing.Optional[int]
	cares_about_vault_nodes: typing.Set[int]
	
	def __init__(self) -> None:
		super().__init__()
		
		# Other attributes are intentionally left unset at first.
		# They will be set in read_connect_packet_data and the message handlers once appropriate.
		self.usable = False
		self.messages_while_disconnected = []
		self.ki_number = None
		self.cares_about_vault_nodes = set()


class AuthConnection(base.BaseMOULConnection):
	CONNECTION_TYPE = base.ConnectionType.cli2auth
	
	client_state: AuthClientState
	
	def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, server_state: state.ServerState) -> None:
		super().__init__(reader, writer, server_state)
		
		self.dh_keys = self.server_state.config.server_auth_keys
		self.client_state = AuthClientState()
	
	async def write(self, data: bytes) -> None:
		try:
			await super().write(data)
		except ConnectionResetError:
			# Remember the message to potentially re-send it if the client reconnects soon.
			self.client_state.messages_while_disconnected.append(data)
	
	def _clean_up_now(self) -> None:
		assert self.client_state.usable
		token = self.client_state.token
		
		# Set the connection's avatar (if any) to offline.
		if self.client_state.ki_number is not None:
			self.server_state.create_background_task(self.server_state.set_avatar_offline(self.client_state.ki_number))
			assert self.server_state.auth_connections_by_ki_number[self.client_state.ki_number] == self
			del self.server_state.auth_connections_by_ki_number[self.client_state.ki_number]
		
		if token not in self.server_state.auth_connections:
			raise AssertionError(f"Attempted to clean up connection {token} even though the corresponding state has already been discarded")
		elif self.server_state.auth_connections[token] != self:
			raise AssertionError(f"Attempted to clean up connection {token} even though the client has reconnected")
		else:
			del self.server_state.auth_connections[token]
	
	async def handle_disconnect(self) -> None:
		if not self.client_state.usable:
			# Either the client disconnected very early
			# and the connection was never added to the auth_connections dicts,
			# or the server marked the connection as unusable
			# and already removed it from the dicts.
			# In either case,
			# nothing needs to be kept around or cleaned up.
			return
		
		timeout = self.server_state.config.server_auth_disconnected_client_timeout
		
		if timeout == 0:
			# If the auth connection timeout is disabled,
			# skip all the timeout logic and clean up the connection immediately.
			self._clean_up_now()
		else:
			def _remove_disconnected_connection_callback() -> None:
				if self.client_state.messages_while_disconnected:
					logger_connect.info("Client with token %s didn't reconnect within %d seconds - discarding its state and %d unsent messages", self.client_state.token, timeout, len(self.client_state.messages_while_disconnected))
				else:
					logger_connect.info("Client with token %s didn't reconnect within %d seconds - discarding its state", self.client_state.token, timeout)
				
				self._clean_up_now()
			
			self.client_state.cleanup_handle = self.server_state.loop.call_later(
				timeout,
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
				prev_conn = self.server_state.auth_connections[token]
			except KeyError:
				raise base.ProtocolError(f"Client attempted to reconnect using an unknown token: {token}")
			
			assert prev_conn.client_state.usable
			# Transfer the client state from the previous connection.
			self.client_state = prev_conn.client_state
			
			# Stop the previous connection's delayed cleanup logic
			# (the new connection will clean everything up as needed).
			self.client_state.cleanup_handle.cancel()
			
			# Replace the previous connection with this one in all auth_connections dicts.
			self.server_state.auth_connections[token] = self
			if self.client_state.ki_number is not None:
				self.server_state.auth_connections_by_ki_number[self.client_state.ki_number] = self
			
			# Send any messages that we tried to send during the disconnect.
			# FIXME This is probably actually not the right place to do this. Should wait until after encryption is set up (and probably after the client re-sends a ClientRegisterRequest).
			if self.client_state.messages_while_disconnected:
				logger_connect.debug("Sending %d messages that were queued during the disconnect", len(self.client_state.messages_while_disconnected))
				while self.client_state.messages_while_disconnected:
					message = self.client_state.messages_while_disconnected[0]
					await self.write(message)
					self.client_state.messages_while_disconnected.pop(0)
		else:
			# Client doesn't have a token yet (probably a new connection) - assign it one.
			self.client_state.token = uuid.uuid4()
			while self.client_state.token in self.server_state.auth_connections:
				logger_connect.warning("Random UUID collision!? %s is already taken, trying again...", self.client_state.token)
				self.client_state.token = uuid.uuid4()
			
			logger_connect.info("New client connection, assigning token %s", self.client_state.token)
			self.client_state.usable = True
			self.server_state.auth_connections[self.client_state.token] = self
	
	async def kicked_off(self, reason: base.NetError) -> None:
		await self.write_message(39, KICKED_OFF.pack(reason))
	
	async def disconnect_with_reason(self, client_reason: base.NetError, server_log_message: str) -> typing.NoReturn:
		"""Send the client a reason why it's being disconnected before actually disconnecting it."""
		
		# Only send the message if the connection is fully set up
		# (otherwise the client won't recognize the message)
		# and hasn't already been kicked.
		if self.client_state.usable:
			await self.kicked_off(client_reason)
		
		raise base.ProtocolError(server_log_message)
	
	def kick_async(self, client_reason: base.NetError, *, set_avatar_offline: bool) -> typing.Optional[asyncio.Task[None]]:
		"""Forcibly kick this connection asynchronously.
		
		This method is non-blocking and safe to call from anywhere
		as long as the auth_connections dicts are in a consistent state.
		
		Once this method returns,
		the connection has been marked as not usable anymore
		and the server no longer tracks it in any way.
		However,
		you still have to await the returned task (if any)
		to ensure that the client is actually disconnected.
		"""
		
		if not self.client_state.usable:
			# Client never fully connected or was already kicked,
			# so there's nothing to be cleaned up
			# and we can't safely send a kicked_off message.
			return None
		
		# In preparation for kicking the client,
		# forget about this connection in all relevant places
		# and mark it as not usable anymore to ensure that the client can't get it back by reconnecting.
		del self.server_state.auth_connections[self.client_state.token]
		if self.client_state.ki_number is not None:
			del self.server_state.auth_connections_by_ki_number[self.client_state.ki_number]
		self.client_state.usable = False
		
		if set_avatar_offline:
			ki_number = self.client_state.ki_number
		else:
			ki_number = None
		
		try:
			self.client_state.cleanup_handle
		except AttributeError:
			# Client is still connected,
			# so tell the player why they're being kicked
			# and then close the connection.
			async def _get_kicked() -> None:
				await self.kicked_off(client_reason)
				# TODO Add a lock for "self is currently processing a message" and wait on that here to ensure that message handlers are never interrupted?
				self.writer.close()
				await self.writer.wait_closed()
				if ki_number is not None:
					await self.server_state.set_avatar_offline(ki_number)
			return self.server_state.loop.create_task(_get_kicked())
		else:
			# Connection is disconnected,
			# but hasn't timed out yet,
			# so stop the usual delayed cleanup from running.
			self.client_state.cleanup_handle.cancel()
			
			# But do still set the connection's avatar to offline if requested.
			if ki_number is not None:
				return self.server_state.loop.create_task(self.server_state.set_avatar_offline(ki_number))
			else:
				return None
	
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
	
	async def server_caps(self, caps: ServerCapsFlags) -> None:
		logger_connect.debug("Sending server caps: %r", caps)
		
		with io.BytesIO() as stream:
			structs.write_bit_vector(stream, caps.value)
			packed_caps_vector = stream.getvalue()
		
		await self.write_message(0x1002, structs.UINT32.pack(len(packed_caps_vector)) + packed_caps_vector)
	
	async def server_caps_compatible(self, caps: ServerCapsFlags) -> None:
		"""Send ServerCaps message for H'uru clients in a way that doesn't break OpenUru clients."""
		
		logger_connect.debug("Sending server caps (OpenUru-compatible): %r", caps)
		
		await self.write(
			# ServerCaps message type number - recognized by H'uru, but ignored by OpenUru.
			b"\x02\x10"
			# ServerCaps message data for H'uru.
			# OpenUru parses this as the start of a FileDownloadChunk message,
			# which will be ignored,
			# because no file download transaction is active.
			# H'uru sees: 0x25 bytes of data, bit vector is 1 dword long, value is [caps]
			# OpenUru sees: message type 0x25 (FileDownloadChunk), transaction ID 0x10000, error code 0x[caps]0000, file size 0x0000[caps] (continued below)
			+ b"\x25\x00\x00\x00\x01\x00\x00\x00" + structs.UINT32.pack(caps.value)
			# ServerCaps message extra data,
			# which is ignored by H'uru,
			# because the bit vector doesn't have this many dwords.
			# OpenUru parses this as the rest of FileDownloadChunk message:
			+ b"\x00\x00" # file size 0x0000[caps] (continued)
			+ b"\x00\x00\x00\x00\x13\x00\x00\x00" # chunk offset 0, chunk size 0x13
			+ b"[ServerCaps compat]" # 0x13 bytes of chunk data
		)
	
	async def send_server_caps_if_enabled(self, caps: ServerCapsFlags) -> None:
		send_mode = self.server_state.config.server_auth_send_server_caps
		
		if send_mode == configuration.SendServerCaps.always:
			await self.server_caps(caps)
		elif send_mode == configuration.SendServerCaps.compatible:
			await self.server_caps_compatible(caps)
		elif send_mode == configuration.SendServerCaps.never:
			pass
		else:
			raise AssertionError(f"Unhandled server caps mode: {send_mode!r}")
	
	async def client_register_reply(self, server_challenge: int) -> None:
		logger_connect.debug("Sending client register reply with server challenge: 0x%08x", server_challenge)
		await self.write_message(3, CLIENT_REGISTER_REPLY.pack(server_challenge))
	
	@base.message_handler(1)
	async def client_register_request(self) -> None:
		(build_id,) = await self.read_unpack(CLIENT_REGISTER_REQUEST)
		logger_connect.debug("Build ID: %d", build_id)
		if build_id != self.build_id:
			await self.disconnect_with_reason(base.NetError.invalid_parameter, f"Client register request build ID ({build_id}) differs from connect packet ({self.build_id})")
		
		# TODO Adjust this once we support any extended features
		await self.send_server_caps_if_enabled(ServerCapsFlags(0))
		
		# Reply to client register request
		if hasattr(self, "server_challenge"):
			logger_connect.warning("Already registered client sent another client register request - generating new server challenge...")
		self.client_state.server_challenge = SYSTEM_RANDOM.randrange(0x100000000)
		await self.client_register_reply(self.client_state.server_challenge)
		
		if self.server_state.config.server_auth_send_server_address:
			try:
				ip_addr = self.server_state.config.server_auth_address_for_client
				if ip_addr is None:
					ip_addr = self.get_own_ipv4_address()
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
		
		# Dissociate the connection from the avatar that it's currently using.
		if self.client_state.ki_number is None:
			prev_ki_number = 0
		else:
			prev_ki_number = self.client_state.ki_number
			del self.server_state.auth_connections_by_ki_number[prev_ki_number]
			self.client_state.ki_number = None
			# Set the previous avatar to offline in the vault
			# (though normally the client should have done this already).
			await self.server_state.set_avatar_offline(prev_ki_number)
		
		if ki_number != 0:
			# If the requested avatar is already in use by another connection,
			# kick/discard that connection.
			# BE CAREFUL: The following code must not await anything
			# until auth_connections_by_ki_number is updated to contain self.
			# Otherwise another connection might grab the same KI number,
			# leading to conflicts with this connection!
			# (... perhaps I should just add a lock around the auth_connections dicts instead?)
			try:
				existing_conn = self.server_state.auth_connections_by_ki_number[ki_number]
			except KeyError:
				pass
			else:
				logger.info("Discarding connection %s because its KI number %d will be used by another connection", existing_conn.client_state.token, ki_number)
				kick_task = existing_conn.kick_async(base.NetError.logged_in_elsewhere, set_avatar_offline=False)
				if kick_task is not None:
					self.server_state.add_background_task(kick_task)
			
			self.client_state.ki_number = ki_number
			self.server_state.auth_connections_by_ki_number[ki_number] = self
			# After this point,
			# await is safe again.
		
		logger_login.info("Account %s switched from avatar %d to %d", self.client_state.account_uuid, prev_ki_number, ki_number)
		await self.account_set_player_reply(trans_id, base.NetError.success)
	
	async def player_delete_reply(self, trans_id: int, result: base.NetError) -> None:
		logger_avatar.debug("Sending player delete reply: transaction ID %d, result %r", trans_id, result)
		await self.write_message(17, PLAYER_DELETE_REPLY.pack(trans_id, result))
	
	@base.message_handler(13)
	async def player_delete_request(self) -> None:
		trans_id, ki_number = await self.read_unpack(PLAYER_DELETE_REQUEST)
		logger_avatar.debug("Player delete request: transaction ID %d, KI number %d", trans_id, ki_number)
		if ki_number == self.client_state.ki_number:
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
	
	def start_caring_about_vault_nodes(self, node_ids: typing.Set[int]) -> None:
		if logger_vault_notify.isEnabledFor(logging.DEBUG):
			newly_caring = node_ids - self.client_state.cares_about_vault_nodes
			if newly_caring:
				logger_vault_notify.debug("Client will now be notified about vault nodes: %s", sorted(newly_caring))
		
		self.client_state.cares_about_vault_nodes |= node_ids
	
	def stop_caring_about_vault_nodes(self, node_ids: typing.Set[int]) -> None:
		if logger_vault_notify.isEnabledFor(logging.DEBUG):
			no_longer_caring = node_ids & self.client_state.cares_about_vault_nodes
			if no_longer_caring:
				logger_vault_notify.debug("Client will no longer notified about vault nodes: %s", sorted(no_longer_caring))
		
		self.client_state.cares_about_vault_nodes -= node_ids
	
	def cares_about_vault_node(self, node_id: int) -> bool:
		return node_id in self.client_state.cares_about_vault_nodes
	
	async def vault_node_created(self, trans_id: int, result: base.NetError, node_id: int) -> None:
		logger_vault_write.debug("Sending vault node created: transaction ID %d, result %r, node ID %d", trans_id, result, node_id)
		await self.write_message(23, VAULT_NODE_CREATED.pack(trans_id, result, node_id))
	
	@base.message_handler(25)
	async def vault_node_create(self) -> None:
		trans_id, packed_node_data_length = await self.read_unpack(VAULT_NODE_CREATE_HEADER)
		packed_node_data = await self.read(packed_node_data_length)
		node_data = state.VaultNodeData.unpack(packed_node_data)
		logger_vault_write.debug("Vault node create: transaction ID %d, node data %s", trans_id, node_data)
		
		if self.client_state.ki_number is None:
			await self.vault_node_created(trans_id, base.NetError.vault_node_access_violation, 0)
			await self.disconnect_with_reason(base.NetError.vault_node_access_violation, "Attempted to create a vault node without an active avatar")
		
		node_data.creator_account_uuid = self.client_state.account_uuid
		node_data.creator_id = self.client_state.ki_number
		
		try:
			node_id = await self.server_state.create_vault_node(node_data)
		except Exception:
			logger_vault_write.error("Unhandled exception while creating vault node", exc_info=True)
			await self.vault_node_created(trans_id, base.NetError.internal_error, 0)
		else:
			self.start_caring_about_vault_nodes({node_id})
			await self.vault_node_created(trans_id, base.NetError.success, node_id)
	
	async def vault_node_fetched(self, trans_id: int, result: base.NetError, node_data: typing.Optional[state.VaultNodeData]) -> None:
		logger_vault_read.debug("Sending fetched vault node: transaction ID %d, result %r, node data %s", trans_id, result, node_data)
		packed_node_data = b"" if node_data is None else node_data.pack()
		await self.write_message(24, VAULT_NODE_FETCHED_HEADER.pack(trans_id, result, len(packed_node_data)) + packed_node_data)
	
	@base.message_handler(26)
	async def vault_node_fetch(self) -> None:
		(trans_id, node_id) = await self.read_unpack(VAULT_NODE_FETCH)
		logger_vault_read.debug("Vault node fetch: transaction ID %d, node ID %d", trans_id, node_id)
		
		self.start_caring_about_vault_nodes({node_id})
		
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
		
		self.start_caring_about_vault_nodes({node_id})
		
		try:
			await self.server_state.update_vault_node(node_id, node_data, revision_id)
		except state.VaultNodeNotFound:
			await self.vault_save_node_reply(trans_id, base.NetError.vault_node_not_found)
		except Exception:
			logger_vault_write.error("Unhandled exception while creating vault node", exc_info=True)
			await self.vault_save_node_reply(trans_id, base.NetError.internal_error)
		else:
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
		
		self.start_caring_about_vault_nodes({parent_id, child_id})
		
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
		
		self.start_caring_about_vault_nodes({parent_id})
		
		try:
			await self.server_state.remove_vault_node_ref(parent_id, child_id)
		except state.VaultNodeNotFound:
			await self.vault_remove_node_reply(trans_id, base.NetError.vault_node_not_found)
		except Exception:
			logger_vault_write.error("Unhandled exception while removing vault node", exc_info=True)
			await self.vault_remove_node_reply(trans_id, base.NetError.internal_error)
		else:
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
			care = {node_id}
			async for ref in self.server_state.fetch_vault_node_refs_recursive(node_id):
				refs.append(ref)
				care.add(ref.child_id)
				if len(refs) > 1048576:
					raise ValueError(f"There are more than 1048576 node refs under node ID {node_id} - that's too many for the client")
		except state.VaultNodeNotFound:
			await self.vault_node_refs_fetched(trans_id, base.NetError.vault_node_not_found, [])
		except Exception:
			logger_vault_read.error("Unhandled exception while fetching vault node refs", exc_info=True)
			await self.vault_node_refs_fetched(trans_id, base.NetError.internal_error, [])
		else:
			self.start_caring_about_vault_nodes(care)
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
	
	@base.message_handler(35)
	async def vault_send_node(self) -> None:
		node_id, receiver_id = await self.read_unpack(VAULT_SEND_NODE)
		logger_vault_write.debug("Vault send node: node ID %d, receiver ID %d", node_id, receiver_id)
		
		if self.client_state.ki_number is None:
			await self.disconnect_with_reason(base.NetError.vault_node_access_violation, "Attempted to send a vault node without an active avatar")
		
		try:
			await self.server_state.send_vault_node(node_id, receiver_id, self.client_state.ki_number)
		except state.VaultNodeNotFound:
			# There's no way to report errors to the client here,
			# so just silently log it...
			logger_vault_write.error("Attempted to send a vault node to receiver %d who doesn't exist or has no inbox folder", receiver_id, exc_info=True)
		except state.VaultNodeAlreadyExists:
			# This happens during normal gameplay when the player sends a node multiple times to the same receiver,
			# so logging the traceback isn't worth it here.
			logger_vault_write.debug("Attempted to send vault node %d to receiver %d who already received that node", node_id, receiver_id)
	
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
				ip_addr = self.get_own_ipv4_address()
			await self.age_reply(trans_id, base.NetError.success, age_node_id, instance_uuid, age_node_id, ip_addr)
	
	async def file_list_reply(self, trans_id: int, result: base.NetError, file_list_data: bytes) -> None:
		count, rem = divmod(len(file_list_data), 2)
		if rem:
			raise ValueError(f"File list data cannot have an odd length: {len(file_list_data)} bytes")
		
		logger_file.debug("Sending file list reply: transaction ID %d, result %r, %d elements, data: %r", trans_id, result, count, file_list_data)
		
		await self.write_message(36, FILE_LIST_REPLY_HEADER.pack(trans_id, result, count) + file_list_data)
	
	@base.message_handler(37)
	async def file_list_request(self) -> None:
		(trans_id,) = await self.read_unpack(FILE_LIST_REQUEST_HEADER)
		directory = await self.read_string_field(260)
		extension = await self.read_string_field(256)
		logger_file.debug("File list request: transaction ID %d, directory %r, extension %r", trans_id, directory, extension)
		
		# TODO Actually serve some files
		if directory == "SDL":
			# This makes recent H'uru clients happy without having to pass /LocalSDL.
			await self.file_list_reply(trans_id, base.NetError.success, b"\x00\x00\x00\x00")
		else:
			await self.file_list_reply(trans_id, base.NetError.file_not_found, b"\x00\x00\x00\x00")
	
	async def file_download_chunk(self, trans_id: int, result: base.NetError, total_file_size: int, chunk_offset: int, chunk: bytes) -> None:
		logger_file.debug("Sending file download chunk: transaction ID %d, result %r, total file size %d bytes, %d bytes at offset %d", trans_id, result, total_file_size, len(chunk), chunk_offset)
		
		await self.write_message(37, FILE_DOWNLOAD_CHUNK_HEADER.pack(trans_id, result, total_file_size, chunk_offset, len(chunk)) + chunk)
	
	@base.message_handler(38)
	async def file_download_request(self) -> None:
		(trans_id,) = await self.read_unpack(FILE_DOWNLOAD_REQUEST_HEADER)
		file_path = await self.read_string_field(260)
		logger_file.debug("File download request: transaction ID %d, file path %r", trans_id, file_path)
		
		# TODO Actually serve some files
		await self.file_download_chunk(trans_id, base.NetError.file_not_found, 0, 0, b"")
	
	@base.message_handler(39)
	async def file_download_chunk_ack(self) -> None:
		(trans_id,) = await self.read_unpack(FILE_DOWNLOAD_CHUNK_ACK)
		logger_file.debug("Client acknowledged file download chunk: transaction ID %d", trans_id)
		
		# TODO Actually serve some files
	
	async def public_age_list(self, trans_id: int, result: base.NetError, age_instances: typing.Sequence[state.PublicAgeInstance]) -> None:
		logger_vault_read.debug("Sending public age list: transaction ID %d, result %r, %d instances: %r", trans_id, result, len(age_instances), age_instances)
		
		message = bytearray(PUBLIC_AGE_LIST_HEADER.pack(trans_id, result, len(age_instances)))
		for instance in age_instances:
			message.extend(instance.pack())
		
		await self.write_message(40, message)
	
	@base.message_handler(41)
	async def get_public_age_list(self) -> None:
		(trans_id,) = await self.read_unpack(GET_PUBLIC_AGE_LIST_HEADER)
		age_file_name = await self.read_string_field(64)
		logger_vault_read.debug("Get public age list: transaction ID %d, age file name %r", trans_id, age_file_name)
		
		try:
			age_instances = []
			async for age_instance in self.server_state.find_public_age_instances(age_file_name):
				age_instances.append(age_instance)
		except Exception:
			logger_age.error("Unhandled exception while getting public age list", exc_info=True)
			await self.public_age_list(trans_id, base.NetError.internal_error, [])
		else:
			await self.public_age_list(trans_id, base.NetError.success, age_instances)
	
	@base.message_handler(42)
	async def set_age_public(self) -> None:
		age_info_id, public = await self.read_unpack(SET_AGE_PUBLIC)
		logger_age.info("Set age public: Age Info node ID %d, public? %r", age_info_id, public)
		
		try:
			await self.server_state.update_vault_node(age_info_id, state.VaultNodeData(int32_2=int(public)), uuid.uuid4())
		except state.VaultNodeNotFound:
			# There's no way to report errors to the client here,
			# so just silently log it...
			logger_vault_write.error("Attempted to change public/private status of nonexistant Age Info node %d", age_info_id, exc_info=True)
	
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
	
	async def score_create_reply(self, trans_id: int, result: base.NetError, score_id: int, creation_time: datetime.datetime) -> None:
		logger_score.debug("Sending score create reply: transaction ID %d, result %r, score ID %d, creation time %s", trans_id, result, score_id, creation_time)
		await self.write_message(41, SCORE_CREATE_REPLY.pack(trans_id, result, score_id, creation_time.timestamp()))
	
	@base.message_handler(46)
	async def score_create(self) -> None:
		trans_id, owner_id = await self.read_unpack(SCORE_CREATE_HEADER)
		game_name = await self.read_string_field(64)
		game_type, points = await self.read_unpack(SCORE_CREATE_FOOTER)
		logger_score.debug("Score create: transaction ID %d, owner ID %d, game name %r, game type %d, %d points", trans_id, owner_id, game_name, game_type, points)
		
		# TODO Actually implement this
		await self.score_create_reply(trans_id, base.NetError.internal_error, 0, structs.ZERO_DATETIME)
	
	async def score_delete_reply(self, trans_id: int, result: base.NetError) -> None:
		logger_score.debug("Sending score delete reply: transaction ID %d, result %r", trans_id, result)
		await self.write_message(42, SCORE_DELETE_REPLY.pack(trans_id, result))
	
	@base.message_handler(47)
	async def score_delete(self) -> None:
		trans_id, score_id = await self.read_unpack(SCORE_DELETE)
		logger_score.debug("Score delete: transaction ID %d, score ID %d", trans_id, score_id)
		
		# TODO Actually implement this
		await self.score_delete_reply(trans_id, base.NetError.score_no_data_found)
	
	async def score_get_scores_reply(self, trans_id: int, result: base.NetError, scores: typing.Sequence[typing.Any]) -> None:
		logger_score.debug("Sending score get reply: transaction ID %d, result %r, scores %r", trans_id, result, scores)
		
		# TODO Implement writing scores
		if scores:
			raise NotImplementedError("Writing score data not supported yet")
		await self.write_message(43, SCORE_GET_SCORES_REPLY_HEADER.pack(trans_id, result, len(scores), 0))
	
	@base.message_handler(48)
	async def score_get_scores(self) -> None:
		trans_id, owner_id = await self.read_unpack(SCORE_GET_SCORES_HEADER)
		game_name = await self.read_string_field(64)
		logger_score.debug("Score get: transaction ID %d, owner ID %d, game name %r", trans_id, owner_id, game_name)
		
		# TODO Actually implement this
		await self.score_get_scores_reply(trans_id, base.NetError.score_no_data_found, [])
	
	async def score_add_points_reply(self, trans_id: int, result: base.NetError) -> None:
		logger_score.debug("Sending score add points reply: transaction ID %d, result %r", trans_id, result)
		await self.write_message(44, SCORE_ADD_POINTS_REPLY.pack(trans_id, result))
	
	@base.message_handler(49)
	async def score_add_points(self) -> None:
		trans_id, score_id, points_diff = await self.read_unpack(SCORE_ADD_POINTS)
		logger_score.debug("Score add points: transaction ID %d, score ID %d, %d points difference", trans_id, score_id, points_diff)
		
		# TODO Actually implement this
		await self.score_add_points_reply(trans_id, base.NetError.score_no_data_found)
	
	async def score_transfer_points_reply(self, trans_id: int, result: base.NetError) -> None:
		logger_score.debug("Sending score transfer points reply: transaction ID %d, result %r", trans_id, result)
		await self.write_message(45, SCORE_TRANSFER_POINTS_REPLY.pack(trans_id, result))
	
	@base.message_handler(50)
	async def score_transfer_points(self) -> None:
		trans_id, source_id, dest_id, points = await self.read_unpack(SCORE_TRANSFER_POINTS)
		logger_score.debug("Score transfer points: transaction ID %d, from %d to %d, %d points", trans_id, source_id, dest_id, points)
		
		if points < 0:
			logger_score.error("Attempted to transfer a negative (or very high...) number of points: %d", points)
			await self.score_transfer_points_reply(trans_id, base.NetError.invalid_parameter)
			return
		
		# TODO Actually implement this
		await self.score_transfer_points_reply(trans_id, base.NetError.score_no_data_found)
	
	async def score_set_points_reply(self, trans_id: int, result: base.NetError) -> None:
		logger_score.debug("Sending score set points reply: transaction ID %d, result %r", trans_id, result)
		await self.write_message(46, SCORE_TRANSFER_POINTS_REPLY.pack(trans_id, result))
	
	@base.message_handler(51)
	async def score_set_points(self) -> None:
		trans_id, score_id, points = await self.read_unpack(SCORE_SET_POINTS)
		logger_score.debug("Score set points: transaction ID %d, score ID %d, %d points", trans_id, score_id, points)
		
		# TODO Actually implement this
		await self.score_set_points_reply(trans_id, base.NetError.score_no_data_found)
	
	async def score_get_ranks_reply(self, trans_id: int, result: base.NetError, ranks: typing.Sequence[typing.Any]) -> None:
		logger_score.debug("Sending score get ranks reply: transaction ID %d, result %r, ranks %r", trans_id, result, ranks)
		
		# TODO Implement writing ranks
		if ranks:
			raise NotImplementedError("Writing rank data not supported yet")
		await self.write_message(47, SCORE_GET_RANKS_REPLY_HEADER.pack(trans_id, result, len(ranks), 0))
	
	@base.message_handler(52)
	async def score_get_ranks(self) -> None:
		trans_id, owner_id, score_group, parent_folder_id = await self.read_unpack(SCORE_GET_RANKS_HEADER)
		game_name = await self.read_string_field(64)
		time_period, result_count, page_number, sort_order = await self.read_unpack(SCORE_GET_RANKS_FOOTER)
		logger_score.debug("Score get ranks: transaction ID %d, owner ID %d, score group %d, parent folder ID %d, game name %r, time period %d, %d results, page %d, sort order %d", trans_id, owner_id, score_group, parent_folder_id, game_name, time_period, result_count, page_number, sort_order)
		
		# TODO Actually implement this (does anybody really care though?)
		await self.score_get_ranks_reply(trans_id, base.NetError.score_no_data_found, [])
