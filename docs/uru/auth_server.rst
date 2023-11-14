.. index:: auth server
  single: server; auth
  single: AuthSrv
  :name: auth_server

Auth server
===========

As the name indicates,
the auth server is responsible for handling player authentication,
but it also does a lot more.
In fact,
the auth server is the communication channel for all aspects of the game that aren't tied to the player's current age.
This includes:

* Sending players to the right :ref:`game server <game_server>` when going to a new age
* Providing access to the vault
* The score mechanism
* Serving "secure" files not provided by the file server

Each shard has a single auth server instance that all clients connect to.
The client code was apparently designed to support multiple alternative auth servers,
but this was not fully implemented.

Messages
--------

The overview tables below aren't *strictly* sorted by message type number.
I've moved a few entries
so that related messages are grouped together
and request/reply pairs align better.

Message types in (parentheses) are never used in practice,
but are at least partially implemented in the open-sourced client code.
Servers usually treat these messages as invalid,
or always reply with an error,
or ignore them outright.

Message types in *(italics)* are completely unused in any open-source client or server code.
Except for their message type number,
nothing is known about them,
not even their structure.

.. csv-table:: Global
  :name: auth_messages_global
  :header: #,Cli2Auth,Auth2Cli,#
  :widths: auto
  
  0,:ref:`PingRequest <cli2auth_ping_request>`,:ref:`PingReply <auth2cli_ping_reply>`,0
  ,,:ref:`ServerAddr <auth2cli_server_addr>`,1
  ,,:ref:`NotifyNewBuild <auth2cli_notify_new_build>`,2

.. csv-table:: Client
  :name: auth_messages_client
  :header: #,Cli2Auth,Auth2Cli,#
  :widths: auto
  
  1,:ref:`ClientRegisterRequest <cli2auth_client_register_request>`,:ref:`ClientRegisterReply <auth2cli_client_register_reply>`,3
  2,(:ref:`ClientSetCCRLevel <cli2auth_client_set_ccr_level>`),,

.. csv-table:: Account
  :name: auth_messages_account
  :header: #,Cli2Auth,Auth2Cli,#
  :widths: auto
  
  3,:ref:`AcctLoginRequest <cli2auth_acct_login_request>`,:ref:`AcctPlayerInfo <auth2cli_acct_player_info>`,6
  ,,:ref:`AcctLoginReply <auth2cli_acct_login_reply>`,4
  4,*(AcctSetEulaVersion)*,,
  5,*(AcctSetDataRequest)*,*(AcctData)*,5
  6,:ref:`AcctSetPlayerRequest <cli2auth_acct_set_player_request>`,:ref:`AcctSetPlayerReply <auth2cli_acct_set_player_reply>`,7
  7,(:ref:`AcctCreateRequest <cli2auth_acct_create_request>`),(:ref:`AcctCreateReply <auth2cli_acct_create_reply>`),8
  8,:ref:`AcctChangePasswordRequest <cli2auth_acct_change_password_request>`,:ref:`AcctChangePasswordReply <cli2auth_acct_change_password_reply>`,9
  9,(:ref:`AcctSetRolesRequest <cli2auth_acct_set_roles_request>`),(:ref:`AcctSetRolesReply <auth2cli_acct_set_roles_reply>`),10
  10,(:ref:`AcctSetBillingTypeRequest <cli2auth_acct_set_billing_type_request>`),(:ref:`AcctSetBillingTypeReply <auth2cli_acct_set_billing_type_reply>`),11
  11,(:ref:`AcctActivateRequest <cli2auth_acct_activate_request>`),(:ref:`AcctActivateReply <auth2cli_acct_activate_reply>`),12
  12,(:ref:`AcctCreateFromKeyRequest <cli2auth_acct_create_from_key_request>`),(:ref:`AcctCreateFromKeyReply <auth2cli_acct_create_from_key_reply>`),13
  53,(:ref:`AccountExistsRequest <cli2auth_account_exists_request>`),(:ref:`AccountExistsReply <auth2cli_account_exists_reply>`),48

.. csv-table:: Player
  :name: auth_messages_player
  :header: #,Cli2Auth,Auth2Cli,#
  :widths: auto
  
  ,,*(PlayerList)*,14
  13,:ref:`PlayerDeleteRequest <cli2auth_player_delete_request>`,:ref:`PlayerDeleteReply <auth2cli_player_delete_reply>`,17
  14,*(PlayerUndeleteRequest)*,,
  15,*(PlayerSelectRequest)*,,
  16,*(PlayerRenameRequest)*,,
  17,:ref:`PlayerCreateRequest <cli2auth_player_create_request>`,:ref:`PlayerCreateReply <auth2cli_player_create_reply>`,16
  18,*(PlayerSetStatus)*,,
  19,*(PlayerChat)*,*(PlayerChat)*,15
  20,(:ref:`UpgradeVisitorRequest <cli2auth_upgrade_visitor_request>`),(:ref:`UpgradeVisitorReply <auth2cli_upgrade_visitor_reply>`),18
  21,(:ref:`SetPlayerBanStatusRequest <cli2auth_set_player_ban_status_request>`),(:ref:`SetPlayerBanStatusReply <auth2cli_set_player_ban_status_reply>`),19
  22,(:ref:`KickPlayer <cli2auth_kick_player>`),:ref:`KickedOff <auth2cli_kicked_off>`,39
  23,(:ref:`ChangePlayerNameRequest <cli2auth_change_player_name_request>`),(:ref:`ChangePlayerNameReply <auth2cli_change_player_name_reply>`),20

.. csv-table:: Friends
  :name: auth_messages_friends
  :header: #,Cli2Auth,Auth2Cli,#
  :widths: auto
  
  24,(:ref:`SendFriendInviteRequest <cli2auth_send_friend_invite_request>`),(:ref:`SendFriendInviteReply <auth2cli_send_friend_invite_reply>`),21
  ,,*(FriendNotify)*,22

.. csv-table:: Vault
  :name: auth_messages_vault
  :header: #,Cli2Auth,Auth2Cli,#
  :widths: auto
  
  25,:ref:`VaultNodeCreate <cli2auth_vault_node_create>`,:ref:`VaultNodeCreated <auth2cli_vault_node_created>`,23
  26,:ref:`VaultNodeFetch <cli2auth_vault_node_fetch>`,:ref:`VaultNodeFetched <auth2cli_vault_node_fetched>`,24
  ,,:ref:`VaultNodeChanged <auth2cli_vault_node_changed>`,25
  27,:ref:`VaultNodeSave <cli2auth_vault_node_save>`,:ref:`VaultSaveNodeReply <auth2cli_vault_save_node_reply>`,32
  28,*(VaultNodeDelete)*,(:ref:`VaultNodeDeleted <auth2cli_vault_node_deleted>`),26
  ,,:ref:`VaultNodeAdded <auth2cli_vault_node_added>`,27
  29,:ref:`VaultNodeAdd <cli2auth_vault_node_add>`,:ref:`VaultAddNodeReply <auth2cli_vault_add_node_reply>`,33
  ,,:ref:`VaultNodeRemoved <auth2cli_vault_node_removed>`,28
  30,:ref:`VaultNodeRemove <cli2auth_vault_node_remove>`,:ref:`VaultRemoveNodeReply <auth2cli_vault_remove_node_reply>`,34
  31,:ref:`VaultFetchNodeRefs <cli2auth_vault_fetch_node_refs>`,:ref:`VaultNodeRefsFetched <auth2cli_vault_node_refs_fetched>`,29
  32,:ref:`VaultInitAgeRequest <cli2auth_vault_init_age_request>`,:ref:`VaultInitAgeReply <auth2cli_vault_init_age_reply>`,30
  33,:ref:`VaultNodeFind <cli2auth_vault_node_find>`,:ref:`VaultNodeFindReply <auth2cli_vault_node_find_reply>`,31
  34,(:ref:`VaultSetSeen <cli2auth_vault_set_seen>`),,
  35,:ref:`VaultSendNode <cli2auth_vault_send_node>`,,

.. csv-table:: Ages
  :name: auth_messages_ages
  :header: #,Cli2Auth,Auth2Cli,#
  :widths: auto
  
  36,:ref:`AgeRequest <cli2auth_age_request>`,:ref:`AgeReply <auth2cli_age_reply>`,35

.. csv-table:: File-related
  :name: auth_messages_file_related
  :header: #,Cli2Auth,Auth2Cli,#
  :widths: auto
  
  37,FileListRequest,FileListReply,36
  38,FileDownloadRequest,FileDownloadChunk,37
  39,FileDownloadChunkAck,,

.. csv-table:: Game
  :name: auth_messages_game
  :header: #,Cli2Auth,Auth2Cli,#
  :widths: auto
  
  40,(:ref:`PropagateBuffer <cli2auth_propagate_buffer>`),(:ref:`PropagateBuffer <auth2cli_propagate_buffer>`),38

.. csv-table:: Public ages
  :name: auth_messages_public_ages
  :header: #,Cli2Auth,Auth2Cli,#
  :widths: auto
  
  41,:ref:`GetPublicAgeList <cli2auth_get_public_age_list>`,:ref:`PublicAgeList <auth2cli_public_age_list>`,40
  42,:ref:`SetAgePublic <cli2auth_set_age_public>`,,

.. csv-table:: Log messages
  :name: auth_messages_log_messages
  :header: #,Cli2Auth,Auth2Cli,#
  :widths: auto
  
  43,:ref:`LogPythonTraceback <cli2auth_log_python_traceback>`,,
  44,:ref:`LogStackDump <cli2auth_log_stack_dump>`,,
  45,:ref:`LogClientDebuggerConnect <cli2auth_log_client_debugger_connect>`,,

.. csv-table:: Score
  :name: auth_messages_score
  :header: #,Cli2Auth,Auth2Cli,#
  :widths: auto
  
  46,:ref:`ScoreCreate <cli2auth_score_create>`,:ref:`ScoreCreateReply <auth2cli_score_create_reply>`,41
  47,(:ref:`ScoreDelete <cli2auth_score_delete>`),(:ref:`ScoreDeleteReply <auth2cli_score_delete_reply>`),42
  48,:ref:`ScoreGetScores <cli2auth_score_get_scores>`,:ref:`ScoreGetScoresReply <auth2cli_score_get_scores_reply>`,43
  49,:ref:`ScoreAddPoints <cli2auth_score_add_points>`,:ref:`ScoreAddPointsReply <auth2cli_score_add_points_reply>`,44
  50,:ref:`ScoreTransferPoints <cli2auth_score_transfer_points>`,:ref:`ScoreTransferPointsReply <auth2cli_score_transfer_points_reply>`,45
  51,:ref:`ScoreSetPoints <cli2auth_score_set_points>`,:ref:`ScoreSetPointsReply <auth2cli_score_set_points_reply>`,46
  52,(:ref:`ScoreGetRanks <cli2auth_score_get_ranks>`),(:ref:`ScoreGetRanksReply <auth2cli_score_get_ranks_reply>`),47

.. csv-table:: H'uru extensions
  :name: auth_messages_h_uru_extensions
  :header: #,Cli2Auth,Auth2Cli,#
  :widths: auto
  
  0x1000,AgeRequestEx,AgeReplyEx,0x1000
  0x1001,ScoreGetHighScores,ScoreGetHighScoresReply,0x1001
  ,,:ref:`ServerCaps <auth2cli_server_caps>`,0x1002

.. _cli2auth_ping_request:

Cli2Auth_PingRequest
^^^^^^^^^^^^^^^^^^^^

* *Message type* = 0
* **Ping time:** 4-byte unsigned int.
* **Transaction ID:** 4-byte unsigned int.
* **Payload byte count:** 4-byte unsigned int.
* **Payload:** Variable-length.

See :ref:`ping` for details.

.. _auth2cli_ping_reply:

Auth2Cli_PingReply
^^^^^^^^^^^^^^^^^^

* *Message type* = 0
* **Ping time:** 4-byte unsigned int.
* **Transaction ID:** 4-byte unsigned int.
* **Payload byte count:** 4-byte unsigned int.
* **Payload:** Variable-length.

See :ref:`ping` for details.

.. _auth2cli_server_addr:

Auth2Cli_ServerAddr
^^^^^^^^^^^^^^^^^^^

* *Message type* = 1
* **Server IP address:** 4-byte packed IPv4 address.
  Auth server address to use when reconnecting.
* **Token:** 16-byte UUID.
  The client remembers this token as long as it remains running
  and sends it back to the auth server if it has to reconnect.

Tells the client an IP address to connect to
if the auth server connection is lost and the client needs to reconnect.
The token UUID is also sent to the auth server upon reconnect,
as part of the :ref:`connect packet <connect_packet>`.

