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

Message types in *italics* are completely unused in any open-source MOUL(a) code.
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
   2,:ref:`ClientSetCCRLevel <cli2auth_client_set_ccr_level>`,,

.. csv-table:: Account
   :name: auth_messages_account
   :header: #,Cli2Auth,Auth2Cli,#
   :widths: auto
   
   3,:ref:`AcctLoginRequest <cli2auth_acct_login_request>`,:ref:`AcctPlayerInfo <auth2cli_acct_player_info>`,6
   ,,:ref:`AcctLoginReply <auth2cli_acct_login_reply>`,4
   4,*AcctSetEulaVersion*,,
   5,*AcctSetDataRequest*,*AcctData*,5
   6,:ref:`AcctSetPlayerRequest <cli2auth_acct_set_player_request>`,:ref:`AcctSetPlayerReply <auth2cli_acct_set_player_reply>`,7
   7,:ref:`AcctCreateRequest <cli2auth_acct_create_request>`,:ref:`AcctCreateReply <auth2cli_acct_create_reply>`,8
   8,:ref:`AcctChangePasswordRequest <cli2auth_acct_change_password_request>`,:ref:`AcctChangePasswordReply <cli2auth_acct_change_password_reply>`,9
   9,:ref:`AcctSetRolesRequest <cli2auth_acct_set_roles_request>`,:ref:`AcctSetRolesReply <auth2cli_acct_set_roles_reply>`,10
   10,:ref:`AcctSetBillingTypeRequest <cli2auth_acct_set_billing_type_request>`,:ref:`AcctSetBillingTypeReply <auth2cli_acct_set_billing_type_reply>`,11
   11,:ref:`AcctActivateRequest <cli2auth_acct_activate_request>`,:ref:`AcctActivateReply <auth2cli_acct_activate_reply>`,12
   12,:ref:`AcctCreateFromKeyRequest <cli2auth_acct_create_from_key_request>`,:ref:`AcctCreateFromKeyReply <auth2cli_acct_create_from_key_reply>`,13
   53,:ref:`AccountExistsRequest <cli2auth_account_exists_request>`,:ref:`AccountExistsReply <auth2cli_account_exists_reply>`,48

.. csv-table:: Player
   :name: auth_messages_player
   :header: #,Cli2Auth,Auth2Cli,#
   :widths: auto
   
   ,,*PlayerList*,14
   13,:ref:`PlayerDeleteRequest <cli2auth_player_delete_request>`,:ref:`PlayerDeleteReply <auth2cli_player_delete_reply>`,17
   14,*PlayerUndeleteRequest*,,
   15,*PlayerSelectRequest*,,
   16,*PlayerRenameRequest*,,
   17,:ref:`PlayerCreateRequest <cli2auth_player_create_request>`,:ref:`PlayerCreateReply <auth2cli_player_create_reply>`,16
   18,*PlayerSetStatus*,,
   19,*PlayerChat*,*PlayerChat*,15
   20,:ref:`UpgradeVisitorRequest <cli2auth_upgrade_visitor_request>`,:ref:`UpgradeVisitorReply <auth2cli_upgrade_visitor_reply>`,18
   21,:ref:`SetPlayerBanStatusRequest <cli2auth_set_player_ban_status_request>`,:ref:`SetPlayerBanStatusReply <auth2cli_set_player_ban_status_reply>`,19
   22,:ref:`KickPlayer <cli2auth_kick_player>`,KickedOff,39
   23,ChangePlayerNameRequest,ChangePlayerNameReply,20

.. csv-table:: Friends
   :name: auth_messages_friends
   :header: #,Cli2Auth,Auth2Cli,#
   :widths: auto
   
   24,SendFriendInviteRequest,SendFriendInviteReply,21
   ,,*FriendNotify*,22

.. csv-table:: Vault
   :name: auth_messages_vault
   :header: #,Cli2Auth,Auth2Cli,#
   :widths: auto
   
   25,VaultNodeCreate,VaultNodeCreated,23
   26,VaultNodeFetch,VaultNodeFetched,24
   27,VaultNodeSave,VaultNodeChanged,25
   ,,VaultSaveNodeReply,32
   28,VaultNodeDelete,VaultNodeDeleted,26
   29,VaultNodeAdd,VaultNodeAdded,27
   ,,VaultAddNodeReply,33
   30,VaultNodeRemove,VaultNodeRemoved,28
   ,,VaultRemoveNodeReply,34
   31,VaultFetchNodeRefs,VaultNodeRefsFetched,29
   32,VaultInitAgeRequest,VaultInitAgeReply,30
   33,VaultNodeFind,VaultNodeFindReply,31
   34,VaultSetSeen,,
   35,VaultSendNode,,

.. csv-table:: Ages
   :name: auth_messages_ages
   :header: #,Cli2Auth,Auth2Cli,#
   :widths: auto
   
   36,AgeRequest,AgeReply,35

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
   
   40,PropagateBuffer,PropagateBuffer,38

.. csv-table:: Public ages
   :name: auth_messages_public_ages
   :header: #,Cli2Auth,Auth2Cli,#
   :widths: auto
   
   41,GetPublicAgeList,PublicAgeList,40
   42,SetAgePublic,,

.. csv-table:: Log messages
   :name: auth_messages_log_messages
   :header: #,Cli2Auth,Auth2Cli,#
   :widths: auto
   
   43,LogPythonTraceback,,
   44,LogStackDump,,
   45,LogClientDebuggerConnect,,

.. csv-table:: Score
   :name: auth_messages_score
   :header: #,Cli2Auth,Auth2Cli,#
   :widths: auto
   
   46,ScoreCreate,ScoreCreateReply,41
   47,ScoreDelete,ScoreDeleteReply,42
   48,ScoreGetScores,ScoreGetScoresReply,43
   49,ScoreAddPoints,ScoreAddPointsReply,44
   50,ScoreTransferPoints,ScoreTransferPointsReply,45
   51,ScoreSetPoints,ScoreSetPointsReply,46
   52,ScoreGetRanks,ScoreGetRanksReply,47

.. csv-table:: H'uru extensions
   :name: auth_messages_h_uru_extensions
   :header: #,Cli2Auth,Auth2Cli,#
   :widths: auto
   
   0x1000,AgeRequestEx,AgeReplyEx,0x1000
   0x1001,ScoreGetHighScores,ScoreGetHighScoresReply,0x1001
   ,,ServerCaps,0x1002

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
* **Server IP address:** 4-byte unsigned int.
  This is an IPv4 address in packed integer form instead of the more common "dotted quad" format.
  For example,
  the address 184.73.198.22 would be represented as the integer 0xb849c616 (= 3091842582 in decimal).
  Keep in mind that Uru uses little-endian byte order,
  so the address will be in reverse order compared to "network byte order" (big-endian).
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
However,
it *doesn't* delete the avatar's vault node and other related data,
so the deleted avatar will continue to appear in its neighborhood member list
and in other players' buddies/recent lists until deleted.
In general,
there's no way for other players to tell that the avatar has been deleted.

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

The client only allows avatar names containing at least three non-space characters.
OpenUru clients also reject non-ASCII names.
If the client accepts the name,
it removes all leading and trailing whitespace and control characters,
non-space whitespace characters are replaced with spaces,
and sequences of two or more spaces are collapsed to a single space.

A friend invite code could be generated by another player using the ``/sendinvite`` command.
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
