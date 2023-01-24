Changelog
=========

Version 0.1.0
-------------

(not released yet)

* Added the ability to set various configuration options
  (e. g. server ports)
  in a config file or on the command line.
* Added initial handling of ``plNetMsgGameMessage``.
  Currently only echoes (if requested) and does no propagation,
  because inter-client communication isn't supported yet.
* Added placeholder handling of ``plNetMsgTestAndSet``,
  allowing the player to interact with most clickables.
* Implemented handling of init age requests with a zero instance UUID,
  which is needed when linking to a child age for the first time.
* Changed vault node refs to be unseen by default,
  matching what the client code assumes.
* Changed the single placeholder account to use a non-zero UUID.
* Fixed vault node creator info not being set in most cases.
* Fixed ``plNetMsgSDLStateBroadcast`` parsing.

Version 0.0.0
-------------

* First tagged version.
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
