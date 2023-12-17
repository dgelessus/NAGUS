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
  * :cpp:class:`plEnableMsg` = 0x0254 = 596
  * :cpp:class:`plServerReplyMsg` = 0x026f = 623
  * :cpp:class:`plMessageWithCallbacks` = 0x0283 = 643 (abstract)
    
    * :cpp:class:`plAnimCmdMsg` = 0x0206 = 518
  * :cpp:class:`plAvatarMsg` = 0x0297 = 663 (abstract)
    
    * :cpp:class:`plAvTaskMsg` = 0x0298 = 664
      
      * :cpp:class:`plAvSeekMsg` = 0x0299 = 665
    * :cpp:class:`plAvBrainGenericMsg` = 0x038f = 911
  * :cpp:class:`plNotifyMsg` = 0x02ed = 749
  * :cpp:class:`plLinkEffectsTriggerMsg` = 0x0300 = 768
  * :cpp:class:`plParticleTransferMsg` = 0x0333 = 819
  * :cpp:class:`plParticleKillMsg` = 0x0334 = 820
  * :cpp:class:`plAvatarInputStateMsg` = 0x0347 = 839
  * :cpp:class:`plInputIfaceMgrMsg` = 0x0363 = 867
  * :cpp:class:`pfKIMsg` = 0x0364 = 868

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

Avatar brains
^^^^^^^^^^^^^

* :cpp:class:`plArmatureBrain` = 0x035b = 859
  
  * ``plAvBrainHuman`` = 0x035c = 860
    
    * ``plAvBrainRideAnimatedPhysical`` = 0x049e = 1182 (unused, cannot be sent over the network)
  * ``plAvBrainCritter`` = 0x035d = 861 (cannot be sent over the network)
  * ``plAvBrainDrive`` = 0x035e = 862 (cannot be sent over the network)
  * :cpp:class:`plAvBrainGeneric` = 0x0360 = 864
  
    * ``plAvBrainCoop`` = 0x045f = 1119
  * ``plAvBrainSwim`` = 0x042d = 1069 (cannot be sent over the network)
  * ``plAvBrainClimb`` = 0x0453 = 1107 (cannot be sent over the network)

.. cpp:class:: plArmatureBrain : public plCreatable
  
  *Class index = 0x035b = 859*
  
  * **Header:** :cpp:class:`plCreatable` class index header.
    (Strictly speaking,
    this isn't part of the serialized :cpp:class:`plArmatureBrain` itself,
    but in practice,
    :cpp:class:`plArmatureBrain`\s are always serialized with a header.)
  * **Reserved:** 21 bytes.
    Set to 0 when writing and ignored when reading.
    For backwards compatibility with old Plasma versions.

.. cpp:class:: plAnimStage : public plCreatable
  
  *Class index = 0x0371 = 881*
  
  * **Header:** :cpp:class:`plCreatable` class index header.
    (Strictly speaking,
    this isn't part of the serialized :cpp:class:`plAnimStage` itself,
    but in practice,
    :cpp:class:`plAnimStage`\s are always serialized with a header.)
  * **Animation name:** :ref:`SafeString <safe_string>`.
  * **Notify flags:** 1-byte unsigned int.
    The following flags are defined:
    
    * **Enter** = 1 << 0
    * **Loop** = 1 << 1
    * **Advance** = 1 << 2
    * **Regress** = 1 << 3
  * **Forward type:** 4-byte unsigned int.
    The following types are defined:
    
    * None = 0
    * On key = 1
    * Automatic = 2
  * **Backward type:** 4-byte unsigned int.
    Supports the same values as the forward type field.
  * **Advance type:** 4-byte unsigned int.
    The following types are defined:
    
    * None = 0
    * On move = 1
    * Automatic = 2
    * On any key = 3
  * **Regress type:** 4-byte unsigned int.
    Supports the same values as the advance type field.
  * **Loop count:** 4-byte signed int.
  * **Do advance to:** 1-byte boolean.
  * **Advance to:** 4-byte unsigned int.
  * **Do regress to:** 1-byte boolean.
  * **Regress to:** 4-byte unsigned int.

