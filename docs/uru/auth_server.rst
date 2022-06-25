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

.. csv-table:: Global
   :header: #,Cli2Auth,Auth2Cli,#
   :widths: auto
   
   0,:ref:`PingRequest <cli2auth_ping_request>`,:ref:`PingReply <auth2cli_ping_reply>`,0
   ,,:ref:`ServerAddr <auth2cli_server_addr>`,1
   ,,:ref:`NotifyNewBuild <auth2cli_notify_new_build>`,2

.. csv-table:: Client
   :header: #,Cli2Auth,Auth2Cli,#
   :widths: auto
   
   1,:ref:`ClientRegisterRequest <cli2auth_client_register_request>`,:ref:`ClientRegisterReply <auth2cli_client_register_reply>`,3
   2,:ref:`ClientSetCCRLevel <cli2auth_client_set_ccr_level>`,,

.. csv-table:: Account
   :header: #,Cli2Auth,Auth2Cli,#
   :widths: auto
   
   3,:ref:`AcctLoginRequest <cli2auth_acct_login_request>`,:ref:`AcctPlayerInfo <auth2cli_acct_player_info>`,6
   ,,:ref:`AcctLoginReply <auth2cli_acct_login_reply>`,4
   4,AcctSetEulaVersion,,
   5,AcctSetDataRequest,AcctData,5
   6,AcctSetPlayerRequest,AcctSetPlayerReply,7
   7,AcctCreateRequest,AcctCreateReply,8
   8,AcctChangePasswordRequest,AcctChangePasswordReply,9
   9,AcctSetRolesRequest,AcctSetRolesReply,10
   10,AcctSetBillingTypeRequest,AcctSetBillingTypeReply,11
   11,AcctActivateRequest,AcctActivateReply,12
   12,AcctCreateFromKeyRequest,AcctCreateFromKeyReply,13
   53,AccountExistsRequest,AccountExistsReply,48

.. csv-table:: Player
   :header: #,Cli2Auth,Auth2Cli,#
   :widths: auto
   
   ,,PlayerList,14
   13,PlayerDeleteRequest,PlayerDeleteReply,17
   14,PlayerUndeleteRequest,,
   15,PlayerSelectRequest,,
   16,PlayerRenameRequest,,
   17,PlayerCreateRequest,PlayerCreateReply,16
   18,PlayerSetStatus,,
   19,PlayerChat,PlayerChat,15
   20,UpgradeVisitorRequest,UpgradeVisitorReply,18
   21,SetPlayerBanStatusRequest,SetPlayerBanStatusReply,19
   22,KickPlayer,KickedOff,39
   23,ChangePlayerNameRequest,ChangePlayerNameReply,20

.. csv-table:: Friends
   :header: #,Cli2Auth,Auth2Cli,#
   :widths: auto
   
   24,SendFriendInviteRequest,SendFriendInviteReply,21
   ,,FriendNotify,22

.. csv-table:: Vault
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
   :header: #,Cli2Auth,Auth2Cli,#
   :widths: auto
   
   36,AgeRequest,AgeReply,35

.. csv-table:: File-related
   :header: #,Cli2Auth,Auth2Cli,#
   :widths: auto
   
   37,FileListRequest,FileListReply,36
   38,FileDownloadRequest,FileDownloadChunk,37
   39,FileDownloadChunkAck,,

.. csv-table:: Game
   :header: #,Cli2Auth,Auth2Cli,#
   :widths: auto
   
   40,PropagateBuffer,PropagateBuffer,38

.. csv-table:: Public ages
   :header: #,Cli2Auth,Auth2Cli,#
   :widths: auto
   
   41,GetPublicAgeList,PublicAgeList,40
   42,SetAgePublic,,

.. csv-table:: Log messages
   :header: #,Cli2Auth,Auth2Cli,#
   :widths: auto
   
   43,LogPythonTraceback,,
   44,LogStackDump,,
   45,LogClientDebuggerConnect,,

.. csv-table:: Score
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
   :header: #,Cli2Auth,Auth2Cli,#
   :widths: auto
   
   0x1000,AgeRequestEx,AgeReplyEx,0x1000
   0x1001,ScoreGetHighScores,ScoreGetHighScoresReply,0x1001
   ,,ServerCaps,0x1002

