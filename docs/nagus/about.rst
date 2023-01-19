About NAGUS
===========

This is NAGUS, an Uru Live server that is not very good.

Scope and goals
---------------

I'm calling this an "Uru Live server",
but it is specifically for Uru Live's latest iteration,
"Myst Online: Uru Live again" (MOULa),
and its derivatives.
NAGUS aims to fully support both the OpenUru and H'uru forks of the open-source MOULa client.
Older MOUL(a) clients may work too,
but this is not a primary goal.
NAGUS does *not* support pre-MOUL clients based on the original Uru Live,
as they use a different network protocol than MOUL(a).

A secondary goal is to keep this server self-contained and easy to set up.
All parts of the server run in a single process,
using an SQLite database instead of a separate database server.
The server is implemented in pure Python using only standard library modules ---
you don't need to install any third-party dependencies.

.. _implementation_status:

Implementation status
---------------------

NAGUS is currently still *very* incomplete ---
you can log in,
link to ages,
and walk around,
but not much more.
A lot of things needed for normal gameplay are still broken.
See :ref:`implementation_status` for details.

What works so far
^^^^^^^^^^^^^^^^^

* Creating and linking to age instances.
* Walking around in-age and interacting with some basic things.
* Creating and deleting avatars.
* The vault mostly works and is saved persistently in a local SQLite database.
* Status message over HTTP.
* Receiving client error stack traces.

Still to be implemented
^^^^^^^^^^^^^^^^^^^^^^^

* Any kind of actual multiplayer functionality.
  The server accepts multiple simultaneous clients,
  but they can't see each other or interact in-game in any way.
  
  * Sending vault change notifications to other clients.
  * Propagating :cpp:class:`plNetMsgGameMessage`\s to other clients.
  * Handling concurrent :cpp:class:`plNetMsgTestAndSet`\s (locking) properly.
  * Multiplayer handling for all the other game server messages that aren't implemented yet.
* Connection encryption.
  Currently,
  client connections are always unencrypted
  and clients must have :ref:`encryption disabled <disabling_connection_encryption>` to connect.
  
  * Generating server keys.
  * Outputting the corresponding client keys in the appropriate formats for H'uru and OpenUru clients.
* Actual authentication and account management.
  Currently,
  there's one single account
  that you can log in to with any username/password.
  
  * Figure out how to do account creation and other account management stuff
    that can't be done via the game client.
* The :ref:`gatekeeper server <gatekeeper_server>` for sending the other server addresses.
* The :ref:`file server <file_server>` to make the patcher work
  (or at least safely do nothing).
* Serving "secure" files (SDL, Python) via the :ref:`auth server <auth_server>`
  to support external clients
  (especially OpenUru).
* Missing vault features:
  sending nodes (KI mail)
  and marking node refs as seen
  (though other servers don't really implement that either).
* Sending clients the list of avatars in an age instance
  and avatar join/leave updates.
* SDL support to make most age state work.
* The :ref:`GameMgr <game_manager>` to support marker games and some puzzles with OpenUru clients.
* Public age management.
* The score server.
* H'uru extended :ref:`auth server <auth_server>` messages.
* A config file for server settings that commonly need changing:
  e. g. welcome message, database file location, listen address, and port number.
* A command line for controlling the server once it's running,
  e. g. listing connections, force-disconnecting someone, and gracefully stopping the server.