.. cpp:class:: plAvBrainGeneric : public plArmatureBrain
  
  *Class index = 0x0360 = 864*
  
  * **Header:** :cpp:class:`plArmatureBrain`.
  * **Stage count:** 4-byte signed int.
    Element count for the following stage array.
  * **Stages:** Variable-length array.
    Each element has the following structure:
    
    * **Stage:** Serialized :cpp:class:`plCreatable` with header.
      Must be an instance of a :cpp:class:`plAnimStage` subclass.
    * **Local time:** 4-byte floating-point number.
    * **Length:** 4-byte floating-point number.
    * **Current loop:** 4-byte signed int.
    * **Attached:** 1-byte boolean.
  * **Current stage:** 4-byte signed int.
  * **Brain type:** 4-byte unsigned int.
    The following types are defined:
    
    * Generic = 0
    * Ladder = 1
    * Sit = 2
    * Sit on ground = 3
    * Emote = 4
    * AFK = 5
  * **Exit flags:** 4-byte unsigned int.
    The following flags are defined:
    
    * **Any task** = 1 << 0
    * **New brain** = 1 << 1
    * **Any input** = 1 << 2
  * **Mode:** 1-byte unsigned int.
    The following modes are defined:
    
    * Entering = 1
    * Normal = 2
    * Fading in = 3
    * Fading out = 4
    * Exit = 5
    * Abort = 6
  * **Forward:** 1-byte boolean.
  * **Start message present:** 1-byte boolean.
    Whether the following start message field is present.
  * **Start message:** Serialized :cpp:class:`plCreatable` with header.
    Must be an instance of a :cpp:class:`plMessage` subclass.
    Only present if the preceding boolean field is true,
    in which case the :cpp:class:`plCreatable` should not be ``nullptr``.
    If the preceding boolean field is false,
    this field is not present and defaults to ``nullptr``.
  * **End message present:** 1-byte boolean.
    Whether the following end message field is present.
  * **End message:** Serialized :cpp:class:`plCreatable` with header.
    Must be an instance of a :cpp:class:`plMessage` subclass.
    Only present if the preceding boolean field is true,
    in which case the :cpp:class:`plCreatable` should not be ``nullptr``.
    If the preceding boolean field is false,
    this field is not present and defaults to ``nullptr``.
  * **Fade in:** 4-byte floating-point number.
  * **Fade out:** 4-byte floating-point number.
  * **Move mode:** 1-byte unsigned int.
    The following modes are defined:
    
    * Absolute = 0
    * Relative = 1
    * Normal = 2
    * Standstill = 3
  * **Body usage:** 1-byte unsigned int.
    The following values are defined:
    
    * Unknown = 0
    * Upper = 1
    * Full = 2
    * Lower = 3
  * **Recipient:** :cpp:class:`plKey`.

Avatar tasks
^^^^^^^^^^^^

* :cpp:class:`plAvTask` = 0x036a = 874 (abstract)
  
  * :cpp:class:`plAvAnimTask` = 0x036b = 875
  * ``plAvSeekTask`` = 0x036c = 876 (cannot be sent over the network)
  * :cpp:class:`plAvOneShotTask` = 0x036e = 878 (cannot be sent over the network)
    
    * :cpp:class:`plAvOneShotLinkTask` = 0x0488 = 1160
  * :cpp:class:`plAvTaskBrain` = 0x0370 = 880
  * ``plAvTaskSeek`` = 0x0390 = 912 (cannot be sent over the network)

.. cpp:class:: plAvTask : public plCreatable
  
  *Class index = 0x036a = 874*
  
  * **Header:** :cpp:class:`plCreatable` class index header.
    (Strictly speaking,
    this isn't part of the serialized :cpp:class:`plAvTask` itself,
    but in practice,
    :cpp:class:`plAvTask`\s are always serialized with a header.)

.. cpp:class:: plAvAnimTask : public plAvTask
  
  *Class index = 0x036b = 875*
  
  * **Header:** :cpp:class:`plAvTask`.
  * **Animation name:** :ref:`SafeString <safe_string>`.
  * **Initial blend:** 4-byte floating-point number.
  * **Target blend:** 4-byte floating-point number.
  * **Fade speed:** 4-byte floating-point number.
  * **Time:** 4-byte floating-point number.
  * **Start:** 1-byte boolean.
  * **Loop:** 1-byte boolean.
  * **Attach:** 1-byte boolean.

