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
(e. g. player info nodes),
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
which is a distinct state and *not* the same as 0/empty.
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
   * :ref:`Player <vault_node_player>` = 2
   * :ref:`Age <vault_node_age>` = 3
   * *VNodeMgr_UNUSED00* = 4
   * *VNodeMgr_UNUSED01* = 5
   * *VNodeMgr_UNUSED02* = 6
   * *VNodeMgr_UNUSED03* = 7
   * *VNodeMgrHigh* = 21
   * :ref:`Folder <vault_node_folder>` = 22
   * :ref:`Player Info <vault_node_player_info>` = 23
   * :ref:`System <vault_node_system>` = 24
   * :ref:`Image <vault_node_image>` = 25
   * Text Note = 26
   * SDL = 27
   * Age Link = 28
   * Chronicle = 29
   * Player Info List = 30
   * *UNUSED00* = 31
   * *UNUSED01* = 32
   * Age Info = 33
   * Age Info List = 34
   * Marker Game = 35

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

* ``CreateAgeName``, ``CreateAgeUuid``: Normally left unset.
  Not supported by MOSS for this node type.
* ``NodeType`` = 2
* ``Int32_1`` = **Disabled:** Not used by the open-sourced client code or fan servers.
  (TODO Does Cyan's server software do anything with it?)
  Normally left unset.
  MOSS initializes it to 0 when creating a new avatar.
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

.. _vault_node_age:

Age
^^^

* ``CreateAgeName``, ``CreateAgeUuid``: Normally left unset.
  Not supported by MOSS for this node type.
* ``NodeType`` = 3
* ``Uuid_1`` = **AgeInstanceGuid:** This age instance's unique ID.
* ``Uuid_2`` = **ParentAgeInstanceGuid:** The AgeInstanceGuid of this age instance's parent instance,
  or unset if this age is not a sub-age.
* ``String64_1`` = **AgeName:** Internal name of the age that this is an instance of.

.. _vault_node_folder:

Folder
^^^^^^

* ``NodeType`` = 22
* ``Int32_1`` = **FolderType:** The folder's general meaning/purpose.
  See :ref:`vault_folder_list_types` for details.
* ``String64_1`` = **FolderName:** Name of the folder.
  If present,
  it's often (but not always) a human-readable name that is displayed to the player,
  e. g. the name of an age inbox folder.
  For many folder types,
  this field is left unset
  and it's expected that the type alone uniquely identifies the folder inside its parent.

.. _vault_node_player_info:

Player Info
^^^^^^^^^^^

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
  Should always be identical to the ``String64_3`` (AgeInstanceName) field of the Age Info node indicated by this node's AgeInstUuid field,
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
    
    * Text Note: Type = Generic, SubType = Generic, Title = "Sharper", Text = *contents of Douglas Sharper's journal*
  
  * :ref:`vault_node_folder`: FolderType = UserDefinedNode, FolderName = "MemorialImager"
    
    * Text Note: Type = Generic, SubType = Generic, Title = "MemorialImager", Text = *list of names to be displayed on the Kahlo Pub memorial imager*
  
  * *additional nodes that will be displayed in every avatar's Incoming folder*

All child nodes of the global inbox folder,
except for :ref:`vault_node_folder` or Chronicle nodes,
are displayed as the first entries in every avatar's KI Incoming folder,
above any nodes from the per-avatar inbox folder.
Players cannot delete nodes from the global inbox folder using the KI user interface,
unlike nodes stored in the per-avatar inbox folder.

.. _vault_node_image:

Image
^^^^^

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

.. _vault_folder_list_types:

Folder/list types
-----------------

The three node types :ref:`vault_node_folder`, Player Info List, and Age Info List use a common numbering scheme for their **FolderType** field (``Int32_1``).
Below is a full list of all folder/list types defined in the open-sourced client code.
Types in *italics* are effectively unused ---
they are never added to the vault by the client or any known server implementation.

.. csv-table::
   :header: #,Folder type,Used in node type
   :widths: auto
   
   0,UserDefinedNode,:ref:`vault_node_folder`
   1,InboxFolder,:ref:`vault_node_folder`
   2,BuddyListFolder,Player Info List
   3,IgnoreListFolder,Player Info List
   4,PeopleIKnowAboutFolder,Player Info List
   5,*VaultMgrGlobalDataFolder*,*unused*
   6,ChronicleFolder,:ref:`vault_node_folder`
   7,AvatarOutfitFolder,:ref:`vault_node_folder`
   8,AgeTypeJournalFolder,:ref:`vault_node_folder`
   9,SubAgesFolder,Age Info List
   10,DeviceInboxFolder,:ref:`vault_node_folder`
   11,*HoodMembersFolder*,*unused in vault*
   12,AllPlayersFolder,Player Info List
   13,*AgeMembersFolder*,*unused in vault*
   14,AgeJournalsFolder,:ref:`vault_node_folder`
   15,AgeDevicesFolder,:ref:`vault_node_folder`
   16,*AgeInstanceSDLNode*,*unused*
   17,*AgeGlobalSDLNode*,*unused*
   18,CanVisitFolder,Player Info List
   19,AgeOwnersFolder,Player Info List
   20,*AllAgeGlobalSDLNodesFolder*,*unused*
   21,*PlayerInfoNode*,*unused*
   22,*PublicAgesFolder*,*unused*
   23,AgesIOwnFolder,Age Info List
   24,AgesICanVisitFolder,Age Info List
   25,AvatarClosetFolder,:ref:`vault_node_folder`
   26,*AgeInfoNode*,*unused*
   27,*SystemNode*,*unused*
   28,PlayerInviteFolder,:ref:`vault_node_folder`
   29,*CCRPlayersFolder*,*unused*
   30,GlobalInboxFolder,:ref:`vault_node_folder`
   31,ChildAgesFolder,Age Info List
   32,*GameScoresFolder*,*unused*