.. _cli2auth_ping_request:

Cli2Auth_PingRequest
^^^^^^^^^^^^^^^^^^^^

* **Ping time:** 4-byte unsigned int.
* **Transaction ID:** 4-byte unsigned int.
* **Payload byte count:** 4-byte unsigned int.
* **Payload:** Variable-length.

See :ref:`ping` for details.

.. _auth2cli_ping_reply:

Auth2Cli_PingReply
^^^^^^^^^^^^^^^^^^

* **Ping time:** 4-byte unsigned int.
* **Transaction ID:** 4-byte unsigned int.
* **Payload byte count:** 4-byte unsigned int.
* **Payload:** Variable-length.

See :ref:`ping` for details.

.. _auth2cli_server_addr:

Auth2Cli_ServerAddr
^^^^^^^^^^^^^^^^^^^

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
this is meant for when there are multiple auth server behind a load balancer,
to allow the client to reconnect directly to the same auth server as before.
No current MOULa shard is large enough to require such a setup,
so this message currently has no practical use.
MOSS nonetheless sends a ServerAddr message to all clients
(in response to the :ref:`ClientRegisterRequest <cli2auth_client_register_request>`)
with the constant token UUID ``8ac671cb-9fd0-4376-9ecb-310c211ae6a4``.
DIRTSAND doesn't use ServerAddr messages at all.
(TODO: What does Cyan's server software do?)

.. _auth2cli_notify_new_build:

Auth2Cli_NotifyNewBuild
^^^^^^^^^^^^^^^^^^^^^^^

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

* **Build ID:** 4-byte unsigned int.
  The client's :ref:`build ID <build_id>`.

Sent by the client immediately after connecting to the auth server
(before even the automatic :ref:`PingRequest <cli2auth_ping_request>`).

DIRTSAND will disconnect clients that send an unexpected build ID.
MOSS doesn't check the build ID here.
(TODO: What does Cyan's server software do?)
If the server is happy with the build ID,
it replies immediately with a :ref:`ClientRegisterReply <auth2cli_client_register_reply>`.

.. _auth2cli_client_register_reply:

Auth2Cli_ClientRegisterReply
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

* **Transaction ID:** 4-byte unsigned int.
* **Client challenge:** 4-byte unsigned int.
  Randomly generated by the client,
  or set to 0 if unused
  (see below).
* **Account name:** :c:macro:`NET_MSG_FIELD_STRING`\(64).
  The account name entered by the user in the login dialog.
  May be overridden using the command-line setting ``screenname``
  (in GameTap-style syntax, see below).
* **Challenge hash:** :c:macro:`NET_MSG_FIELD_STRING`\(40).
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

Password hash
'''''''''''''

The client supports two different ways of hashing the password.
They are referred to as "SHA-1" and "SHA-0" after the hash algorithms they are based on,
but both password hashing methods actually perform extra steps on top of plain SHA-0/SHA-1.

"SHA-1"
    The password is encoded as UTF-8 (H'uru) or the ANSI code page (OpenUru) and hashed using SHA-1.
    In the resulting hash,
    every group of 4 bytes is byte-swapped
    (as if the hash was a 5-element array of 4-byte ints).
"SHA-0"
    The password is concatenated with the account name.
    All ASCII letters in the account name are converted to lowercase.
    The last character of the account name and password (respectively) is replaced with U+0000.
    The resulting string is encoded as UTF-16 (little-endian) and hashed using SHA-0.

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
otherwise it is set to all zeroes.
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

* **Transaction ID:** 4-byte unsigned int.
* **Player int (?):** 4-byte unsigned int.
* **Player name:** :c:macro:`NET_MSG_FIELD_STRING`\(40).
* **Avatar shape:** :c:macro:`NET_MSG_FIELD_STRING`\(64).
* **Explorer:** 4-byte unsigned int.

.. _auth2cli_acct_login_reply:

Auth2Cli_AcctLoginReply
^^^^^^^^^^^^^^^^^^^^^^^

* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte unsigned int.
* **Account ID:** 16-byte UUID.
* **Account flags:** 4-byte unsigned int.
* **Billing type:** 4-byte unsigned int.
* **notthedroids encryption key:** 4-element array of 4-byte unsigned ints.
