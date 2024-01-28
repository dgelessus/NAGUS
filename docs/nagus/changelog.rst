Changelog
=========

Version 0.2.0
-------------

* Added configurable automatic creation of static public age instances,
  using the same static_ages.ini configuration format as DIRTSAND.
  This generic mechanism replaces the previous hardcoded creation of Bevin and a public Ae'gura instance.
  
  * Added a default static_ages.ini
    that closely follows that from DIRTSAND.
    As a result,
    many more ages are now accessible by normal gameplay means,
    namely Kirel, the Watcher's Pub, Phil's Relto, and all ages reachable from there.
    (Note that many of them can only be accessed after manually changing some SDL settings.)
* Implemented the gatekeeper server.
  This is necessary preparation for making the launcher work
  (once the file server is implemented).

Version 0.1.1
-------------

* Implemented sending the Auth2Cli_ServerCaps message to clients.
  This makes H'uru clients not use the game manager
  (which this server doesn't support yet).
* Implemented all remaining game server messages.
  This has no effect on gameplay,
  but fixes multiple warning/error messages on the server side.
* Implemented parsing of many (but not all) ``plMessage`` subclasses
  that can be sent over the network.
  This should have no effect on gameplay,
  but gives more useful log messages if ``plMessage`` parsing and logging is enabled.
* Changed SDL state handling to not persist states for avatar and/or clone objects,
  which become unusable once the age instance is unloaded.
  This should have no effect on gameplay,
  but fixes some warnings on the client side.
* Changed game server ``plNetMessage`` parsing to treat an incompletely parsed message as a hard error
  (this previously only logged a warning).
  Unknown message types are still allowed
  (they log an error,
  but don't disconnect the client).
* Fixed OpenUru clients displaying the hood membership in the KI as "Member of (null) Bevin".

Version 0.1.0
-------------

First version with somewhat working one-player gameplay.
Many important gameplay features work
and progress is saved persistently.
There is still no support for multiplayer, encrypted connections, or serving files to clients.

* Added the ability to set various configuration options
  (e. g. server ports)
  in a config file or on the command line.
* Added a simple console for controlling the server while running.
* Added initial handling of ``plNetMsgGameMessage``.
  Currently only echoes (if requested) and does no propagation,
  because inter-client communication isn't supported yet.
* Added handling of ``plNetMsgTestAndSet``,
  allowing the player to interact with most clickables.
* Added Bevin as the only neighborhood instance for now.
  All new avatars are members of Bevin.
* Implemented sending vault nodes
  (KI mail).
* Implemented the public age interface.
  This makes the city and neighborhood links visible in the Nexus.
* Implemented handling of init age requests with a zero instance UUID,
  which is needed when linking to a child age for the first time.
* Implemented experimental SDL blob parsing based on "guessing" the structure.
  Works without .sdl files on the server side,
  but can break for unlucky combinations of SDL variables.
* Implemented saving of SDL states for age instances and objects within them.
* Implemented a minimal version of the score server ---
  just enough to avoid errors when the player opens the big KI.
  This doesn't actually allow saving any scores.
* Changed vault node refs to be unseen by default,
  matching what the client code assumes.
* Changed the single placeholder account to use a non-zero UUID.
* Improved status server to work around the quirks and limitations of current clients,
  specifically with status messages that are very long and/or contain non-ASCII characters.
* Improved performance of some vault-heavy operations
  (like creating a new avatar)
  by sending vault change notifications only for nodes that the client knows about.
* Improved sending of AgeSDLHook initial SDL states
  and fixed calculation of their sequence numbers.
  Clients should now receive the initial age SDL correctly and more reliably.
* Fixed vault node creator info not being set in most cases.
* Fixed ``plNetMsgSDLStateBroadcast`` parsing.
* Fixed avatars staying online if the game is closed without logging out first.

Version 0.0.0
-------------

First tagged version.
Minimum barely playable state,
assuming a single client with encryption disabled and ``/LocalData``.

* Placeholder login code that doesn't check username/password.
* Creating and deleting avatars.
* The vault mostly works and is saved persistently in a local SQLite database.
* Creating and linking to age instances.
* Barely working game server.
  Ignores all ``plNetMessage`` types,
  except for sending an empty age state to the client.
* Status message over HTTP.
* Receiving client error stack traces.
