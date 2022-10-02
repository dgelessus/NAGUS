.. index:: vault
   :name: vault

The vault
=========

Nearly all persistent game state is stored in a database called the vault.
Some higher-level persistent state mechanisms,
such as chronicles and age SDL,
are also based on the vault.
(Other state mechanisms are separate from the vault though,
such as the score mechanism and the game manager.)

Every entry in the vault,
called a vault node,
has the same :ref:`generic structure <vault_node_structure>`.
Vault nodes are linked together by parent/child relationships,
called "node refs",
which form a directed graph.
Each node can have any number of child nodes,
and a node may have multiple parents.

Additionally,
each node ref can have an owner node,
which is the player node (KI number) of the avatar that created the ref.
Not all refs have their owner set though ---
in various cases,
the client sets owner ID 0 instead of the proper owner.

Node refs should never form cycles.
According to comments in the open-sourced client code,
the server is supposed to check for reference cycles and forbid adding refs that would create a cycle,
but no open-source server implementation does this.
(TODO What does Cyan's server software do?)
(TODO How well does the client handle reference cycles?)

There is no single root node or entry point from which all other nodes can be reached.
In a usual vault database,
the nodes form many different trees
that usually share some nodes with each other
(e. g. the :ref:`vault_node_system` node),
but are otherwise not connected.

.. _vault_node_structure:

Vault node structure
--------------------

Every vault node has the following fields.
Most of them are generic and may be used for different purposes
depending on the concrete node type (see :ref:`vault_node_types`).
This generic structure allows introducing new node types and (within limits) extending existing types
without requiring changes to the database schema
or code that operates generically on vault nodes.

Any of these fields may be unset,
which is a distinct state and *not* the same as 0/empty
(although some code treats them identically).
In the client code and over the network,
this is implemented using a set of bit flags indicating which fields are set/unset.
In an SQL database (as used by servers to store the vault),
this is usually represented using nullable columns.

Some fields (strings and blobs) have variable sizes.
There is no direct limit to these sizes,
but when sent over the network,
the representation of a single vault node cannot exceed 1 MiB.

The field names are taken from the open-sourced client code.
Fan tools also use these same field names
(modulo capitalization of the first letter).

* ``NodeId``: 4-byte unsigned int.
  Unique identifier for this vault node.
  This field is always present in every vault node,
  although in some network messages it's left unset
  (e. g. when creating or finding a node,
  where the ID will be filled in by the server).
* ``CreateTime``: 4-byte unsigned int.
  Unix timestamp indicating when this node was created.
* ``ModifyTime``: 4-byte unsigned int.
  Unix timestamp indicating when this node was last modified.
* ``CreateAgeName``: Variable-length, zero-terminated UTF-16 string.
  File name of the age in which this node was created (?).
  Unset for nodes that weren't created in a particular age.
  DIRTSAND limits this to 64 characters,
  but MOSS doesn't.
* ``CreateAgeUuid``: 16-byte UUID.
  UUID of the age instance in which this node was created (?).
  Unset for nodes that weren't created in a particular age.
* ``CreatorAcct``: 16-byte UUID.
  UUID of the account (or other thing?) that created the node.
  This field is apparently always present,
  but set to all zeroes for nodes that don't have an obvious creator.
* ``CreatorId``: 4-byte unsigned integer.
  Vault node ID (KI number) of the avatar (or other thing?) that created the node.
  This field is apparently always present,
  but set to zero for nodes that that don't have an obvious creator.
* ``NodeType``: 4-byte unsigned integer.
  Indicates the meaning of the remaining generic fields.
  See :ref:`vault_node_types` for a list of all node types and corresponding field meanings.
  This field is always present in every vault node.
* ``Int32_1``, ``Int32_2``, ``Int32_3``, ``Int32_4``: Each a 4-byte signed integer.
  Generic fields with no pre-defined purpose.
* ``UInt32_1``, ``UInt32_2``, ``UInt32_3``, ``UInt32_4``: Each a 4-byte unsigned integer.
  Generic fields with no pre-defined purpose.
* ``Uuid_1``, ``Uuid_2``, ``Uuid_3``, ``Uuid_4``: Each a 16-byte UUID.
  Generic fields with no pre-defined purpose.
* ``String64_1``, ``String64_2``, ``String64_3``, ``String64_4``, ``String64_5``, ``String64_6``: Each a variable-length, zero-terminated UTF-16 string.
  Generic fields with no pre-defined purpose.
  DIRTSAND limits these to 64 characters each,
  but MOSS doesn't.
* ``IString64_1``, ``IString64_2``: Each a variable-length, zero-terminated UTF-16 string.
  Same as the other ``String64`` fields,
  but their values are compared case-insensitively.
* ``Text_1``, ``Text_2``: Each a variable-length, zero-terminated UTF-16 string.
  Generic fields with no pre-defined purpose.
  DIRTSAND limits these to 1024 characters each,
  but MOSS doesn't.
* ``Blob_1``, ``Blob_2``: Each a free-form byte array with an explicit length and no restrictions.
  Generic fields with no pre-defined purpose.

.. _vault_node_network_format:

Vault node network format
^^^^^^^^^^^^^^^^^^^^^^^^^

When sent over the network,
every vault node starts with an 8-byte integer of bit flags
that indicate which fields are present in the data.
The bits are assigned from least to most significant in the field order listed above ---
for example,
bit 0 (least significant) corresponds to ``NodeId``, bit 1 to ``CreateTime``, and bit 31 to ``Blob_2``.
(The most significant 4 bytes of the flag integer are unused.)

Following these flags is the data for all present fields,
again in the order listed above
and with no padding/alignment between fields.
Integers and UUIDs are transmitted in packed little-endian format,
as described in :doc:`protocol`.
Strings and blobs are preceded with a 4-byte unsigned integer byte count.
Strings are encoded as UTF-16 (little-endian, as usual)
and include a zero terminator (despite the explicit length).
Any field whose corresponding flag *isn't* set is omitted entirely.

.. _moss_vault:

MOSS vault database structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Almost all Uru server implementations store all vault nodes in a single big database table.
The only exception is MOSS,
which uses separate tables for the different vault node types.
These tables don't support the full set of generic vault node fields ---
each table only has columns for the fields that the client actually uses in practice for that node type.

In practice,
this implementation difference isn't noticeable most of the time.
Despite this different internal representation,
the network protocol has remained unchanged
and the vault is still exposed to clients as a single unified collection of nodes.
The only noticeable difference is that it's impossible for clients to create nodes of unknown types
or to set unexpected fields on supported node types.
Introducing new node types or adding fields to existing types requires updating the server and extending the database schema.

This is a problem e. g. when using H'uru clients on MOSS,
as H'uru has introduced a new format for marker games that no longer relies on the :ref:`GameMgr <game_server>`,
using a previously unused fields on marker game nodes.
This new marker game format isn't handled correctly by MOSS unless the database is updated accordingly
(MOSS ships with a script ``postgresql/UpdateForHuruGames.sql`` for this purpose).

For all node types,
MOSS supports the type-independent fields
``NodeId``, ``CreateTime``, ``ModifyTime``, ``CreatorAcct``, ``CreatorId``.
The fields ``CreateAgeName``, ``CreateAgeUuid`` are supported for most node types,
but are omitted for some nodes that are never tied to a particular age instance.
Such node types are pointed out in the documentation below.
The ``NodeType`` field is implicitly derived from the database table in which each node is stored.
For all other fields (whose meanings are fully type-dependent),
assume that MOSS only supports exactly the fields listed below in the documentation for the respective node type.

.. _vault_node_types:

Node types
----------

Node types in *italics* are defined as constants in the open-sourced client code,
but are not real node types ---
they should never appear in the actual vault database or over the network.

.. hlist::
   
   * *Invalid* = 0
   * *VNodeMgrLow* = 1
   * :ref:`vault_node_player` = 2
   * :ref:`vault_node_age` = 3
   * *VNodeMgr_UNUSED00* = 4
   * *VNodeMgr_UNUSED01* = 5
   * *VNodeMgr_UNUSED02* = 6
   * *VNodeMgr_UNUSED03* = 7
   * *VNodeMgrHigh* = 21
   * :ref:`vault_node_folder` = 22
   * :ref:`vault_node_player_info` = 23
   * :ref:`vault_node_system` = 24
   * :ref:`vault_node_image` = 25
   * :ref:`vault_node_text_note` = 26
   * :ref:`vault_node_sdl` = 27
   * :ref:`vault_node_age_link` = 28
   * :ref:`vault_node_chronicle` = 29
   * :ref:`vault_node_player_info_list` = 30
   * *UNUSED00* = 31
   * *UNUSED01* = 32
   * :ref:`vault_node_age_info` = 33
   * :ref:`vault_node_age_info_list` = 34
   * :ref:`vault_node_marker_game` = 35

.. commented out - this is way too wide
   csv-table:: Vault node types and field meanings
   :name: vault_node_types
   :header: #,Type Desc.,Int32_1,Int32_2,Int32_3,UInt32_1,UInt32_2,UInt32_3,Uuid_1,Uuid_2,String64_1,String64_2,String64_3,String64_4,IString64_1,Text_1,Text_2,Blob_1
   :widths: auto
   
   2,Player,Disabled,Explorer,,OnlineTime,,,AccountUuid,InviteUuid,AvatarShapeName,,,,PlayerName,,,
   3,Age,,,,,,,AgeInstanceGuid,ParentAgeInstanceGuid,AgeName,,,,,,,
   22,Folder,FolderType,,,,,,,,FolderName,,,,,,,
   23,Player Info,Online,CCRLevel,,PlayerId,,,AgeInstUuid,,AgeInstName,,,,PlayerName,,,
   24,System,CCRStatus,,,,,,,,,,,,,,,
   25,Image,ImageType,,,,,,,,ImageTitle,,,,,,,ImageData
   26,Text Note,NoteType,NoteSubType,,,,,,,NoteTitle,,,,,NoteText,,
   27,SDL,SDLIdent,,,,,,,,SDLName,,,,,,,SDLData
   28,Age Link,Unlocked,Volatile,,,,,,,,,,,,,,SpawnPoints
   29,Chronicle,EntryType,,,,,,,,EntryName,,,,,EntryValue,,
   30,Player Info List,folderType,,,,,,,,folderName,,,,,,,
   33,Age Info,AgeSequenceNumber,IsPublic,AgeLanguage,AgeId,AgeCzarId,AgeInfoFlags,AgeInstanceGuid,ParentAgeInstanceGuid,,AgeFilename,AgeInstanceName,AgeUserDefinedName,,AgeDescription,,
   34,Age Info List,folderType,,,,,,,,folderName,,,,,,,
   35,Marker Game,,,,,,,GameGuid,,,,,,,GameName,Reward (H'uru),MarkerData (H'uru)

.. _vault_node_player:

Player
^^^^^^

Top-level node for all data related to an avatar.

* ``CreateAgeName``, ``CreateAgeUuid``: Normally left unset.
  Not supported by MOSS for this node type.
* ``NodeType`` = 2
* ``Int32_1`` = **Disabled:** Not used by the open-sourced client code or fan servers.
  At some point in the past (at least 2011),
  setting this field to a non-zero value made Cyan's server software permanently delete the avatar.
  As of 2022,
  this *seems* to be no longer the case.
  (Don't quote me on that though.
  I accept no responsibility for any lost avatars.)
  Cyan's server software and MOSS initialize this field to 0 when creating a new avatar,
  whereas DIRTSAND leaves it unset.
* ``Int32_2`` = **Explorer:**
  1 if the avatar is a full :ref:`explorer <explorer>`,
  or 0 if it's just a :ref:`visitor <visitor>`.
* ``UInt32_1`` = **OnlineTime:** Not used by the open-sourced client code or fan servers.
  (TODO Does Cyan's server software do anything with it?)
  Normally left unset.
  MOSS initializes it to 0 when creating a new avatar.
* ``Uuid_1`` = **AccountUuid:** Account ID to which this avatar belongs.
* ``Uuid_2`` = **InviteUuid:** Identifies friend invites sent by this avatar.
  Unset by default.
  The client automatically generates a random invite UUID and stores it into this field
  before sending a :ref:`cli2auth_send_friend_invite_request` for the first time.
* ``String64_1`` = **AvatarShapeName:**
  The avatar's gender.
  Either ``"female"`` or ``"male"``.
* ``IString64_1`` = **PlayerName:**
  The avatar's display name.

Some of these fields overlap with those returned in :ref:`auth2cli_acct_player_info`,
namely the explorer flag, avatar shape, and player name.
These fields should always stay in sync with the corresponding player vault node,
as the client may use the values from either of the two sources,
depending on context.
DIRTSAND stores the AcctPlayerInfo fields in a different database table separate from the vault,
whereas MOSS uses the same database table for both purposes.
(TODO What does Cyan's server software do?)
In practice this doesn't make a difference,
because the affected fields should never change anyway ---
the explorer flag is effectively unused and should always be 1,
and there's no way for the player to change the name or gender of an existing avatar.

A Player node should never appear as the child of another node.
Other nodes should instead reference the Player node indirectly via the corresponding :ref:`vault_node_player_info` node.

A Player node should always have the following children:

* :ref:`vault_node_system` (the single System node)
* :ref:`vault_node_player_info` (corresponding to this Player node)
* :ref:`vault_node_folder`: FolderType = InboxFolder
* :ref:`vault_node_folder`: FolderType = AgeJournalsFolder
  
  * (for every age journal) :ref:`vault_node_folder`: FolderType = AgeTypeJournalFolder, FolderName = *the age's display name*
* :ref:`vault_node_player_info_list`: FolderType = BuddyListFolder
  
  * *Player Info nodes for all buddies*
* :ref:`vault_node_player_info_list`: FolderType = IgnoreListFolder
  
  * *Player Info nodes for all ignored avatars*
* :ref:`vault_node_player_info_list`: FolderType = PeopleIKnowAboutFolder
  
  * *Player Info nodes for all recently seen avatars*
* :ref:`vault_node_folder`: FolderType = ChronicleFolder
  
  * *Chronicle nodes for the avatar's chronicle entries*
* :ref:`vault_node_folder`: FolderType = AvatarOutfitFolder
  
  * (for every currently worn clothing item) :ref:`vault_node_sdl`: SDLData = *state data record of type clothingItem*
* :ref:`vault_node_folder`: FolderType = AvatarClosetFolder
  
  * (for every owned clothing item) :ref:`vault_node_sdl`: SDLData = *state data record of type clothingItem*
* :ref:`vault_node_folder`: FolderType = PlayerInviteFolder
  
  * (for every invite key) :ref:`vault_node_text_note`: NoteType = *unset*, NoteSubType = *unset*, NoteTitle = *invite key*, NoteText = *unset*
* :ref:`vault_node_age_info_list`: FolderType = AgesIOwnFolder
  
  * :ref:`vault_node_age_link` (for the avatar's Personal/Relto)
  * :ref:`vault_node_age_link` (for the avatar's Neighborhood)
  * :ref:`vault_node_age_link` (for the public Ae'gura/city, with SpawnPoints storing the Ae'gura Nexus links collected by the avatar)
  * *Age Link nodes for all other personal age instances*
* :ref:`vault_node_age_info_list`: FolderType = AgesICanVisitFolder
  
  * *Age Link nodes for all age instances that the avatar is invited to*
* (optional, DIRTSAND only) :ref:`vault_node_player_info_list`: FolderType = AllPlayersFolder (the single All Players list)
  
  * *Player Info nodes for all currently online avatars*

.. _vault_node_age:

Age
^^^

Top-level node for all data related to an age instance.
The name is somewhat misleading ---
no data is shared between different instances of the same age.

* ``CreateAgeName``, ``CreateAgeUuid``: Normally left unset.
  Not supported by MOSS for this node type.
* ``NodeType`` = 3
* ``Uuid_1`` = **AgeInstanceGuid:** This age instance's unique ID.
* ``Uuid_2`` = **ParentAgeInstanceGuid:** The AgeInstanceGuid of this age instance's parent instance,
  or unset if this age is not a sub-age or child age.
* ``String64_1`` = **AgeName:** Internal name of the age that this is an instance of.

An Age node should never appear as the child of another node.
Other nodes should instead reference the Age node indirectly via the corresponding :ref:`vault_node_age_info` node.

An Age node should always have the following children:

* :ref:`vault_node_system` (the single System node)
* :ref:`vault_node_age_info` (corresponding to this Age node)
* :ref:`vault_node_player_info_list`: FolderType = PeopleIKnowAboutFolder (apparently never has any children?)
* :ref:`vault_node_folder`: FolderType = ChronicleFolder (apparently never has any children?)
* :ref:`vault_node_age_info_list`: FolderType = SubAgesFolder
  
  * *Age Link nodes for all sub-ages*
* :ref:`vault_node_folder`: FolderType = AgeDevicesFolder
  
  * (for every device) :ref:`vault_node_text_note`: NoteType = Device, NoteTitle = *device name*
* (Personal/Relto only) :ref:`vault_node_player_info_list` (AgesIOwnFolder of the avatar who owns this Relto)

.. _vault_node_folder:

Folder
^^^^^^

A generic collection of other nodes.
Stores almost no data of its own.

* ``NodeType`` = 22
* ``Int32_1`` = **FolderType:** The folder's general meaning/purpose.
  See :ref:`vault_folder_list_types` for details.
  The open-sourced client code sometimes leaves this field unset.
* ``String64_1`` = **FolderName:** Name of the folder.
  If present,
  it's often (but not always) a human-readable name that is displayed to the player,
  e. g. the name of an age inbox folder.
  For many folder types,
  this field is left unset
  and it's expected that the type alone uniquely identifies the folder inside its parent.

A Folder node has no fixed structure and may contain child nodes of almost any type.
See the structure descriptions of the other node types for details.

.. _vault_node_player_info:

Player Info
^^^^^^^^^^^

Lightweight reference to an avatar.
Stores key information about the avatar,
its current state in the game,
and the corresponding :ref:`vault_node_player` node
that stores further data related to the avatar.

* ``CreateAgeName``, ``CreateAgeUuid``: Normally left unset.
  Not supported by MOSS for this node type.
* ``NodeType`` = 23
* ``Int32_1`` = **Online:**
  1 if the avatar is currently online,
  or 0 otherwise.
* ``Int32_2`` = **CCRLevel:**
  The avatar's current CCR level.
  Normally left unset if the avatar's CCR level has never been changed from the default 0.
  Not supported by MOSS.
* ``UInt32_1`` = **PlayerId:**
  ID of the corresponding :ref:`vault_node_player` node,
  i. e. the avatar's KI number.
* ``String64_1`` = **AgeInstName:**
  Display name of the age instance that the avatar is currently in.
  Should always be identical to the ``String64_3`` (AgeInstanceName) field of the :ref:`vault_node_age_info` node indicated by this node's AgeInstUuid field,
  or set to an empty string if the avatar is not currently in any instance.
* ``IString64_1`` = **PlayerName:**
  The avatar's display name.
  Should always be identical to the same field in the corresponding :ref:`vault_node_player` node.
* ``Uuid_1`` = **AgeInstUuid:**
  UUID of the age instance that the avatar is currently in.
  Set to all zeroes if the avatar is not currently in any instance.

A Player Info node should never have any child nodes.

.. _vault_node_system:

System
^^^^^^

Singleton node storing global data that can be accessed from any avatar and age.

* ``CreateAgeName``, ``CreateAgeUuid``: Normally left unset.
  Not supported by MOSS for this node type.
* ``NodeType`` = 24
* ``Int32_1`` = **CCRStatus:**
  1 if any CCRs are currently online,
  or 0 otherwise.
  Normally left unset if no CCR has ever been online.
  No open-source client actively uses this field.
  Not supported by MOSS.

There should only ever be a single System node in the entire vault.
It is normally the first vault node that is ever created
and has the lowest possible vault node ID:
1 for Cyan's server software,
101 for MOSS,
and 10001 for DIRTSAND.
All :ref:`vault_node_player` and :ref:`vault_node_age` nodes should have the System node as their first child node.

The System node should have the following children:

* :ref:`vault_node_folder`: FolderType = GlobalInboxFolder
  
  * :ref:`vault_node_folder`: FolderType = UserDefinedNode, FolderName = "Journals"
    
    * :ref:`vault_node_text_note`: Type = Generic, SubType = Generic, Title = "Sharper", Text = *contents of Douglas Sharper's journal*
  
  * :ref:`vault_node_folder`: FolderType = UserDefinedNode, FolderName = "MemorialImager"
    
    * :ref:`vault_node_text_note`: Type = Generic, SubType = Generic, Title = "MemorialImager", Text = *list of names to be displayed on the Kahlo Pub memorial imager*
  
  * *additional nodes that will be displayed in every avatar's Incoming folder*

All child nodes of the global inbox folder,
except for :ref:`vault_node_folder` or :ref:`vault_node_chronicle` nodes,
are displayed as the first entries in every avatar's KI Incoming folder,
above any nodes from the per-avatar inbox folder.
Players cannot delete nodes from the global inbox folder using the KI user interface,
unlike nodes stored in the per-avatar inbox folder.

.. _vault_node_image:

Image
^^^^^

A KI image/picture/screenshot,
as seen in the KI interface or on imagers.

* ``NodeType`` = 25
* ``Int32_1`` = **ImageType:**
  Indicates the format of the ImageData field.
  May be one of:
  
  * None = 0: Placeholder type to indicate that image saving failed.
    The image data should be empty.
  * JPEG = 1: Default image type and the only one supported by OpenUru clients.
  * PNG = 2: Only supported by H'uru clients.
    Not actively used.
* ``String64_1`` = **ImageTitle:**
  Human-readable title/caption for the image.
  For images stored in the KI,
  it can be edited by the player.
* ``Blob_1`` = **ImageData:**
  The image's raw data in the format indicated by ImageType.

An Image node should never have any child nodes.

.. _vault_node_text_note:

Text Note
^^^^^^^^^

Usually a KI note/message/journal entry,
as seen in the KI interface or on imagers.
Also used internally to represent imagers themselves,
age instance visit (un)invitations,
and miscellaneous text data.

* ``NodeType`` = 26
* ``Int32_1`` = **NoteType:**
  The text note's general purpose/meaning.
  May be one of:
  
  * Generic = 0: Default type,
    used for text notes containing human-readable text
    with no specific meaning to the game.
  * CCRPetition = 1: Not used by the open-sourced client code.
  * Device = 2: Stores the contents of an imager.
    Unlike other text note types,
    the NoteText field isn't relevant and usually left empty.
    The imager's contents are instead stored inside a device inbox child node (see below).
  * Invite = 3: Not used by the open-sourced client code.
    (Text Note nodes under a PlayerInviteFolder have their NoteType unset.)
  * Visit = 4: An invitation to another avatar's age instance.
  * UnVisit = 5: An un-invitation that revokes a previous invitation for an age instance.
* ``Int32_2`` = **NoteSubType:**
  The open-sourced client code only defines a single subtype: Generic = 0.
  All text notes have this field set to 0 or left unset.
  This field is otherwise not actively used.
* ``String64_1`` = **NoteTitle:**
  Human-readable title for the text note.
  For text notes stored in the KI,
  it can be edited by the player.
  Left unset if NoteType is Visit or UnVisit.
* ``Text_1`` = **NoteText:**
  The text note's contents,
  normally human-readable text.
  For text notes stored in the KI,
  it can be edited by the player.
  For Device notes,
  this field is left unset.
  For Visit and UnVisit notes,
  this is a machine-readable string in the format
  :samp:`{AgeFilename}|{AgeInstanceName}|{AgeUserDefinedName}|{AgeDescription}|{AgeInstanceGuid}|{AgeLanguage}|{AgeSequenceNumber}`,
  with all values taken from the :ref:`vault_node_age_info` node of the age instance being invited to.

Most Text Note nodes should never have any child nodes.
The only exception are notes with NoteType Device,
which should have a single child node:

* :ref:`vault_node_folder`: FolderType = DeviceInboxFolder, FolderName = "DevInbox"
  
  * *any nodes stored in the imager*

.. _vault_node_sdl:

SDL
^^^

A state data record in packed binary format,
used to store an age instance's persistent state
and an avatar's clothing.

* ``NodeType`` = 27
* ``Int32_1`` = **SDLIdent:**
  Practically unused.
  When initializing the SDL node in an :ref:`vault_node_age_info` node,
  the server sets this field to 0.
  The open-sourced client code never sets it or uses it for anything.
* ``String64_1`` = **SDLName:**
  Name of the state descriptor (.sdl file) to use for this node.
  This field is only relevant when the SDLData field is unset or empty.
  Otherwise the SDLData itself indicates which state descriptor to use
  and this field is ignored.
  When initializing the SDL node in an :ref:`vault_node_age_info` node,
  the server sets this field to the age file name.
  The open-sourced client code never sets this field
  and only uses it in one case (see below).
* ``Blob_1`` = **SDLData:**
  The serialized state data record ("SDL blob").
  When initializing the SDL node in an :ref:`vault_node_age_info` node,
  the server leaves this field unset.
  When the client finds this field unset or empty,
  it looks up the state descriptor named by the SDLName field
  and uses that to initialize this field with a default state data record.
  If no state descriptor with that name could be found,
  the client leaves this field unset/empty.

An SDL node should never have any child nodes.

.. _vault_node_age_link:

Age Link
^^^^^^^^

A link to an age instance.
Usually visible to the player as a book on the Relto bookshelf or a Nexus link,
but also used internally to reference an age's sub-ages and/or child ages.

* ``NodeType`` = 28
* ``Int32_1`` = **Unlocked:**
  1 if the player has shared this link
  by unlocking its tab on the Relto bookshelf,
  or 0 or unset if the tab is currently locked.
  For links that don't appear on the Relto bookshelf,
  this field should never be set.
  Unset by default.
* ``Int32_2`` = **Volatile:**
  1 if the age instance should be recreated the next time this link is used,
  or 0 or unset otherwise.
  This field is controlled using the delete buttons on the Relto bookshelf.
  For other links,
  this field should never be set.
  Unset by default.
* ``Blob_1`` = **SpawnPoints:**
  List of link-in points that the avatar has collected for the age.
  This usually corresponds to the pages of the corresponding book on the Relto bookshelf.
  Unset by default.
  If set,
  the value is a sequence of semicolon-terminated entries
  in the format :samp:`{Title}:{SpawnPoint}:{CameraStack};`,
  with the following meanings:
  
  * :samp:`{Title}`: Identifier for the linking book page.
    For the most part,
    these identifiers can be chosen freely,
    but the following ones have special meanings:
    
    * ``Default``: The age's primary linking panel/link-in point.
      If present,
      this should be the first entry in the list.
      If not present,
      the Relto bookshelf book will show a "broken link" panel on the first (non-bookmark) page.
    * ``JCSavePoint``, ``SCSavePoint``: The Relto bookshelf book displays this link as a journey cloth bookmark instead of a regular linking panel
      and makes it the first page of the book.
      ``JCSavePoint`` represents a hand journey cloth and ``SCSavePoint`` a shell cloth.
      A single Age Link should only contain at most one of these two cloth link types.
  * :samp:`{SpawnPoint}`: Internal name of the spawn point in the age.
  * :samp:`{CameraStack}`: A ``~``-separated sequence of camera names that should be restored when arriving at the link-in point.
    Only used for cloth bookmark links.
    For other links,
    this part should always be empty.

An Age Link node should always have exactly one child node:
the :ref:`vault_node_age_info` node for the age instance that the link points to.

.. _vault_node_chronicle:

Chronicle
^^^^^^^^^

A simple string key/value pair associated with an avatar,
used to store persistent state
that is needed across multiple age instances
or not associated with any particular age.

* ``NodeType`` = 29
* ``Int32_1`` = **EntryType:**
  Appears to be meaningless and not actively used.
  All known chronicle entries use type 0, 1, or 2.
  The open-sourced client code sometimes leaves this field unset
  when creating Chronicle nodes manually instead of through the usual API.
  This happens for Chronicle nodes nested inside other Chronicle nodes
  or located outside of a ChronicleFolder.
  This field shouldn't change after creation.
* ``String64_1`` = **EntryName:**
  Name of the chronicle entry.
  Every Chronicle node's name should be unique within its parent node.
  Should always be set
  and shouldn't change after creation.
* ``Text_1`` = **EntryValue:**
  Value of the chronicle entry.
  The format and meaning of this field depends on the EntryName.
  Should always be set.

A Chronicle node's children should all be Chronicle nodes as well.
Most Chronicle nodes have no children at all.

.. _vault_node_player_info_list:

Player Info List
^^^^^^^^^^^^^^^^

Collection of :ref:`vault_node_player_info` nodes.
Stores no data of its own.

* ``CreateAgeName``, ``CreateAgeUuid``: Normally left unset.
  Not supported by MOSS for this node type.
* ``NodeType`` = 30
* ``Int32_1`` = **FolderType:** The player info list's meaning/purpose.
  See :ref:`vault_folder_list_types` for details.

A Player Info List's children should all be :ref:`vault_node_player_info` nodes.

.. _vault_node_age_info:

Age Info
^^^^^^^^

A reference to an age instance.
Stores key information identifying the instance
and the corresponding :ref:`vault_node_age` node
that stores further data related to the instance.

* ``CreateAgeName``, ``CreateAgeUuid``: Normally left unset.
  Not supported by MOSS for this node type.
* ``NodeType`` = 33
* ``Int32_1`` = **AgeSequenceNumber:**
  A sequential number identifying multiple different instances of the same age with the same owner.
  The first instance has sequence number 0.
  Each further instance receives a sequence number one higher than the previous one.
* ``Int32_2`` = **IsPublic:**
  1 if the age instance is public,
  or 0 or unset otherwise.
  When creating a new private age instance,
  Cyan's server software and MOSS leave this field unset by default,
  whereas DIRTSAND explicitly sets it to 0.
* ``Int32_3`` = **AgeLanguage:**
  Apparently not actively used.
  In practice,
  the open-sourced client code always sets this field to -1.
* ``UInt32_1`` = **AgeId:**
  ID of the corresponding :ref:`vault_node_age` node.
* ``UInt32_2`` = **AgeCzarId:**
  Not used by the open-sourced client code.
  The server sets this field to 0 when creating a new age instance.
* ``UInt32_3`` = **AgeInfoFlags:**
  Not used by the open-sourced client code.
  The server sets this field to 0 when creating a new age instance.
* ``Uuid_1`` = **AgeInstanceGuid:**
  This age instance's unique ID.
  Should always be identical to the AgeInstanceGuid of the corresponding :ref:`vault_node_age` node.
* ``Uuid_2`` = **ParentAgeInstanceGuid:**
  The AgeInstanceGuid of this age instance's parent instance,
  or unset if this age is not a sub-age or child age.
  Should always be identical to the ParentAgeInstanceGuid of the corresponding :ref:`vault_node_age` node.
* ``String64_2`` = **AgeFilename:**
  Internal name of the age that this is an instance of.
  Should always be identical to the AgeName of the corresponding :ref:`vault_node_age` node.
* ``String64_3`` = **AgeInstanceName:**
  Display name of the age that this is an instance of.
* ``String64_4`` = **AgeUserDefinedName:**
  A prefix describing the owner of this age instance.
  This is usually the owner's name in possessive form,
  e. g. "Douglas Sharper's" (including the "'s").
  For automatically created neighborhoods,
  this is normally the string "DRC" (without "'s"),
  although some shards change this.
  Unset for age instances with no owner,
  e. g. public age instances.
  For neighborhoods,
  this field can be edited by the instance's owners in the KI neighborhood settings screen
  (although this only works in H'uru clients).
* ``Text_1`` = **AgeDescription:**
  For some age instances
  (personal instances and some neighborhoods apparently),
  this is set to the combination :samp:`{AgeUserDefinedName} {AgeInstanceName}`
  (the sequence number is *not* included here).
  For other instances,
  this field is left unset.
  For neighborhoods,
  this field can be edited by the instance's owners in the KI neighborhood settings screen
  (although this only works in H'uru clients).

An Age Info node should have the following children:

* :ref:`vault_node_sdl`: SDLIdent = 0, SDLName = AgeFilename
* :ref:`vault_node_player_info_list`: FolderType = AgeOwnersFolder
  
  * *Player Info nodes for all avatars that own this age instance*
* :ref:`vault_node_player_info_list`: FolderType = CanVisitFolder
  
  * *Player Info nodes for all avatars invited to this age instance*
* :ref:`vault_node_age_info_list`: FolderType = ChildAgesFolder
  
  * *Age Link nodes for all child age instances of this age instance*
* (optional) :ref:`vault_node_folder`: FolderType = *unset*, FolderName = "AgeData"
  
  * *age-specific Chronicle nodes*

.. _vault_node_age_info_list:

Age Info List
^^^^^^^^^^^^^

Collection of :ref:`vault_node_age_link` nodes.
Stores no data of its own.

* ``CreateAgeName``, ``CreateAgeUuid``: Normally left unset.
  Not supported by MOSS for this node type.
* ``NodeType`` = 34
* ``Int32_1`` = **FolderType:** The age info list's meaning/purpose.
  See :ref:`vault_folder_list_types` for details.

An Age Info List's children should all be :ref:`vault_node_age_link` nodes
(not :ref:`vault_node_age_info`,
despite the name).

.. _vault_node_marker_game:

Marker Game
^^^^^^^^^^^

A player-created marker game/mission,
as seen in the KI interface.

There are two incompatible internal representations of marker games,
both of which use this node type.
The original open-sourced client code,
as well as current OpenUru clients,
rely mainly on the :ref:`GameMgr <game_server>` to work with marker games
and store almost no information about marker games in the vault.
H'uru introduced a different implementation of marker games that isn't based on the GameMgr
and as a result stores the entire marker game in its vault node.
Currently,
OpenUru clients only support GameMgr-based marker games
and H'uru clients only support vault-based ones,
but work is ongoing to re-add GameMgr marker game support to H'uru.

* ``NodeType`` = 35
* ``Uuid_1`` = **GameGuid:**
  Internal identifier for this marker game in the :ref:`GameMgr <game_server>`.
  Unset for H'uru vault-based marker games.
* ``Text_1`` = **GameName:**
  Name of the marker game,
  chosen freely by the player.
  Should always be set.
* ``Text_2`` = **Reward:**
  List of rewards to be granted to the avatar when completing this marker game.
  Unset by default,
  but can be set using the chat command ``/gamereward`` in internal H'uru clients.
  Only used by H'uru clients and silently ignored by OpenUru clients.
  Not supported by MOSS.
  The value is a ``;``-separated string,
  with each element having one of the following formats:
  
  * :samp:`chron:{name}`
    or :samp:`chron:{name}:{value}` ---
    Set the chronicle entry :samp:`{name}` to :samp:`{value}`
    (defaults to ``1`` if omitted).
    The chronicle entry's type is assumed to be 0.
    If a chronicle entry with matching name and type already exists,
    it is updated in-place,
    otherwise a new chronicle entry is created.
  * :samp:`clothing:{name}`,
    :samp:`clothing:{name}:{tint1}`,
    or :samp:`clothing:{name}:{tint1}:{tint2}` ---
    Add the specified clothing item to the avatar's wardrobe.
    The :samp:`{name}` is automatically prefixed with ``F`` or ``M`` based on the avatar's clothing group/gender.
    :samp:`{tint1}` and :samp:`{tint2}` are in the format :samp:`{r},{g},{b}`,
    with each RGB component in decimal from 0 to 255.
    One or both tint colors may be omitted,
    in which case they default to white.
* ``Blob_1`` = **MarkerData:**
  The game's markers in packed binary form.
  Unset for GameMgr-based marker games.
  Only set by H'uru clients for vault-based marker games.
  Not understood by OpenUru clients.
  Not supported by MOSS,
  unless the database is updated using the script ``postgresql/UpdateForHuruGames.sql`` from the MOSS repository.
  The data format is as follows,
  with all values in little-endian byte order as usual:
  
  * **Marker count:** 4-byte unsigned integer.
  * **Markers:** Variable-length array.
    
    * **ID:** 4-byte unsigned integer.
    * **Age:** "Safe" string.
    * **X, Y, Z:** Each a 4-byte floating-point number.
    * **Description:** "Safe" string.

A Marker Game node should never have any child nodes.

.. _vault_folder_list_types:

Folder/list types
-----------------

The three node types :ref:`vault_node_folder`, :ref:`vault_node_player_info_list`, and :ref:`vault_node_age_info_list` use a common numbering scheme for their **FolderType** field (``Int32_1``).
Below is a full list of all folder/list types defined in the open-sourced client code.
Types in *italics* are effectively unused ---
they are never added to the vault by the client or any known server implementation.

.. csv-table::
   :header: #,Folder type,Used in node type
   :widths: auto
   
   0,UserDefinedNode,:ref:`vault_node_folder`
   1,InboxFolder,:ref:`vault_node_folder`
   2,BuddyListFolder,:ref:`vault_node_player_info_list`
   3,IgnoreListFolder,:ref:`vault_node_player_info_list`
   4,PeopleIKnowAboutFolder,:ref:`vault_node_player_info_list`
   5,*VaultMgrGlobalDataFolder*,*unused*
   6,ChronicleFolder,:ref:`vault_node_folder`
   7,AvatarOutfitFolder,:ref:`vault_node_folder`
   8,AgeTypeJournalFolder,:ref:`vault_node_folder`
   9,SubAgesFolder,:ref:`vault_node_age_info_list`
   10,DeviceInboxFolder,:ref:`vault_node_folder`
   11,*HoodMembersFolder*,*unused in vault*
   12,AllPlayersFolder,:ref:`vault_node_player_info_list`
   13,*AgeMembersFolder*,*unused in vault*
   14,AgeJournalsFolder,:ref:`vault_node_folder`
   15,AgeDevicesFolder,:ref:`vault_node_folder`
   16,*AgeInstanceSDLNode*,*unused*
   17,*AgeGlobalSDLNode*,*unused*
   18,CanVisitFolder,:ref:`vault_node_player_info_list`
   19,AgeOwnersFolder,:ref:`vault_node_player_info_list`
   20,*AllAgeGlobalSDLNodesFolder*,*unused*
   21,*PlayerInfoNode*,*unused*
   22,*PublicAgesFolder*,*unused*
   23,AgesIOwnFolder,:ref:`vault_node_age_info_list`
   24,AgesICanVisitFolder,:ref:`vault_node_age_info_list`
   25,AvatarClosetFolder,:ref:`vault_node_folder`
   26,*AgeInfoNode*,*unused*
   27,*SystemNode*,*unused*
   28,PlayerInviteFolder,:ref:`vault_node_folder`
   29,*CCRPlayersFolder*,*unused*
   30,GlobalInboxFolder,:ref:`vault_node_folder`
   31,ChildAgesFolder,:ref:`vault_node_age_info_list`
   32,*GameScoresFolder*,*unused*