.. cpp:class:: plAvOneShotTask : public plAvTask
  
  *Class index = 0x036e = 878*
  
  Identical structure to its superclass :cpp:class:`plAvTask`
  (i. e. contains no data of its own).
  This message itself should never be sent over the network,
  but its subclass :cpp:class:`plAvOneShotLinkTask` can be.

.. cpp:class:: plAvOneShotLinkTask : public plAvOneShotTask
  
  *Class index = 0x0488 = 1160*
  
  * **Header:** :cpp:class:`plAvOneShotTask`.
  * **Animation name:** :ref:`SafeString <safe_string>`.
  * **Marker name:** :ref:`SafeString <safe_string>`.

.. cpp:class:: plAvTaskBrain : public plAvTask
  
  *Class index = 0x0370 = 880*
  
  * **Header:** :cpp:class:`plAvOneShotTask`.
  * **Brain:** Serialized :cpp:class:`plCreatable` with header.
    Must be an instance of a :cpp:class:`plArmatureBrain` subclass.

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
      Only used with :cpp:class:`plAvatarInputStateMsg` and ``plControlEventMsg``.
      
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
      Only used with :cpp:class:`pfKIMsg`, ``plCCRCommunicationMsg``, ``plLinkingMgrMsg``, and ``plLinkToAgeMsg``.
      
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
    Must be an instance of a :cpp:class:`plAvTask` subclass.
    Only present if the preceding boolean field is true,
    in which case the :cpp:class:`plCreatable` should not be ``nullptr``.
    If the preceding boolean field is false,
    this field is not present and defaults to ``nullptr``.
  * **User string:** :ref:`SafeString <safe_string>`.
    Usually empty,
    but sometimes set to a short description
    (e. g. for quabs).
    Ignored by the client and all fan servers.

:cpp:class:`plEnableMsg`
------------------------

.. cpp:class:: plEnableMsg : public plMessage
  
  *Class index = 0x0254 = 596*
  
  * **Header:** :cpp:class:`plMessage`.
  * **Commands:** :cpp:class:`hsBitVector`.
    The following flags are currently defined:
    
    * **Disable** = 1 << 0: Disable the receiver.
    * **Enable** = 1 << 1: Enable the receiver.
    * **Drawable** = 1 << 2: When received by a ``plSceneObject``,
      forwards the message to its ``plDrawInterface`` (if any) and ``plLightInfo`` (if any).
    * **Physical** = 1 << 3: When received by a ``plSceneObject``,
      forwards the message to its ``plSimulationInterface`` if it has one,
      otherwise to all of its modifiers.
    * **Audible** = 1 << 4: When received by a ``plSceneObject``,
      forwards the message to its ``plAudioInterface``.
    * **All** = 1 << 5: When received by a ``plSceneObject``,
      forwards the message to all interfaces and modifiers listed above
      and to all of its ``plObjInterface``\s.
    * **By type** = 1 << 6: When received by a ``plSceneObject``,
      forwards the message to all of its ``plObjInterface``\s whose class index
      (or that of one of their superclasses)
      appears in the types field.
  * **Types:** :cpp:class:`hsBitVector`.
    Each bit represents a class index
    (the least significant bit is class index 0).
    Controls which interfaces receive this message
    if it's sent to a ``plSceneObject``
    and the commands field has the "by type" flag set.
    
    The following flag also has a secondary meaning,
    probably by accident:
    
    * **Drawable** = 1 << 2: When received by a ``plArmatureMod``,
      disable or enable drawing for the receiver,
      depending on the disable and enable flags in the commands field.
      (Note that if the "by type" flag is set in the commands field,
      this flag is also interpreted as the class index for ``hsKeyedObject``!
      To avoid ambiguities/conflicts,
      this flag should never be set at the same time as the "by type" command.)

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

:cpp:class:`plMessageWithCallbacks`
-----------------------------------

.. cpp:class:: plMessageWithCallbacks : public plMessage
  
  *Class index = 0x0283 = 643*
  
  * **Header:** :cpp:class:`plMessage`.
  * **Callback count:** 4-byte unsigned int.
    Element count for the following callback array.
  * **Callbacks:** Variable-length array of serialized :cpp:class:`plCreatable`\s with header.
    Each element must be a subclass of :cpp:class:`plMessage`.

