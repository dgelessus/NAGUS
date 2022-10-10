Version, build, and "product" info
==================================

MOUL clients have multiple different bits of version info and other metadata compiled into the executable.
I'm explaining it here,
because some of this information is either sent to the server
or indirectly affects how the client behaves.

Most of this information is displayed to the user as the "product string",
which might look like "UruLive.Live.1.918.OpenUru#205 - External.Release" for example.
The product string consists of the following parts:

* :ref:`core name <core_name>` --- UruLive
* :ref:`build type <build_type>` --- Live
* :ref:`branch ID <branch_id>` --- 1
* :ref:`build ID <build_id>` --- 918
* :ref:`factory ID <factory_id>` --- OpenUru#205
* :ref:`internal/external client <internal_external_client>` --- External
* :ref:`debug/release build <debug_release_build>` --- Release

Below is a list of *all* different kinds of version/build/product metadata,
including some bits that *aren't* displayed in the product string.

.. index::
   single: core name
   single: short name
   single: long name
   :name: core_name

Core name, short name, long name
--------------------------------

The name of the game is stored three times,
in slightly different formats.
Apparently the core name was meant to be an internal identifier
and the short and long names for display to the user,
but actual usage is all over the place.

None of these names are sent over the network.
They have almost no functional effect on the client.
A notable exception is that the long name is used as the name of the user data folder
(where settings, logs, KI pictures, etc. are stored),
so two clients with the same long name will share their settings.

For Cyan MOULa and Minkata clients,
as well as default OpenUru and H'uru builds,
the core and short names are "UruLive" and the long name is "Uru Live".
Many shards change this ---
for example,
Gehn uses core name "UruGehn" and long name "Uru - Gehn Shard",
and TOC-Moul uses core name "TOC" and long name "The Open Cave".

.. index:: product UUID
   :name: product_uuid

Product ID (UUID/GUID)
----------------------

A UUID/GUID identifying the game.
All MOUL shards that I know of use the UUID ``ea489821-6c35-4bd0-9dae-bb17c585e680``.
This value is sent to the server during :ref:`connection setup <connect_packet>`.
It has no other effect on the client.

.. index:: build type
   :name: build_type

Build type
----------

Indicates the stage in the release cycle for which the client was built.
The open-sourced client code defines the following build types:

* Dev = 10
* QA = 20
* Test = 30
* Beta = 40
* Live = 50

Build type Live is typically used for production builds distributed by shards.
It is also the default build type for H'uru clients built from source.
OpenUru source builds default to build type Dev instead.
The other build types are practically unused.

This value is sent to the server during :ref:`connection setup <connect_packet>`.
For OpenUru clients,
each build type uses its own separate user data folder,
and build type Dev enables a few extra assertions.
For H'uru clients,
the build type has no functional effect on the client.

.. index:: branch ID
   :name: branch_id

Branch ID
---------

Has always been 1 for most shards,
including GameTap MOUL, Cyan's MOULa, Minkata, and Gehn.
OpenUru and H'uru builds also default to branch ID 1.
TOC-Moul currently uses branch ID 2.

This value is sent to the server during :ref:`connection setup <connect_packet>`.
It has no other effect on the client.

.. index:: build ID
   :name: build_id

Build ID
--------

This is meant to be a build number that is increased with every update.
This value is sent to the server during :ref:`connection setup <connect_packet>`.
Cyan's server software and DIRTSAND check this value to ensure that the expected client version is used,
but MOSS does not.

All updates to Cyan's MOULa shard since June 2013 have used build number 918,
to allow updating the client without also having to rebuild the server every time.
(The actual build number is now indicated by the :ref:`factory ID <factory_id>`.)
For compatibility,
both OpenUru and H'uru clients also use build number 918 by default.
Other shards not coupled to Cyan's MOULa,
such as Gehn or TOC-Moul,
may use different build numbers that change on updates.

Cyan MOULa build IDs
^^^^^^^^^^^^^^^^^^^^

.. note::
   
   There are probably some builds missing between 1.866 and 1.897,
   because during that period Cyan didn't post detailed update notes on the forum.

* Build 1.866:
  Released `2010-02-11 <https://web.archive.org/web/20100220152603/http://www.fileplanet.com/209790/200000/fileinfo/Myst-Online:-URU-Live-Client-v.866>`__.
  This appears to be the first release of MOULa.