According to comments in the open-sourced client code,
this is meant for when there are multiple auth servers behind a load balancer,
to allow the client to reconnect directly to the same auth server as before.
No current MOULa shard is large enough to require such a setup,
so this message currently has no practical use.
Nonetheless,
Cyan's server software and MOSS send a ServerAddr message to all clients
in response to the :ref:`ClientRegisterRequest <cli2auth_client_register_request>`.
MOSS uses the constant token UUID ``8ac671cb-9fd0-4376-9ecb-310c211ae6a4``,
whereas Cyan's server sends a random token (UUID version 4) on every connection.
DIRTSAND doesn't use ServerAddr messages at all.

.. _auth2cli_notify_new_build:

Auth2Cli_NotifyNewBuild
^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 2
* **foo:** 4-byte unsigned int.
  Yes, that's the original name from the open-sourced client code
  (which doesn't use this field for anything).
  One could guess that this might contain the newly released build number.

May be sent by the server to tell clients that a game update has been released.
The client displays it to the user as a chat message saying
"Uru has been updated. Please quit the game and log back in.".

Neither MOSS nor DIRTSAND supports sending this message.
Cyan's server software presumably supports it,
but it's not used in practice ---
Cyan always shuts down the server while an update is being released,
so there can be no clients connected when the new update becomes available.

.. _cli2auth_client_register_request:

Cli2Auth_ClientRegisterRequest
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 1
* **Build ID:** 4-byte unsigned int.
  The client's :ref:`build ID <build_id>`.

Sent by the client immediately after connecting to the auth server
(before even the automatic :ref:`PingRequest <cli2auth_ping_request>`).

Cyan's server software and DIRTSAND will disconnect clients that send an unexpected build ID.
MOSS doesn't check the build ID here.
If the server is happy with the build ID,
it replies immediately with a :ref:`ClientRegisterReply <auth2cli_client_register_reply>`.

.. _auth2cli_client_register_reply:

Auth2Cli_ClientRegisterReply
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 3
* **Server challenge:** 4-byte unsigned int.
  Random value generated by the server,
  which the client incorporates into the password hash when logging in.
  This prevents replay attacks in case an attacker captures a login transaction in unencrypted form.

Reply to the :ref:`ClientRegisterRequest <cli2auth_client_register_request>`.
The client waits for this reply before sending any other messages (except pings) to the auth server.

.. index:: CCR level
  :name: ccr_level

.. index:: stealth mode
  :name: stealth_mode

.. _cli2auth_client_set_ccr_level:

Cli2Auth_ClientSetCCRLevel
^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 2
* **CCR level:** 4-byte unsigned int.
  The player's new CCR level.

Notifies the auth server that the player has changed their CCR level.
All players initially have CCR level 0,
and during normal gameplay it is never changed.
Higher CCR levels are only meant to be used by customer care representatives (CCRs).

If a player has a non-zero CCR level,
they become "invisible" to all other players with a lower CCR level.
By default,
this means that they are hidden from the Age Players list of lower-level players,
but their avatar in the world is still visible.
A CCR player can additionally enable "stealth mode" to also make their avatar invisible to lower-level players.
(Other CCRs with the same or higher lever will see "stealth" avatars as semi-transparent instead of fully invisible.)

No open-source version of the client allows the player to change their CCR level,
so this message isn't used anymore in practice.
MOSS and DIRTSAND also hardcode all players to CCR level 0
and don't accept this message from clients.
Only Cyan's server software implements this message,
and presumably Cyan's internal CCR clients allowed changing the CCR level.

.. _cli2auth_acct_login_request:

Cli2Auth_AcctLoginRequest
^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 3
* **Transaction ID:** 4-byte unsigned int.
* **Client challenge:** 4-byte unsigned int.
  Randomly generated by the client,
  or set to 0 if unused
  (see below).
* **Account name:** :c:macro:`NET_MSG_FIELD_STRING`\(64).
  The account name entered by the user in the login dialog.
  May be overridden using the command-line setting ``screenname``
  (in GameTap-style syntax, see below).
* **Challenge hash:** 20-byte SHA hash.
  Derived from the password, acount name, and the server and client challenge values
  (details vary, see below).
* **Auth token:** :c:macro:`NET_MSG_FIELD_STRING`\(64).
  Normally always set to an empty string.
  May be overridden using the command-line setting ``authtoken``
  (in GameTap-style syntax, see below).
* **Operating system:** :c:macro:`NET_MSG_FIELD_STRING`\(8).
  Normally always set to ``"win"``.
  If running in the old TransGaming Cider wrapper,
  set to ``"mac"`` instead.
  May be overridden using the command-line setting ``os``
  (in GameTap-style syntax, see below).

Logs in to an account using the given credentials.
Sent by the client after having received the :ref:`ClientRegisterReply <auth2cli_client_register_reply>`.

If the login was successful,
the server replies with any number of :ref:`AcctPlayerInfo <auth2cli_acct_player_info>` messages,
one for each avatar in the account
(possibly none at all),
terminated by an :ref:`AcctLoginReply <auth2cli_acct_login_reply>` message.
If the login failed for any reason,
the server replies immediately with an :ref:`AcctLoginReply <auth2cli_acct_login_reply>` and nothing else.

Account name
''''''''''''

The account name entered by the user is sent unmodified to the server,
but the format of the account name affects the way the password is hashed.
Specifically,
if an account name is in the format :samp:`{name}@{domain}.{tld}` (regex ``.+@.+\..+``),
it's recognized as an email address and treated differently from a plain username ---
unless the second-level domain of the email address is "gametap",
in which case it's considered a plain username.

.. note::
  
  For example,
  the following account names are considered email addresses:
  
  * ``noreply@example.net``
  * ``noreply@example.co.uk``
  * ``noreply@gametap.co.uk``
  
  And these account names are considered plain usernames:
  
  * ``account``
  * ``@example``
  * ``@example.com``
  * ``noreply@example``
  * ``noreply@example.``
  * ``noreply@.com``
  * ``noreply@gametap.com``
  * ``noreply@gametap.net``
  * ``noreply@spam.gametap.net``

.. _password_hash:

Password hash
'''''''''''''

The client supports two different ways of hashing the password.
They are referred to as "SHA-1" and "SHA-0" after the hash algorithms they are based on,
but both password hashing methods actually perform extra steps on top of plain SHA-0/SHA-1.

Regardless of which hash algorithm is used,
the client first truncates the account name to 63 characters
and the password to 15 characters.
(To be precise,
the truncation is based on ``wchar``\s,
aka UTF-16 code units.)

.. note::
  
  For example,
  the password ``correct horse battery staple`` is truncated to ``correct horse b``.
  
  Not all shards replicate this truncation when *registering* an account,
  meaning that if one chooses a password longer than 15 characters,
  it may be impossible to log in with the game client
  until the password is changed to a shorter one.

"SHA-1"
  The password is encoded as UTF-8 (H'uru) or the ANSI code page (OpenUru) and hashed using SHA-1.
  In the resulting hash,
  every group of 4 bytes is byte-swapped
  (as if the hash was a 5-element array of 4-byte ints).
  
  .. note::
    
    For example,
    the password ``hunter2`` would be hashed as ``66bdbbf3f14b3da65740797410d0c38e1de23035``.
    (Regular SHA-1 would be ``f3bbbd66a63d4bf1747940578ec3d0103530e21d``.)

"SHA-0"
  The password is concatenated with the account name.
  All ASCII letters in the account name are converted to lowercase.
  The last character of the account name and password (respectively) is replaced with U+0000.
  The resulting string is encoded as UTF-16 (little-endian) and hashed using SHA-0.
  
  .. note::
    For example,
    the password ``hunter2``
    would be hashed as ``8598c0ad2f51fb1605c7433654baca9bdc589212`` if the account name is ``AzureDiamond``,
    or as ``0ee474a4a95caf724b52e4931434108176860b25`` if the account name is ``AzureDiamond@example.com``.

Recent OpenUru clients (since March 2017) will always attempt to log in using the "SHA-1" password hash first,
and only if that fails fall back to "SHA-0".
The original open-sourced client code as well as H'uru will use "SHA-1" only for plain usernames (and @gametap emails, see above)
and "SHA-0" only for email address account names.

Challenge hash
''''''''''''''

If the account name is an email address (except @gametap, see above),
then the challenge hash is derived from the password hash as follows:

1. The client generates a random value for the client challenge.
2. The client challenge,
   server challenge,
   and password hash
   are concatenated.
   (The server challenge comes from the :ref:`ClientRegisterReply <auth2cli_client_register_reply>` sent by the server.
   Client and server challenge are packed in little-endian byte order,
   as usual.)
3. The concatenated data is hashed using SHA-0,
   resulting in the challenge hash.

.. note::
  
  For example,
  if the client and server challenge are both 0,
  then the password ``hunter2`` with account name ``AzureDiamond@example.com``
  would produce the challenge hash ``475df2fc21a36ede01bf381ea10a5a8121a11c81`` (with "SHA-1" password hash)
  or ``72650da5e84e37994acd3e07da5658915bf588fe`` (with "SHA-0" password hash).

If the account name is a plain username,
the challenge hash is identical to the password hash
and the client challenge is set to 0.

Automatic login using auth token
''''''''''''''''''''''''''''''''

OpenUru clients allow automatically logging in to an account
by passing the account name and an authentication token on the command line.
The expected format for the command line is
:samp:`screenname={ACCOUNT_NAME} authtoken={AUTH_TOKEN} os={OS}`.
This is the only case where the auth token field is used ---
otherwise it is left empty.
If an auth token is used,
the challenge hash is set to zero
(or possibly left uninitialized --- I don't know C++ well enough to tell).

This login mechanism was used by GameTap
to automatically log in players using their GameTap account
when launching MOUL from the GameTap application.
Since MOULa,
Cyan no longer uses this login mechanism.
MOSS and DIRTSAND don't support token-based logins
and H'uru clients no longer allow passing one on the command line,
so no fan shard uses it either.

Automatic login using :option:`/SkipLoginDialog`
''''''''''''''''''''''''''''''''''''''''''''''''

:ref:`Internal clients <internal_external_client>` support another method for automatic login,
enabled using the following command-line option:

.. option:: /SkipLoginDialog
  
  Don't prompt the user for login information
  and instead log in automatically using saved/pre-configured credentials.
  
  In H'uru clients,
  this option will use the last saved credentials entered by the user.
  If there are none
  (i. e. the user never logged in before or didn't save the password),
  the regular login dialog is shown.
  
  OpenUru clients instead read the account name and password from UruLive.cfg
  (file name depends on the client :ref:`core name <core_name>`)
  in the user data folder.
  The UruLive.cfg must contain a section like this:
  
  .. code-block:: ini
    
    [Net.Account]
        Username=noreply@example.net
        Password=hunter2
  
  When using this automatic login method,
  OpenUru clients always hash the password using SHA-0.
  The SHA-1-based hash is never tried,
  unlike when logging in manually.

.. _auth2cli_acct_player_info:

Auth2Cli_AcctPlayerInfo
^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 6
* **Transaction ID:** 4-byte unsigned int.
* **Player vault node ID:** 4-byte unsigned int.
  Displayed to players as the KI number.
* **Player name:** :c:macro:`NET_MSG_FIELD_STRING`\(40).
  The avatar's in-game display name.
* **Avatar shape:** :c:macro:`NET_MSG_FIELD_STRING`\(64).
  Also known as "avatar dataset",
  or in practical terms,
  the avatar's gender.
  Either ``"female"`` or ``"male"``.
* **Explorer:** 4-byte unsigned int.
  1 if the player is a full :ref:`explorer <explorer>`,
  or 0 if it's just a :ref:`visitor <visitor>`.

Reports information about a single avatar associated with the client's account.
Sent by the server after a successful login,
but before the :ref:`AcctLoginReply <auth2cli_acct_login_reply>`.

One message is sent per avatar in the account ---
possibly none at all,
if the account currently has no avatars.
The client technically supports at most 6 avatars per account ---
1 visitor and 5 explorers ---
but because visitors are no longer used in MOULa,
the practical limit is 5 avatars.

.. index:: visitor
  :name: visitor

.. index:: explorer
  :name: explorer

.. note::
  
  Visitors are a holdover from GameTap-era MOUL,
  where non-paying players were only allowed to create a single visitor avatar
  that had limited customization options
  and could only visit a restricted set of locations
  (Relto, Cleft, Nexus, a single neighborhood and its Gahreesen).
  With MOULa being free to play,
  all accounts are considered "paying",
  so visitor avatars no longer have any use and can't be created anymore.
  H'uru clients no longer support visitor avatars at all.

.. _auth2cli_acct_login_reply:

Auth2Cli_AcctLoginReply
^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 4
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.
* **Account ID:** 16-byte UUID.
  The client sends this UUID to the game server when linking to an age instance.
* **Account flags:** 4-byte unsigned int.
  A set of bit flags describing the account's "role".
  Not actually used on the client side.
* **Billing type:** 4-byte unsigned int.
  A set of bit flags describing the account's payment/billing status (see below).
* **notthedroids encryption key:** 4-element array of 4-byte unsigned ints.
  Key for decrypting :ref:`notthedroids <notthedroids>`-encrypted files
  that may be served by the auth server.

Reply to an :ref:`AcctLoginRequest <cli2auth_acct_login_request>`.
Sent after all :ref:`AcctPlayerInfo <auth2cli_acct_player_info>` messages (if any).

The result is usually one of:

* :cpp:enumerator:`kNetSuccess`
* :cpp:enumerator:`kNetErrAccountNotFound`: Account name doesn't exist.
  DIRTSAND never returns this error
  and instead also uses :cpp:enumerator:`kNetErrAuthenticationFailed` to report nonexistant accounts.
  This prevents leaking information about the existence of other people's accounts.
* :cpp:enumerator:`kNetErrVaultNodeNotFound`: For some reason,
  the open-sourced client code considers this a successful login.
* :cpp:enumerator:`kNetErrAuthenticationFailed`: Password is invalid,
  or in the case of DIRTSAND,
  the account name might also be invalid.
  In response to this error,
  OpenUru clients may try to send another login request using a different password hash function
  (see :ref:`AcctLoginRequest <cli2auth_acct_login_request>`).
* :cpp:enumerator:`kNetErrLoginDenied`: Login failed for some other reason,
  e. g. the server currently has logins restricted to admins only.
* :cpp:enumerator:`kNetErrAccountNotActivated`: Only used by Cyan's server software.
* :cpp:enumerator:`kNetErrAccountBanned`

If the login failed,
all fields except for the transaction ID and result should be zeroed out.
Cyan's server software isn't always consistent about this ---
e. g. the notthedroids key is returned even for failed logins.
The error code is displayed to the user as a text description.

.. _account_flags:

Account flags
'''''''''''''

The open-sourced client code defines these flags
even though it doesn't use them in any way.
Most likely they are only used by Cyan's server software.

The flags :cpp:var:`kAccountRoleBetaTester`,
:cpp:var:`kAccountRoleUser`,
and :cpp:var:`kAccountRoleSpecialEvent`
apparently indicate the user's primary "role".
It seems that exactly one of these flags is meant to be set on every account,
although DIRTSAND doesn't do this and instead sets no flags at all for normal accounts.
All other flags seem to be true flags that may be set in any combination on top of the primary "role".

.. cpp:var:: const unsigned kAccountRoleDisabled = 0 << 0
  
  Default state if no role flags are set.

.. cpp:var:: const unsigned kAccountRoleAdmin = 1 << 0
  
  Exact original meaning unknown.
  In DIRTSAND,
  has the same effect as :cpp:var:`kAccountRoleBetaTester`
  and additionally allows the player in question to send certain unsafe Plasma messages over the network.

.. cpp:var:: const unsigned kAccountRoleDeveloper = 1 << 1
  
  Meaning unknown.
  Not supported by any fan server implementation.

.. cpp:var:: const unsigned kAccountRoleBetaTester = 1 << 2
  
  Exact original meaning unknown.
  In DIRTSAND,
  allows logging in to the account in question even when logins are restricted
  (normally the login would fail with :cpp:enumerator:`kNetErrLoginDenied`).

.. cpp:var:: const unsigned kAccountRoleUser = 1 << 3
  
  Apparently meant to indicate normal users.
  MOSS sets this flag in all sucessful login replies
  (and never any other flags).
  DIRTSAND *never* sets this flag.

.. cpp:var:: const unsigned kAccountRoleSpecialEvent = 1 << 4
  
  Meaning unknown.
  Not supported by any fan server implementation.

.. cpp:var:: const unsigned kAccountRoleBanned = 1 << 16
  
  Supported by DIRTSAND ---
  if set,
  logging in to the account in question always fails with :cpp:enumerator:`kNetErrAccountBanned`.
  Not used by MOSS ---
  it handles account bans using an internal database flag
  that isn't sent to the client.

.. _billing_type:

Billing type
''''''''''''

The open-sourced client code defines the following billing types:

.. cpp:var:: const unsigned kBillingTypeFree = 0 << 0
  
  Technically the default state,
  but no longer used in MOULa,
  as all accounts are considered "paid subscribers".

.. cpp:var:: const unsigned kBillingTypePaidSubscriber = 1 << 0
  
  Indicates that the account has full access to all game content.
  Before MOULa,
  this was only set for paying subscribers,
  as the name indicates.
  With MOULa being free to play,
  all accounts have this flag set
  despite not actually paying for a subscription.
  
  Accounts with this flag unset can only create a single :ref:`visitor <visitor>` avatar.
  Accounts with this flag set can only create :ref:`explorer <explorer>` avatars,
  and any existing visitor avatar is automatically upgraded to an explorer
  (see :ref:`UpgradeVisitorRequest <cli2auth_upgrade_visitor_request>`).
  
  DIRTSAND sets this flag for all accounts and doesn't allow changing it.
  MOSS has a few bits of code that theoretically handle non-paid accounts,
  but this seems to be unused in practice.

.. cpp:var:: const unsigned kBillingTypeGameTap = 1 << 1
  
  Exact meaning unknown ---
  not used in the open-sourced client code.
  MOSS sets this flag in all successful login replies,
  presumably mirroring what Cyan's server software did during the GameTap era.

.. _cli2auth_acct_set_player_request:

Cli2Auth_AcctSetPlayerRequest
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 6
* **Transaction ID:** 4-byte unsigned int.
* **Player vault node ID:** 4-byte unsigned int.
  KI number of the avatar to be made active,
  or 0 to explicitly switch to no active avatar
  (used for the avatar creation/selection screen).

Switch to a different avatar.
Sent by the client after the player has selected an avatar,
or when going to the avatar creation/selection screen
(to switch away from any previous avatar).

.. _auth2cli_acct_set_player_reply:

Auth2Cli_AcctSetPlayerReply
^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 7
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.

Reply to an :ref:`AcctSetPlayerRequest <cli2auth_acct_set_player_request>`.

The result is usually one of:

* :cpp:enumerator:`kNetSuccess`
* :cpp:enumerator:`kNetErrTimeout`
* :cpp:enumerator:`kNetErrPlayerNotFound`
* :cpp:enumerator:`kNetErrLoggedInElsewhere`:
  DIRTSAND responds with this error code if a client tries to switch to an avatar that's already in use.
  This differs from Cyan's server software and MOSS,
  which reject parallel logins at the account level
  and will kick an already logged-in client
  rather than refusing the new login.
* :cpp:enumerator:`kNetErrVaultNodeNotFound`: For some reason,
  the open-sourced client code considers this a success.

.. _cli2auth_acct_create_request:

Cli2Auth_AcctCreateRequest
^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 7
* **Transaction ID:** 4-byte unsigned int.
* **Account name:** :c:macro:`NET_MSG_FIELD_STRING`\(64).
* **Password hash:** 20-byte SHA hash.
  Same format as the :ref:`password hash <password_hash>` in :ref:`AcctLoginRequest <cli2auth_acct_login_request>`.
* **Account flags:** 4-byte unsigned int.
  Same meaning as the :ref:`account flags <account_flags>` in :ref:`AcctLoginReply <auth2cli_acct_login_reply>`.
* **Billing type:** 4-byte unsigned int.
  Same meaning as the :ref:`billing type <billing_type>` in :ref:`AcctLoginReply <auth2cli_acct_login_reply>`.

Implemented in the open-sourced client code,
but never actually used,
and not supported by any fan server implementation.
Unclear if Cyan's server software still supports it.
All current shards (Cyan and fan-run) implement account creation using a web interface or other mechanism.

.. _auth2cli_acct_create_reply:

Auth2Cli_AcctCreateReply
^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 8
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.
* **Account ID:** 16-byte UUID.
  Same meaning as the account ID in :ref:`AcctLoginReply <auth2cli_acct_login_reply>`.

Reply to an :ref:`AcctCreateRequest <cli2auth_acct_create_request>`
and similarly unused in practice.

.. _cli2auth_acct_change_password_request:

Cli2Auth_AcctChangePasswordRequest
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 8
* **Transaction ID:** 4-byte unsigned int.
* **Account name:** :c:macro:`NET_MSG_FIELD_STRING`\(64).
  Name of the account for which to change the password.
  Must match the name of the account with which the client is currently logged in.
* **Password hash:** 20-byte SHA hash.
  Hashed version of the new password.
  Same format as the :ref:`password hash <password_hash>` in :ref:`AcctLoginRequest <cli2auth_acct_login_request>`.

Change the password of an existing account.
Sent by the client when the user uses the ``/changepassword`` chat command.
The client always uses the SHA-0-based hash function for the new password,
even for account names where the SHA-1-based hash should be used,
which may lead to the player being unable to log in with the new password.
At least MOSS detects this case and rejects such a password change.

This message doesn't authenticate the client ---
it can only be sent after a successful :ref:`AcctLoginRequest <cli2auth_acct_login_request>`,
and the account name field must exactly match the one sent at login.

MOSS appears to fully implement this message,
whereas Cyan's server software seems to ignore it.
DIRTSAND doesn't support it at all.

All current public shards (Cyan and fan-run) also provide a web interface to change account passwords,
so this message and the ``/changepassword`` command is no longer the primary way to change passwords,
even where the server does implement the message.

.. _cli2auth_acct_change_password_reply:

Auth2Cli_AcctChangePasswordReply
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 9
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.

Reply to an :ref:`AcctChangePasswordRequest <cli2auth_acct_change_password_request>`.

The result is usually one of:

* :cpp:enumerator:`kNetSuccess`
* :cpp:enumerator:`kNetErrAccountNotFound`
* :cpp:enumerator:`kNetErrInvalidParameter`

.. _cli2auth_acct_set_roles_request:

Cli2Auth_AcctSetRolesRequest
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 9
* **Transaction ID:** 4-byte unsigned int.
* **Account name:** :c:macro:`NET_MSG_FIELD_STRING`\(64).
* **Account flags:** 4-byte unsigned int.
  Same meaning as the :ref:`account flags <account_flags>` in :ref:`AcctLoginReply <auth2cli_acct_login_reply>`.

Implemented in the open-sourced client code,
but never actually used,
and not supported by any fan server implementation.
Unclear if Cyan's server software supports it.

.. _auth2cli_acct_set_roles_reply:

Auth2Cli_AcctSetRolesReply
^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 10
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.

Reply to an :ref:`AcctSetRolesRequest <cli2auth_acct_set_roles_request>`
and similarly unused in practice.

.. _cli2auth_acct_set_billing_type_request:

Cli2Auth_AcctSetBillingTypeRequest
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 10
* **Transaction ID:** 4-byte unsigned int.
* **Account name:** :c:macro:`NET_MSG_FIELD_STRING`\(64).
* **Billing type:** 4-byte unsigned int.
  Same meaning as the :ref:`billing type <billing_type>` in :ref:`AcctLoginReply <auth2cli_acct_login_reply>`.

Implemented in the open-sourced client code,
but never actually used,
and not supported by any fan server implementation.
Unclear if Cyan's server software supports it.

.. _auth2cli_acct_set_billing_type_reply:

Auth2Cli_AcctSetBillingTypeReply
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 11
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.

Reply to an :ref:`AcctSetBillingTypeRequest <cli2auth_acct_set_billing_type_request>`
and similarly unused in practice.

.. _cli2auth_acct_activate_request:

Cli2Auth_AcctActivateRequest
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 11
* **Transaction ID:** 4-byte unsigned int.
* **Activation key:** 16-byte UUID.

Implemented in the open-sourced client code,
but never actually used,
and not supported by any fan server implementation.
Unclear if Cyan's server software supports it.
All current shards (Cyan and fan-run) that require account activation implement it using a web interface.

.. _auth2cli_acct_activate_reply:

Auth2Cli_AcctActivateReply
^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 12
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.

Reply to an :ref:`AcctActivateRequest <cli2auth_acct_activate_request>`
and similarly unused in practice.

.. _cli2auth_acct_create_from_key_request:

Cli2Auth_AcctCreateFromKeyRequest
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 12
* **Transaction ID:** 4-byte unsigned int.
* **Account name:** :c:macro:`NET_MSG_FIELD_STRING`\(64).
* **Password hash:** 20-byte SHA hash.
  Same format as the :ref:`password hash <password_hash>` in :ref:`AcctLoginRequest <cli2auth_acct_login_request>`.
* **Key:** 16-byte UUID.
* **Billing type:** 4-byte unsigned int.
  Same meaning as the :ref:`billing type <billing_type>` in :ref:`AcctLoginReply <auth2cli_acct_login_reply>`.

Variant of :ref:`AcctCreateRequest <cli2auth_acct_create_request>`.
Implemented in the open-sourced client code,
but never actually used,
and not supported by any fan server implementation.
Unclear if Cyan's server software still supports it.
All current shards (Cyan and fan-run) implement account creation using a web interface or other mechanism.

.. _auth2cli_acct_create_from_key_reply:

Auth2Cli_AcctCreateFromKeyReply
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 13
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.
* **Account ID:** 16-byte UUID.
  Same meaning as the account ID in :ref:`AcctLoginReply <auth2cli_acct_login_reply>`.
* **Activation key:** 16-byte UUID.

Reply to an :ref:`AcctCreateFromKeyRequest <cli2auth_acct_create_from_key_request>`
and similarly unused in practice.

.. _cli2auth_account_exists_request:

Cli2Auth_AccountExistsRequest
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 53
* **Transaction ID:** 4-byte unsigned int.
* **Account name:** :c:macro:`NET_MSG_FIELD_STRING`\(64).

Implemented in the open-sourced client code,
but never actually used,
and not supported by any fan server implementation.
Unclear if Cyan's server software still supports it.

.. _auth2cli_account_exists_reply:

Auth2Cli_AccountExistsReply
^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 48
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.
* **Account exists:** 1-byte unsigned int.
  Presumably a boolean.

Reply to an :ref:`AccountExistsRequest <cli2auth_account_exists_request>`
and similarly unused in practice.

.. _cli2auth_player_delete_request:

Cli2Auth_PlayerDeleteRequest
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 13
* **Transaction ID:** 4-byte unsigned int.
* **Player vault node ID:** 4-byte unsigned int.
  KI number of the avatar to be deleted.
  Must correspond to one of the avatars in the currently logged in account.

Delete an existing avatar.
Sent by the client when the player uses the "Delete Explorer" button on the avatar selection screen.

Deleting an avatar removes it from the account and allows its name to be reused for a new avatar.
Some other data related to the avatar is also deleted,
though the details of this depend on the server implementation.

Cyan's server software deletes only the avatar's :ref:`vault_node_player` vault node.
All other nodes belonging to the avatar remain in the vault,
most notably the :ref:`vault_node_player_info` node.
As a result,
the deletion isn't noticeable to other players ---
the deleted avatar will continue to appear in its neighborhood member list
and in other players' buddies/recent lists
(until the other player removes it).

MOSS and DIRTSAND delete the avatar's :ref:`vault_node_player_info` node,
removing it from all avatar lists in which it appears.
DIRTSAND doesn't delete any other vault nodes belonging to the avatar,
notably the :ref:`vault_node_player` node and its children.
MOSS thoroughly deletes all vault nodes under the :ref:`vault_node_player` node,
as well as any associated marker game data,
if they aren't referenced anywhere else.

.. _auth2cli_player_delete_reply:

Auth2Cli_PlayerDeleteReply
^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 17
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.

Reply to a :ref:`PlayerDeleteRequest <cli2auth_player_delete_request>`.

The result is usually one of:

* :cpp:enumerator:`kNetSuccess`
* :cpp:enumerator:`kNetErrPlayerNotFound`

.. _cli2auth_player_create_request:

Cli2Auth_PlayerCreateRequest
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 17
* **Transaction ID:** 4-byte unsigned int.
* **Player name:** :c:macro:`NET_MSG_FIELD_STRING`\(40).
  The avatar's in-game display name.
* **Avatar shape:** :c:macro:`NET_MSG_FIELD_STRING`\(260).
  Also known as "avatar dataset",
  or in practical terms,
  the avatar's gender.
  Either ``"female"`` or ``"male"``.
* **Friend invite code:** :c:macro:`NET_MSG_FIELD_STRING`\(260).
  A hex string invite code.
  Normally set to an empty string for no invite code.

Create a new avatar in the current account.
Sent by the client after the player selects an empty slot in the avatar selection screen
and enters all the necessary information.
The server will do roughly the following:

* Create :ref:`vault_node_player` and :ref:`vault_node_player_info` vault nodes for the new avatar,
  along with all appropriate child nodes.
  The ID of the new :ref:`vault_node_player` node serves as the avatar's KI number.
* Add the new :ref:`vault_node_player_info` node to the AllPlayersFolder
  (if the server supports/uses it).
* Create a Personal/Relto age instance for the new avatar,
  make the avatar the instance's owner,
  and add the avatar's AgesIOwnFolder to the Personal/Relto :ref:`vault_node_age` node.
* Find or create a default Neighborhood for the new avatar
  and make the avatar a member/owner of the instance.
* Add an entry in the table of avatars returned by :ref:`AcctPlayerInfo <auth2cli_acct_player_info>`
  (if the server tracks it separately from :ref:`vault_node_player` vault nodes, e. g. DIRTSAND).

The client only allows avatar names containing at least three non-space characters.
OpenUru clients also reject non-ASCII names.
If the client accepts the name,
it removes all leading and trailing whitespace and control characters,
non-space whitespace characters are replaced with spaces,
and sequences of two or more spaces are collapsed to a single space.

A friend invite code could be generated by another player using the ``/sendinvite`` command
(see :ref:`SendFriendInviteRequest <cli2auth_send_friend_invite_request>`).
The newly created avatar would then automatically start as a member of the inviter's neighborhood.
The client expects all invite codes to be in hex format
and will normalize some non-hex characters to hex
(``i`` and ``l`` to ``1``, ``o`` to ``0``).

No current shard supports generating friend invites anymore,
so in practice nothing useful can be entered in this field.
Since the MOULa 2022 Q1 update,
the invite code field has been completely removed from the avatar creation screen
(replaced by the start path choice)
and the client always sends an empty invite code.

The Cleft/Relto start path choice isn't passed as part of this message ---
the client instead writes it into a vault chronicle after avatar creation.

All of the newly created nodes have their ``CreatorAcct`` set to the current account's UUID
and their ``CreatorId`` to the new :ref:`vault_node_player` node ID.
The only exceptions are the new :ref:`vault_node_player` node itself,
whose ``CreatorId`` is set to 0,
and :ref:`vault_node_age` nodes and their children,
which have their ``CreatorAcct`` and ``CreatorId`` set as described in :ref:`VaultInitAgeRequest <cli2auth_vault_init_age_request>`.
The newly created nodes have the following structure and fields:

* :ref:`vault_node_player`:
  
  * ``Int32_1`` = **Disabled** = 0 (or unset for DIRTSAND)
  * ``Int32_2`` = **Explorer** = 1 (usually, or 0 if not a "paid" account --- see :ref:`account_flags`)
  * ``UInt32_1`` = **OnlineTime** = 0 (MOSS only?)
  * ``Uuid_1`` = **AccountUuid** = *the current account's UUID*
  * ``String64_1`` = **AvatarShapeName** = *avatar shape*
  * ``IString64_1`` = **PlayerName** = *player name*
  * Child nodes:
    
    * :ref:`vault_node_system` (the single System node)
    * :ref:`vault_node_player_info`: ``UInt32_1`` = **PlayerId** = *new Player node ID*, ``IString64_1`` = **PlayerName** = *player name*
    * :ref:`vault_node_folder`: ``Int32_1`` = **FolderType** = 1 (InboxFolder)
    * :ref:`vault_node_folder`: ``Int32_1`` = **FolderType** = 14 (AgeJournalsFolder)
    * :ref:`vault_node_player_info_list`: ``Int32_1`` = **FolderType** = 2 (BuddyListFolder)
    * :ref:`vault_node_player_info_list`: ``Int32_1`` = **FolderType** = 3 (IgnoreListFolder)
    * :ref:`vault_node_player_info_list`: ``Int32_1`` = **FolderType** = 4 (PeopleIKnowAboutFolder)
    * :ref:`vault_node_folder`: ``Int32_1`` = **FolderType** = 6 (ChronicleFolder)
    * :ref:`vault_node_folder`: ``Int32_1`` = **FolderType** = 7 (AvatarOutfitFolder)
    * :ref:`vault_node_folder`: ``Int32_1`` = **FolderType** = 25 (AvatarClosetFolder)
    * :ref:`vault_node_folder`: ``Int32_1`` = **FolderType** = 28 (PlayerInviteFolder)
    * :ref:`vault_node_age_info_list`: ``Int32_1`` = **FolderType** = 23 (AgesIOwnFolder)
      
      * :ref:`vault_node_age_link`: ``Blob_1`` = **SpawnPoints** = "Default:LinkInPointDefault:;"
        
        * :ref:`vault_node_age_info` (for the avatar's newly created Personal/Relto age instance)
      * :ref:`vault_node_age_link`: ``Blob_1`` = **SpawnPoints** = "Default:LinkInPointDefault:;"
        
        * :ref:`vault_node_age_info` (for the avatar's automatically assigned/created Neighborhood)
      * :ref:`vault_node_age_link`: ``Blob_1`` = **SpawnPoints** = "Ferry Terminal:LinkInPointFerry:;"
        
        * :ref:`vault_node_age_info` (for the public City/Ae'gura)
    * :ref:`vault_node_age_info_list`: ``Int32_1`` = **FolderType** = 24 (AgesICanVisitFolder)

The avatar's new Personal/Relto instance is created
as if by a :ref:`VaultInitAgeRequest <cli2auth_vault_init_age_request>`
with no instance and parent instance ID,
file name ``Personal``,
instance name ``Relto``,
user-defined name :samp:`{PlayerName}'s`,
description :samp:`{PlayerName}'s Relto`,
sequence number 0 (TODO Does Cyan's server software also do this?),
and language -1.

If there is an existing automatically created Neighborhood instance with less than 20 members
(DIRTSAND allows configuring this limit),
the new avatar is made a member/owner of that neighborhood.
If there is no neighborhood with room left,
then a new Neighborhood instance is created
as if by a :ref:`VaultInitAgeRequest <cli2auth_vault_init_age_request>`
with no instance and parent instance ID,
file name ``Neighborhood``,
description :samp:`{UserDefinedName} {InstanceName}`,
and language -1.

The instance and user-defined names of auto-created hoods
and the exact logic for assigning their sequence numbers
vary depending on the server implementation and shard:

* Cyan's server software uses the instance name ``Hood``
  and the user-defined name ``DRC``.
  Until October (?) 2021,
  it used the instance name ``Bevin``,
  but this was changed to ``Hood`` for lore accuracy reasons.
  Before this server-side update,
  there have been efforts to manually rename existing hoods from ``Bevin`` to ``Hood``,
  but this wasn't a complete fix
  as new hoods auto-created after the rename were named ``Bevin`` again.
  As a result,
  exising auto-created hoods from before the permanent fix
  may be named either ``Hood`` or ``Bevin``.
  Sequence numbers start at 0
  and seem to be tracked separately for each name combination,
  so e. g. there can be both a "DRC (123) Bevin" and "DRC (123) Hood".
* MOSS uses the instance name ``Bevin``,
  the user-defined name ``DRC``,
  and an empty description rather than ``DRC Bevin``.
  Sequence numbers start at 1
  and a new auto-created hood is assigned one sequence number higher than the highest existing one.
* DIRTSAND by default uses the instance name ``Neighborhood``
  and the user-defined name ``DS``,
  but both can be configured at compile time.
  For example,
  Gehn uses ``GoW`` as the user-defined name.
  Sequence numbers start at 1 and increment sequentially.

.. _auth2cli_player_create_reply:

Auth2Cli_PlayerCreateReply
^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 16
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.
* **Player vault node ID:** 4-byte unsigned int.
  KI number of the newly created avatar,
  or 0 if avatar creation failed.
* **Explorer:** 4-byte unsigned int.
  1 if the new avatar is a full explorer,
  or 0 if it's just a visitor
  (or if avatar creation failed).
* **Player name:** :c:macro:`NET_MSG_FIELD_STRING`\(40).
  The player name from the :ref:`PlayerCreateRequest <cli2auth_player_create_request>`,
  possibly adjusted by the server,
  or left empty if avatar creation failed.
* **Avatar shape:** :c:macro:`NET_MSG_FIELD_STRING`\(64).
  The avatar shape from the :ref:`PlayerCreateRequest <cli2auth_player_create_request>`,
  possibly adjusted by the server,
  or left empty if avatar creation failed.

Reply to a :ref:`PlayerCreateRequest <cli2auth_player_create_request>`.

The avatar name and shape are normally identical to those sent in the request,
but the server might have changed them,
e. g. to remove unexpected characters from the name
or to ensure that the avatar shape matches one of the two supported genders.

The result is usually one of:

* :cpp:enumerator:`kNetSuccess`
* :cpp:enumerator:`kNetErrPlayerAlreadyExists`: There is already another avatar with the same name.
* :cpp:enumerator:`kNetErrInvalidParameter`: The friend invite code is invalid.
* :cpp:enumerator:`kNetErrPlayerNameInvalid`: The server is unhappy with the avatar name.
* :cpp:enumerator:`kNetErrInviteNoMatchingPlayer`: The avatar associated with the friend invite code couldn't be found.
* :cpp:enumerator:`kNetErrInviteTooManyHoods`: The avatar associated with the friend invite code has too many hoods (?).
  Probably actually means too many members in the inviter's hood.

.. _cli2auth_upgrade_visitor_request:

Cli2Auth_UpgradeVisitorRequest
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 20
* **Transaction ID:** 4-byte unsigned int.
* **Player vault node ID:** 4-byte unsigned int.
  KI number of the avatar to be upgraded.
  Must correspond to a visitor avatar in the currently logged in account.

Upgrade an avatar from :ref:`visitor <visitor>` to :ref:`explorer <explorer>` status.

Automatically sent by OpenUru clients upon loading the avatar selection screen
if the account contains a visitor avatar despite having :cpp:var:`kBillingTypePaidSubscriber`.
This would happen during the GameTap era
when a player started playing on a free trial
and then switched to a paid subscription.

With MOULa being free to play,
all accounts are considered "paid" from the beginning
and there is no chance for the player to create a visitor avatar,
so this message is practically unused.
The H'uru client no longer has any support for visitor avatars,
including the automatic upgrade from visitor to explorer.
MOSS ignores this message,
and DIRTSAND doesn't support it at all.
Unclear if Cyan's server software still supports it.

.. _auth2cli_upgrade_visitor_reply:

Auth2Cli_UpgradeVisitorReply
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 18
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.

Reply to an :ref:`UpgradeVisitorRequest <cli2auth_upgrade_visitor_request>`.

.. _cli2auth_set_player_ban_status_request:

Cli2Auth_SetPlayerBanStatusRequest
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 21
* **Transaction ID:** 4-byte unsigned int.
* **Player vault node ID:** 4-byte unsigned int.
  KI number of the avatar whose ban status should be changed.
* **Banned:** 4-byte unsigned int.
  Presumably a boolean.

Implemented in the open-sourced client code,
but never actually used,
and not supported by any fan server implementation.
Unclear if Cyan's server software supports it.

.. _auth2cli_set_player_ban_status_reply:

Auth2Cli_SetPlayerBanStatusReply
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 19
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.

Reply to a :ref:`SetPlayerBanStatusRequest <cli2auth_set_player_ban_status_request>`
and similarly unused in practice.

.. _cli2auth_kick_player:

Cli2Auth_KickPlayer
^^^^^^^^^^^^^^^^^^^

* *Message type* = 22
* **Player vault node ID:** 4-byte unsigned int.
  KI number of the avatar to kick.

Implemented in the open-sourced client code,
but never actually used,
and not supported by any fan server implementation.
Unclear if Cyan's server software supports it.

.. _auth2cli_kicked_off:

Auth2Cli_KickedOff
^^^^^^^^^^^^^^^^^^

* *Message type* = 39
* **Reason:** 4-byte :cpp:enum:`ENetError`.
  Indicates why the player was kicked.

Sent by the server to tell the client why it's being disconnected.
The obvious use case is when a shard admin kicks the player in question,
but it's also used when disconnecting clients for other reasons
to display a more helpful message to players.

Implemented by Cyan's server software and MOSS,
but not DIRTSAND.

The reason is usually one of:

* :cpp:enumerator:`kNetErrLoggedInElsewhere`:
  Sent by Cyan's server software and MOSS
  when another client logs into the client's currently logged in account.
* :cpp:enumerator:`kNetErrKickedByCCR`

.. _cli2auth_change_player_name_request:

Cli2Auth_ChangePlayerNameRequest
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 23
* **Transaction ID:** 4-byte unsigned int.
* **Player vault node ID:** 4-byte unsigned int.
  KI number of the avatar to rename.
* **Player name:** :c:macro:`NET_MSG_FIELD_STRING`\(40).
  The avatar's new display name.

Implemented in the open-sourced client code,
but never actually used,
and not supported by any fan server implementation.
Unclear if Cyan's server software supports it.

.. _auth2cli_change_player_name_reply:

Auth2Cli_ChangePlayerNameReply
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 20
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.

Reply to a :ref:`ChangePlayerNameRequest <cli2auth_change_player_name_request>`
and similarly unused in practice.

.. _cli2auth_send_friend_invite_request:

Cli2Auth_SendFriendInviteRequest
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 24
* **Transaction ID:** 4-byte unsigned int.
* **Invite UUID:** 16-byte UUID.
  Identifies the player sending the invite.
  Randomly generated the first time an avatar sends a friend invite,
  afterwards it's stored in the vault
  and reused for all future invites sent from that avatar.
* **Receiver email address:** :c:macro:`NET_MSG_FIELD_STRING`\(64).
  Email address to which to send the friend invite.
* **Receiver name:** :c:macro:`NET_MSG_FIELD_STRING`\(40).
  Name of the friend who will receive the invite.
  If no receiver name is passed by the sender,
  the client defaults it to the string ``"Friend"``.

Send a friend invite code via email,
which may be used when creating a new avatar
(see :ref:`PlayerCreateRequest <cli2auth_player_create_request>`).
Sent by the client through the ``/sendinvite`` chat command.

No current shard supports generating (or using) friend invites anymore.
Cyan's server software always replies to this message with "Friend invites currently disabled.".
MOSS understands the message,
but also always replies with an error.
DIRTSAND doesn't implement it at all.

.. _auth2cli_send_friend_invite_reply:

Auth2Cli_SendFriendInviteReply
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 21
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.

Reply to a :ref:`SendFriendInviteRequest <cli2auth_send_friend_invite_request>`.

The result is usually one of:

* :cpp:enumerator:`kNetSuccess`
* :cpp:enumerator:`kNetErrNotSupported`:
  MOSS always returns this result.
* :cpp:enumerator:`kNetErrServiceForbidden`:
  Displayed by the client as "Friend invites are currently disabled.".
  Since MOULa,
  Cyan's server software always returns this result.

.. _cli2auth_vault_node_create:

Cli2Auth_VaultNodeCreate
^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 25
* **Transaction ID:** 4-byte unsigned int.
* **Node data length:** 4-byte unsigned int.
  Byte length of the following node data field.
  Can be at most 1 MiB.
* **Node data:** Variable-length byte array in the format described in :ref:`vault_node_network_format`.

Create a new vault node based on the given fields.
In general,
all fields sent by the client are stored as-is into the new vault node,
and all fields are optional and will be left unset if not set by the client.
The following fields have special behavior though:

* ``NodeId``: Initialized by the server to a new unused node ID.
  Ignored when set by the client.
* ``CreateTime``, ``ModifyTime``: Initialized by the server to the current time.
  Ignored when set by the client.
* ``CreatorAcct``, ``CreatorId``: Cyan's server software and MOSS always set these fields to the client's current account/avatar info,
  ignoring any values sent by the client.
  DIRTSAND uses whatever values the client sends,
  or zero if the client leaves them unset
  (which is always the case in practice).
* ``NodeType``: Should always be set.
  MOSS *requires* this field and replies with :cpp:enumerator:`kNetErrBadServerData` if left unset.
  DIRTSAND technically allows creating a node without a type.

.. _auth2cli_vault_node_created:

Auth2Cli_VaultNodeCreated
^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 23
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.
* **Node ID:** 4-byte unsigned int.
  ID of the newly created vault node.

Reply to a :ref:`VaultNodeCreate <cli2auth_vault_node_create>` message.

Upon receiving this message,
if the result is successful,
the client automatically sends a :ref:`VaultNodeFetch <cli2auth_vault_node_fetch>` message for the new node ID.

.. _cli2auth_vault_node_fetch:

Cli2Auth_VaultNodeFetch
^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 26
* **Transaction ID:** 4-byte unsigned int.
* **Node ID:** 4-byte unsigned int.
  ID of the vault node to fetch.

Retrieve the entire contents of a vault node by its ID.

.. _auth2cli_vault_node_fetched:

Auth2Cli_VaultNodeFetched
^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 24
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.
* **Node data length:** 4-byte unsigned int.
  Byte length of the following node data field.
  Can be at most 1 MiB.
  Set to 0 on error.
* **Node data:** Variable-length byte array in the format described in :ref:`vault_node_network_format`.

Reply to a :ref:`VaultNodeFetch <cli2auth_vault_node_fetch>` message.

The result is usually one of:

* :cpp:enumerator:`kNetSuccess`
* :cpp:enumerator:`kNetErrVaultNodeNotFound`: There is no vault node with the given ID.

.. _auth2cli_vault_node_changed:

Auth2Cli_VaultNodeChanged
^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 25
* **Node ID:** 4-byte unsigned int.
  ID of the vault node that changed.
* **Revision ID:** 16-byte UUID.
  As sent in the :ref:`VaultNodeSave <cli2auth_vault_node_save>` message by the client that performed the change.
  If the node change wasn't caused by a VaultNodeSave message,
  this may be any UUID that's different from the last revision ID sent by any client.
  The revision ID should never be all zeroes ---
  otherwise the change notification may be ignored by the open-sourced client code.

Notify the client about a change to a vault node.

This message is sent even for changes made by the client itself using :ref:`VaultNodeSave <cli2auth_vault_node_save>`.
Clients can detect self-caused change notifications using the revision ID field in both messages.

Not all clients are notified about every vault node change.
The exact rules for which clients are notified about which changes depend on the server.
Both MOSS and DIRTSAND notify each client about changes to its respective current player and age nodes,
as well as any of their child nodes.
MOSS additionally notifies all clients about changes to the system vault node.

.. _cli2auth_vault_node_save:

Cli2Auth_VaultNodeSave
^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 27
* **Transaction ID:** 4-byte unsigned int.
* **Node ID:** 4-byte unsigned int.
  ID of the vault node to update.
* **Revision ID:** 16-byte UUID.
  Sent to this and other clients as part of the :ref:`VaultNodeChanged <auth2cli_vault_node_changed>` message.
  Not stored permanently.
* **Node data length:** 4-byte unsigned int.
  Byte length of the following node data field.
  Can be at most 1 MiB.
* **Node data:** Variable-length byte array in the format described in :ref:`vault_node_network_format`.

Update the contents of an existing vault node.

In general,
all fields sent by the client are written into the vault node,
overwriting any existing values for the respective fields.
Fields *not* sent by the client are left unchanged,
i. e. remain unset or keep their existing values.
There is no way to explicitly unset a previously set field.

The following fields have special behavior:

* ``NodeId``: Should never be changed.
  OpenUru clients will never send changes for this field.
  MOSS theoretically allows changing it,
  whereas DIRTSAND ignores it when set by the client.
* ``CreateTime``: Should never be changed.
  OpenUru clients will never send changes for this field.
  Ignored by MOSS and DIRTSAND when set by the client.
* ``ModifyTime``: Automatically set by the server to the current time.
  Ignored when set by the client.
* ``CreatorAcct``, ``CreatorId``: Should never be changed.
  OpenUru clients will never send changes for these fields.
  MOSS and DIRTSAND theoretically allow changing them anyway.
* ``NodeType``: Always sent by the client,
  even though it should never be changed.
  Ignored by MOSS,
  whereas DIRTSAND theoretically allows changing it.
* ``String64_1``: For SDL nodes,
  H'uru clients always send this field even if it hasn't changed,
  because of an unspecified issue with Cyan's server software.

After the vault node has been changed,
the server sends a :ref:`VaultSaveNodeReply <auth2cli_vault_save_node_reply>` to the client that performed the change,
as well as :ref:`VaultNodeChanged <auth2cli_vault_node_changed>` messages to all clients for which the changed node is relevant.
The order of these messages can vary
(e. g. MOSS sends the reply before the change notifications,
but DIRTSAND does it the other way around).

.. _auth2cli_vault_save_node_reply:

Auth2Cli_VaultSaveNodeReply
^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 32
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.

Reply to a :ref:`VaultNodeSave <cli2auth_vault_node_save>` message.

.. _auth2cli_vault_node_deleted:

Auth2Cli_VaultNodeDeleted
^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 26
* **Node ID:** 4-byte unsigned int.
  ID of the vault node that was deleted.

Notify the client that a vault node has been deleted.

This message is practically unused.
Although the open-sourced client code fully supports it,
there's no situation where the server would send it,
because clients cannot delete vault nodes
(the corresponding Cli2Auth_VaultNodeDelete message is unimplemented in the client code).

MOSS and DIRTSAND never send this message,
and it's unclear if Cyan's server software still uses it.

.. _auth2cli_vault_node_added:

Auth2Cli_VaultNodeAdded
^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 27
* **Parent node ID:** 4-byte unsigned int.
* **Child node ID:** 4-byte unsigned int.
* **Owner node ID:** 4-byte unsigned int.

Notify the client about a newly added vault node relationship.

This message is sent even for changes made by the client itself using :ref:`Cli2Auth_VaultNodeAdd <cli2auth_vault_node_add>`.

Not all clients are notified about every new vault node relationship.
The rules are the same as for :ref:`VaultNodeChanged <auth2cli_vault_node_changed>` messages ---
if a client receives change notifications for a node,
then it also receives notifications for new relationships where that node is the parent.

.. _cli2auth_vault_node_add:

Cli2Auth_VaultNodeAdd
^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 29
* **Transaction ID:** 4-byte unsigned int.
* **Parent node ID:** 4-byte unsigned int.
  Node to which the child node should be added.
* **Child node ID:** 4-byte unsigned int.
  Node to be added under the parent node.
* **Owner node ID:** 4-byte unsigned int.
  KI number of the avatar adding the relationship,
  or 0 if it shouldn't/can't be associated with any particular avatar.

Add a new relationship between the given vault nodes.

After the relationship has been added,
the server sends a :ref:`VaultAddNodeReply <auth2cli_vault_add_node_reply>` to the client that performed the change,
as well as :ref:`VaultNodeAdded <auth2cli_vault_node_added>` messages to all clients for which the changed node is relevant.
The order of these messages can vary
(though currently both MOSS and DIRTSAND send the added notifications before the reply).

.. _auth2cli_vault_add_node_reply:

Auth2Cli_VaultAddNodeReply
^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 33
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.

Reply to a :ref:`VaultNodeAdd <cli2auth_vault_node_add>` message.

.. _auth2cli_vault_node_removed:

Auth2Cli_VaultNodeRemoved
^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 28
* **Parent node ID:** 4-byte unsigned int.
  Parent node of the relationship that was removed.
* **Child node ID:** 4-byte unsigned int.
  Child node of the relationship that was removed.

Notify the client that an existing vault node relationship was removed.

This message is sent even for changes made by the client itself using :ref:`Cli2Auth_VaultNodeRemove <cli2auth_vault_node_remove>`.

Not all clients are notified about every removed vault node relationship.
The rules are the same as for :ref:`VaultNodeChanged <auth2cli_vault_node_changed>` messages ---
if a client receives change notifications for a node,
then it also receives notifications for removed relationships where that node is the parent.

.. _cli2auth_vault_node_remove:

Cli2Auth_VaultNodeRemove
^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 30
* **Transaction ID:** 4-byte unsigned int.
* **Parent node ID:** 4-byte unsigned int.
  Parent node of the relationship to remove.
* **Child node ID:** 4-byte unsigned int.
  Child node of the relationship to remove.

Remove an existing relationship between the given vault nodes.
The vault nodes themselves are *not* deleted!
(Clients cannot fully delete vault nodes,
see :ref:`VaultNodeDeleted <auth2cli_vault_node_deleted>`.)

After the relationship has been removed,
the server sends a :ref:`VaultRemoveNodeReply <auth2cli_vault_remove_node_reply>` to the client that performed the change,
as well as :ref:`VaultNodeRemoved <auth2cli_vault_node_removed>` messages to all clients for which the changed node is relevant.
The order of these messages can vary
(though currently both MOSS and DIRTSAND send the removed notifications before the reply).

.. _auth2cli_vault_remove_node_reply:

Auth2Cli_VaultRemoveNodeReply
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 34
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.

Reply to a :ref:`VaultNodeRemove <cli2auth_vault_node_remove>` message.

.. _cli2auth_vault_fetch_node_refs:

Cli2Auth_VaultFetchNodeRefs
^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 31
* **Transaction ID:** 4-byte unsigned int.
* **Node ID:** 4-byte unsigned int.
  Top of the node tree whose relationships should be fetched.

Retrieve a list of all vault node refs under the given node ID,
i. e. all refs whose parent is that node ID or any of its children.

This message always recursively fetches the entire tree of refs.
There is no equivalent message for fetching just the refs directly under the node.

.. _auth2cli_vault_node_refs_fetched:

Auth2Cli_VaultNodeRefsFetched
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 29
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.
* **Ref count:** 4-byte unsigned int.
  May be at most 1048576.
* **Refs:** Variable-length array.
  All node refs that make up the tree under the requested node ID.
  Each element has the following structure:
  
  * **Parent node ID:** 4-byte unsigned int.
  * **Child node ID:** 4-byte unsigned int.
  * **Owner node ID:** 4-byte unsigned int.
  * **Seen:** 1-byte boolean.
    Meant to be used as an unread/read flag for user-visible vault node refs
    (i. e. KI mail).
    The client semi-ignores this field though and considers all refs unread all the time.
    No known server implementation persistently stores the seen status of refs.
    MOSS always sets this field to 0xcc (yes, really),
    DIRTSAND always to 0,
    and Cyan's server software sets it to unpredictable junk data
    (apparently always non-zero).

Reply to a :ref:`VaultFetchNodeRefs <cli2auth_vault_fetch_node_refs>` message.

.. _cli2auth_vault_init_age_request:

Cli2Auth_VaultInitAgeRequest
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 32
* **Transaction ID:** 4-byte unsigned int.
* **Instance ID:** 16-byte UUID.
  AgeInstanceGuid of the new :ref:`vault_node_age` and :ref:`vault_node_age_info` nodes.
  If this field is set to all zeroes,
  the server automatically generates a random AgeInstanceGuid.
  In practice,
  the open-sourced client code almost never relies on this behavior though ---
  it usually generates a random UUID itself if needed
  and sends that to the server.
  One case where the client does send an all-zeroes instance ID is when linking to a child age that doesn't exist yet.
* **Parent instance ID:** 16-byte UUID.
  ParentAgeInstanceGuid of the new :ref:`vault_node_age` and :ref:`vault_node_age_info` nodes.
  If this field is set to all zeroes,
  the ParentAgeInstanceGuid will be left unset.
* **File name:** :c:macro:`NET_MSG_FIELD_STRING`\(260).
  AgeName of the new :ref:`vault_node_age` node
  and AgeFilename of the new :ref:`vault_node_age_info` node.
  This field must never be empty.
* **Instance name:** :c:macro:`NET_MSG_FIELD_STRING`\(260).
  AgeInstanceName of the new :ref:`vault_node_age_info` node.
  If this field is empty,
  the AgeInstanceName field will be left unset.
* **User-defined name:** :c:macro:`NET_MSG_FIELD_STRING`\(260).
  AgeUserDefinedName of the new :ref:`vault_node_age_info` node.
  If this field is empty,
  the AgeUserDefinedName field will be left unset.
* **Description:** :c:macro:`NET_MSG_FIELD_STRING`\(1024).
  AgeDescription of the new :ref:`vault_node_age_info` node.
  If this field is empty,
  the AgeDescription field will be left unset.
* **Sequence number:** 4-byte signed int.
  AgeSequenceNumber of the new :ref:`vault_node_age_info` node.
  In practice,
  the client always sets this field to 0.
  If this field is negative,
  DIRTSAND automatically assigns a free sequence number,
  otherwise it stores the requested sequence number as-is.
  MOSS ignores this field and instead changes behavior depending on the age:
  when creating a DRC Neighborhood or a BahroCave or LiveBahroCaves instance,
  it chooses the next free sequence number (starting at 1),
  otherwise it sets the sequence number to 0.
  (TODO What does Cyan's server software do?
  It seems to automatically assign sequence numbers
  even if the client sends 0.)
* **Language:** 4-byte signed int.
  AgeLanguage of the new :ref:`vault_node_age_info` node.
  In practice,
  the client always sets this field to -1.
  MOSS ignores this field and instead always sets AgeLanguage to -1.

Create a new age instance in the vault,
if a matching one doesn't exist already.

If the instance ID is not all zeroes
and there is already an :ref:`vault_node_age`/:ref:`vault_node_age_info` node pair
with a matching instance ID and file name,
the server replies with the IDs of these nodes
and doesn't create a new instance.

DIRTSAND ignores the file name and matches only on the instance ID,
but this makes no difference in practice,
because random UUID collisions are extremely unlikely.

If the parent instance ID is not all zeroes,
MOSS ignores the instance ID and instead uses the *parent* instance ID to look for an existing instance.
This ensures that within a single parent instance,
there can only ever be at most one child/sub-age instance of the same age.

If no matching existing instance was found,
the server creates a new :ref:`vault_node_age` node,
a corresponding :ref:`vault_node_age_info` node,
and all appropriate child nodes.
All of the newly created nodes have their ``CreatorAcct`` set to the instance ID
and their ``CreatorId`` to the new :ref:`vault_node_age` node ID
(except for the new :ref:`vault_node_age` node itself,
whose ``CreatorId`` is set to 0).

The newly created nodes have the following structure and fields:

* :ref:`vault_node_age`:
  
  * ``Uuid_1`` = **AgeInstanceGuid** = *instance ID*
  * ``Uuid_2`` = **ParentAgeInstanceGuid** = *parent instance ID*
  * ``String64_1`` = **AgeName** = *file name*
  * Child nodes:
    
    * :ref:`vault_node_system` (the single System node)
    * :ref:`vault_node_age_info`:
      
      * ``Int32_1`` = **AgeSequenceNumber** = *sequence number*
      * ``Int32_2`` = **Public** = 0 (DIRTSAND only, others leave it unset)
      * ``Int32_3`` = **AgeLanguage** = *language*
      * ``UInt32_1`` = **AgeId** = *new Age node ID*
      * ``UInt32_2`` = **AgeCzarId** = 0
      * ``UInt32_3`` = **AgeInfoFlags** = 0
      * ``Uuid_1`` = **AgeInstanceGuid** = *instance ID*
      * ``Uuid_2`` = **ParentAgeInstanceGuid** = *parent instance ID*
      * ``String64_2`` = **AgeFilename** = *file name*
      * ``String64_3`` = **AgeInstanceName** = *instance name*
      * ``String64_4`` = **AgeUserDefinedName** = *user-defined name*
      * ``Text_1`` = **AgeDescription** = *description*
      * Child nodes:
        
        * :ref:`vault_node_sdl`: ``Int32_1`` = **SDLIdent** = 0, ``String64_1`` = **SDLName** = *file name*, ``Blob_1`` = **SDLData** = *default state data record* (DIRTSAND only, others leave it unset)
        * :ref:`vault_node_player_info_list`: ``Int32_1`` = **FolderType** = 19 (AgeOwnersFolder)
        * :ref:`vault_node_player_info_list`: ``Int32_1`` = **FolderType** = 18 (CanVisitFolder)
        * :ref:`vault_node_age_info_list`: ``Int32_1`` = **FolderType** = 31 (ChildAgesFolder)
    * :ref:`vault_node_player_info_list`: ``Int32_1`` = **FolderType** = 4 (PeopleIKnowAboutFolder)
    * :ref:`vault_node_folder`: ``Int32_1`` = **FolderType** = 6 (ChronicleFolder)
    * :ref:`vault_node_age_info_list`: ``Int32_1`` = **FolderType** = 9 (SubAgesFolder)
    * :ref:`vault_node_folder`: ``Int32_1`` = **FolderType** = 15 (AgeDevicesFolder)

.. _auth2cli_vault_init_age_reply:

Auth2Cli_VaultInitAgeReply
^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 30
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.
* **Age node ID:** 4-byte unsigned int.
  ID of the newly created :ref:`vault_node_age` node,
  or 0 if age instance creation failed.
* **Age info node ID:** 4-byte unsigned int.
  ID of the newly created :ref:`vault_node_age_info` node,
  or 0 if age instance creation failed.

Reply to a :ref:`VaultInitAgeRequest <cli2auth_vault_init_age_request>`.

.. _cli2auth_vault_node_find:

Cli2Auth_VaultNodeFind
^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 33
* **Transaction ID:** 4-byte unsigned int.
* **Template node data length:** 4-byte unsigned int.
  Byte length of the following node data field.
  Can be at most 1 MiB.
* **Template node data:** Variable-length byte array in the format described in :ref:`vault_node_network_format`.

Search for vault nodes whose field values match the given template node.
For a node to match,
it must have all fields set that are set in the template mode
and they must have exactly equal values,
except for ``IString64_1`` and ``IString64_2``,
which are compared case-insensitively.
Any fields not set in the template node are ignored and don't affect the match.

In practice,
the open-sourced client code only uses this message for one purpose:
finding a :ref:`vault_node_player_info` node by the ID of its corresponding :ref:`vault_node_player` node,
i. e. looking up an avatar by its KI number.
In this case,
the template node always has its ``NodeType`` set to 23 (PlayerInfo),
the ``UInt32_1`` field (PlayerId) set to the desired KI number,
and all other fields unset.

MOSS places certain restrictions on the template node
to disallow some overly broad find operations:

* The template node must always have its ``NodeType`` field set,
  due to :ref:`its internal database structure <moss_vault>`.
* ``CreateTime`` and ``ModifyTime`` fields in the template node are silently ignored.
* The template node must have at least one field other than the above set,
  i. e. one cannot find all nodes of a single type with no other restrictions.

DIRTSAND only requires that the template node has at least one field set
and otherwise allows arbitrary find operations.
(TODO What does Cyan's server software do?)

.. _auth2cli_vault_node_find_reply:

Auth2Cli_VaultNodeFindReply
^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 31
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.
* **Found node ID count:** 4-byte unsigned int.
  May be at most 512.
* **Found node IDs:** Variable-length array of 4-byte unsigned ints.

Reply to a :ref:`VaultNodeFind <cli2auth_vault_node_find>` message.

The result is usually one of:

* :cpp:enumerator:`kNetSuccess`
* :cpp:enumerator:`kNetErrInternalError`:
  Sent by DIRTSAND when the template node has no fields set.
* :cpp:enumerator:`kNetErrVaultNodeNotFound`:
  Sent by MOSS if no matching nodes were found.
  DIRTSAND sends :cpp:enumerator:`kNetSuccess` in this case instead.
  (TODO What does Cyan's server software do?)
* :cpp:enumerator:`kNetErrServiceForbidden`:
  Sent by MOSS when the template node doesn't fulfill the requirements described above.

.. _cli2auth_vault_set_seen:

Cli2Auth_VaultSetSeen
^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 34
* **Parent node ID:** 4-byte unsigned int.
  Parent node of the node ref to set as seen.
* **Child node ID:** 4-byte unsigned int.
  Child node of the node ref to set as seen.
* **Seen:** 1-byte boolean.
  1 to set the node ref as seen
  or 0 to set it as unseen.

Change a vault node ref's seen status.

In practice,
the open-sourced client code never sends this message,
because unread message handling is incomplete and somewhat broken.
As a result,
no known fan server implementation supports this message.
Cyan's server software seems to ignore it,
or at least doesn't update the seen status properly
(see :ref:`VaultNodeRefsFetched <auth2cli_vault_node_refs_fetched>` for details).

.. _cli2auth_vault_send_node:

Cli2Auth_VaultSendNode
^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 35
* **Node ID:** 4-byte unsigned int.
  ID of the node to send.
* **Receiver ID:** 4-byte unsigned int.
  KI number of the avatar to send the node to.

Send a node to another avatar.
This creates a new node ref with the receiver's inbox as the parent,
the sent node ID as the child,
and the current avatar's KI number as the owner.

.. _cli2auth_age_request:

Cli2Auth_AgeRequest
^^^^^^^^^^^^^^^^^^^

* *Message type* = 36
* **Transaction ID:** 4-byte unsigned int.
* **File name:** :c:macro:`NET_MSG_FIELD_STRING`\(64).
  Internal file name of the age to join.
* **Instance UUID:** 16-byte UUID.
  Identifies the specific age instance to join.

Request all necessary information to join the game server for the given age instance.

.. _auth2cli_age_reply:

Auth2Cli_AgeReply
^^^^^^^^^^^^^^^^^

* *Message type* = 35
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.
* **MCP ID:** 4-byte unsigned int.
  The client sends this ID to the game server to identify the age instance to join.
* **Instance UUID:** 16-byte UUID.
  In practice,
  this seems to be always identical to the instance UUID previously sent by the client,
  although the open-sourced client code can apparently handle the server returning a different UUID.
* **Age vault node ID:** 4-byte unsigned int.
  ID of the :ref:`vault_node_age` vault node for the age instance.
  The open-sourced client code also accepts 0 for no age vault.
* **Server IP address:** 4-byte packed IPv4 address.
  The game server for the age instance.

Reply to an :ref:`AgeRequest <cli2auth_age_request>`.
Upon receiving this message,
if the result is successful,
the client connects to the instance's game server
and sends it a :ref:`cli2game_join_age_request`.

The result is usually one of:

* :cpp:enumerator:`kNetSuccess`
* :cpp:enumerator:`kNetErrVaultNodeNotFound`: For some reason,
  the open-sourced client code considers this a success.

.. _cli2auth_propagate_buffer:

Cli2Auth_PropagateBuffer
^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 40
* **Class index:** 4-byte unsigned int.
  :cpp:class:`plCreatable` class index of the message stored in the following buffer.
  Must be one of :cpp:class:`plNetMessage`'s subclasses.
* **Buffer length:** 4-byte unsigned int.
  Byte length of the following buffer field.
  Can be at most 1 MiB.
* **Buffer:** Variable-length byte array.
  The serialized message,
  in the format produced by ``plNetMessage::PokeBuffer``
  and understood by ``plNetMessage::PeekBuffer``.
  The class index in the serialized buffer must match the one in the class index field.

Transmits a serialized :cpp:class:`plNetMessage` from the client to the server.
Implemented in the open-sourced client code,
but never actually used,
and not supported by any fan server implementation.
Unclear if Cyan's server software supports it.
All :cpp:class:`plNetMessage`\s are sent via the game server instead ---
see :ref:`cli2game_propagate_buffer`.

.. _auth2cli_propagate_buffer:

Auth2Cli_PropagateBuffer
^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 38

Identical message format as :ref:`cli2auth_propagate_buffer`
(except for the type),
but sent from the server to the client.
Similarly unused in practice.
All :cpp:class:`plNetMessage`\s are sent via the game server instead ---
see :ref:`game2cli_propagate_buffer`.

.. _cli2auth_get_public_age_list:

Cli2Auth_GetPublicAgeList
^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 41
* **Transaction ID:** 4-byte unsigned int.
* **Age file name:** :c:macro:`NET_MSG_FIELD_STRING`\(64).

Request information about the public instances of an age.
This is used by the Nexus to get the list of public neighborhoods
and the current population counts for neighborhoods and single-instance public ages.

.. _auth2cli_public_age_list:

Auth2Cli_PublicAgeList
^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 40
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.
* **Age instance count:** 4-byte unsigned int.
  Element count for the following array of age instances.
  May be at most 512,
  but in practice,
  all server implementations return at most 50 age instances.
* **Age instances:** Variable-length array.
  Information about all public instances of the requested age.
  Unless indicated otherwise,
  this information is taken from the :ref:`vault_node_age_info` vault nodes of the age instances in question.
  The elements are sorted by the ``ModifyTime`` of their :ref:`vault_node_age_info` vault nodes,
  with the most recently modified ones appearing first
  (meaning that the age instances that were most recently set to public appear first in the list).
  Each element has the following structure:
  
  * **Instance UUID:** 16-byte UUID.
  * **File name:** 128-byte zero-terminated UTF-16 string.
    Should always match the age file name sent in the :ref:`GetPublicAgeList <cli2auth_get_public_age_list>` message.
  * **Instance name:** 128-byte zero-terminated UTF-16 string.
  * **User-defined name:** 128-byte zero-terminated UTF-16 string.
  * **Description:** 2048-byte zero-terminated UTF-16 string.
  * **Sequence number:** 4-byte signed int.
  * **Language:** 4-byte signed int.
  * **Owner count:** 4-byte unsigned int.
    How many owners this age instance has.
    The open-sourced client code calls this the "population",
    because in the case of neighborhoods,
    this is the number of owners.
  * **Current population:** 4-byte unsigned int.
    How many avatars are currently in the age instance.

Reply to a :ref:`GetPublicAgeList <cli2auth_get_public_age_list>` message.

.. _cli2auth_set_age_public:

Cli2Auth_SetAgePublic
^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 42
* **Age info node ID:** 4-byte unsigned int.
  ID of the :ref:`vault_node_age_info` vault node of the age instance to be made public/private.
* **Public:** 1-byte boolean.
  True if the age instance should be set to public,
  or false if it should be set to private.

Make an age instance public or private.
The client uses this only for neighborhoods ---
there is no support for other player-managed public age instances.

Internally,
this sets the :ref:`vault_node_age_info` node's ``Int32_2`` (IsPublic) field
and updates the node's ``ModifyTime``,
the same way as a :ref:`VaultNodeSave <cli2auth_vault_node_save>` message.
H'uru clients rely on the fact that a SetAgePublic message always updates the ``ModifyTime``,
even if the public/private status is set to the same value as before.

The server doesn't directly reply to this message,
but the vault node change causes a :ref:`VaultNodeChanged <auth2cli_vault_node_changed>` message,
which the client uses to detect that the age instance's public/private status actually changed.

.. _cli2auth_log_python_traceback:

Cli2Auth_LogPythonTraceback
^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 43
* **Traceback text:** :c:macro:`NET_MSG_FIELD_STRING`\(1024).
  The Python traceback and exception info in plain text form.

Sent by the client when a Python exception is raised and never handled.

.. _cli2auth_log_stack_dump:

Cli2Auth_LogStackDump
^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 44
* **Stack dump text:** :c:macro:`NET_MSG_FIELD_STRING`\(1024).
  The crash stack trace in plain text form.

Sent by the client when a crash (usually an access violation) occurs in native code.
Such crashes are fatal,
so the client will disconnect after sending this message.

.. _cli2auth_log_client_debugger_connect:

Cli2Auth_LogClientDebuggerConnect
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 45
* **Nothing:** 4-byte unsigned int.
  Always set to 0.

Sent by H'uru-based :ref:`external clients <internal_external_client>` upon detecting that a debugger was connected.
The client automatically exits after sending this message.
Since 2020,
OpenUru-based clients have this debugger trap disabled by default,
unless the macro ``PLASMA_EXTERNAL_NODEBUGGER`` is defined.

.. _cli2auth_score_create:

Cli2Auth_ScoreCreate
^^^^^^^^^^^^^^^^^^^^

* *Message type* = 46
* **Transaction ID:** 4-byte unsigned int.
* **Owner ID:** 4-byte unsigned int.
  Vault node ID of the thing that the score belongs to.
  May be a :ref:`vault_node_player_info` ID (KI number) for a score owned by an avatar,
  a :ref:`vault_node_age_info` ID for a score belonging to an age instance,
  or 0 for a global score.
* **Game name:** :c:macro:`NET_MSG_FIELD_STRING`\(64).
  The "game" to which the score belongs.
  The following names are currently used:
  
  * :samp:`GreatZeroCalibration_{i}` (fixed): Great Zero calibration mission times.
    :samp:`{i}` is the number of the calibration mission,
    as a decimal index counting from 0
    (always 2 digits,
    with leading 0 if necessary).
    Only used by H'uru clients since 2015.
    OpenUru clients and older H'uru clients save the times as :ref:`chronicles <vault_node_chronicle>` in the vault instead.
  * ``HeekPoints`` (accumulative allowing subtraction): Ayoheek points.
  * ``PelletDrop`` (accumulative): Er'cana pellet points.
* **Game type:** 4-byte unsigned int.
  Indicates how the game scores are counted.
  The following types are currently defined:
  
  * Fixed = 0: A normal high score.
    Despite the name,
    a fixed score's value *can* be changed after creation,
    but it doesn't support the other operations that accumulative scores have.
  * Accumulative = 1: A running total score that can have points added after creation.
    Points can also be transferred from one accumulative score to another,
    which reduces the source score's value again.
    Other than that,
    it's impossible to subtract points or set the score's value directly.
    DIRTSAND calls this type "Football".
  * Accumulative allowing subtraction = 2: A running total score that can have points added or subtracted after creation.
    Although the score's value can't be set directly like a fixed score,
    it can still be changed to any value by adding or subtracting points as needed.
    DIRTSAND calls this type "Golf".
* **Points:** 4-byte signed int.
  The score's value.

.. _auth2cli_score_create_reply:

Auth2Cli_ScoreCreateReply
^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 41
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.
* **Score ID:** 4-byte unsigned int.
  ID of the newly created score.
* **Creation time:** 4-byte unsigned int.
  Unix timestamp when the score was created
  (i. e. roughly the current time).
  Ignored by the client.

Reply to a :ref:`ScoreCreate <cli2auth_score_create>` message.

The result is usually one of:

* :cpp:enumerator:`kNetSuccess`
* :cpp:enumerator:`kNetErrScoreWrongType`: Sent by MOSS if the game type isn't supported.
* :cpp:enumerator:`kNetErrScoreAlreadyExists`: The owner already has a score for this game.

.. _cli2auth_score_delete:

Cli2Auth_ScoreDelete
^^^^^^^^^^^^^^^^^^^^

* *Message type* = 47
* **Transaction ID:** 4-byte unsigned int.
* **Score ID:** 4-byte unsigned int.
  ID of the score to delete.

Delete a previously created score.
Implemented in the open-sourced client code,
but never actually used,
and not supported by any fan server implementation.
Unclear if Cyan's server software supports it.

.. _auth2cli_score_delete_reply:

Auth2Cli_ScoreDeleteReply
^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 42
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.

Reply to a :ref:`ScoreDelete <cli2auth_score_delete>` message
and similarly unused in practice.

.. _cli2auth_score_get_scores:

Cli2Auth_ScoreGetScores
^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 48
* **Transaction ID:** 4-byte unsigned int.
* **Owner ID:** 4-byte unsigned int.
  Vault node ID of the thing for which to get the score,
  as originally passed to :ref:`ScoreCreate <cli2auth_score_create>`.
* **Game name:** :c:macro:`NET_MSG_FIELD_STRING`\(64).
  The "game" to which the score belongs,
  as originally passed to :ref:`ScoreCreate <cli2auth_score_create>`.

Retrieve all information about the given owner's scores for a game.
Despite the plural in the name,
this should only ever return a single score or none at all,
because it's impossible to create multiple scores with the same game and owner.

.. _auth2cli_score_get_scores_reply:

Auth2Cli_ScoreGetScoresReply
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 43
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.
* **Score count:** 4-byte unsigned int.
  Should always be either 0 or 1,
  because there's no way to create multiple scores for the same game and owner.
* **Score data length:** 4-byte unsigned int.
  Byte length of the following score data field.
  Can be at most 1 MiB.
* **Score data:** Variable-length array.
  Each element has the following structure:
  
  * **Score ID:** 4-byte unsigned int.
  * **Owner ID:** 4-byte unsigned int.
  * **Creation time:** 4-byte unsigned int.
  * **Game type:** 4-byte unsigned int.
  * **Points:** 4-byte signed int.
  * **Game name byte count:** 4-byte unsigned int.
    Byte length of the following game name field.
  * **Game name:** Variable-length, zero-terminated UTF-16 string.
    (The zero terminator is stored explicitly and included in the byte count.)

Reply to a :ref:`ScoreGetScores <cli2auth_score_get_scores>` message.

The result is usually one of:

* :cpp:enumerator:`kNetSuccess`
* :cpp:enumerator:`kNetErrInternalError`:
  Sent by MOSS if more than one matching score was found.
  DIRTSAND doesn't consider that an error,
  even though it should normally never happen.
  (TODO What does Cyan's server software do?)
* :cpp:enumerator:`kNetErrScoreNoDataFound`:
  Sent by MOSS if no matching scores were found.
  DIRTSAND sends :cpp:enumerator:`kNetSuccess` (with count 0) in this case instead.
  (TODO What does Cyan's server software do?)

.. _cli2auth_score_add_points:

Cli2Auth_ScoreAddPoints
^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 49
* **Transaction ID:** 4-byte unsigned int.
* **Score ID:** 4-byte unsigned int.
  ID of the score to modify.
  The score's type must be one of the two accumulative types ---
  fixed scores can only be updated using :ref:`ScoreSetPoints <cli2auth_score_set_points>`.
* **Points difference:** 4-byte signed int.
  Number of points to add to the current score value.
  If the score is of type "accumulative allow negative",
  this value may be negative to subtract points,
  otherwise it must be positive.

Modify an existing accumulative score by adding or subtracting points.

.. _auth2cli_score_add_points_reply:

Auth2Cli_ScoreAddPointsReply
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 44
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.

Reply to a :ref:`ScoreAddPoints <cli2auth_score_add_points>` message.

The result is usually one of:

* :cpp:enumerator:`kNetSuccess`
* :cpp:enumerator:`kNetErrScoreWrongType`: The ID refers to a fixed score,
  which can't have points added/subtracted.
  MOSS also sends this when trying to subtract points from an accumulative score that doesn't allow subtraction.
  DIRTSAND allows this and sends :cpp:enumerator:`kNetSuccess` in that case,
  but silently sets the score's value to 0 if it would have become negative.
* :cpp:enumerator:`kNetErrScoreNoDataFound`: There is no score with the given ID.

.. _cli2auth_score_transfer_points:

Cli2Auth_ScoreTransferPoints
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 50
* **Transaction ID:** 4-byte unsigned int.
* **Source score ID:** 4-byte unsigned int.
  ID of the score from which to transfer points.
  The score's type must be one of the two accumulative types.
* **Destination score ID:** 4-byte unsigned int.
  ID of the score to which to transfer points.
  The score's type must be one of the two accumulative types.
* **Points to transfer:** 4-byte signed int.
  The number of points to transfer.
  May be negative to transfer points from the destination to the source score.
  DIRTSAND considers this field an unsigned int
  and doesn't support transferring a negative amount of points.

Transfer a certain amount of points from one accumulative score to another.
This is used to implement uploading personal pellet scores to neighborhoods.

The client can theoretically transfer a negative amount of points,
which transfers points in the reverse direction
(from the destination to the source).
This isn't used in practice though
and fan servers only support it inconsistently.
One can get the same result more reliably
by transferring a positive amount of points with the source and destination swapped.

.. _auth2cli_score_transfer_points_reply:

Auth2Cli_ScoreTransferPointsReply
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 45
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.

Reply to a :ref:`ScoreTransferPoints <cli2auth_score_transfer_points>` message.

The result is usually one of:

* :cpp:enumerator:`kNetSuccess`
* :cpp:enumerator:`kNetErrScoreWrongType`: One or both score IDs refer to a fixed score.
  Also sent by MOSS if the number of points is negative,
  but one or both score IDs don't allow subtraction.
  (DIRTSAND doesn't support negative score transfers at all.)
  MOSS mistakenly sends :cpp:enumerator:`kNetErrScoreNoDataFound` instead of this result.
* :cpp:enumerator:`kNetErrScoreNotEnoughPoints`: Tried to transfer more points than the source score currently has.
  DIRTSAND allows this though if the source score allows subtraction,
  in which case the transfer will make the source score go negative.
  MOSS allows any transfer as long as it doesn't change the sign of the source score.
* :cpp:enumerator:`kNetErrScoreNoDataFound`: One or both score IDs don't exist.
  MOSS mistakenly sends :cpp:enumerator:`kNetErrScoreWrongType` instead of this result.

.. _cli2auth_score_set_points:

Cli2Auth_ScoreSetPoints
^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 51
* **Transaction ID:** 4-byte unsigned int.
* **Score ID:** 4-byte unsigned int.
  ID of the score to modify.
  Must be a fixed score ---
  accumulative scores can only be modified using :ref:`ScoreAddPoints <cli2auth_score_add_points>` or :ref:`ScoreTransferPoints <cli2auth_score_transfer_points>`.
* **Points:** 4-byte signed int.
  The score's new value.

Set an existing fixed score to a new value.
Not supported by MOSS.

.. _auth2cli_score_set_points_reply:

Auth2Cli_ScoreSetPointsReply
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 46
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.

Reply to a :ref:`ScoreSetPoints <cli2auth_score_set_points>` message.

The result is usually one of:

* :cpp:enumerator:`kNetSuccess`
* :cpp:enumerator:`kNetErrScoreWrongType`: The ID refers to an accumulative score,
  whose value can't be set directly.
* :cpp:enumerator:`kNetErrScoreNoDataFound`: There is no score with the given ID.

.. _cli2auth_score_get_ranks:

Cli2Auth_ScoreGetRanks
^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 52
* **Transaction ID:** 4-byte unsigned int.
* **Owner ID:** 4-byte unsigned int.
* **Score group:** 4-byte unsigned int.
* **Parent folder ID:** 4-byte unsigned int.
* **Game name:** :c:macro:`NET_MSG_FIELD_STRING`\(64).
* **Time period:** 4-byte unsigned int.
* **Result count:** 4-byte unsigned int.
* **Page number:** 4-byte unsigned int.
* **Sort order:** 4-byte unsigned int.
  0 if the returned ranks should be sorted in ascending order
  or 1 for descending order.

Implemented in the open-sourced client code,
but never actually used,
and not supported by any fan server implementation.
Unclear if Cyan's server software supports it.

H'uru clients and DIRTSAND implement a ScoreGetHighScores message as an extension,
which has a similar purpose as this message presumably had,
but is overall simpler.

.. _auth2cli_score_get_ranks_reply:

Auth2Cli_ScoreGetRanksReply
^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 47
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.
* **Rank count:** 4-byte unsigned int.
* **Rank data length:** 4-byte unsigned int.
  Byte length of the following score data field.
  Can be at most 1 MiB.
* **Rank data:** Variable-length array.
  Each element has the following structure:
  
  * **Rank:** 4-byte unsigned int.
    Presumably the rank of this score on the leaderboard.
  * **Score:** 4-byte signed int.
    The score's value.
  * **Name byte count:** 4-byte unsigned int.
    Byte length of the following name field.
  * **Name:** Variable-length, zero-terminated UTF-16 string.
    (The zero terminator is stored explicitly and included in the byte count.)
    Presumably the name of the player who owns this score.

Reply to a :ref:`ScoreGetRanks <auth2cli_score_get_ranks_reply>` message
and similarly unused in practice.

.. _auth2cli_server_caps:

Auth2Cli_ServerCaps
^^^^^^^^^^^^^^^^^^^

* *Message type* = 0x1002
* **Capabilities byte count:** 4-byte unsigned int.
  Byte length of the following capabilities field.
* **Capabilities:** Variable-length byte array containing a :cpp:class:`hsBitVector`.
  A set of bit flags describing whether the server does or doesn't support certain features.
  Clients should ignore any capability flags that they don't understand.
  The following features have capability flags defined:
  
  * **Score leaderboards** = 1 << 0: The ScoreGetHighScores message.
    Only supported by DIRTSAND.
    Assumed unsupported by default.
  * **Game manager blue spiral** = 1 << 1: :ref:`Game manager <game_manager>` support for the door puzzle in the neighborhood garden ages
    (Eder Delin and Eder Tsogahl).
    Supported by Cyan's server software and MOSS.
    Assumed supported by default.
  * **Game manager climbing wall** = 1 << 2: :ref:`Game manager <game_manager>` support for the Gahreesen wall
    (not used in the current implementation of the wall).
    Not supported by MOSS or DIRTSAND.
    Unclear if Cyan's server software supports it.
    Assumed unsupported by default.
  * **Game manager Heek** = 1 << 3: :ref:`Game manager <game_manager>` support for Ayoheek.
    Supported by Cyan's server software and MOSS.
    Assumed supported by default.
  * **Game manager marker** = 1 << 4: :ref:`Game manager <game_manager>` support for marker games.
    Supported by Cyan's server software and MOSS.
    Assumed supported by default.
  * **Game manager Tic-Tac-Toe** = 1 << 5: :ref:`Game manager <game_manager>` support for Tic-Tac-Toe
    (apparently a test game,
    only used by console commands in OpenUru clients).
    Only supported by Cyan's server software.
    Assumed supported by default.
  * **Game manager VarSync** = 1 << 6: :ref:`Game manager <game_manager>` support for VarSync
    (used for the Ahnonay detector puzzles).
    Supported by Cyan's server software and MOSS.
    Assumed supported by default.

May be sent by the server in response to a :ref:`ClientRegisterRequest <cli2auth_client_register_request>`
(along with the main :ref:`ClientRegisterReply <auth2cli_client_register_reply>` message)
to inform the client about the server's supported feature set.
If the client doesn't receive this message,
it assumes a default feature set that matches Cyan's server software
(see the capabilities field above for a list of these defaults).

This message is a H'uru extension.
It's only sent by DIRTSAND versions since 2018
and only recognized by H'uru clients since 2017.
Cyan's server software and MOSS never send this message.
OpenUru clients and older H'uru clients don't support this message
and will fail to connect to a server that sends it.