:cpp:class:`plAnimCmdMsg`
-------------------------

.. cpp:class:: plAnimCmdMsg : public plMessageWithCallbacks
  
  *Class index = 0x0206 = 518*
  
  * **Header:** :cpp:class:`plMessageWithCallbacks`.
  * **Commands:** :cpp:class:`hsBitVector`.
    The following flags are currently defined:
    
    * **Continue** = 1 << 0
    * **Stop** = 1 << 1
    * **Set looping** = 1 << 2
    * **Unset looping** = 1 << 3
    * **Set begin** = 1 << 4
    * **Set end** = 1 << 5
    * **Set loop end** = 1 << 6
    * **Set loop begin** = 1 << 7
    * **Set speed** = 1 << 8
    * **Go to time** = 1 << 9
    * **Set backwards** = 1 << 10
    * **Set forwards** = 1 << 11
    * **Toggle state** = 1 << 12
    * **Add callbacks** = 1 << 13
    * **Remove callbacks** = 1 << 14
    * **Go to begin** = 1 << 15
    * **Go to end** = 1 << 16
    * **Go to loop begin** = 1 << 17
    * **Go to loop end** = 1 << 18
    * **Increment forward** = 1 << 19
    * **Increment backward** = 1 << 20
    * **Run forward** = 1 << 21
    * **Run backward** = 1 << 22
    * **Play to time** = 1 << 23
    * **Play to percentage** = 1 << 24
    * **Fast-forward** = 1 << 25
    * **Go to percent** = 1 << 26
  * **Begin:** 4-byte floating-point number.
  * **End:** 4-byte floating-point number.
  * **Loop begin:** 4-byte floating-point number.
  * **Loop end:** 4-byte floating-point number.
  * **Speed:** 4-byte floating-point number.
  * **Speed change rate:** 4-byte floating-point number.
  * **Time:** 4-byte floating-point number.
  * **Animation name:** :ref:`SafeString <safe_string>`.
  * **Loop name:** :ref:`SafeString <safe_string>`.

:cpp:class:`plAvatarMsg`
------------------------

.. cpp:class:: plAvatarMsg : public plMessage
  
  *Class index = 0x0297 = 663*
  
  Identical structure to its superclass :cpp:class:`plMessage`.

:cpp:class:`plAvTaskMsg`
------------------------

.. cpp:class:: plAvTaskMsg : public plAvatarMsg
  
  *Class index = 0x0298 = 664*
  
  * **Header:** :cpp:class:`plAvatarMsg`.
  * **Task present:** 1-byte boolean.
    Whether the following initial task field is present.
  * **Task:** Serialized :cpp:class:`plCreatable` with header.
    Must be an instance of a :cpp:class:`plAvTask` subclass.
    Only present if the preceding boolean field is true,
    in which case the :cpp:class:`plCreatable` should not be ``nullptr``.
    If the preceding boolean field is false,
    this field is not present and defaults to ``nullptr``.

:cpp:class:`plAvSeekMsg`
------------------------

.. cpp:class:: plAvSeekMsg : public plAvTaskMsg
  
  *Class index = 0x0299 = 665*
  
  * **Header:** :cpp:class:`plAvTaskMsg`.
  * **Seek point:** :cpp:class:`plKey`.
  * **Target position:** 12-byte :cpp:class:`hsPoint3`.
    Only present if the seek point is ``nullptr``.
  * **Target look at:** 12-byte :cpp:class:`hsPoint3`.
    Only present if the seek point is ``nullptr``.
  * **Duration:** 4-byte floating-point number.
  * **Smart seek:** 1-byte boolean.
  * **Animation name:** :ref:`SafeString <safe_string>`.
  * **Alignment type:** 2-byte unsigned int.
    The following types are defined:
    
    * Align handle with seek point = 0
    * Align handle with seek point at animation end = 1
    * Align handle with world origin = 2: Unimplemented.
    * Align bone with seek point = 3: Unimplemented.
    * Align bone with seek point at animation end = 4: Unimplemented.
  * **No seek:** 1-byte boolean.
  * **Flags:** 1-byte unsigned int.
    The following flags are defined:
    
    * **Un-force third person on finish** = 1 << 0
    * **Force third person on start** = 1 << 1
    * **No warp on timeout** = 1 << 2
    * **Rotation only** = 1 << 3
  * **Finish key:** :cpp:class:`plKey`.

