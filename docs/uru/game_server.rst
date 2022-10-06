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

.. _cli2game_propagate_buffer:

Cli2Game_PropagateBuffer
^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 2
* **Class index:** 4-byte unsigned int.
  ``plCreatable`` class index of the message stored in the following buffer.
  Must be one of ``plNetMessage``'s subclasses.
* **Buffer length:** 4-byte unsigned int.
  Byte length of the following buffer field.
  Can be at most 1 MiB.
* **Buffer:** Variable-length byte array.
  The serialized message,
  in the format produced by ``plNetMessage::PokeBuffer``
  and understood by ``plNetMessage::PeekBuffer``.
  The class index in the serialized buffer must match the one in the class index field.

Transmits a serialized ``plNetMessage`` from the client to the server.
See :ref:`pl_net_messages` for details on the different kinds of messages that are sent this way.

.. _game2cli_propagate_buffer:

Game2Cli_PropagateBuffer
^^^^^^^^^^^^^^^^^^^^^^^^

Identical message type and format as :ref:`cli2game_propagate_buffer`,
but sent from the server to the client.

.. _pl_net_messages:

``plNetMessage``\s
------------------

Most communication with the game server
(and, indirectly, with other clients)
happens using serialized ``plNetMessage`` objects,
which are wrapped in :ref:`cli2game_propagate_buffer`/:ref:`game2cli_propagate_buffer` when sent to/from the game server.

The different ``plNetMessage`` subclasses are identified by their ``plCreatable`` class index.
Unlike the :ref:`lower-level message protocol <messages>`,
``plNetMessage``\s aren't strictly separated by communication direction.
Many message types are in fact sent in both directions between client and server,
but others are only supposed to go in one direction.
In all cases,
the class index uniquely identifies the message class with no further context.

Below is an overview of the ``plNetMessage`` class hierarchy in the open-sourced client code,
along with the corresponding class indices and the intended message direction.
Classes marked as "abstract" are only used as base classes ---
a message should never be a direct instance of one of these classes,
only of one of their non-abstract subclasses.
Classes marked as "unused" are fully defined in the open-sourced client code,
but never actually used by the client
and not supported by MOSS or DIRTSAND
(it's unknown if Cyan's server software supports them).

* ``plNetMessage`` = 0x025e = 606 (abstract)
  
  * ``plNetMsgRoomsList`` = 0x0263 = 611 (abstract)
    
    * ``plNetMsgPagingRoom`` = 0x0218 = 536 (client -> server)
    * ``plNetMsgGameStateRequest`` = 0x0265 = 613 (client -> server)
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
