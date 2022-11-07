.. index:: game server
   single: server; game
   single: GameSrv
   :name: game_server

Game server
===========

Provides communication within a single age instance
by relaying Plasma messages over the network.

.. index:: game manager
   single: GameMgr
   :name: game_manager

The game server also provides the "game manager" (GameMgr),
a different mechanism used for some multiplayer activities,
like Ayoheek, marker games, and the hood garden age puzzle.
To reduce complexity of the server side,
the H'uru client has moved away from using the game manager
and the DIRTSAND server has never implemented it.
The OpenUru client continues to use the game manager
and the necessary server support is implemented in MOSS and Cyan's server software.

There can theoretically be multiple game server instances,
but in practice all MOULa servers use a single game server for all age instances.

Messages
--------

.. csv-table:: Game server messages
   :name: game_messages
   :header: #,Cli2Game,Game2Cli,#
   :widths: auto
   
   0,:ref:`PingRequest <cli2game_ping_request>`,:ref:`PingReply <game2cli_ping_reply>`,0
   1,:ref:`JoinAgeRequest <cli2game_join_age_request>`,:ref:`JoinAgeReply <game2cli_join_age_reply>`,1
   2,:ref:`PropagateBuffer <cli2game_propagate_buffer>`,:ref:`PropagateBuffer <game2cli_propagate_buffer>`,2
   3,GameMgrMsg,GameMgrMsg,3

.. _cli2game_ping_request:

Cli2Game_PingRequest
^^^^^^^^^^^^^^^^^^^^

* *Message type* = 0
* **Ping time:** 4-byte unsigned int.

See :ref:`ping` for details.

.. _game2cli_ping_reply:

Game2Cli_PingReply
^^^^^^^^^^^^^^^^^^

* *Message type* = 0
* **Ping time:** 4-byte unsigned int.

See :ref:`ping` for details.

.. _cli2game_join_age_request:

Cli2Game_JoinAgeRequest
^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 1
* **Transaction ID:** 4-byte unsigned int.
* **MCP ID:** 4-byte unsigned int.
  Identifies the age instance to join.
  This value must be obtained from an :ref:`auth2cli_age_reply`.
* **Account ID:** 16-byte UUID.
  ID of the account that owns the avatar joining the age.
* **Player vault node ID:** 4-byte unsigned int.
  KI number of the avatar joining the age.

Request to join the given age instance using the specified avatar.
Sent by the client as part of the linking process,
immediately after connecting to the game server.

.. _game2cli_join_age_reply:

Game2Cli_JoinAgeReply
^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 1
* **Transaction ID:** 4-byte unsigned int.
* **Result:** 4-byte :cpp:enum:`ENetError`.

Reply to a :ref:`JoinAgeRequest <cli2game_join_age_request>`.
Upon receiving this message,
if the result is successful,
the client fetches the entire tree of vault nodes under the age instance's :ref:`vault_node_age` node
(whose node ID was previously sent to the client in the :ref:`auth2cli_age_reply`)
and then begins loading the age.

.. _cli2game_propagate_buffer:

Cli2Game_PropagateBuffer
^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 2
* **Class index:** 4-byte unsigned int.
  ``plCreatable`` class index of the message stored in the following buffer.
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
See :ref:`pl_net_messages` for details on the different kinds of messages that are sent this way.

.. _game2cli_propagate_buffer:

Game2Cli_PropagateBuffer
^^^^^^^^^^^^^^^^^^^^^^^^

Identical message type and format as :ref:`cli2game_propagate_buffer`,
but sent from the server to the client.

.. _pl_net_messages:

:cpp:class:`plNetMessage`\s
---------------------------

Most communication with the game server
(and, indirectly, with other clients)
happens using serialized :cpp:class:`plNetMessage` objects,
which are wrapped in :ref:`cli2game_propagate_buffer`/:ref:`game2cli_propagate_buffer` when sent to/from the game server.

The different :cpp:class:`plNetMessage` subclasses are identified by their ``plCreatable`` class index.
Unlike the :ref:`lower-level message protocol <messages>`,
:cpp:class:`plNetMessage`\s aren't strictly separated by communication direction.
Many message types are in fact sent in both directions between client and server,
but others are only supposed to go in one direction.
In all cases,
the class index uniquely identifies the message class with no further context.

Below is an overview of the :cpp:class:`plNetMessage` class hierarchy in the open-sourced client code,
along with the corresponding class indices and the intended message direction.
Classes marked as "abstract" are only used as base classes ---
a message should never be a direct instance of one of these classes,
only of one of their non-abstract subclasses.
Classes marked as "unused" are fully defined in the open-sourced client code,
but never actually used by the client
and not supported by MOSS or DIRTSAND
(it's unknown if Cyan's server software supports them).

