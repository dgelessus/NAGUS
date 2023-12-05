Plasma messages
===============

:cpp:class:`plNetMsgGameMessage` and its subclasses contain another kind of message,
:cpp:class:`plMessage`.
These messages are mainly used locally by the clients,
but can also be propagated over the network.

Almost all :cpp:class:`plMessage`\s sent over the network originate from a client,
with the server only relaying the messages from the sender to any number of receiving clients.
In some cases,
the server also sends :cpp:class:`plMessage`\s of its own though,
e. g. when responding to a :cpp:class:`plNetMsgTestAndSet`.

Like with :cpp:class:`plNetMessage`,
the different :cpp:class:`plMessage` subclasses are identified by their :cpp:class:`plCreatable` class index
and can often be sent both from client to server and from server to client.

Below is an overview of the :cpp:class:`plMessage` class hierarchy in the open-sourced client code,
along with the corresponding class indices and the intended message direction.
Classes marked as "abstract" are only used as base classes ---
a message should never be a direct instance of one of these classes,
only of one of their non-abstract subclasses.

.. note::
  
  This is not a complete list.
  The open-sourced client code contains around 200 different :cpp:class:`plMessage` subclasses,
  many of which are either completely unused
  or only used locally and never propagated over the network.
  
  Eventually,
  this list should contain all :cpp:class:`plMessage` subclasses that can be propagated over the network,
  but at the moment it only lists a few important messages,
  such as ones that originate from the server
  or require special server-side handling.

* :cpp:class:`plMessage` = 0x0202 = 514 (abstract)
  
  * :cpp:class:`plLoadCloneMsg` = 0x0253 = 595
    
    * :cpp:class:`plLoadAvatarMsg` = 0x03b1 = 945
  * :cpp:class:`plServerReplyMsg` = 0x026f = 623
  * :cpp:class:`plNotifyMsg` = 0x02ed = 749
  * :cpp:class:`plParticleTransferMsg` = 0x0333 = 819
  * :cpp:class:`plParticleKillMsg` = 0x0334 = 820

Common data types
-----------------

Assorted data types used by the message classes below.

.. seealso::
  
  :ref:`common_data_types` under :doc:`../protocol`.

.. cpp:class:: hsPoint3
  
  * **X:** 4-byte floating-point number.
  * **Y:** 4-byte floating-point number.
  * **Z:** 4-byte floating-point number.

.. cpp:class:: hsVector3
  
  * **X:** 4-byte floating-point number.
  * **Y:** 4-byte floating-point number.
  * **Z:** 4-byte floating-point number.

:cpp:class:`plMessage`
----------------------

