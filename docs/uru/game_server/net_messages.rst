Game network messages
=====================

Most communication with the :ref:`game server <game_server>`
(and, indirectly, with other clients)
happens using serialized :cpp:class:`plNetMessage` objects,
which are wrapped in :ref:`cli2game_propagate_buffer`/:ref:`game2cli_propagate_buffer` when sent to/from the game server.

The different :cpp:class:`plNetMessage` subclasses are identified by their :cpp:class:`plCreatable` class index.
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
-----------------

Assorted data types used by the message classes below.

.. seealso::
  
  :ref:`common_data_types` under :doc:`../protocol`.

.. cpp:class:: plGenericType
  
  * **Type:** 1-byte :cpp:enum:`pnGenericType::Types`.
    Indicates the type and meaning of the following data field.
  * **Data:** Varies depending on the type field
    (see below).
  
  .. cpp:enum:: Types
    
    .. cpp:enumerator:: kInt = 0
      
      4-byte signed int.
    
    .. cpp:enumerator:: kFloat = 1
      
      4-byte floating-point number.
      Not used in the open-sourced client code.
    
    .. cpp:enumerator:: kBool = 2
      
      1-byte boolean.
    
    .. cpp:enumerator:: kString = 3
      
      :ref:`SafeString <safe_string>`.
    
    .. cpp:enumerator:: kChar = 4
      
      A single 8-bit character.
      Not used in the open-sourced client code.
    
    .. cpp:enumerator:: kAny = 4
      
      An arbitrary untyped value.
      Stored as a :ref:`SafeString <safe_string>`,
      but may be implicitly converted to any of the other data types.
      Not used in the open-sourced client code.
      
      Converting to string returns the string as-is.
      
      Converting to char returns the first character of the string
      (or a zero byte if the string is empty).
      
      Converting to any of the integer or floating-point types
      parses the string as a decimal literal of that number type.
      The open-sourced client code performs the conversion using the standard C functions ``atoi`` and ``atof``,
      so any leading whitespace and trailing non-number characters are ignored
      (though it's probably best not to rely on this).
      H'uru clients use ``strtol``/``strtoul`` for integer parsing,
      meaning that out-of-range integer values are clamped to the minimum/maximum 32-bit integer value
      (unlike in OpenUru clients,
      where such values wrap around in two's complement fashion)
      and C octal and hexadecimal prefixes are understood
      (this is probably not intentional).
      
      Converting to bool returns true if the string is ``true`` or a valid non-zero integer (see above),
      or false in all other cases.
    
    .. cpp:enumerator:: kUInt = 5
      
      4-byte unsigned int.
      Not used in the open-sourced client code.
    
    .. cpp:enumerator:: kDouble = 6
      
      8-byte floating-point number.
    
    .. cpp:enumerator:: kNone = 255
      
      No value.
      "Stored" as 0 bytes of data.
      Not used in the open-sourced client code.

.. cpp:class:: plNetGroupId
  
  * **ID:** 6-byte :cpp:class:`plLocation`.
  * **Flags:** 1-byte unsigned int.
    See :cpp:enum:`NetGroupConstants` for details.
  
  .. cpp:enum:: NetGroupConstants
    
    .. cpp:enumerator:: kNetGroupConstant = 1 << 0
    .. cpp:enumerator:: kNetGroupLocal = 1 << 1

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
-------------------------

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
      if the wrapped :cpp:class:`plMessage` has at least one receiver whose :cpp:class:`plLocation` is not virtual or reserved.
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
      
      Set by the client when sending a :cpp:class:`plNetMsgSDLState` (or subclass) message for an object that the server doesn't know about yet.
      Once a message with this flag has been sent for an object,
      or if the client receives a state for an object from the server,
      this flag will be unset for all further :cpp:class:`plNetMsgSDLState` messages for that object.
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
      if the wrapped :cpp:class:`plMessage` has the :cpp:enumerator:`~plMessage::plBCastFlags::kNetUseRelevanceRegions` flag set,
      and for some :cpp:class:`plNetMsgSDLState` (or subclass) messages caused by ``plArmatureMod``.
      Ignored by MOSS and DIRTSAND.
    
    .. cpp:enumerator:: kHasAcctUUID = 1 << 14
      
      Whether the account UUID field is present.
      Always unset in practice.
    
    .. cpp:enumerator:: kInterAgeRouting = 1 << 15
      
      Whether the message should also be sent across age instances,
      not just within the current age instance as usual.
      Set for :cpp:class:`plNetMsgGameMessage` (or subclass) messages
      if the wrapped :cpp:class:`plMessage` has the :cpp:enumerator:`~plMessage::plBCastFlags::kNetAllowInterAge` flag set
      (unless :cpp:enumerator:`kRouteToAllPlayers`/:cpp:enumerator:`~plMessage::plBCastFlags::kCCRSendToAllPlayers` is also set).
      This should only happen for :cpp:class:`plNetMsgGameMessageDirected` messages.
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
      and the wrapped :cpp:class:`plMessage` has the :cpp:enumerator:`~plMessage::plBCastFlags::kCCRSendToAllPlayers` flag set.
      Should never be set for other message types.
      DIRTSAND implements this flag,
      but only respects it if the sender is permitted to send unsafe :cpp:class:`plMessage`\s
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
------------------------------

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
-------------------------------

.. cpp:class:: plNetMsgPagingRoom : public plNetMsgRoomsList
  
  *Class index = 0x0218 = 536*
  
  * **Header:** :cpp:class:`plNetMsgRoomsList`.
  * **Flags:** 1-byte unsigned int.
    See :cpp:enum:`PageFlags` for details.
  
  Sent by the client after loading and before unloading a page.
  The rooms array
  (from :cpp:class:`plNetMsgRoomsList`)
  contains the pages that are being (un)loaded.
  It should never be empty
  and in practice always contains exactly one element.
  
  The open-sourced client code sends page-in messages only for pages loaded during the initial age loading process,
  not for ones loaded later on demand ---
  it's unclear if this is intentional.
  Page-out messages are sent for all page unloads.
  
  The server can theoretically use these messages to track which clients have which pages loaded,
  but because of the inconsistent page-in messages,
  this would be unreliable in practice.
  MOSS ignores this message type completely.
  DIRTSAND only broadcasts it to other clients
  (even though the client doesn't support receiving it)
  and otherwise also ignores it.
  Unclear if Cyan's server software does anything with it.
  
  .. cpp:enum:: PageFlags
    
    .. cpp:enumerator:: kPagingOut = 1 << 0
      
      Set if the pages in question are being unloaded,
      or unset if they are being loaded.
    
    .. cpp:enumerator:: kResetList = 1 << 1
      
      Unused and always unset.
    
    .. cpp:enumerator:: kRequestState = 1 << 2
      
      Unused and always unset.
    
    .. cpp:enumerator:: kFinalRoomInAge = 1 << 3
      
      Unused and always unset.

:cpp:class:`plNetMsgGameStateRequest`
-------------------------------------

.. cpp:class:: plNetMsgGameStateRequest : public plNetMsgRoomsList
  
  *Class index = 0x0265 = 613*
  
  Identical structure to its superclass :cpp:class:`plNetMsgRoomsList`.
  
  Request the current state of the age instance.
  Sent by the client exactly once as part of the link-in/loading process,
  immediately after the :cpp:class:`plNetMsgMembersListReq`.
  
  The rooms list can be used to limit the request only to objects in certain rooms,
  but in practice the client always sends an empty list,
  which requests the state for all rooms loaded by the client.
  MOSS has code for handling both empty and non-empty rooms lists.
  DIRTSAND ignores the rooms list and unconditionally sends all states.
  
  The server replies immediately with the following messages:
  
  * One :cpp:class:`plNetMsgLoadClone` for every clone currently in the age instance.
    DIRTSAND actually sends these messages in response to :cpp:class:`plNetMsgMembersListReq` already,
    but this makes no practical difference,
    because the messages are sent in the same order either way.
    DIRTSAND also doesn't count them towards the total number of sent states (see below),
    but this is also not a problem,
    because the communication is TCP-based and so there's no possibility of any state messages getting lost.
  * One :cpp:class:`plNetMsgSDLState` for the state of every object currently in the age instance.
    This notably includes the age SDL state (if any),
    which is sent as the SDL state for the :ref:`AgeSDLHook <age_sdl_hook>` object.
  * A single :cpp:class:`plNetMsgInitialAgeStateSent` containing the number of state messages that were sent.
    DIRTSAND doesn't include :cpp:class:`plNetMsgLoadClone` messages in this count.
  
  After sending the request,
  the client blocks the link-in/loading process
  until it has received the :cpp:class:`plNetMsgInitialAgeStateSent` message and the indicated number of state mesages.
  
  The exact order of the reply messages doesn't matter,
  except that an object's :cpp:class:`plNetMsgLoadClone` message must be sent before any other messages referring to that object.
  
  DIRTSAND uses the following order:
  
  * :cpp:class:`plNetMsgLoadClone`\s for all non-avatar clones
  * :cpp:class:`plNetMsgLoadClone`\s for all avatars
  * :cpp:class:`plNetMsgSDLState` for the :ref:`AgeSDLHook <age_sdl_hook>` (if any)
  * :cpp:class:`plNetMsgSDLState`\s for all other objects
  * :cpp:class:`plNetMsgInitialAgeStateSent`
  
  MOSS sends all clones and states in the order in which they were first received,
  except that the clone of the requester's avatar is skipped.
  The :cpp:class:`plNetMsgInitialAgeStateSent` message is sent last.

:cpp:class:`plNetMsgObject`
---------------------------

.. cpp:class:: plNetMsgObject : public plNetMessage
  
  *Class index = 0x0268 = 616*
  
  * **Header:** :cpp:class:`plNetMessage`.
  * **UOID:** :cpp:class:`plUoid`.

:cpp:class:`plNetMsgStreamedObject`
-----------------------------------

.. cpp:class:: plNetMsgStreamedObject : public plNetMsgObject
  
  *Class index = 0x027b = 635*
  
  * **Header:** :cpp:class:`plNetMsgObject`.
  * **Stream:** :cpp:class:`plNetMsgStreamHelper`.
    The format of the stream data depends on the subclass.

:cpp:class:`plNetMsgSharedState`
--------------------------------

.. cpp:class:: plNetMsgSharedState : public plNetMsgStreamedObject
  
  *Class index = 0x027c = 636*
  
  * **Header:** :cpp:class:`plNetMsgStreamedObject`.
  * **Lock request:** 1-byte boolean.
  
  The stream data has the following format
  (although in practice,
  only two specific combinations of values are used ---
  see :cpp:class:`plNetMsgTestAndSet`):
  
  * **State name length:** 2-byte unsigned int.
    Byte count for the following state name field.
  * **State name:** Variable-length byte string.
  * **Variable count:** 4-byte signed int
    (yes,
    it's signed for some reason,
    even though it can never be negative).
    Element count for the following array of variables.
  * **Server may delete:** 1-byte boolean.
    Set to true if the state is being set to its default value,
    in which case the server doesn't have to store the value anymore,
    or set to false if the state is being set to a non-default value.
  * **Variables:** Variable-length array of:
    
    * **Variable name:** :ref:`SafeString <safe_string>`.
    * **Variable value:** :cpp:class:`plGenericType`.

:cpp:class:`plNetMsgTestAndSet`
-------------------------------

.. cpp:class:: plNetMsgTestAndSet : public plNetMsgSharedState
  
  *Class index = 0x027d = 637*
  
  Identical structure to its superclass :cpp:class:`plNetMsgSharedState`.
  
  Update a server-side shared state variable attached to an object.
  
  In practice,
  this is only used to implement simple mutexes.
  Almost all fields have fixed or restricted values:
  
  * **UOID:** Always has class type 0x002d (``plLogicModifier``).
  * **Stream data:**
    
    * **State name:** Always the string ``TrigState``.
    * **Variable count:** Always 1.
    * **Server may delete:** False if triggering,
      or true if un-triggering.
    * **Variables:**
      
      * **Variable name:** Always the string ``Triggered``.
      * **Variable value:**
        
        * **Type:** Always :cpp:enumerator:`pnGenericType::Types::kBool`.
        * **Data:** True if triggering,
          or false if un-triggering.
  * **Lock request:** True if triggering,
    or false if un-triggering.
  
  MOSS only accepts this exact structure.
  DIRTSAND implements a full parser for the stream data
  that accepts any state name and variables,
  but then ignores the parsed data entirely
  and only acts based on the lock request field.
  
  If the lock request field is true,
  the server tries to lock the object
  and then replies with a :cpp:class:`plNetMsgGameMessage` containing a :cpp:class:`plServerReplyMsg`.
  The message has no sender and its only receiver is the UOID sent by the client in the :cpp:class:`plNetMsgTestAndSet` message.
  The reply's type field is set to 1 (affirm) if the lock request succeeded
  (i. e. the client now has the lock)
  or 0 (deny) if it failed
  (i. e. another client already has the lock at the moment).
  
  If the lock request field is false,
  the server clears the client's lock on the object.
  DIRTSAND also sends a :cpp:class:`plServerReplyMsg` in this case,
  with its type field set to -1 (uninitialized).
  MOSS doesn't send any reply at all.
  (TODO What does Cyan's server software do?)

:cpp:class:`plNetMsgSDLState`
-----------------------------

.. cpp:class:: plNetMsgSDLState : public plNetMsgStreamedObject
  
  *Class index = 0x02cd = 717*
  
  * **Header:** :cpp:class:`plNetMsgStreamedObject`.
  * **Is initial state:** 1-byte boolean.
    Set to true by the server when replying to a :cpp:class:`plNetMsgGameStateRequest`.
    The client always sets it to false.
    When the client receives a message with this flag set,
    it initializes all variables *not* present in the received SDL record to their default values and sets their dirty flag.
    (See also the :cpp:enumerator:`~plNetMessage::BitVectorFlags::kNewSDLState` flag.)
  * **Persist on server:** 1-byte boolean.
    Normally always set to true.
    The client sets it to false for SDL states that shouldn't be saved permanently on the server.
    In that case,
    the state is only broadcast to other clients (if requested)
    and saved temporarily as long as the game server is running
    so that it can be sent to newly joining clients.
    MOSS ignores this flag and instead only saves states
    if the blob doesn't have the volatile flag set
    and the UOID doesn't have clone IDs
    (this filters out all avatar states).
  * **Is avatar state:** 1-byte boolean.
    Set to true by the client for SDL states related/attached to an avatar.
    If true,
    the persist on server flag should be false.
    MOSS and DIRTSAND ignore this flag.
  
  Notifies the other side about the SDL state of an object in the age instance.
  The UOID field (from :cpp:class:`plNetMsgObject`) identifies the object to which the state belongs.
  The stream data is an :ref:`SDL blob <sdl_blob>`,
  including its stream header.
  
  This message can be sent both from the client to the server and the other way around.
  In most cases,
  the message is sent from the client and then possibly broadcast by the server to other clients.
  When a client joins an age instance,
  the server sends it the states of all objects in the age instance
  (see :cpp:class:`plNetMsgGameStateRequest`).
  In a few cases,
  the server also sends this message to clients unprompted,
  especially for the :ref:`AgeSDLHook <age_sdl_hook>`.
  
  The SDL blob often doesn't contain the object's entire state,
  but only the variable values that were actually changed.
  The complete state is only sent if the other side doesn't know the object's state yet ---
  that is,
  when the server sends the initial SDL states to a client joining the age instance,
  or when the client sends the SDL state for an object that the server doesn't know about yet.
  
  If the receiver already has an SDL state for the object in question,
  it updates that state using the received SDL blob.
  For every variable in the received SDL blob:
  
  * Copy the notification info from the received variable to the existing variable.
    The client does this only if the received variable has notification info at all
    and its hint string is non-empty ---
    i. e. it avoids overwriting an existing non-empty string with an empty one.
    MOSS and DIRTSAND overwrite the string unconditionally.
  * If it's a simple variable:
    
    * If the received variable does *not* have the dirty flag set,
      MOSS skips the variable entirely.
      DIRTSAND and the client don't interpret the dirty flag this way.
      (This makes no difference in practice,
      because the client only sends variables with the dirty flag set.)
    * Copy the variable value from the received variable to the existing variable.
    * Update the timestamp and flags of the existing (now updated) variable.
      
      * MOSS unconditionally sets the timestamp to the current time
        and sets the "has timestamp" flag.
        All other flags are copied as-is from the received variable.
      * DIRTSAND checks if the dirty and "want timestamp" flags are set
        and if so,
        sets the timestamp to the current time,
        sets the "has timestamp" flag
        and unsets the "want timestamp" flag.
        All other flags are copied as-is from the received variable.
      * The client unconditionally *unsets* the timestamp and all flags,
        except for the "same as default" flag,
        which is updated based on whether the variable value is equal to the default.
  * If it's a nested SDL variable,
    copy the variable value from the received variable to the existing variable.
    The client recursively updates every record in the existing variable
    using the corresponding record in the received variable.
    MOSS and DIRTSAND instead *overwrite* the existing records without any recursive updates.
  
  If the receiver doesn't have an SDL state for the object in question yet,
  the received SDL blob *must* contain a complete SDL record with all variables set.
  In this case,
  the client still follows the update process above,
  but using a new SDL record with no variables set as the "existing" state.
  DIRTSAND skips most of the update process
  and uses the received SDL record mostly unchanged,
  except for updating its timestamps as described above.
  MOSS skips the update process entirely
  and uses the received SDL record as-is.
  
  As a special case,
  the :ref:`AgeSDLHook <age_sdl_hook>` object stands for the state of the age instance itself.
  The AgeSDLHook state is handled differently on the server side than all other object states:
  it isn't stored directly as an SDL record,
  but is actually a combination of the age instance's :ref:`vault_node_sdl` vault node
  and any shard-wide settings for the age.
  For any SDL variables set in both places,
  the age instance vault node takes priority over the shard-wide settings.
  If a client changes the AgeSDLHook state,
  the changed values are always stored in the age instance vault node ---
  even when changing a variable whose value came from the shard-wide settings
  and wasn't previously set in the age instance!

:cpp:class:`plNetMsgSDLStateBCast`
----------------------------------

.. cpp:class:: plNetMsgSDLStateBCast : public plNetMsgSDLState
  
  *Class index = 0x0329 = 809*
  
  Identical structure to its superclass :cpp:class:`plNetMsgSDLState`.
  
  Handled the same way as :cpp:class:`plNetMsgSDLState`,
  except that on the server side,
  the state change is additionally broadcast to all other clients in the same age instance.
  
  MOSS broadcasts the received SDL blob as-is,
  which most likely contains an incomplete SDL record.
  DIRTSAND instead always broadcasts a complete SDL record,
  serialized from its own version of the object's state
  after it was updated with the SDL record received from the client.

:cpp:class:`plNetMsgGetSharedState`
-----------------------------------

.. cpp:class:: plNetMsgGetSharedState : public plNetMsgObject
  
  *Class index = 0x027e = 638*
  
  * **Header:** :cpp:class:`plNetMsgObject`.
  * **Shared state name:** 32-byte zero-terminated string.

:cpp:class:`plNetMsgObjStateRequest`
------------------------------------

.. cpp:class:: plNetMsgObjStateRequest : public plNetMsgObject
  
  *Class index = 0x0286 = 646*
  
  Identical structure to its superclass :cpp:class:`plNetMsgObject`.

:cpp:class:`plNetMsgStream`
---------------------------

.. cpp:class:: plNetMsgStream : public plNetMessage
  
  *Class index = 0x026c = 620*
  
  * **Header:** :cpp:class:`plNetMessage`.
  * **Stream:** :cpp:class:`plNetMsgStreamHelper`.
    The format of the stream data depends on the subclass.

:cpp:class:`plNetMsgGameMessage`
--------------------------------

.. cpp:class:: plNetMsgGameMessage : public plNetMsgStream
  
  *Class index = 0x026b = 619*
  
  * **Header:** :cpp:class:`plNetMsgStream`.
  * **Delivery time present:** 1-byte boolean.
    Whether the following delivery time field is set.
  * **Delivery time:** 8-byte :cpp:class:`plUnifiedTime`.
    Only present if the preceding boolean field is true,
    otherwise defaults to all zeroes
    (i. e. the Unix epoch).
    Set by the client when sending based on the wrapped :cpp:class:`plMessage`'s timestamp field:
    if the timestamp lies in the future,
    it's converted from local game time to an absolute time and stored in this field,
    otherwise the timestamp is set to zero and this field is left unset.
    It seems that all server implementations ignore this field and pass it on unmodified.
    If this field is set when received by the client,
    it's converted to the client's local game time and stored in the :cpp:class:`plMessage`'s timestamp field.
  
  Wraps a :cpp:class:`plMessage` to be sent between clients.
  The stream data contains the :cpp:class:`plMessage` as a serialized :cpp:class:`plCreatable` with header.
  See :doc:`plasma_messages` for details on that format.
  
  If the contained :cpp:class:`plMessage` is an instance of :cpp:class:`plLoadCloneMsg`,
  then the wrapper message must have the class :cpp:class:`plNetMsgLoadClone` instead.
  
  When the client sends (locally) a :cpp:class:`plMessage` that has the :cpp:enumerator:`~plMessage::plBCastFlags::kNetPropagate` flag set,
  it wraps the :cpp:class:`plMessage` in a :cpp:class:`plNetMsgGameMessage`
  (or one of its subclasses)
  and sends it to the game server.
  Afterwards,
  the :cpp:class:`plMessage` is also sent locally on the client side
  if it has the :cpp:enumerator:`~plMessage::plBCastFlags::kLocalPropagate` flag set
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
  
  DIRTSAND by default blocks forwarding of certain :cpp:class:`plMessage`\s
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
  * DIRTSAND sets the :cpp:enumerator:`~plMessage::plBCastFlags::kNetNonLocal` flag on the wrapped :cpp:class:`plMessage` before forwarding it
    (unless the wrapper message is a :cpp:class:`plNetMsgLoadClone` ---
    but that might just be a bug).
    MOSS never sets this flag
    and that apparently has no negative effect on gameplay.
    (TODO What does Cyan's server software do?)

:cpp:class:`plNetMsgGameMessageDirected`
----------------------------------------

.. cpp:class:: plNetMsgGameMessageDirected : public plNetMsgGameMessage
  
  *Class index = 0x032e = 814*
  
  * **Header:** :cpp:class:`plNetMsgGameMessage`.
  * **Receiver count:** 1-byte unsigned int.
    Element count of the following receiver array.
  * **Receivers:** Variable-length array of 4-byte unsigned ints,
    each a KI number of an avatar that should receive this message.
    Note that this is independent of the wrapped :cpp:class:`plMessage`'s list of receiver keys ---
    in fact,
    the latter is usually empty for directed messages.
  
  Behaves like its superclass :cpp:class:`plNetMsgGameMessage`,
  except that the server only forwards it to the specified list of receivers,
  not all avatars in the age instance.
  The wrapped :cpp:class:`plMessage` should be an instance of ``pfKIMsg``, ``plCCRCommunicationMsg``, ``plAvatarInputStateMsg``, ``plInputIfaceMgrMsg``, or :cpp:class:`plNotifyMsg`.
  
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
------------------------------

.. cpp:class:: plNetMsgLoadClone : public plNetMsgGameMessage
  
  *Class index = 0x03b3 = 947*
  
  * **Header:** :cpp:class:`plNetMsgGameMessage`.
  * **UOID:** :cpp:class:`plUoid`.
  * **Is player:** 1-byte boolean.
    If the wrapped message is a :cpp:class:`plLoadAvatarMsg`,
    this field matches its "is player" field,
    otherwise it's always set to false.
  * **Is loading:** 1-byte boolean.
    Matches the "is loading" field of the wrapped :cpp:class:`plLoadCloneMsg`.
  * **Is initial state:** 1-byte boolean.
    Set to true by the server when replying to a :cpp:class:`plNetMsgGameStateRequest`.
    The client always sets it to false.
    This field is only used by the client to count how many initial state messages it has received ---
    it has no effect on how the message itself is handled.
  
  Special case of :cpp:class:`plNetMsgGameMessage`
  used if the wrapped :cpp:class:`plMessage` is an instance of :cpp:class:`plLoadCloneMsg`
  (or its only subclass :cpp:class:`plLoadAvatarMsg`).
  
  These messages are always forwarded to all clients within the same age instance ---
  they cannot be directed and should never have the :cpp:enumerator:`~plNetMessage::BitVectorFlags::kInterAgeRouting` or :cpp:enumerator:`~plNetMessage::BitVectorFlags::kRouteToAllPlayers` flags set.

:cpp:class:`plNetMsgVoice`
--------------------------

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
    
    The voice data has the following format:
    
    * **Frames:** Variable-length array.
      The number of elements is stored in the message's frame count field.
      Each element has the following structure:
      
      * **Byte count:** 1-byte unsigned int.
        Byte count for the following data field.
      * **Data:** Variable-length byte array.
        A single Speex frame.
  
  .. cpp:enumerator:: kEncodedOpus = 1 << 2
    
    Whether the voice data is encoded using the Opus codec.
    If set,
    then :cpp:enumerator:`kEncoded` must also be set.
    H'uru clients use Opus by default,
    but this can be changed using the ``Audio.SetVoiceCodec`` console command.
    OpenUru defines this flag as the macro ``VOICE_ENH``,
    but ignores it and never sets it ---
    OpenUru clients don't support Opus compression.
    
    The voice data has the following format:
    
    * **Ignored:** 4-byte unsigned int.
      Set to 0 when writing and ignored when reading.
      This is a compatibility measure for clients that assume that all encoded/compressed voice data is Speex-encoded.
    * **Data:** Variable-length byte array
      (the entire remaining data).
      A single Opus packet.

.. cpp:class:: plNetMsgVoice : public plNetMessage
  
  *Class index = 0x0279 = 633*
  
  * **Header:** :cpp:class:`plNetMessage`.
  * **Flags:** 1-byte unsigned int.
    Describes the format/codec of the voice data.
    See :cpp:enum:`plVoiceFlags` for details.
  * **Frame count:** 1-byte unsigned int.
    Number of compressed audio frames in the voice data.
    For OpenUru clients,
    this seems to be always set to 10.
    For H'uru clients,
    it's usually very low
    (1 or 2 frames),
    regardless of whether Opus or Speex is used.
    Set to 0 for uncompressed voice data.
  * **Voice data length:** 2-byte unsigned int.
    Byte count for the following voice data.
  * **Voice data:** Variable-length byte array.
    The actual voice data.
    The format depends on the flags ---
    see :cpp:enum:`plVoiceFlags` for details.
  * **Receiver count:** 1-byte unsigned int.
    Element count for the following receiver array.
  * **Receivers:** Variable-length array of 4-byte unsigned ints,
    each a KI number of an avatar that should receive this voice chat.
    Contains the sender's KI number iff the message has the :cpp:enumerator:`~plNetMessage::BitVectorFlags::kEchoBackToSender` flag set.
    Left empty if no avatars are in voice range of the sender and echo is disabled.

:cpp:class:`plNetMsgObjectUpdateFilter`
---------------------------------------

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
-----------------------------------

.. cpp:class:: plNetMsgMembersListReq : public plNetMessage
  
  *Class index = 0x02ad = 685*
  
  Identical structure to its superclass :cpp:class:`plNetMessage`.
  
  Request a list of all other clients/avatars currently in the age instance.
  Sent by the client exactly once as part of the link-in/loading process,
  after it has finished loading the age and avatar.
  
  The server replies immediately with a :cpp:class:`plNetMsgMembersList` message.
  DIRTSAND also uses this as the trigger for sending :cpp:class:`plNetMsgLoadClone` messages for all existing clones in the age instance.
  MOSS sends the :cpp:class:`plNetMsgLoadClone` messages in response to :cpp:class:`plNetMsgGameStateRequest` instead.
  This makes practically no difference,
  because the two request messages are sent immediately after one another.

:cpp:class:`plNetMsgServerToClient`
-----------------------------------

.. cpp:class:: plNetMsgServerToClient : public plNetMessage
  
  *Class index = 0x02b2 = 690*
  
  Identical structure to its superclass :cpp:class:`plNetMessage`.

:cpp:class:`plNetMsgGroupOwner`
-------------------------------

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
--------------------------------

.. cpp:class:: plNetMsgMembersList : public plNetMsgServerToClient
  
  *Class index = 0x02ae = 686*
  
  * **Header:** :cpp:class:`plNetMsgServerToClient`.
  * **Member count:** 2-byte signed int
    (yes,
    it's signed for some reason,
    even though it can never be negative).
    Element count for the following member array.
  * **Members:** Variable-length array of :cpp:class:`plNetMsgMemberInfoHelper`\s.
  
  Reply to a :cpp:class:`plNetMsgMembersListReq`.
  The members list contains information about every other client currently in the age instance
  and the UOID of each corresponding avatar.
  The state of each of these avatars is sent separately,
  in response to the :cpp:class:`plNetMsgGameStateRequest`.

:cpp:class:`plNetMsgMemberUpdate`
---------------------------------

.. cpp:class:: plNetMsgMemberUpdate : public plNetMsgServerToClient
  
  *Class index = 0x02b1 = 689*
  
  * **Header:** :cpp:class:`plNetMsgServerToClient`.
  * **Member:** :cpp:class:`plNetMsgMemberInfoHelper`.
  * **Was added:** 1-byte boolean.
    Set to true if the member in question was added,
    or set to false if it was removed.

:cpp:class:`plNetMsgInitialAgeStateSent`
----------------------------------------

.. cpp:class:: plNetMsgInitialAgeStateSent : public plNetMsgServerToClient
  
  *Class index = 0x02b8 = 696*
  
  * **Header:** :cpp:class:`plNetMsgServerToClient`.
  * **Initial SDL state count:** 4-byte unsigned int.
    The number of :cpp:class:`plNetMsgLoadClone` and :cpp:class:`plNetMsgSDLState` messages sent by the server.
  
  Reply to a :cpp:class:`plNetMsgGameStateRequest`.
  Once the client has received this message and the expected number of clone/state messages,
  it finishes the link-in/loading process,
  hides the loading screen,
  and finally allows the player to interact with the game again.

:cpp:class:`plNetMsgListenListUpdate`
-------------------------------------

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
-------------------------------------

.. cpp:class:: plNetMsgRelevanceRegions : public plNetMessage
  
  *Class index = 0x03ac = 940*
  
  * **Header:** :cpp:class:`plNetMessage`.
  * **Regions I care about:** :cpp:class:`hsBitVector`.
    Bit mask of regions for which the client wants to receive messages.
    The least significant bit (region 0) and all bits from the "regions I'm in" field should always be set.
  * **Regions I'm in:** :cpp:class:`hsBitVector`.
    Bit mask of regions in which the client's avatar is currently located.
    At least one bit should always be set ---
    if the avatar isn't in any region,
    it's considered to be in region 0,
    so the least significant bit should be set in that case.
  
  Sent by the client when its avatar enters or leaves a relevance region.
  
  Only a few ages define relevance regions,
  namely Ae'gura (city) and Minkata.
  The regions themselves are defined using ``plRelevanceRegion`` objects in the .prp files.
  The "care about" relationships between regions are defined in a separate .csv file for the age.
  
  There is always an implicit relevance region 0,
  which represents everything not contained in any explicit relevance region.
  All avatars implicitly care about region 0
  and avatars in region 0 care about all regions.
  For ages with no relevance regions defined,
  region 0 is the only region and contains everything.
  
  Based on this information,
  the server can theoretically reduce network traffic
  by delivering broadcast messages only to clients for which they are currently relevant ---
  see the :cpp:enumerator:`~plMessage::plBCastFlags::kNetUseRelevanceRegions` flag.
  MOSS and DIRTSAND ignore this message though
  and deliver all broadcast messages to all clients.
  Unclear if Cyan's server software uses this message or respects the :cpp:enumerator:`~plMessage::plBCastFlags::kNetUseRelevanceRegions` in any way.

:cpp:class:`plNetMsgPlayerPage`
-------------------------------

.. cpp:class:: plNetMsgPlayerPage : public plNetMessage
  
  *Class index = 0x03b4 = 948*
  
  * **Header:** :cpp:class:`plNetMessage`.
  * **Unload:** 1-byte boolean.
    True if the avatar object was unloaded
    or false if it was loaded.
    Always false in practice.
  * **UOID:** :cpp:class:`plUoid`.
    Identifies the avatar object that was un-/loaded.
  
  Sent by the client after it has loaded its own avatar object.
  
  This message is only sent when an avatar is loaded for the first time,
  i. e. on the first link-in after selecting an avatar on the avatar selection screen,
  or when changing to another avatar via the console.
  When an already loaded avatar links to another age instance,
  this message is *not* sent again to the new game server.
  Although this message could also be sent when the avatar is unloaded again,
  the open-sourced client code never does this.
  
  MOSS broadcasts this message to other clients
  (even though the client doesn't support receiving it),
  but otherwise ignores it.
  DIRTSAND ignores it completely.
  Unclear if Cyan's server software does anything with it.