* :cpp:class:`plNetMessage` = 0x025e = 606 (abstract)
  
  * :cpp:class:`plNetMsgRoomsList` = 0x0263 = 611 (abstract)
    
    * :cpp:class:`plNetMsgPagingRoom` = 0x0218 = 536 (client -> server)
    * :cpp:class:`plNetMsgGameStateRequest` = 0x0265 = 613 (client -> server)
  * :cpp:class:`plNetMsgObject` = 0x0268 = 616 (abstract)
    
    * :cpp:class:`plNetMsgStreamedObject` = 0x027b = 635 (abstract)
      
      * :cpp:class:`plNetMsgSharedState` = 0x027c = 636 (abstract)
        
        * :cpp:class:`plNetMsgTestAndSet` = 0x027d = 637 (client -> server)
      * :cpp:class:`plNetMsgSDLState` = 0x02cd = 717 (client <-> server)
        
        * :cpp:class:`plNetMsgSDLStateBCast` = 0x0329 = 809 (client <-> server)
    * :cpp:class:`plNetMsgGetSharedState` = 0x027e = 638 (client -> server, unused)
    * :cpp:class:`plNetMsgObjStateRequest` = 0x0286 = 646 (client -> server, unused)
  * :cpp:class:`plNetMsgStream` = 0x026c = 620 (abstract)
    
    * :cpp:class:`plNetMsgGameMessage` = 0x026b = 619 (client <-> server)
      
      * :cpp:class:`plNetMsgGameMessageDirected` = 0x032e = 814 (client <-> server)
      * :cpp:class:`plNetMsgLoadClone` = 0x03b3 = 947 (client <-> server)
  * :cpp:class:`plNetMsgVoice` = 0x0279 = 633 (client <-> server)
  * :cpp:class:`plNetMsgObjectUpdateFilter` = 0x029d = 669 (client -> server, not handled by MOSS or DIRTSAND)
  * :cpp:class:`plNetMsgMembersListReq` = 0x02ad = 685 (client -> server)
  * :cpp:class:`plNetMsgServerToClient` = 0x02b2 = 690 (abstract)
    
    * :cpp:class:`plNetMsgGroupOwner` = 0x0264 = 612 (server -> client)
    * :cpp:class:`plNetMsgMembersList` = 0x02ae = 686 (server -> client)
    * :cpp:class:`plNetMsgMemberUpdate` = 0x02b1 = 689 (server -> client)
    * :cpp:class:`plNetMsgInitialAgeStateSent` = 0x02b8 = 696 (server -> client)
  * :cpp:class:`plNetMsgListenListUpdate` = 0x02c8 = 712 (client <-> server, unused, but client theoretically handles it)
  * :cpp:class:`plNetMsgRelevanceRegions` = 0x03ac = 940 (client -> server)
  * :cpp:class:`plNetMsgPlayerPage` = 0x03b4 = 948 (client -> server)

Common data types
^^^^^^^^^^^^^^^^^

.. index:: SafeString
   single: safe string
   :name: safe_string

.. object:: SafeString
   
   * **Count:** 2-byte unsigned int.
     Number of 8-bit characters in the string.
     The high 4 bits of this field are masked out when reading and should always be set when writing.
     As a result,
     a single SafeString can contain at most 4095 characters.
   * **Ignored:** 2-byte unsigned int.
     Only present if the count field has none of its high 4 bits set.
     The open-sourced client code calls this a "backward compat hack" that should have been removed in July 2003.
   * **String:** Variable-length string of 8-bit characters.
     If the first character has its high bit set,
     then the string is obfuscated by bitwise negating every character,
     otherwise the string is stored literally.
     When writing,
     the open-sourced client code always uses this obfuscation.
     None of the characters should be 0.

.. index:: SafeWString
   single: safe string; wide
   :name: safe_w_string

.. object:: SafeWString
   
   * **Count:** 2-byte unsigned int.
     Number of UTF-16 code units in the string.
     The high 4 bits of this field are masked out when reading and should always be set when writing.
     As a result,
     a single SafeWString can contain at most 4095 UTF-16 code units.
   * **String:** Variable-length string of UTF-16 code units.
     The string is obfuscated by bitwise negating every code unit.
     (Unlike with non-wide SafeStrings,
     there is no support for un-obfuscated SafeWStrings.)
     None of the characters should be 0.
   * **Terminator:** 2-byte unsigned int.
     Should always be 0.
     This string terminator is stored in the data,
     but not counted in the count field.

.. cpp:class:: hsBitVector
   
   * **Count:** 4-byte unsigned int.
     Element count for the following array.
   * **Bit vector:** Variable-length array of 4-byte unsigned ints.
     The contents of the bit vector,
     grouped into 4-byte units,
     with the first element containing the least significant bits
     and the last one the most significant bits.

.. cpp:class:: plUnifiedTime
   
   * **Seconds:** 4-byte unsigned int.
     Unix timestamp (seconds since 1970).
   * **Microseconds:** 4-byte unsigned int.
     Fractional part of the timestamp for sub-second precision.

.. cpp:class:: plLocation
   
   * **Sequence number:** 4-byte unsigned int.
   * **Flags:** 2-byte unsigned int.
     See :cpp:enum:`LocFlags` for details.
   
   .. cpp:enum:: LocFlags
      
      .. cpp:enumerator:: kLocalOnly = 1 << 0
      .. cpp:enumerator:: kVolatile = 1 << 1
      .. cpp:enumerator:: kReserved = 1 << 2
      .. cpp:enumerator:: kBuiltIn = 1 << 3
      .. cpp:enumerator:: kItinerant = 1 << 4

.. cpp:class:: plNetGroupId
   
   * **ID:** 6-byte :cpp:class:`plLocation`.
   * **Flags:** 1-byte unsigned int.
     See :cpp:enum:`NetGroupConstants` for details.
   
   .. cpp:enum:: NetGroupConstants
      
      .. cpp:enumerator:: kNetGroupConstant = 1 << 0
      .. cpp:enumerator:: kNetGroupLocal = 1 << 1

.. cpp:class:: plLoadMask
   
   * **Quality and capability:** 1-byte unsigned int.
     Decoded as follows
     (where *qc* is the value of this field)
     into separate quality and capability fields,
     each of which is a 1-byte unsigned int after decoding:
     
     * **Quality** = (*qc* >> 4 & 0xf) | 0xf0
     * **Capability** = (*qc* >> 0 & 0xf) | 0xf0
   
   .. cpp:var:: static const plLoadMask kAlways
      
      Has both quality and capability set to 0xff.