* Build 1.871:
  Released `2010-02-17 <https://mystonline.com/forums/viewtopic.php?f=36&t=19753>`__.
* Build 1.887:
  Released `2010-04-02 <https://web.archive.org/web/20110515133633/http://www.atomicgamer.com:80/games/1835/myst-online-uru-live/files>`__.
* Build 1.893:
  Released `2010-05-21 <https://distfiles.macports.org/mystonline/UruLauncher.exe-1.893.zip>`__ (or earlier?).
* Build 1.897:
  Released ???.
  CWE Git commit `30bbdbd3 <https://foundry.openuru.org/gitblit/commit/?r=CWE.git&h=30bbdbd327c2ea6832b88e40ceca2a6707a3a0d5>`__ (2011-03-12).
* Build 1.902:
  Released `2011-04-15 <https://mystonline.com/forums/viewtopic.php?f=36&t=24583>`__.
  CWE Git commit `a363a783 <https://foundry.openuru.org/gitblit/commit/?r=CWE.git&h=a363a783c5d2ffc7aa104275e5f34feb81db0e4b>`__ (2011-04-19).
* Build 1.905:
  Released `2012-02-13 <https://mystonline.com/forums/viewtopic.php?f=36&t=25435>`__.
  CWE Git commit `cbea546c <https://foundry.openuru.org/gitblit/commit/?r=CWE.git&h=cbea546c61507f9d549d41354ec8993482304680>`__ (2012-02-07).
* Build 1.906:
  Released `2012-03-26 <https://mystonline.com/forums/viewtopic.php?f=36&t=25583>`__.
  CWE Git commit `136c27c7 <https://foundry.openuru.org/gitblit/commit/?r=CWE.git&h=136c27c7f3bed150c25a17596a287493f31c39e0>`__ (2012-05-09).
* Build 1.912:
  Released `2012-05-29 <https://mystonline.com/forums/viewtopic.php?f=36&t=25730>`__.
  CWE Git commit `68ba122a <https://foundry.openuru.org/gitblit/commit/?r=CWE.git&h=68ba122afeb131b31e7d5f22fadffb16c987b802>`__ (2012-06-14).
* Build 1.918:
  Released `2013-06-11 <https://mystonline.com/forums/viewtopic.php?f=36&t=26572>`__.
  CWE Git commit `46a0cf62 <https://foundry.openuru.org/gitblit/commit/?r=CWE.git&h=46a0cf6206211366c43d5132b6190b3f4ca35c62>`__ (2013-07-05).
  All later client updates (as of 2022) also use this build number.

.. index:: factory ID
   :name: factory_id

Factory ID
----------

Contains the real build number of OpenUru-built clients
(for Cyan's MOULa shard and Minkata),
since the main build ID has been fixed at 918.
Clients built from the OpenUru codebase won't have a factory ID by default ---
this information is
`patched <https://foundry.openuru.org/gitblit/blob/?r=Foundry/CWE-ou-LocalData.git&f=MOULa/moula-1.patch&h=master>`__
into the product string by the OpenUru build servers.

H'uru clients don't have a factory ID,
but H'uru's CMake build inserts the current Git tag or commit hash into the product string,
which serves a similar purpose.

This value is not sent over the network and has no other effect on the client.

.. index::
   single: internal client
   single: client; internal
   single: external client
   single: client; external
   :name: internal_external_client

Internal/external client
------------------------

MOUL clients can be built as either "Internal" or "External".
Internal clients have a number of extra features over external clients
that are not meant for use by normal players,
such as increased logging, a developer console, and the ability to use custom data files.
For most shards,
the pre-built clients distributed to players are external clients.

Note that this setting is independent of the :ref:`build type <build_type>` ---
you can build an external client with build type Dev
or an internal one with build type Live.

For the most part,
if the player doesn't invoke any internal-only features,
internal clients behave like external ones and don't explicitly tell the server that they are internal.
The main exception is when updating through the file server,
where internal clients will request different manifests than external clients.

.. index::
   single: debug build
   single: release build
   :name: debug_release_build

Debug/release build
-------------------

This corresponds to the standard debug/release setting in Visual Studio and CMake.
Clients built in debug mode have many additional assertions and some extra logging enabled
(in addition to the standard compiler option changes).

This setting is not sent over the network and should have no visible effect on the client.
