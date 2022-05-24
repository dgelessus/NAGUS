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
   0,PingRequest,PingReply,0
   ,,ServerAddr,1
   ,,NotifyNewBuild,2
   ,*Client*,,
   1,ClientRegisterRequest,ClientRegisterReply,3
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