.. cpp:class:: plUoid
   
   * **Flags:** 1-byte unsigned int.
     See :cpp:enum:`ContentsFlags` for details.
   * **Location:** 6-byte :cpp:class:`plLocation`.
   * **Load mask:** 1-byte :cpp:class:`plLoadMask`.
     Only present if the :cpp:enumerator:`~ContentsFlags::kHasLoadMask` flag is set,
     otherwise defaults to :cpp:var:`plLoadMask::kAlways`.
   * **Class type:** 2-byte unsigned int.
   * **Object ID:** 4-byte unsigned int.
   * **Object name:** :ref:`SafeString <safe_string>`.
   * **Clone ID:** 2-byte unsigned int.
     Only present if the :cpp:enumerator:`~ContentsFlags::kHasCloneIDs` flag is set,
     otherwise defaults to 0.
   * **Ignored:** 2-byte unsigned int.
     Only present if the :cpp:enumerator:`~ContentsFlags::kHasCloneIDs` flag is set.
   * **Clone player ID:** 4-byte unsigned int.
     Only present if the :cpp:enumerator:`~ContentsFlags::kHasCloneIDs` flag is set,
     otherwise defaults to 0.
   
   .. cpp:enum:: ContentsFlags
      
      .. cpp:enumerator:: kHasCloneIDs = 1 << 0
      .. cpp:enumerator:: kHasLoadMask = 1 << 1

.. cpp:class:: plClientGuid : public plCreatable
   
   * **Flags:** 2-byte unsigned int.
     See :cpp:enum:`Flags` for details.
   * **Account UUID:** 16-byte UUID.
     Only present if the :cpp:enumerator:`~Flags::kAccountUUID` flag is set.
     Always unset in practice and not used by client or servers.
     Unclear if Cyan's server software does anything with it.
   * **Player ID:** 4-byte unsigned int.
     Only present if the :cpp:enumerator:`~Flags::kPlayerID` flag is set.
     The avatar's KI number.
   * **Temp player ID:** 4-byte unsigned int.
     Only present if the :cpp:enumerator:`~Flags::kTempPlayerID` flag is set.
     Always unset in practice and not used by fan servers.
     Unclear if Cyan's server software does anything with it.
     The open-sourced client code treats this identically to the regular player ID field.
   * **Player name length:** 2-byte unsigned int.
     Only present if the :cpp:enumerator:`~Flags::kPlayerName` flag is set.
     Byte count for the following player name.
   * **Player name:** Variable-length byte string.
     Only present if the :cpp:enumerator:`~Flags::kPlayerName` flag is set.
     The avatar's display name.
   * **CCR level:** 1-byte unsigned int.
     Only present if the :cpp:enumerator:`~Flags::kCCRLevel` flag is set.
     The avatar's current CCR level.
     MOSS hardcodes this field to 0,
     whereas DIRTSAND doesn't set it at all.
   * **Protected login:** 1-byte boolean.
     Only present if the :cpp:enumerator:`~Flags::kProtectedLogin` flag is set.
     Always unset in practice and not used by client or servers.
     Unclear if Cyan's server software does anything with it.
   * **Build type:** 1-byte unsigned int.
     Only present if the :cpp:enumerator:`~Flags::kBuildType` flag is set.
     Always unset in practice and not used by client or servers.
     Unclear if Cyan's server software does anything with it.
   * **Source IP address:** 4-byte packed IPv4 address.
     Only present if the :cpp:enumerator:`~Flags::kSrcAddr` flag is set.
     Always unset in practice and not used by client or servers.
     Unclear if Cyan's server software does anything with it.
   * **Source port:** 2-byte unsigned int.
     Only present if the :cpp:enumerator:`~Flags::kSrcPort` flag is set.
     Always unset in practice and not used by client or servers.
     Unclear if Cyan's server software does anything with it.
   * **Reserved:** 1-byte boolean.
     Only present if the :cpp:enumerator:`~Flags::kReserved` flag is set.
     Always unset in practice and not used by client or servers.
     Unclear if Cyan's server software does anything with it.
   * **Client key length:** 2-byte unsigned int.
     Only present if the :cpp:enumerator:`~Flags::kClientKey` flag is set.
     Byte count for the following client key.
   * **Client key:** Variable-length byte string.
     Only present if the :cpp:enumerator:`~Flags::kClientKey` flag is set.
     Always unset in practice and not used by client or servers.
     Unclear if Cyan's server software does anything with it.
   
   .. cpp:enum:: Flags
      
      .. cpp:enumerator:: kAccountUUID = 1 << 0
      .. cpp:enumerator:: kPlayerID = 1 << 1
      .. cpp:enumerator:: kTempPlayerID = 1 << 2
      .. cpp:enumerator:: kCCRLevel = 1 << 3
      .. cpp:enumerator:: kProtectedLogin = 1 << 4
      .. cpp:enumerator:: kBuildType = 1 << 5
      .. cpp:enumerator:: kPlayerName = 1 << 6
      .. cpp:enumerator:: kSrcAddr = 1 << 7
      .. cpp:enumerator:: kSrcPort = 1 << 8
      .. cpp:enumerator:: kReserved = 1 << 9
      .. cpp:enumerator:: kClientKey = 1 << 10

.. cpp:class:: plNetMsgStreamHelper : public plCreatable
   
   * **Uncompressed length:** 4-byte unsigned int.
     Byte length of the stream data after decompression.
     If the stream data is not compressed,
     this field is set to 0.
   * **Compression type:** 1-byte :cpp:enum:`plNetMessage::CompressionType`.
   * **Stream length:** 4-byte unsigned int.
     Byte length of the following stream data field.
   * **Stream data:** Variable-length byte array.
     The format of this data depends on the class of the containing message.
     Additionally,
     the data may be compressed,
     depending on the compression type field.

.. cpp:enum:: plNetMember::Flags
   
   .. cpp:enumerator:: kWaitingForLinkQuery = 1 << 0
      
      "only used server side"
   
   .. cpp:enumerator:: kIndirectMember = 1 << 1
      
      "this guy is behind a firewall of some sort"
   
   .. cpp:enumerator:: kRequestP2P = 1 << 2
      
      "wants to play peer to peer"
   
   .. cpp:enumerator:: kWaitingForChallengeResponse = 1 << 3
      
      "waiting for client response"
   
   .. cpp:enumerator:: kIsServer = 1 << 4
      
      "used by transport member"
   
   .. cpp:enumerator:: kAllowTimeOut = 1 << 5
      
      "used by gameserver"