:cpp:class:`plAvBrainGenericMsg`
--------------------------------

.. cpp:class:: plAvBrainGenericMsg : public plAvatarMsg
  
  *Class index = 0x038f = 911*
  
  * **Header:** :cpp:class:`plAvatarMsg`.
  * **Type:** 4-byte unsigned int.
    The following types are currently defined:
    
    * Next stage = 0
    * Previous stage = 1
    * Go to stage = 2
    * Set loop count = 3
  * **Stage:** 4-byte signed int.
    The stage to switch to,
    or -1 to exit the current multi-stage behavior.
    Only used if the type is "go to stage".
  * **Set time:** 1-byte boolean.
  * **Time:** 4-byte floating-point number.
  * **Set direction:** 1-byte boolean.
  * **Direction:** 1-byte boolean.
  * **Transition time:** 4-byte floating-point number.

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

:cpp:class:`plLinkEffectsTriggerMsg`
------------------------------------

.. cpp:class:: plLinkEffectsTriggerMsg : public plMessage
  
  *Class index = 0x0300 = 768*
  
  * **Header:** :cpp:class:`plMessage`.
  * **CCR level:** 4-byte signed int.
    :ref:`CCR level <ccr_level>` of the linking avatar.
  * **Linking out:** True if the avatar is linking out,
    or false if it's linking in.
  * **Linker:** :cpp:class:`plKey`.
    The ``plSceneObject`` clone for the avatar that's linking in/out.
    Should never be ``nullptr``.
  * **Flags:** 4-byte unsigned int.
    Only one flag is currently defined:
    
    * **Mute link sound effect** = 1 << 0: If set,
      the link sound isn't played as the avatar links.
  * **Link-in animation:** :cpp:class:`plKey`.
    The ``plATCAnim`` for an avatar animation to play once the avatar has linked in ---
    usually to make the avatar visually return from its linking pose to a normal standing pose.
    May be ``nullptr`` if the avatar should link in in a standing pose with no animation.
    If the linking out field is true,
    this field should be ``nullptr``.

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

:cpp:class:`plAvatarInputStateMsg`
----------------------------------

.. cpp:class:: plAvatarInputStateMsg : public plMessage
  
  *Class index = 0x0347 = 839*
  
  * **Header:** :cpp:class:`plMessage`.
  * **State:** 2-byte unsigned int.
    The following flags are defined:
    
    * **Forward** = 1 << 0
    * **Backward** = 1 << 1
    * **Rotate left** = 1 << 2
    * **Rotate right** = 1 << 3
    * **Strafe left** = 1 << 4
    * **Strafe right** = 1 << 5
    * **Always run** = 1 << 6
    * **Jump** = 1 << 7
    * **Consumable jump** = 1 << 8
    * **Run modifier** = 1 << 9
    * **Strafe modifier** = 1 << 10
    * **Ladder inverted** = 1 << 11

:cpp:class:`plInputIfaceMgrMsg`
-------------------------------

.. cpp:class:: plInputIfaceMgrMsg : public plMessage
  
  *Class index = 0x0363 = 867*
  
  * **Header:** :cpp:class:`plMessage`.
  * **Command:** 1-byte unsigned int.
    The following commands are currently defined:
    
    * Add interface = 0
    * Remove interface = 1
    * Enable clickables = 2
    * Disable clickables = 3
    * Set offer book mode = 4
    * Clear offer book mode = 5
    * Notify offer accepted = 6
    * Notify offer rejected = 7
    * Notify offer completed = 8
    * Disable avatar clickable = 9
    * Enable avatar clickable = 10
    * GUI disable avatar clickable = 11
    * GUI enable avatar clickable = 12
    * Set share spawn point = 13
    * Set share age instance GUID = 14
  * **Offeree KI number:** 4-byte unsigned int.
    Only used if the command is "notify offer completed".
    Otherwise,
    the open-sourced client code leaves this field uninitialized
    and usually sends unpredictable junk data.
  * **Age name:** :ref:`SafeString <safe_string>`.
  * **Age file name:** :ref:`SafeString <safe_string>`.
  * **Spawn point:** :ref:`SafeString <safe_string>`.
  * **Avatar:** :cpp:class:`plKey`.

