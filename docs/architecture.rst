The Uru network architecture
============================

MOULa uses a client-server architecture with a client-authoritative model.
That is,
all communication goes through centralized servers (not peer-to-peer),
but most aspects of gameplay are managed by the clients,
without much logic and checks on the server side.

The server side of MOULa actually consists of multiple servers that are mostly independent from each other.
Each of these servers may be hosted at a different address or port,
and certain server types may also have multiple instances,
allowing the server side to be distributed over multiple processes or machines,
This is not a requirement though ---
despite the name,
it is actually possible to host multiple (or all!) of these "servers" on the same port
and implement them all using a single server program.
This is the solution chosen by all fan-developed server implementations.
Cyan's MOULa server is the only one that actually uses the distributed architecture,
and even it only separates the file server and runs everything else on a single shared port.

Server types
------------

These are all the server types used by the open-sourced MOULa client code:

* **Status server:**
  Serves the status message (unsurprisingly)
  that is displayed in the patcher and login window.
  Unlike all the other servers,
  this one uses regular HTTP via the conventional port 80.
  The status message can be hosted with a standard HTTP server,
  with the advantage that the status will display even if the Uru server itself is down.
  Alternatively,
  DIRTSAND also includes an optional minimal HTTP server for the status message.
* **Gatekeeper server (GateKeeperSrv):**
  Used by the patcher and game to get the address of the file server.
  If the file server address was overridden on the command line,
  the gatekeeper server is not contacted.
* **File server (FileSrv):**
  Used by the patcher and game to update the data files.
  This is the only server that uses unencrypted communication during normal operation.
  Some files are considered "secure" and are served via the auth server instead,
  although especially H'uru/DIRTSAND-based servers serve everything via the file server.
* **Auth server (AuthSrv):**
  Handles not just the login process,
  but all kinds of global communication
  that is not specific to the player's current age.
  This includes sending players to the right game server when going to a new age,
  providing access to the vault and score mechanisms,
  and serving "secure" files not provided by the file server.
  The client code was apparently designed to support multiple alternative auth servers,
  but this was not fully implemented,
  so in practice there can be only one.
* **Game server (GameSrv):**
  Provides communication within a single age instance
  by relaying Plasma messages over the network.
  It also provides the "game manager" (GameMgr),
  a different mechanism used for some multiplayer activities,
  like Ayoheek, marker games, and the hood garden age puzzle.
  For reasons that are not written down anywhere,
  the H'uru client no longer uses the game manager
  and the DIRTSAND server has never implemented it.
  There can theoretically be multiple game server instances,
  but in practice all MOULa servers use a single game server for all age instances.
* **CsrSrv:**
  Not clear what this stands for --- "customer service representative"?
  Included in the open-sourced client code,
  but not actually used anywhere.
  No fan server software implements it.

The open-sourced client code also mentions a number of backend servers:
Mcp, Vault, Db, State, Log, Score.
These are apparently used internally by Cyan's MOULa server,
but because that has not been open-sourced,
very little is publicly known about them.
The client does not communicate with them directly
and no open-source server software implements them in this form,
so they are not relevant here.

As of 2022,
MOULa uses the following hosts for its public-facing servers:

* account.mystonline.com (184.73.198.22): status, gatekeeper, auth, game
* 52.72.29.91: TODO unclear --- only contacted very briefly when the login screen appears
* 54.236.8.109: file