.. cpp:class:: plNetMsgMemberInfoHelper : public plCreatable
   
   * **Flags:** 4-byte unsigned int.
     See :cpp:enum:`plNetMember::Flags` for details.
     MOSS and DIRTSAND always set this field to 0.
   * **Client info:** :cpp:class:`plClientGuid`.
   * **Avatar UOID:** :cpp:class:`plUoid`.

:cpp:class:`plNetMessage`
^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:class:: plNetMessage : public plCreatable
   
   *Class index = 0x025e = 606*
   
   The serialized format has the following common header structure,
   with any subclass-specific data directly after the header.
   
   * **Class index:** 2-byte unsigned int.
     Identifies the specific :cpp:class:`plNetMessage` subclass
     that this message is an instance of.
   * **Flags:** 4-byte unsigned int.
     Collection of various boolean flags,
     some of which affect the format of the remaining message data.
     See :cpp:enum:`BitVectorFlags` for details.
   * **Protocol version:** 2 bytes.
     Only present if the :cpp:enumerator:`~BitVectorFlags::kHasVersion` flag is set.
     Always unset in practice and not used by client or servers.
     Not supported by MOSS.
     Unclear if Cyan's server software does anything with it.
     According to comments in the open-sourced client code,
     this version number has remained unchanged since 2003-12-01.
     
     * **Major version:** 1-byte unsigned int.
       Always set to 12.
     * **Minor version:** 1-byte unsigned int.
       Always set to 6.
   * **Time sent:** 8-byte :cpp:class:`plUnifiedTime`.
     Only present if the :cpp:enumerator:`~BitVectorFlags::kHasTimeSent` flag is set.
     Timestamp indicating when this message was sent.
     Used by the client to adjust for differences between the client and server clocks.
     The client sets this field for *every* message it sends,
     and so does every server implementation apparently.
   * **Context:** 4-byte unsigned int.
     Only present if the :cpp:enumerator:`~BitVectorFlags::kHasContext` flag is set.
     Always unset in practice and not used by client or servers.
     Not supported by MOSS.
     Unclear if Cyan's server software does anything with it.
   * **Transaction ID:** 4-byte unsigned int.
     Only present if the :cpp:enumerator:`~BitVectorFlags::kHasTransactionID` flag is set.
     Always unset in practice and not used by client or servers
     (the MOSS source code says "should never happen" about the code that reads this field).
     Unclear if Cyan's server software does anything with it.
   * **Player ID:** 4-byte unsigned int.
     Only present if the :cpp:enumerator:`~BitVectorFlags::kHasPlayerID` flag is set.
     KI number of the avatar being played by the client that sent the message.
     The client sets this field for *every* message it sends,
     but messages originating from the server usually leave it unset.
   * **Account UUID:** 16-byte UUID.
     Only present if the :cpp:enumerator:`~BitVectorFlags::kHasAcctUUID` flag is set.
     Always unset in practice and not used by client or servers
     (the MOSS source code says "should never happen" about the code that reads this field).
     Unclear if Cyan's server software does anything with it.
   
   .. cpp:enum:: BitVectorFlags
      
      .. cpp:enumerator:: kHasTimeSent = 1 << 0
         
         Whether the time sent field is present.
         Always set in practice.
      
      .. cpp:enumerator:: kHasGameMsgRcvrs = 1 << 1
         
         Set for :cpp:class:`plNetMsgGameMessage` (or subclass) messages
         if the wrapped ``plMessage`` has at least one receiver whose :cpp:class:`plLocation` is not virtual or reserved.
         Should never be set for other message types.
         According to comments in the open-sourced client code,
         this flag is meant to allow some server-side optimization.
         MOSS and DIRTSAND ignore it though.
      
      .. cpp:enumerator:: kEchoBackToSender = 1 << 2
         
         Request that the server sends the message back to the client that sent it.
         DIRTSAND implements this flag for broadcast and propagate messages
         MOSS doesn't implement it and silently ignores it.
         The open-sourced client code sets this flag in two cases:
         
         * If ``plNetClientRecorder`` is enabled using the console command ``Demo.RecordNet``,
           this flag is set on all :cpp:class:`plNetMsgSDLState`, :cpp:class:`plNetMsgSDLStateBCast`, :cpp:class:`plNetMsgGameMessage`, and :cpp:class:`plNetMsgLoadClone` messages.
         * If voice chat echo has been enabled using the console command ``Net.Voice.Echo``,
           this flag is set on all :cpp:class:`plNetMsgVoice` messages
           (this is broken in OpenUru clients if compression is disabled using the console command ``Audio.EnableVoiceCompression``).
         
         Because both of these features can only be enabled via console commands,
         this flag is almost never set in practice.
      
      .. cpp:enumerator:: kRequestP2P = 1 << 3
         
         Unused and always unset.
      
      .. cpp:enumerator:: kAllowTimeOut = 1 << 4
         
         Unused and always unset.
         MOSS has some incomplete code that handles this flag,
         which interprets it as adding an extra 6 bytes to the message size,
         supposedly for IP address and port fields.
         This interpretation seems incorrect though,
         especially because it's based on what Alcugs does,
         and it seems that this bit had a different meaning in pre-MOUL Uru.
      
      .. cpp:enumerator:: kIndirectMember = 1 << 5
         
         Unused and always unset.
      
      .. cpp:enumerator:: kPublicIPClient = 1 << 6
         
         Unused and always unset.
      
      .. cpp:enumerator:: kHasContext = 1 << 7
         
         Whether the context field is present.
         Always unset in practice.
         Not supported by MOSS.
      
      .. cpp:enumerator:: kAskVaultForGameState = 1 << 8
         
         Unused and always unset.
      
      .. cpp:enumerator:: kHasTransactionID = 1 << 9
         
         Whether the transaction ID field is present.
         Always unset in practice.
      
      .. cpp:enumerator:: kNewSDLState = 1 << 10
         
         When a ``plSDLModifier`` sends a :cpp:class:`plNetMsgSDLState` (or subclass) message for the first time,
         the client sets this flag in the message.
         All further messages from the same ``plSDLModifier`` have it unset.
         Should never be set for other message types.
         Ignored by MOSS and DIRTSAND.
      
      .. cpp:enumerator:: kInitialAgeStateRequest = 1 << 11
         
         Set by the client for all :cpp:class:`plNetMsgGameStateRequest` messages.
         Should never be set for other message types.
         Ignored by MOSS and DIRTSAND.
      
      .. cpp:enumerator:: kHasPlayerID = 1 << 12
         
         Whether the player ID field is present.
      
      .. cpp:enumerator:: kUseRelevanceRegions = 1 << 13
         
         Whether the message should be filtered by relevance regions.
         The client sets this flag for :cpp:class:`plNetMsgGameMessage` (or subclass) messages
         if the wrapped ``plMessage`` has the ``kNetUseRelevanceRegions`` flag set,
         and for some :cpp:class:`plNetMsgSDLState` (or subclass) messages caused by ``plArmatureMod``.
         Ignored by MOSS and DIRTSAND.
      
      .. cpp:enumerator:: kHasAcctUUID = 1 << 14
         
         Whether the account UUID field is present.
         Always unset in practice.
      
      .. cpp:enumerator:: kInterAgeRouting = 1 << 15
         
         Whether the message should also be sent across age instances,
         not just within the current age instance as usual.
         Set for :cpp:class:`plNetMsgGameMessage` (or subclass) messages
         if the wrapped ``plMessage`` has the ``kNetAllowInterAge`` flag set
         (unless :cpp:enumerator:`kRouteToAllPlayers`/``kCCRSendToAllPlayers`` is also set).
         This should only happen for :cpp:class:`plNetMsgGameMessageDirected` messages
         where the wrapped ``plMessage`` is a ``pfKIMsg``, ``plCCRCommunicationMsg``, ``plLinkingMgrMsg``, or ``plLinkToAgeMsg``.
         Should never be set for other message types.
         Ignored by MOSS and DIRTSAND.
      
      .. cpp:enumerator:: kHasVersion = 1 << 16
         
         Whether the protocol version field is present.
         Always unset in practice.
      
      .. cpp:enumerator:: kIsSystemMessage = 1 << 17
         
         Set for all :cpp:class:`plNetMsgRoomsList`, :cpp:class:`plNetMsgObjStateRequest`, :cpp:class:`plNetMsgMembersListReq`, and :cpp:class:`plNetMsgServerToClient` messages
         (including subclasses, if any).
         DIRTSAND also sets it for some :cpp:class:`plNetMsgSDLStateBCast` messages.
         MOSS, DIRTSAND, and the client never use this flag for anything.
         Unclear if Cyan's server software does anything with it.
      
      .. cpp:enumerator:: kNeedsReliableSend = 1 << 18
         
         The client sets this flag for all messages other than :cpp:class:`plNetMsgVoice`, :cpp:class:`plNetMsgObjectUpdateFilter`, and :cpp:class:`plNetMsgListenListUpdate`.
         DIRTSAND sets it for all messages it creates,
         whereas MOSS never sets it for its own messages.
         MOSS, DIRTSAND, and the client never use this flag for anything.
         Unclear if Cyan's server software does anything with it.
      
      .. cpp:enumerator:: kRouteToAllPlayers = 1 << 19
         
         Whether the message should be sent to all players in all age instances.
         If this flag is set,
         :cpp:enumerator:`kInterAgeRouting` should be unset.
         The client sets this flag for :cpp:class:`plNetMsgGameMessage` (or subclass) messages
         if the client is :ref:`internal <internal_external_client>`
         and the wrapped ``plMessage`` has the ``kCCRSendToAllPlayers`` flag set.
         Should never be set for other message types.
         The open-sourced client code and OpenUru clients never set this flag ---
         most likely only Cyan's internal CCR client used it.
         Internal H'uru clients set this flag when sending CCR broadcast chat messages
         (using the ``/system`` chat command or the All Players list).
         DIRTSAND implements this flag,
         but only respects it if the sender is permitted to send unsafe ``plMessage``\s
         (i. e. if the sender's account has the :cpp:var:`kAccountRoleAdmin` flag set).
         MOSS doesn't implement this flag at all and always ignores it.
   
   .. cpp:enum:: CompressionType
      
      Only used within the subclass :cpp:class:`plNetMsgStreamedObject`.
      
      .. cpp:enumerator:: kCompressionNone = 0
         
         The stream data is not compressed
         because it didn't meet the length threshold for compression.
      
      .. cpp:enumerator:: kCompressionFailed = 1
         
         This is an internal error value used when the stream data could not be (de)compressed.
         It should never appear in a serialized message.
      
      .. cpp:enumerator:: kCompressionZlib = 2
         
         The stream data is partially compressed:
         the first two bytes are uncompressed,
         followed by the remaining data,
         which is zlib-compressed.
         The open-sourced client code uses zlib compression iff the stream data is at least 256 bytes long.
      
      .. cpp:enumerator:: kCompressionDont = 3
         
         The stream data is not compressed
         because compression has been explicitly disabled.
         The open-sourced client code does this iff the :cpp:enumerator:`~BitVectorFlags::kHasGameMsgRcvrs` flag is set on the message.

:cpp:class:`plNetMsgRoomsList`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:class:: plNetMsgRoomsList : public plNetMessage
   
   *Class index = 0x0263 = 611*
   
   * **Header:** :cpp:class:`plNetMessage`.
   * **Room count:** 4-byte unsigned int
     (or signed in the original/OpenUru code for some reason).
     Element count for the following array of rooms.
   * **Rooms:** Variable-length array.
     Each element has the following structure:
     
     * **Location:** 6-byte :cpp:class:`plLocation`.
     * **Name length:** 2-byte unsigned int.
       Byte count for the following name string.
     * **Name:** Variable-length byte string.

:cpp:class:`plNetMsgPagingRoom`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:class:: plNetMsgPagingRoom : public plNetMsgRoomsList
   
   *Class index = 0x0218 = 536*
   
   * **Header:** :cpp:class:`plNetMsgRoomsList`.
   * **Flags:** 1-byte unsigned int.
     See :cpp:enum:`PageFlags` for details.
   
   .. cpp:enum:: PageFlags
      
      .. cpp:enumerator:: kPagingOut = 1 << 0
      .. cpp:enumerator:: kResetList = 1 << 1
      .. cpp:enumerator:: kRequestState = 1 << 2
      .. cpp:enumerator:: kFinalRoomInAge = 1 << 3

:cpp:class:`plNetMsgGameStateRequest`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:class:: plNetMsgGameStateRequest : public plNetMsgRoomsList
   
   *Class index = 0x0265 = 613*
   
   Identical structure to its superclass :cpp:class:`plNetMsgRoomsList`.

:cpp:class:`plNetMsgObject`
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:class:: plNetMsgObject : public plNetMessage
   
   *Class index = 0x0268 = 616*
   
   * **Header:** :cpp:class:`plNetMessage`.
   * **UOID:** :cpp:class:`plUoid`.

:cpp:class:`plNetMsgStreamedObject`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:class:: plNetMsgStreamedObject : public plNetMsgObject
   
   *Class index = 0x027b = 635*
   
   * **Header:** :cpp:class:`plNetMsgObject`.
   * **Stream:** :cpp:class:`plNetMsgStreamHelper`.
     The format of the stream data depends on the subclass.

:cpp:class:`plNetMsgSharedState`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:class:: plNetMsgSharedState : public plNetMsgStreamedObject
   
   *Class index = 0x027c = 636*
   
   * **Header:** :cpp:class:`plNetMsgStreamedObject`.
   * **Lock request:** 1-byte boolean.

:cpp:class:`plNetMsgTestAndSet`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:class:: plNetMsgTestAndSet : public plNetMsgSharedState
   
   *Class index = 0x027d = 637*
   
   Identical structure to its superclass :cpp:class:`plNetMsgSharedState`.

:cpp:class:`plNetMsgSDLState`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:class:: plNetMsgSDLState : public plNetMsgStreamedObject
   
   *Class index = 0x02cd = 717*
   
   * **Header:** :cpp:class:`plNetMsgStreamedObject`.
   * **Is initial state:** 1-byte boolean.
     Set to true by the server when replying to a :cpp:class:`plNetMsgGameStateRequest`.
     The client always sets it to false.
   * **Persist on server:** 1-byte boolean.
     Normally always set to true.
     The client sets it to false for SDL states that should only be propagated to other clients,
     but not saved permanently on the server.
   * **Is avatar state:** 1-byte boolean.
     Set to true by the client for SDL states related/attached to an avatar.
     If true,
     the persist on server flag should be false.

:cpp:class:`plNetMsgSDLStateBCast`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:class:: plNetMsgSDLStateBCast : public plNetMsgSDLState
   
   *Class index = 0x0329 = 809*
   
   Identical structure to its superclass :cpp:class:`plNetMsgSDLState`.

:cpp:class:`plNetMsgGetSharedState`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:class:: plNetMsgGetSharedState : public plNetMsgObject
   
   *Class index = 0x027e = 638*
   
   * **Header:** :cpp:class:`plNetMsgObject`.
   * **Shared state name:** 32-byte zero-terminated string.

:cpp:class:`plNetMsgObjStateRequest`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:class:: plNetMsgObjStateRequest : public plNetMsgObject
   
   *Class index = 0x0286 = 646*
   
   Identical structure to its superclass :cpp:class:`plNetMsgObject`.

:cpp:class:`plNetMsgStream`
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:class:: plNetMsgStream : public plNetMessage
   
   *Class index = 0x026c = 620*
   
   * **Header:** :cpp:class:`plNetMessage`.
   * **Stream:** :cpp:class:`plNetMsgStreamHelper`.
     The format of the stream data depends on the subclass.

:cpp:class:`plNetMsgGameMessage`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:class:: plNetMsgGameMessage : public plNetMsgStream
   
   *Class index = 0x026b = 619*
   
   * **Header:** :cpp:class:`plNetMsgStream`.
   * **Delivery time present:** 1-byte boolean.
     Whether the following delivery time field is set.
     MOSS, DIRTSAND, and the open-sourced client code always set it to false.
   * **Delivery time:** 8-byte :cpp:class:`plUnifiedTime`.
     Only present if the preceding boolean field is true,
     otherwise defaults to all zeroes
     (i. e. the Unix epoch).
     The open-sourced client code never sets this field,
     but handles it if received.
     MOSS and DIRTSAND ignore this field and never set it.
     Unclear if Cyan's server software does anything with it.
   
   Wraps a ``plMessage`` to be sent between clients.
   The stream data contains the serialized ``plMessage``
   in the format produced by ``hsResMgr::WriteCreatable``
   and understood by ``hsResMgr::ReadCreatable``.
   
   If the contained ``plMessage`` is an instance of ``plLoadCloneMsg``,
   then the wrapper message must have the class :cpp:class:`plNetMsgLoadClone` instead.
   
   When the client sends (locally) a ``plMessage`` that has the ``kNetPropagate`` flag set,
   it wraps the ``plMessage`` in a :cpp:class:`plNetMsgGameMessage`
   (or one of its subclasses)
   and sends it to the game server.
   Afterwards,
   the ``plMessage`` is also sent locally on the client side
   if it has the ``kLocalPropagate`` flag set
   (which is the case by default).
   
   When the server receives this message,
   by default it forwards it to all other clients in the same age instance.
   
   If the message has the :cpp:enumerator:`~plNetMessage::BitVectorFlags::kEchoBackToSender` flag set,
   it's also repeated back to the sender.
   MOSS doesn't support this flag.
   DIRTSAND ignores it for :cpp:class:`plNetMsgGameMessageDirected` messages.
   
   If the message has the :cpp:enumerator:`~plNetMessage::BitVectorFlags::kRouteToAllPlayers` flag set,
   it's forwarded to *all* clients on the entire shard,
   even ones in other age instances.
   MOSS doesn't support this flag.
   DIRTSAND only allows it if the sender's account has the :cpp:var:`kAccountRoleAdmin` flag set
   and the message class is exactly :cpp:class:`plNetMsgGameMessage`.
   
   DIRTSAND by default blocks forwarding of certain ``plMessage``\s
   that cannot occur during normal gameplay and should only be used by CCRs and developers.
   Such messages are silently dropped and not forwarded to anyone,
   unless the sender's account has the :cpp:var:`kAccountRoleAdmin` flag set,
   which allows bypassing this check.
   
   The server forwards the message completely unmodified,
   with the following exceptions:
   
   * If the message has the :cpp:enumerator:`~BitVectorFlags::kHasTimeSent` flag set
     (which is always the case in practice),
     MOSS updates the time sent to the current time when forwarding the message.
     DIRTSAND leaves it untouched and keeps the time sent that was originally set by the sending client.
     (TODO What does Cyan's server software do?)
     This difference shouldn't be noticeable in practice.
   * DIRTSAND sets the ``kNetNonLocal`` flag on the wrapped ``plMessage`` before forwarding it
     (unless the wrapper message is a :cpp:class:`plNetMsgLoadClone` ---
     but that might just be a bug).
     MOSS never sets this flag
     and that apparently has no negative effect on gameplay.
     (TODO What does Cyan's server software do?)

:cpp:class:`plNetMsgGameMessageDirected`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:class:: plNetMsgGameMessageDirected : public plNetMsgGameMessage
   
   *Class index = 0x032e = 814*
   
   * **Header:** :cpp:class:`plNetMsgGameMessage`.
   * **Receiver count:** 1-byte unsigned int.
     Element count of the following receiver array.
   * **Receivers:** Variable-length array of 4-byte unsigned ints,
     each a KI number of an avatar that should receive this message.
     Note that this is independent of the wrapped ``plMessage``'s list of receiver keys ---
     in fact,
     the latter is usually empty for directed messages.
   
   Behaves like its superclass :cpp:class:`plNetMsgGameMessage`,
   except that the server only forwards it to the specified list of receivers,
   not all avatars in the age instance.
   The wrapped ``plMessage`` should be an instance of ``pfKIMsg``, ``plCCRCommunicationMsg``, ``plAvatarInputStateMsg``, ``plInputIfaceMgrMsg``, or ``plNotifyMsg``.
   
   By default,
   the message is only forwarded to receivers that are in the same age instance as the sender.
   If the :cpp:enumerator:`~plNetMessage::BitVectorFlags::kInterAgeRouting` flag is set,
   it's also forwarded to receivers in other age instances.
   MOSS and DIRTSAND ignore this flag though
   and always forward the message to all receivers,
   regardless of which age instance they're in.
   
   DIRTSAND ignores the :cpp:enumerator:`~plNetMessage::BitVectorFlags::kEchoBackToSender` for directed messages
   and instead repeats the message back if and only if the sender's KI number is in the list of receivers.
   
   The :cpp:enumerator:`~plNetMessage::BitVectorFlags::kRouteToAllPlayers` flag shouldn't be used with directed messages.

:cpp:class:`plNetMsgLoadClone`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:class:: plNetMsgLoadClone : public plNetMsgGameMessage
   
   *Class index = 0x03b3 = 947*
   
   * **Header:** :cpp:class:`plNetMsgGameMessage`.
   * **UOID:** :cpp:class:`plUoid`.
   * **Is player:** 1-byte boolean.
   * **Is loading:** 1-byte boolean.
   * **Is initial state:** 1-byte boolean.
   
   Special case of :cpp:class:`plNetMsgGameMessage`
   used if the wrapped ``plMessage`` is an instance of ``plLoadCloneMsg``
   (or its only subclass ``plLoadAvatarMsg``).
   
   These messages are always forwarded to all clients within the same age instance ---
   they cannot be directed and should never have the :cpp:enumerator:`~plNetMessage::BitVectorFlags::kInterAgeRouting` or :cpp:enumerator:`~plNetMessage::BitVectorFlags::kRouteToAllPlayers` flags set.

:cpp:class:`plNetMsgVoice`
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:enum:: plVoiceFlags
   
   .. cpp:enumerator:: kEncoded = 1 << 0
      
      Whether the voice data is compressed/encoded.
      This flag is normally always set,
      because all clients use some kind of compression by default ---
      although the exact codec depends on the other flags explained below.
      Compression can be disabled using the console command ``Audio.EnableVoiceCompression`` (OpenUru) or ``Audio.SetVoiceCodec`` (H'uru),
      in which case this flag is left unset
      and the voice data is transmitted as uncompressed PCM data, mono, 16-bit, 8 kHz.
      OpenUru defines this flag as the macro ``VOICE_ENCODED``.
   
   .. cpp:enumerator:: kEncodedSpeex = 1 << 1
      
      Whether the voice data is encoded using the Speex codec.
      If set,
      then :cpp:enumerator:`kEncoded` must also be set.
      Only set by H'uru clients if Speex is manually selected using the ``Audio.SetVoiceCodec`` console command.
      OpenUru defines this flag as the macro ``VOICE_NARROWBAND``,
      but ignores it and never sets it ---
      OpenUru clients don't support any codecs other than Speex
      and assume that all messages with :cpp:enumerator:`kEncoded`/``VOICE_ENCODED`` set use Speex.
      For compatibility,
      H'uru clients also assume Speex compression if only :cpp:enumerator:`kEncoded` and no other codec flags are set.
   
   .. cpp:enumerator:: kEncodedOpus = 1 << 2
      
      Whether the voice data is encoded using the Opus codec.
      If set,
      then :cpp:enumerator:`kEncoded` must also be set.
      H'uru clients use Opus by default,
      but this can be changed using the ``Audio.SetVoiceCodec`` console command.
      OpenUru defines this flag as the macro ``VOICE_ENH``,
      but ignores it and never sets it ---
      OpenUru clients don't support Opus compression.

.. cpp:class:: plNetMsgVoice : public plNetMessage
   
   *Class index = 0x0279 = 633*
   
   * **Header:** :cpp:class:`plNetMessage`.
   * **Flags:** 1-byte unsigned int.
     See :cpp:enum:`plVoiceFlags` for details.
   * **Frame count:** 1-byte unsigned int.
   * **Voice data length:** 2-byte unsigned int.
     Byte count for the following voice data.
   * **Voice data:** Variable-length byte array.
   * **Receiver count:** 1-byte unsigned int.
     Element count for the following receiver array.
   * **Receivers:** Variable-length array of 4-byte unsigned ints,
     each a KI number of an avatar that should receive this message.

:cpp:class:`plNetMsgObjectUpdateFilter`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:class:: plNetMsgObjectUpdateFilter : public plNetMessage
   
   *Class index = 0x029d = 669*
   
   * **Header:** :cpp:class:`plNetMessage`.
   * **UOID count:** 2-byte signed int
     (yes,
     it's signed for some reason,
     even though it can never be negative).
     Element count for the following UOID array.
   * **UOIDs:** Variable-length array of :cpp:class:`plUoid`\s.
   * **Maximum update frequency:** 4-byte floating-point number.

:cpp:class:`plNetMsgMembersListReq`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:class:: plNetMsgMembersListReq : public plNetMessage
   
   *Class index = 0x02ad = 685*
   
   Identical structure to its superclass :cpp:class:`plNetMessage`.

:cpp:class:`plNetMsgServerToClient`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:class:: plNetMsgServerToClient : public plNetMessage
   
   *Class index = 0x02b2 = 690*
   
   Identical structure to its superclass :cpp:class:`plNetMessage`.

:cpp:class:`plNetMsgGroupOwner`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:class:: plNetMsgGroupOwner : public plNetMsgServerToClient
   
   *Class index = 0x0264 = 612*
   
   * **Header:** :cpp:class:`plNetMsgServerToClient`.
   * **Group count:** 4-byte signed int
     (yes,
     it's signed for some reason,
     even though it can never be negative).
     Element count for the following group array.
   * **Groups:** Variable-length array of:
     
     * **ID:** 7-byte :cpp:class:`plNetGroupId`.
     * **Owned:** 1-byte boolean.

:cpp:class:`plNetMsgMembersList`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:class:: plNetMsgMembersList : public plNetMsgServerToClient
   
   *Class index = 0x02ae = 686*
   
   * **Header:** :cpp:class:`plNetMsgServerToClient`.
   * **Member count:** 2-byte signed int
     (yes,
     it's signed for some reason,
     even though it can never be negative).
     Element count for the following member array.
   * **Members:** Variable-length array of :cpp:class:`plNetMsgMemberInfoHelper`\s.

:cpp:class:`plNetMsgMemberUpdate`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:class:: plNetMsgMemberUpdate : public plNetMsgServerToClient
   
   *Class index = 0x02b1 = 689*
   
   * **Header:** :cpp:class:`plNetMsgServerToClient`.
   * **Member:** :cpp:class:`plNetMsgMemberInfoHelper`.
   * **Was added:** 1-byte boolean.
     Set to true if the member in question was added,
     or set to false if it was removed.

:cpp:class:`plNetMsgInitialAgeStateSent`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:class:: plNetMsgInitialAgeStateSent : public plNetMsgServerToClient
   
   *Class index = 0x02b8 = 696*
   
   * **Header:** :cpp:class:`plNetMsgServerToClient`.
   * **Initial SDL state count:** 4-byte unsigned int.

:cpp:class:`plNetMsgListenListUpdate`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:class:: plNetMsgListenListUpdate : public plNetMessage
   
   *Class index = 0x02c8 = 712*
   
   * **Header:** :cpp:class:`plNetMessage`.
   * **Adding:** 1-byte boolean.
     Set to true if the avatars in question should be added,
     or set to false if they should be removed.
   * **Receiver count:** 1-byte unsigned int.
     Element count for the following receiver array.
   * **Receivers:** Variable-length array of 4-byte unsigned ints,
     each a KI number of another avatar.

:cpp:class:`plNetMsgRelevanceRegions`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:class:: plNetMsgRelevanceRegions : public plNetMessage
   
   *Class index = 0x03ac = 940*
   
   * **Header:** :cpp:class:`plNetMessage`.
   * **Regions I care about:** :cpp:class:`hsBitVector`.
   * **Regions I'm in:** :cpp:class:`hsBitVector`.

:cpp:class:`plNetMsgPlayerPage`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. cpp:class:: plNetMsgPlayerPage : public plNetMessage
   
   *Class index = 0x03b4 = 948*
   
   * **Header:** :cpp:class:`plNetMessage`.
   * **Unload:** 1-byte boolean.
   * **UOID:** :cpp:class:`plUoid`.
