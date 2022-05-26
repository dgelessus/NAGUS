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

The overview table below isn't *strictly* sorted by message type number.
I've moved a few entries
so that related messages are grouped together
and request/reply pairs align better.

.. csv-table::
   :header: #,Cli2Auth,Auth2Cli,#
   :widths: auto
   
   ,*Global*,,
   0,:ref:`PingRequest <cli2auth_ping_request>`,:ref:`PingReply <auth2cli_ping_reply>`,0
   ,,:ref:`ServerAddr <auth2cli_server_addr>`,1
   ,,:ref:`NotifyNewBuild <auth2cli_notify_new_build>`,2
   ,*Client*,,
   1,:ref:`ClientRegisterRequest <cli2auth_client_register_request>`,:ref:`ClientRegisterReply <auth2cli_client_register_reply>`,3
   2,ClientSetCCRLevel,,
   ,*Account*,,
   3,AcctLoginRequest,AcctLoginReply,4
   4,AcctSetEulaVersion,,
   5,AcctSetDataRequest,AcctData,5
   ,,AcctPlayerInfo,6
   6,AcctSetPlayerRequest,AcctSetPlayerReply,7
   7,AcctCreateRequest,AcctCreateReply,8
   8,AcctChangePasswordRequest,AcctChangePasswordReply,9
   9,AcctSetRolesRequest,AcctSetRolesReply,10
   10,AcctSetBillingTypeRequest,AcctSetBillingTypeReply,11
   11,AcctActivateRequest,AcctActivateReply,12
   12,AcctCreateFromKeyRequest,AcctCreateFromKeyReply,13
   53,AccountExistsRequest,AccountExistsReply,48
   ,*Player*,,
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
   ,*Friends*,,
   24,SendFriendInviteRequest,SendFriendInviteReply,21
   ,,FriendNotify,22
   ,*Vault*,,
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
   ,*Ages*,,
   36,AgeRequest,AgeReply,35
   ,*File-related*,,
   37,FileListRequest,FileListReply,36
   38,FileDownloadRequest,FileDownloadChunk,37
   39,FileDownloadChunkAck,,
   ,*Game*,,
   40,PropagateBuffer,PropagateBuffer,38
   ,*Public ages*,,
   41,GetPublicAgeList,PublicAgeList,40
   42,SetAgePublic,,
   ,*Log messages*,,
   43,LogPythonTraceback,,
   44,LogStackDump,,
   45,LogClientDebuggerConnect,,
   ,*Score*,,
   46,ScoreCreate,ScoreCreateReply,41
   47,ScoreDelete,ScoreDeleteReply,42
   48,ScoreGetScores,ScoreGetScoresReply,43
   49,ScoreAddPoints,ScoreAddPointsReply,44
   50,ScoreTransferPoints,ScoreTransferPointsReply,45
   51,ScoreSetPoints,ScoreSetPointsReply,46
   52,ScoreGetRanks,ScoreGetRanksReply,47
   ,*H'uru extensions*,,
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