.. cpp:class:: plMessage : public plCreatable
  
  *Class index = 0x0202 = 514*
  
  The serialized format has the following common header structure,
  with any subclass-specific data directly after the header.
  
  * **Header:** :cpp:class:`plCreatable` class index header.
    (Strictly speaking,
    this isn't part of the serialized :cpp:class:`plMessage` itself,
    but in practice,
    :cpp:class:`plMessage`\s are always serialized with a header.)
  * **Sender:** :cpp:class:`plKey`.
    Identifies the object that sent this message.
    Might be ``nullptr``?
  * **Receiver count:** 4-byte unsigned int
    (or signed in the original/OpenUru code for some reason).
    Element count for the following receiver array.
  * **Receivers:** Variable-length array of :cpp:class:`plKey`\s.
    Objects that this message should be sent to.
    May be ignored depending on the broadcast flags.
    Any of the elements might be ``nullptr``?
  * **Timestamp:** 8-byte floating-point number.
    Allows artificially delaying the message
    so that it's delivered only after a specific point in time has passed.
    If the time is already in the past,
    the message is delivered immediately.
    The value zero indicates that the message shouldn't be delayed artificially.
    
    .. note::
      
      Although this field is serialized and sent over the network,
      it's basically ignored in the serialized data.
      The timestamp is in local game time
      (as returned by ``hsTimer::GetSysSeconds``),
      which only makes sense to the client that sent the message.
      When the message is sent over the network,
      the timestamp is converted to an absolute :cpp:class:`plUnifiedTime`
      and stored in the delivery time field of the wrapper :cpp:class:`plNetMsgGameMessage`.
      When the message is received,
      that absolute time is used to re-initialize this timestamp field
      with the corresponding local game time for the receiving client.
  * **Broadcast flags:** 4-byte unsigned int.
    Various boolean flags that describe how the message should be (and has already been) propagated locally and over the network.
    See :cpp:enum:`plBCastFlags` for details.
  
  .. cpp:enum:: plBCastFlags
    
    .. cpp:enumerator:: kBCastByType = 1 << 0
      
      If set,
      the receiver objects array is ignored
      and the message is instead broadcast to all objects that have registered themselves as receivers for the message's class
      or any of its superclasses.
      
      This flag is only relevant to local propagation
      and is ignored by the server.
    
    .. cpp:enumerator:: kPropagateToChildren = 1 << 2
      
      If a ``plSceneObject`` (or subclass) instance receives a message with this flag set,
      it automatically propagates the message to all of its children,
      after any handling by the object itself
      and forwarding to the object's modifiers,
      if enabled
      (see :cpp:enumerator:`kPropagateToModifiers`).
      
      This flag is only relevant to local propagation
      and is ignored by the server.
    
    .. cpp:enumerator:: kBCastByExactType = 1 << 3
      
      Behaves exactly like :cpp:enumerator:`kBCastByType`.
      Despite the name,
      messages with this flag set
      are also received by objects that have registered for superclasses of the message class.
      
      This flag is only relevant to local propagation
      and is ignored by the server.
    
    .. cpp:enumerator:: kPropagateToModifiers = 1 << 4
      
      If a ``plSceneObject`` (or subclass) instance receives a message with this flag set,
      it automatically propagates the message to all of its modifiers,
      after any handling by the object itself,
      but before forwarding to the object's children,
      if enabled
      (see :cpp:enumerator:`kPropagateToChildren`).
      
      This flag is only relevant to local propagation
      and is ignored by the server.
    
    .. cpp:enumerator:: kClearAfterBCast = 1 << 5
      
      Should only be set if :cpp:enumerator:`kBCastByType` or :cpp:enumerator:`kBCastByExactType` is also set ---
      this flag is ignored otherwise.
      If set,
      then as soon as the message is sent,
      all receivers for the message's class are automatically unregistered.
      The receivers will still receive this message,
      but not any further type-based broadcast messages of this class.
      Only used by ``plTransformMsg`` and its only subclass ``plDelayedTransformMsg``.
      
      This flag is only relevant to local propagation
      and is ignored by the server.
    
    .. cpp:enumerator:: kNetPropagate = 1 << 6
      
      Enables propagation of the message over the network to other clients.
      This flag should be set for all game messages sent by clients to the server.
      Game messages originating from the server itself
      (i. e. not propagated from another client)
      do *not* have this flag set.
      
      Even with this flag set,
      the message is not *guaranteed* to be sent over the network.
      See the :cpp:enumerator:`kNetSent`,
      :cpp:enumerator:`kNetForce`,
      and :cpp:enumerator:`kCCRSendToAllPlayers` flags for details.
      
      Although this flag controls network propagation,
      it's ignored by the server and only used by clients.
    
    .. cpp:enumerator:: kNetSent = 1 << 7
      
      Should only be set if :cpp:enumerator:`kNetPropagate` is also set.
      If set,
      the client won't propagate the message over the network again.
      This can be bypassed using the :cpp:enumerator:`kNetForce` and :cpp:enumerator:`kCCRSendToAllPlayers` flags.
      
      Set by the client after the message has been sent over the network once.
      Also set for messages that the client has received over the network
      if they have the :cpp:enumerator:`kNetPropagate` flag set
      (i. e. the message originated from another client and not the server itself).
      This flag is inherited by child messages.
      
      Although this flag controls network propagation,
      it's ignored by the server and only used by clients.
    
    .. cpp:enumerator:: kNetUseRelevanceRegions = 1 << 8
      
      Should only be set if :cpp:enumerator:`kNetPropagate` is also set.
      Only used with ``plAvatarInputStateMsg`` and ``plControlEventMsg``.
      
      This corresponds to the :cpp:class:`plNetMsgGameMessage` flag :cpp:enumerator:`~plNetMessage::BitVectorFlags::kUseRelevanceRegions`.
      See that documentation for details.
    
    .. cpp:enumerator:: kNetForce = 1 << 9
      
      Should only be set if :cpp:enumerator:`kNetPropagate` is also set.
      If set,
      the :cpp:enumerator:`kNetSent` flag is ignored
      and the message is *always* sent over the network when it's sent locally.
      
      Although this flag controls network propagation,
      it's ignored by the server and only used by clients.
    
    .. cpp:enumerator:: kNetNonLocal = 1 << 10
      
      Set by the client for messages received over the network.
      This flag is inherited by child messages.
      
      DIRTSAND also sets this flag on all game messages that it propagates between clients,
      even though the receiving clients should also set this flag themselves.
      MOSS doesn't touch this flag.
      (TODO What does Cyan's server software do?)
    
    .. cpp:enumerator:: kLocalPropagate = 1 << 11
      
      Whether the message should be propagated locally.
      This flag is set for all messages by default,
      but may be unset to propagate a message only over the network.
      If this flag isn't set,
      then :cpp:enumerator:`kNetPropagate` should always be set,
      otherwise the message won't be propagated anywhere at all!
      
      This flag is set by the client for messages received over the network
      so that they are propagated locally within the receiving client.
      It's also set on :cpp:class:`plServerReplyMsg`\s sent by MOSS and DIRTSAND,
      even though the receiving clients should also set this flag themselves.
      The flag is otherwise ignored by the server.
    
    .. cpp:enumerator:: kMsgWatch = 1 << 12
      
      Debugging flag.
      Although it's set in one place in the open-sourced client code,
      it's ignored by the client and all fan servers.
      Unclear if Cyan's server software does anything with it.
    
    .. cpp:enumerator:: kNetStartCascade = 1 << 13
      
      Set by the client for messages received over the network
      and then unset again once the received message has been fully propagated locally.
      This flag is *not* inherited by child messages.
      
      This flag should never be sent on messages sent over the network.
    
    .. cpp:enumerator:: kNetAllowInterAge = 1 << 14
      
      Should only be set if :cpp:enumerator:`kNetPropagate` is also set.
      Only used with ``pfKIMsg``, ``plCCRCommunicationMsg``, ``plLinkingMgrMsg``, and ``plLinkToAgeMsg``.
      
      This corresponds to the :cpp:class:`plNetMsgGameMessage` flag :cpp:enumerator:`~plNetMessage::BitVectorFlags::kInterAgeRouting`.
      See that documentation for details.
    
    .. cpp:enumerator:: kNetSendUnreliable = 1 << 15
      
      Should only be set if :cpp:enumerator:`kNetPropagate` is also set.
      If this flag is set,
      the wrapper :cpp:class:`plNetMsgGameMessage` flag :cpp:enumerator:`~plNetMessage::BitVectorFlags::kNeedsReliableSend` should be *unset*.
      Nearly unused in the open-sourced client code
      and ignored by MOSS and DIRTSAND.
      Unclear if Cyan's server software does anything with it.
    
    .. cpp:enumerator:: kCCRSendToAllPlayers = 1 << 16
      
      Should only be set if :cpp:enumerator:`kNetPropagate` is also set.
      
      Like :cpp:enumerator:`kNetForce`,
      this flag causes the :cpp:enumerator:`kNetSent` flag to be ignored ignored
      and the message is *always* sent over the network when it's sent locally.
      
      The open-sourced client code and OpenUru clients never set this flag ---
      most likely only Cyan's internal CCR client used it.
      Internal H'uru clients set this flag when sending CCR broadcast chat messages
      (using the ``/system`` chat command or the All Players list).
      
      This corresponds to the :cpp:class:`plNetMsgGameMessage` flag :cpp:enumerator:`~plNetMessage::BitVectorFlags::kRouteToAllPlayers`.
      See that documentation for details.
    
    .. cpp:enumerator:: kNetCreatedRemotely = 1 << 17
      
      Set by the client for messages received over the network.
      Unlike :cpp:enumerator:`kNetNonLocal`,
      this flag is *not* inherited by child messages,
      and unlike :cpp:enumerator:`kNetStartCascade`,
      it remains set after the message has been propagated locally.
      
      This flag should never be sent on messages sent over the network.
      
      Although this flag is related to network propagation,
      it's ignored by the server and only used by clients.

:cpp:class:`plLoadCloneMsg`
---------------------------

.. cpp:class:: plLoadCloneMsg : public plMessage
  
  *Class index = 0x0253 = 595*
  
  * **Header:** :cpp:class:`plMessage`.
  * **Clone:** :cpp:class:`plKey`.
    The clone object that this message is about.
  * **Requestor:** :cpp:class:`plKey`.
  * **Originating player:** 4-byte unsigned int.
    KI number of the player that created the clone.
    For player avatar clones,
    this should be the avatar's KI number.
  * **User data:** 4-byte unsigned int.
  * **Is valid:** 1-byte boolean.
    Should always be true when sent over the network.
    May be set to false internally by the client for messages that aren't fully constructed yet.
  * **Is loading:** 1-byte boolean.
    Set to true if this message loads a clone,
    or to false if it unloads a clone.
  * **Trigger message:** Serialized :cpp:class:`plCreatable` with header.
    Must be an instance of a :cpp:class:`plMessage` subclass.
    In practice,
    this is usually ``nullptr``,
    but may sometimes be a :cpp:class:`plParticleTransferMsg`.

:cpp:class:`plLoadAvatarMsg`
----------------------------

.. cpp:class:: plLoadAvatarMsg : public plLoadCloneMsg
  
  *Class index = 0x03b1 = 945*
  
  * **Header:** :cpp:class:`plLoadCloneMsg`.
  * **Is player:** 1-byte boolean.
    Set to true if the clone is a player avatar,
    or to false if it's an NPC avatar.
  * **Spawn point:** :cpp:class:`plKey`.
    The ``plSceneObject`` for the spawn point at which the avatar will appear.
  * **Initial task present:** 1-byte boolean.
    Whether the following initial task field is present.
  * **Initial task:** Serialized :cpp:class:`plCreatable` with header.
    Must be an instance of a ``plAvTask`` subclass.
    Only present if the preceding boolean field is true,
    in which case the :cpp:class:`plCreatable` should not be ``nullptr``.
    If the preceding boolean field is false,
    this field is not present and defaults to ``nullptr``.
  * **User string:** :ref:`SafeString <safe_string>`.
    Usually empty,
    but sometimes set to a short description
    (e. g. for quabs).
    Ignored by the client and all fan servers.

:cpp:class:`plServerReplyMsg`
-----------------------------

.. cpp:class:: plServerReplyMsg : public plMessage
  
  *Class index = 0x026f = 623*
  
  * **Header:** :cpp:class:`plMessage`.
  * **Type:** 4-byte signed int.
    One of the following:
    
    * Uninitialized = -1 (normally not sent over the network)
    * Deny = 0
    * Affirm = 1
  
  Reply to a :cpp:class:`plNetMsgTestAndSet`.

:cpp:class:`plNotifyMsg`
------------------------

.. cpp:class:: proEventData
  
  A single event inside a :cpp:class:`plNotifyMsg`.
  
  All events have the following common header structure,
  with any event type-specific data directly after the header.
  
  * **Type:** 4-byte signed int.
    Identifies the event type and the structure of the following event data.
    One of the following:
    
    * :cpp:class:`proCollisionEventData` = 1
    * :cpp:class:`proPickedEventData` = 2
    * :cpp:class:`proControlKeyEventData` = 3 (unused)
    * :cpp:class:`proVariableEventData` = 4
    * :cpp:class:`proFacingEventData` = 5
    * :cpp:class:`proContainedEventData` = 6
    * :cpp:class:`proActivateEventData` = 7
    * :cpp:class:`proCallbackEventData` = 8 (unused)
    * :cpp:class:`proResponderStateEventData` = 9
    * :cpp:class:`proMultiStageEventData` = 10
    * :cpp:class:`proSpawnedEventData` = 11
    * ``proClickDragEventData`` = 12 (unused, cannot be sent over the network)
    * :cpp:class:`proCoopEventData` = 13
    * :cpp:class:`proOfferLinkingBookEventData` = 14
    * :cpp:class:`proBookEventData` = 15 (unused over the network)
    * :cpp:class:`proClimbingBlockerHitEventData` = 16 (unused)

.. cpp:class:: proCollisionEventData : public proEventData
  
  *Type = 1*
  
  * **Header:** :cpp:class:`proEventData`.
  * **Enter:** 1-byte boolean.
    True if the hitter entered the hittee
    or false if it exited.
  * **Hitter:** :cpp:class:`plKey`.
    The object that collided with the hittee.
  * **Hittee:** :cpp:class:`plKey`.
    The object that the hitter collided with.
  
  One object collided (or stopped colliding) with another.
  Used mainly by ``plActivatorConditionalObject`` (in combination with ``plCollisionDetector``) and ``plVolumeSensorConditionalObject``.

.. cpp:class:: proPickedEventData : public proEventData
  
  *Type = 2*
  
  * **Header:** :cpp:class:`proEventData`.
  * **Picker:** :cpp:class:`plKey`.
    The object that did the "picking".
    This should always be the ``plSceneObject`` clone for the avatar of the player who clicked on the object.
  * **Picked:** :cpp:class:`plKey`.
    The object that was "picked" (clicked on) by the picker.
  * **Enabled:** 1-byte boolean.
    True if the object is now "picked" (mouse click began)
    or false if it's no longer "picked" (mouse click ended).
  * **Hit point:** 12-byte :cpp:class:`hsPoint3`.
    The absolute 3D coordinates where the mouse "hit" the object.
    Set to all zeroes if the enabled field is false
    or the picked event wasn't caused by a normal mouse click.
  
  An object was clicked on by the player.
  Used mainly by ``plActivatorConditionalObject`` (in combination with ``plPickingDetector``).

.. cpp:class:: proControlKeyEventData : public proEventData
  
  *Type = 3*
  
  * **Header:** :cpp:class:`proEventData`.
  * **Control key:** 4-byte signed int.
  * **Down:** 1-byte boolean.
  
  Implemented in the open-sourced client code,
  but never used in the code
  and also seems to be never used in any .prp files.
  Should never be sent over the network.

.. cpp:class:: proVariableEventData : public proEventData
  
  *Type = 4*
  
  * **Header:** :cpp:class:`proEventData`.
  * **Variable name:** :ref:`SafeString <safe_string>`.
    Has no pre-defined meaning.
    Usually an identifier chosen by the sender so the receivers can distinguish multiple different types of notifications/events.
    Some code also uses the name field to encode additional values (in string form) if the one provided value field isn't enough.
  * **Data type:** 4-byte signed int.
    Indicates which of the value fields (if any) are used and what data type is stored in them.
    May be one of:
    
    * Float = 1
    * Key = 2
    * Int = 3
    * Null = 4
  * **Number value:** 4-byte value.
    The value of a numeric variable.
    Has no pre-defined meaning.
    If the data type is float,
    this is a 4-byte floating-point value.
    If the data type is int,
    this is a 4-byte signed int.
    For all other data types,
    this field is ignored when reading
    and set to all zero bytes when writing.
  * **Key value:** :cpp:class:`plKey`.
    The value of a key variable.
    Has no pre-defined meaning.
    If the data type isn't key,
    this field should be ``nullptr``.
  
  Free-form event containing a named variable whose value is a single number or an UOID.
  Used mainly by game scripts to send notifications that don't fit any of the other pre-defined event types,
  but still need more data than the basic :cpp:class:`plNotifyMsg` fields.

.. cpp:class:: proFacingEventData : public proEventData
  
  *Type = 5*
  
  * **Header:** :cpp:class:`proEventData`.
  * **Facer:** :cpp:class:`plKey`.
    The object that is facing the facee.
    This should always be an avatar ``plSceneObject`` clone.
  * **Facee:** :cpp:class:`plKey`.
    The object that the facer is facing.
  * **Dot product:** 4-byte floating-point number.
    The dot product of the view vectors of the facer and facee.
    This indicates how closely the objects are facing each other.
  * **Enabled:** 1-byte boolean.
    True if the facer is now facing the facee
    or false if this is no longer the case.
  
  One object is facing (or stopped facing) another.
  Used mainly by ``plFacingConditionalObject``.

.. cpp:class:: proContainedEventData : public proEventData
  
  *Type = 6*
  
  * **Header:** :cpp:class:`proEventData`.
  * **Contained:** :cpp:class:`plKey`.
    The object located in the container.
  * **Container:** :cpp:class:`plKey`.
    The object in which the contained object is located.
  * **Entering:** 1-byte boolean.
    True if the contained object has entered the container
    or false if the contained object has left the container.
  
  One object is located within (or stopped being located within) another.
  Used mainly by ``plObjectInBoxConditionalObject``.

.. cpp:class:: proActivateEventData : public proEventData
  
  *Type = 7*
  
  * **Header:** :cpp:class:`proEventData`.
  * **Active:** 1-byte boolean.
    Always set to true.
    Not used by the open-sourced client code.
  * **Activate:** 1-byte boolean.
    True if the sender was activated
    or false if it's no longer activated.
    Should always match the state field of the containing :cpp:class:`plNotifyMsg`.
  
  The sender of the :cpp:class:`plNotifyMsg` was activated
  (or is no longer activated).
  ``plLogicModifier`` inserts this as the last event in every :cpp:class:`plNotifyMsg` that it sends.

.. cpp:class:: proCallbackEventData : public proEventData
  
  *Type = 8*
  
  * **Header:** :cpp:class:`proEventData`.
  * **Callback event type:** 4-byte signed int.
    The few uses all set this field to 1.
  
  Seems to be a legacy leftover that's almost,
  but not completely,
  unused.
  Implemented in the open-sourced client code,
  but never used anywhere in the engine or scripts.
  Only found in the .prp files for Ahnonay and Er'cana,
  as part of the ``plResponderModifier``\s for shell cloths.

.. cpp:class:: proResponderStateEventData : public proEventData
  
  *Type = 9*
  
  * **Header:** :cpp:class:`proEventData`.
  * **State:** 4-byte signed int.
    The responder state to switch to.
  
  Tells the receiving ``plResponderModifier`` to ignore its current state and instead switch to the given state and run that.
  The :cpp:class:`plNotifyMsg` type field still controls if and how the state's commands are run
  (normally, fast-forward, or not at all).

.. cpp:class:: proMultiStageEventData : public proEventData
  
  *Type = 10*
  
  * **Header:** :cpp:class:`proEventData`.
  * **Stage:** 4-byte signed int.
    The stage that was entered or finished.
  * **Event:** 4-byte signed int.
    One of the following:
    
    * Enter stage = 1: The stage in question has been entered.
    * Beginning of loop = 2: Unused.
    * Advance next stage = 3: The stage in question has finished
      and the behavior will advance to the next stage.
    * Regress previous stage = 3: The stage in question has finished
      and the behavior will return to the previous stage.
  * **Avatar:** :cpp:class:`plKey`.
    The avatar ``plSceneObject`` clone that is doing the multi-stage behavior in question.
  
  A multi-stage behavior entered or finished a stage.
  Used by ``plAnimStage``.

.. cpp:class:: proSpawnedEventData : public proEventData
  
  *Type = 11*
  
  * **Header:** :cpp:class:`proEventData`.
  * **Spawner:** :cpp:class:`plKey`.
    The ``plNPCSpawnMod`` that spawned the NPC avatar.
  * **Spawnee:** :cpp:class:`plKey`.
    The ``plSceneObject`` clone for the newly spawned NPC avatar.
  
  An NPC avatar was spawned.
  Used by ``plNPCSpawnMod``.

.. cpp:class:: proCoopEventData : public proEventData
  
  *Type = 13*
  
  * **Header:** :cpp:class:`proEventData`.
  * **Initiator KI number:** 4-byte unsigned int.
    KI number of the avatar that initiated the cooperative action.
  * **Serial number:** 2-byte unsigned int.
    Identifies the cooperative action.
    This number is chosen by the initiating client from a local counter,
    so it's only unique in combination with the initiator KI number.
  
  Included along with a :cpp:class:`proMultiStageEventData` to indicate that the multi-stage behavior is part of a cooperative action between multiple avatars.
  Used by ``plAvBrainCoop``.

.. cpp:class:: proOfferLinkingBookEventData : public proEventData
  
  *Type = 14*
  
  * **Header:** :cpp:class:`proEventData`.
  * **Offerer:** :cpp:class:`plKey`.
    The ``plSceneObject`` clone for the avatar that is sharing the book.
  * **Event:** 4-byte signed int.
    Indicates which step of the book sharing process is taking place.
    (The open-sourced client code calls this field ``targetAge`` in some places,
    but this seems to be an outdated name and doesn't match its actual usage.)
    May be one of the following:
    
    * Finish = 0: Only used locally and should never be sent over the network.
    * Offer = 999: The offerer has begun offering a book to the offeree.
    * Rescind = -999: The offerer has rescinded a previous offer to the offeree.
  * **Offeree KI number:** 4-byte unsigned int.
    KI number of the avatar with whom the offerer is sharing the book.
  
  An avatar is offering (or stopped offering) to share a linking book with another avatar.
  Used by ``plSceneInputInterface``.

.. cpp:class:: proBookEventData : public proEventData
  
  *Type = 15*
  
  * **Header:** :cpp:class:`proEventData`.
  * **Event:** 4-byte unsigned int.
  * **Link ID:** 4-byte unsigned int.
  
  Only used locally.
  Should never be sent over the network.

.. cpp:class:: proClimbingBlockerHitEventData : public proEventData
  
  *Type = 16*
  
  * **Header:** :cpp:class:`proEventData`.
  * **Blocker:** :cpp:class:`plKey`.
  
  Implemented in the open-sourced client code,
  but never used in the code
  and also seems to be never used in any .prp files.
  Should never be sent over the network.

.. cpp:class:: plNotifyMsg : public plMessage
  
  *Class index = 0x02ed = 749*
  
  * **Header:** :cpp:class:`plMessage`.
  * **Notification type:** 4-byte signed int.
    Often set to 0 and not used.
    Seems to be only relevant for messages sent to a ``plResponderModifier``,
    where a few of the defined types have a special meaning.
    All other types behave the same.
    The following types are defined:
    
    * Activator = 0: Default type used by most :cpp:class:`plNotifyMsg`\s.
    * Variable notification = 1: Seems to be unused.
    * Notify self = 2: Seems to be unused.
    * Responder fast-forward = 3: When received by a ``plResponderModifier``,
      the responder state is run in "fast-forward" mode,
      where its commands are skipped as much as possible.
      For example,
      animations and sounds immediately switch to their finished state without being played in real time.
      All commands are run at once,
      ignoring any "wait on" fields,
      and then the responder switches directly to the next state.
    * Responder change state = 4: When received by a ``plResponderModifier``,
      the responder state won't run at all.
      This is only useful in combination with a :cpp:class:`proResponderStateEventData`,
      to make the responder switch directly to a different state without any other actions.
  * **State:** 4-byte floating-point number.
    Has no pre-defined meaning.
    Despite the type,
    this field normally only has one of two values:
    0.0 (false) or 1.0 (true).
  * **ID:** 4-byte signed int.
    Has no pre-defined meaning.
    Almost always unused and set to 0.
    Seems to be only relevant for ``plAvLadderMod``.
  * **Event count:** 4-byte unsigned int.
    Element count for the following events array.
  * **Events:** Variable-length array of :cpp:class:`proEventData` values.
    Contains additional info regarding what exactly the notification is about.
    For example,
    for :cpp:class:`plNotifyMsg`\s sent by a ``plLogicModifier``,
    this contains info about all the conditions that had to be met for the modifier to trigger.
    May be empty for some simple notifications,
    for example some :cpp:class:`plNotifyMsg`\s sent to a ``plResponderModifier``.
  
  General-purpose notification sent for many kinds of gameplay events.
  Primarily used by ``plLogicModifier`` and ``plResponderModifier``,
  but also by other engine code and many scripts for their own purposes.
  
  A ``plLogicModifier`` object will only send a :cpp:class:`plNotifyMsg` while holding a server-side lock on itself using :cpp:class:`plNetMsgTestAndSet`.
  Other users of :cpp:class:`plNotifyMsg` don't use any locking like this.
  
  :cpp:class:`plNotifyMsg`\s are not only created by the engine code and scripts,
  but can also be read from .prp files,
  usually as part of a ``plLogicModifier`` or other modifier.
  Often,
  a :cpp:class:`plNotifyMsg` is read from the .prp file
  and then adjusted by the engine code before being sent.
  This makes it difficult to say in general how :cpp:class:`plNotifyMsg`\s can/should be structured.

:cpp:class:`plParticleTransferMsg`
----------------------------------

.. cpp:class:: plParticleTransferMsg : public plMessage
  
  *Class index = 0x0333 = 819*
  
  * **Header:** :cpp:class:`plMessage`.
  * **Particle system scene object:** :cpp:class:`plKey`.
    The original particle system from which to transfer particles.
  * **Particle count to transfer:** 2-byte unsigned int.
    How many particles to transfer.

:cpp:class:`plParticleKillMsg`
------------------------------

.. cpp:class:: plParticleKillMsg : public plMessage
  
  *Class index = 0x0334 = 820*
  
  * **Header:** :cpp:class:`plMessage`.
  * **Amount to kill:** 4-byte floating-point number.
    How many particles to remove.
    If the percentage flag is set,
    this is a fractional amount (from 0 to 1) relative to the current particle count,
    otherwise it's an absolute number.
  * **Time left:** 4-byte floating-point number.
  * **Flags:** 1-byte unsigned int.
    The following flags are defined:
    
    * **Immortal only** = 1 << 0
    * **Percentage** = 1 << 1: Whether the amount to kill is a fractional amount or an absolute number.
