The MOUL network architecture
=============================

Myst Online: Uru Live and its derivatives use a client-server architecture with a client-authoritative model.
That is,
all communication goes through centralized servers (not peer-to-peer),
but most aspects of gameplay are managed by the clients,
without much logic and checks on the server side.

.. index:: server
   :name: server

The server side of MOUL actually consists of multiple servers that are mostly independent from each other.
Each of these servers may be hosted at a different address or port,
and certain server types may also have multiple instances,
allowing the server side to be distributed over multiple processes or machines.
This is not a requirement though ---
despite the name,
it is actually possible to host multiple (or all!) of these "servers" on the same port
and implement them all in a single monolithic server process.
This is the solution chosen by all fan-developed server implementations.
Cyan's MOULa shard is the only one that actually uses the distributed architecture,
and even it only separates the file server and runs everything else on a single shared port.

.. _server_types:

Server types
------------

These are all the server types used by the open-sourced MOULa client code:

* .. index:: status server
     single: server; status
     :name: status_server
  
  **Status server:**
  Serves the status message (unsurprisingly)
  that is displayed in the patcher and login window.
  Unlike all the other servers,
  this one uses regular HTTP via the conventional port 80.
  The status message can be hosted with a standard HTTP server,
  with the advantage that the status will display even if the Uru server itself is down.
  Alternatively,
  DIRTSAND also includes an optional minimal HTTP server for the status message.

* .. index:: gatekeeper server
     single: server; gatekeeper
     single: GateKeeperSrv
     :name: gatekeeper_server
  
  **Gatekeeper server (GateKeeperSrv):**
  Used by the patcher and game to get the address of the file server.
  This enables limited load balancing and allows changing the file server address without breaking self-updates for older installations.
  If a file server address was explicitly set in server.ini (for H'uru clients) or on the command line,
  that file server is always used and the gatekeeper server is not contacted.

* .. index:: file server
     single: server; file
     single: FileSrv
     :name: file_server
  
  **File server (FileSrv):**
  Used by the patcher and game to update the data files.
  This is the only server that uses unencrypted communication during normal operation.
  Some files are considered "secure" and are served via the auth server instead,
  although especially H'uru/DIRTSAND-based shards serve everything via the file server.

* .. index:: auth server
     single: server; auth
     single: AuthSrv
     :name: auth_server
  
  **Auth server (AuthSrv):**
  Handles not just the login process,
  but all kinds of global communication
  that is not specific to the player's current age.
  This includes sending players to the right game server when going to a new age,
  providing access to the vault and score mechanisms,
  and serving "secure" files not provided by the file server.
  The client code was apparently designed to support multiple alternative auth servers,
  but this was not fully implemented,
  so in practice there can be only one.

* .. index:: game server
     single: server; game
     single: GameSrv
     single: game manager
     single: GameMgr
     :name: game_server
  
  **Game server (GameSrv):**
  Provides communication within a single age instance
  by relaying Plasma messages over the network.
  It also provides the "game manager" (GameMgr),
  a different mechanism used for some multiplayer activities,
  like Ayoheek, marker games, and the hood garden age puzzle.
  To reduce complexity of the server side,
  the H'uru client no longer uses the game manager
  and the DIRTSAND server has never implemented it.
  There can theoretically be multiple game server instances,
  but in practice all MOULa servers use a single game server for all age instances.

* .. index:: CsrSrv
     single: server; CSR
     :name: csr_server
  
  **CsrSrv:**
  It's not clear what "CSR" stands for --- "customer support representative" (or "remote")?
  Apparently it provided some way for Cyan support or developers to remotely control other clients.
  The open-sourced client codebase contains code to communicate with a CSR server,
  but it is incomplete and unused in the open-source codebase,
  as it was apparently intended for the Cyan side of things.
  No fan server software implements the CsrSrv
  and H'uru has dropped all CSR-related code.

* .. index:: SimpleNet
     :name: simplenet
  
  **SimpleNet:**
  A generic unencrypted network protocol meant for remote connections *to* a client.
  In the open-sourced client code,
  SimpleNet is only used by some CSR-related code that is ``#ifdef``\ed out by default.
  Default client builds do not use SimpleNet in any way
  and H'uru has dropped it entirely.

The open-sourced client code also mentions a number of backend servers:

* **McpSrv**: master control process
* **VaultSrv**
* **DbSrv**: database
* **StateSrv**
* **LogSrv**
* **ScoreSrv**

These are apparently used internally by Cyan's MOUL(a) server software,
but because that has not been open-sourced,
very little is publicly known about them.
The client does not communicate with them directly
and no open-source server software implements them in this form,
so they are not relevant here.

As of 2022,
Cyan's MOULa shard uses the following hosts for its public-facing servers:

* account.mystonline.com (184.73.198.22): status, gatekeeper, auth, game
* 52.72.29.91: TODO unclear --- only contacted very briefly when the login screen appears
* 54.236.8.109: file

All fan-run shards use a single host for all public-facing "servers",
including the status server.
For example,
Minkata uses foundry.openuru.org aka urufoundry.haverhillcoop.net (70.91.173.88)
and Gehn uses guildofwriters.org (155.254.30.63).

.. warning::
   
   You probably shouldn't hardcode these IP addresses anywhere,
   although they seem to be quite stable.