:cpp:class:`pfKIMsg`
--------------------

.. cpp:class:: pfKIMsg : public plMessage
  
  *Class index = 0x0364 = 868*
  
  * **Header:** :cpp:class:`plMessage`.
  * **Command:** 1-byte unsigned int.
    For :cpp:class:`pfKIMsg`\s sent over the network,
    this field should always be 0,
    indicating a chat message.
    Other values are only used locally by the client.
    H'uru clients require this field to be 0 for :cpp:class:`pfKIMsg`\s received over the network
    and ignore the message otherwise.
  * **Sender name:** :ref:`SafeString <safe_string>`.
    Name of the avatar who sent the chat message.
  * **Sender KI number:** 4-byte unsigned int.
    KI number of the avatar who sent the chat message.
  * **Message text:** :ref:`SafeWString <safe_w_string>`.
  * **Flags:** 1-byte unsigned int.
    The following flags are defined:
    
    * **Private** = 1 << 0: The chat message is a private message,
      sent only to one receiver.
      If this flag is set,
      the inter-age flag should also be set
      (even if the receiver is in the same age instance as the sender).
    * **Admin** = 1 << 1: The chat message was sent by an "admin".
      This makes the client highlight the sender name in cyan
      (or in red if the message also has the private flag set),
      but otherwise it's treated like a normal chat message.
      DIRTSAND only allows this flag if the sender is permitted to send unsafe :cpp:class:`plMessage`\s
      (i. e. if the sender's account has the :cpp:var:`kAccountRoleAdmin` flag set),
      otherwise it unsets the flag before forwarding the message to other clients.
    * **Global** = 1 << 2: The chat message was sent as a broadcast by a CCR.
    * **Inter-age** = 1 << 3: The chat message may travel across age instances.
      Set for all private messages and those sent to all buddies or neighbors.
      The private and neighbors flags indicate who the sender addressed the message to;
      if none of those flags is set,
      the message was sent to the sender's buddies.
      If the inter-age flag is set,
      the :cpp:class:`plMessage` flag :cpp:enumerator:`~plMessage::plBCastFlags::kNetAllowInterAge` should also be set.
    * **Status** = 1 << 4: This message is a "status" text,
      usually generated by the /me command
      or any of the emote commands.
    * **Neighbors** = 1 << 5: The chat message was sent to the sender's neighbors.
      If this flag is set,
      the inter-age flag should also be set.
    * **Subtitle** = 1 << 6: This message is an NPC speech subtitle line
      and not a real chat message.
      Should never be set for :cpp:class:`pfKIMsg`\s sent over the network.
      Supported by H'uru clients since 2021 and OpenUru clients since 2022.
    * **Localization key** = 1 << 7: The message text is actually one or more localization keys,
      which must be looked up by the receiving client in its .loc files
      to display the message in the player's chosen language.
      If there are multiple localization keys,
      they are separated by ``:`` (colon) characters.
      Usually used in combination with the status flag
      to localize the descriptions for the game's standard emotes.
      Supported by OpenUru and H'uru clients since 2022.
  * **Channel** = 1-byte unsigned int.
    Indicates which private chat channel the sender is currently in.
    Very few areas of the game use private chat channels,
    so this field is usually set to 0
    (the default public channel).
    If an avatar is in a private chat channel,
    then *all* chat messages sent by it have the channel field set accordingly,
    even chat messages sent to specific receivers
    (private/buddies/neighbors messages).
    The following channels are currently used:
    
    * Channel 0 is the default public channel,
      used when the sender isn't in any private chat channel.
    * Channels 1 through 5 are used by the private rooms in the neighborhood egg room.
      Channel 1 is for the room directly in front of the entrance.
      The remaining rooms are numbered clockwise in ascending order.
    * Channels 6 and 7 are used by each team's Maintainer's Nexus for the Gahreesen Wall.
      Channel 6 is for the yellow team ("black"/north/team 1)
      and Channel 7 for the purple team ("white"/south/team 2).
  * **Reserved flags:** 2-byte unsigned int.
    Currently unused space for more flags.
  * **Delay:** 4-byte floating-point number.
    Not used for chat messages and should always be 0.
  * **Value:** 4-byte signed int.
    Not used for chat messages and should always be 0.
