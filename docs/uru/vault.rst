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

.. _vault_node_types:

Node types
----------

Node types in *italics* are defined as constants in the open-sourced client code,
but are not real node types ---
they should never appear in the actual vault database or over the network.

.. hlist::
   
   * *Invalid* = 0
   * *VNodeMgrLow* = 1
   * Player = 2
   * Age = 3
   * *VNodeMgr_UNUSED00* = 4
   * *VNodeMgr_UNUSED01* = 5
   * *VNodeMgr_UNUSED02* = 6
   * *VNodeMgr_UNUSED03* = 7
   * *VNodeMgrHigh* = 21
   * Folder = 22
   * Player Info = 23
   * System = 24
   * Image = 25
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
