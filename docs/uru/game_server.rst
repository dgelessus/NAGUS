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
  * ``plNetMsgObject`` = 0x0268 = 616 (abstract)
    
    * ``plNetMsgStreamedObject`` = 0x027b = 635 (abstract)
      
      * ``plNetMsgSharedState`` = 0x027c = 636 (abstract)
        
        * ``plNetMsgTestAndSet`` = 0x027d = 637 (client -> server)
      * ``plNetMsgSDLState`` = 0x02cd = 717 (client <-> server)
        
        * ``plNetMsgSDLStateBCast`` = 0x0329 = 809 (client <-> server)
    * ``plNetMsgGetSharedState`` = 0x027e = 638 (client -> server, unused)
    * ``plNetMsgObjStateRequest`` = 0x0286 = 646 (client -> server, unused)
  * ``plNetMsgStream`` = 0x026c = 620 (abstract)
    
    * ``plNetMsgGameMessage`` = 0x026b = 619 (client <-> server)
      
      * ``plNetMsgGameMessageDirected`` = 0x032e = 814 (client <-> server)
      * ``plNetMsgLoadClone`` = 0x03b3 = 947 (client <-> server)
  * ``plNetMsgVoice`` = 0x0279 = 633 (client <-> server)
  * ``plNetMsgObjectUpdateFilter`` = 0x029d = 669 (client -> server, not handled by MOSS or DIRTSAND)
  * ``plNetMsgMembersListReq`` = 0x02ad = 685 (client -> server)
  * ``plNetMsgServerToClient`` = 0x02b2 = 690 (abstract)
    
    * ``plNetMsgGroupOwner`` = 0x0264 = 612 (server -> client)
    * ``plNetMsgMembersList`` = 0x02ae = 686 (server -> client)
    * ``plNetMsgMemberUpdate`` = 0x02b1 = 689 (server -> client)
    * ``plNetMsgInitialAgeStateSent`` = 0x02b8 = 696 (server -> client)
  * ``plNetMsgListenListUpdate`` = 0x02c8 = 712 (client <-> server, unused, but client theoretically handles it)
  * ``plNetMsgRelevanceRegions`` = 0x03ac = 940 (client -> server)
  * ``plNetMsgPlayerPage`` = 0x03b4 = 948 (client -> server)

Common data types
^^^^^^^^^^^^^^^^^

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
   * **Time sent:** 8 bytes.
     Only present if the :cpp:enumerator:`~BitVectorFlags::kHasTimeSent` flag is set.
     Timestamp indicating when this message was sent.
     Used by the client to adjust for differences between the client and server clocks.
     The client sets this field for *every* message it sends,
     and so does every server implementation apparently.
     
     * **Seconds:** 4-byte unsigned int.
       Unix timestamp (seconds since 1970).
     * **Microseconds:** 4-byte unsigned int.
       Fractional part of the timestamp for sub-second precision.
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
         
         Set for ``plNetMsgGameMessage`` (or subclass) messages if they use "direct communication".
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
           this flag is set on all ``plNetMsgSDLState``, ``plNetMsgSDLStateBCast``, ``plNetMsgGameMessage``, and ``plNetMsgLoadClone`` messages.
         * If voice chat echo has been enabled using the console command ``Net.Voice.Echo``,
           this flag is set on all ``plNetMsgVoice`` messages
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
         
         When a ``plSDLModifier`` sends a ``plNetMsgSDLState`` (or subclass) message for the first time,
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
         The client sets this flag for ``plNetMsgGameMessage`` (or subclass) messages
         if the wrapped ``plMessage`` has the ``kNetUseRelevanceRegions`` flag set,
         and for some ``plNetMsgSDLState`` (or subclass) messages caused by ``plArmatureMod``.
         Ignored by MOSS and DIRTSAND.
      
      .. cpp:enumerator:: kHasAcctUUID = 1 << 14
         
         Whether the account UUID field is present.
         Always unset in practice.
      
      .. cpp:enumerator:: kInterAgeRouting = 1 << 15
         
         Whether the message should also be sent across age instances,
         not just within the current age instance as usual.
         Set for ``plNetMsgGameMessage`` (or subclass) messages
         if the wrapped ``plMessage`` has the ``kNetAllowInterAge`` flag set
         (unless :cpp:enumerator:`kRouteToAllPlayers`/``kCCRSendToAllPlayers`` is also set).
         Should never be set for other message types.
         Ignored by MOSS and DIRTSAND.
      
      .. cpp:enumerator:: kHasVersion = 1 << 16
         
         Whether the protocol version field is present.
         Always unset in practice.
      
      .. cpp:enumerator:: kIsSystemMessage = 1 << 17
         
         Set for all :cpp:class:`plNetMsgRoomsList`, ``plNetMsgObjStateRequest``, ``plNetMsgMembersListReq``, and ``plNetMsgServerToClient`` messages
         (including subclasses, if any).
         DIRTSAND also sets it for some ``plNetMsgSDLStateBCast`` messages.
         MOSS, DIRTSAND, and the client never use this flag for anything.
         Unclear if Cyan's server software does anything with it.
      
      .. cpp:enumerator:: kNeedsReliableSend = 1 << 18
         
         The client sets this flag for all messages other than ``plNetMsgVoice``, ``plNetMsgObjectUpdateFilter``, and ``plNetMsgListenListUpdate``.
         DIRTSAND sets it for all messages it creates,
         whereas MOSS never sets it for its own messages.
         MOSS, DIRTSAND, and the client never use this flag for anything.
         Unclear if Cyan's server software does anything with it.
      
      .. cpp:enumerator:: kRouteToAllPlayers = 1 << 19
         
         Whether the message should be sent to all players in all age instances.
         If this flag is set,
         :cpp:enumerator:`kInterAgeRouting` should be unset.
         The client sets this flag for ``plNetMsgGameMessage`` (or subclass) messages
         if the client is :ref:`internal <internal_external_client>`,
         the current :ref:`CCR level <ccr_level>` is greater than 0,
         and the wrapped ``plMessage`` has the ``kCCRSendToAllPlayers`` flag set.
         Should never be set for other message types.
         DIRTSAND implements this flag,
         but only respects it if the sender is permitted to send unsafe messages
         (i. e. if the sender's account has the :cpp:var:`kAccountRoleAdmin` flag set).
         MOSS doesn't implement this flag at all and always ignores it.

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
