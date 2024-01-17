About NAGUS
===========

This is NAGUS, an Uru Live server that is not very good.

I started writing this server while trying to understand how MOULa's networking works.
It's meant to be a simple cross-platform MOULa server
that I can easily experiment with.

NAGUS is still a work-in-progress and *very* incomplete.
See the :ref:`implementation status <implementation_status>` for details on what works and what doesn't yet.
My long-term goal is to make NAGUS a complete standalone MOULa server
that can run a small MOULa shard for testing.

.. note::
  
  That will still take a while
  and I might not even get to that point.
  Even once development has progressed,
  NAGUS is *not* intended for running a large, production-quality, public MOULa shard.

Ideally,
I want to keep the setup process as simple as possible,
especially compared to MOSS and DIRTSAND.
For this reason,
NAGUS only requires a Python interpreter
and no extra dependencies or external components
(like a database server).

.. note::
  
  You may also be interested in `MOULArs <https://github.com/zrax/moulars>`__,
  another cross-platform MOULa server under development
  that aims to be simpler to set up.

Scope
-----

I'm calling this an "Uru Live server",
but it is specifically for Uru Live's latest iteration,
"Myst Online: Uru Live again" (MOULa),
and its derivatives.
NAGUS aims to fully support both the OpenUru and H'uru forks of the open-source MOULa client.
The main focus is on current versions of these clients,
but NAGUS will retain compatibility with old client versions where practical.

Pre-MOULa clients are *not* supported.
Some late GameTap-era MOUL clients *might* work,
but this hasn't been tested.
Pre-MOUL clients based on the original Uru Live will *not* work,
because they use a completely different network protocol than MOUL(a).

Goals
-----

* Keeping the server self-contained and easy to set up.
  
  * All parts of the server run in a single process.
    Notably,
    NAGUS uses an SQLite database instead of a separate database server.
  * No third-party libraries or native modules are required.
    Some *optional* third-party/native dependencies might be added in the future though.
  * The server configures itself automatically as much as possible
    and tries to use reasonable defaults otherwise.
* Compatibility with both OpenUru and H'uru clients,
  including old versions of those clients where practical.
  
  * Configurability of server-side behavior that could cause compatibility issues.
* Checking the data sent by clients
  to detect errors and problematic or unusual data.
* Providing optional logging and debugging features for examining the network communication.
* Using static type annotations in the code where possible.

Non-goals
^^^^^^^^^

* Being a high-performance, parallel, scalable, distributed, Serious Business server
  that can support a large MOULa shard with hundreds of players.
  NAGUS is written in Python,
  so the potential maximum performance is already limited.
  I probably won't optimize the code much,
  unless it's slow enough to cause problems for small player counts.
* Implementing irrelevant parts of the protocol.
  My general principle is:
  if a feature has never been used by clients and is unlikely to ever be used in the future,
  I probably won't implement it in NAGUS.
* Implementing a full creatable factory system like Plasma or DIRTSAND
  or a keeping a complete list of class indices like MOSS.
  In each place where a dynamic creatable object needs to be read,
  NAGUS only supports the appropriate classes for that place
  and fails fast for unexpected classes.
  This prevents type confusion in case a buggy or malicious client sends invalid data.

.. _implementation_status:

Implementation status
---------------------

NAGUS is currently still *very* incomplete.
Most ages are playable,
but some mechanics are still missing
and multiplayer generally doesn't work yet.

What works so far
^^^^^^^^^^^^^^^^^

* Creating and linking to age instances.
* Walking around in-age and interacting with most things.
* Creating and deleting avatars.
* The vault is fully working and saved persistently in a local SQLite database.
* Limited saving of SDL states.
  Works without .sdl files on the server side,
  but can break for unlucky combinations of SDL variables.
* The score server interface exists,
  but doesn't actually allow saving any scores.
* Status message over HTTP.
* Receiving client error stack traces.
* Adjustable configuration via a config file and/or command-line arguments.
* Command-line console for controlling the server while running.

Still to be implemented
^^^^^^^^^^^^^^^^^^^^^^^

* Any kind of actual multiplayer functionality.
  The server accepts multiple simultaneous clients,
  but they can't see each other or interact in-game in any way.
  
  * Propagating :cpp:class:`plNetMsgGameMessage`\s, :cpp:class:`plNetMsgSDLStateBCast`, and :cpp:class:`plNetMsgVoice` to other clients.
  * Tracking non-persistent SDL states on the server side
    and sending them to other clients when joining an existing game server.
  * Handling concurrent :cpp:class:`plNetMsgTestAndSet`\s (locking) properly.
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
  to support OpenUru external clients
  and H'uru clients without :option:`/LocalSDL`.
* Marking vault node refs as seen
  (though other servers don't really implement that either).
* Sending clients the list of avatars in an age instance
  and avatar join/leave updates.
* Reporting current population counts for public age instances.
* Better SDL support.
  
  * Proper parsing of SDL blobs based on state descriptors
    instead of guessing their structure.
  * Updating SDL blobs to a newer version of the same state descriptor.
  * Global (shard-wide) age SDL settings.
* The :ref:`game manager <game_manager>` to support marker games and some puzzles with OpenUru clients.
* Actual score server functionality instead of the current stub implementation.
* H'uru extended :ref:`auth server <auth_server>` messages.
* More console commands.
  
  * Interacting with the vault.
  * Restricting connections and/or logins.
