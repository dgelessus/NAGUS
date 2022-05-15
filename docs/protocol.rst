The MOUL network protocol
=========================

All the different MOUL servers
(except for the status server)
use the same basic network protocol to talk with clients.
Communication is over TCP,
by default on port 14617.

The protocol mostly uses packed binary data structures.
Unless indicated otherwise,
all integers use little-endian byte order
and there is no padding/alignment between fields.

UUIDs use the Microsoft-style "little-endian" format,
where the first four bytes are swapped,
the following two pairs of bytes are each swapped individually,
and the remaining 8 bytes are not swapped.
For example,
the UUID ``12345678-1234-5678-1234-567812345678`` is stored as bytes ``78 56 34 12  34 12 78 56  12 34 56 78  12 34 56 78``.

.. note::
   
   The MOULa client code internally uses C ``struct``\s to encode/decode network data.
   This is generally not a good idea,
   because the exact format of ``struct``\s in memory varies depending on the target architecture and C compiler.
   In the case of MOULa,
   this is not a big problem in practice,
   because all supported architectures are little-endian
   and the code explicitly disables field padding/alignment.

.. _packet_boundaries:

Some parts of the Cyan codebase require data to arrive as individual packets of specific lengths,
even though the protocol is based on TCP,
which is stream-based and does not guarantee that packet boundaries will be maintained in transmission.
To avoid potential issues when interacting with Cyan clients/servers,
it's probably safest to send each packet individually instead of combining multiple packets.
To ensure that the OS network stack also doesn't combine packets,
you should disable `Nagle's algorithm <https://en.wikipedia.org/wiki/Nagle%27s_algorithm>`__
by setting ``TCP_NODELAY``
(this also reduces latency).

.. index:: connect packet
   :name: connect_packet

Connect packet
--------------

When a client connects to a server,
it immediately sends a *connect packet* with some information about the client and the requested connection type.
A connect packet consists of a generic header and a connection type-specific data section.
Both sections should be sent together :ref:`as a single packet <packet_boundaries>`.

* **Header:**
  
  * **Connection type:** 1-byte unsigned int.
    Indicates what type of server the client is expecting to connect to.
    This is what allows multiple "servers" to run on a single shared port.
    A full :ref:`list of connection types <connection_types>` can be found below.
  * **Header byte count:** 2-byte unsigned int.
    Always 31.
  * **Client build ID:** 4-byte unsigned int.
    Set to the client's :ref:`build ID <build_id>`.
    When connecting to the file server,
    this field is set to 0 instead,
    so that any client version can connect to update itself.
  * **Client build type:** 4-byte unsigned int.
    Set to the client's :ref:`build type <build_type>`.
  * **Client branch ID:** 4-byte unsigned int.
    Set to the client's :ref:`branch ID <branch_id>`.
  * **Client product UUID:** 16-byte UUID.
    Set to the client's :ref:`product ID <product_uuid>`.
  
* **Data:** Varies depending on the connection type,
  but always has a fixed size for each type.

The server doesn't reply to the connect packet in any way.
If the server isn't happy with the connect packet (e. g. wrong build number),
it simply closes the connection.
Otherwise the server awaits the next packet from the client.

.. _connection_types:

Connection types
^^^^^^^^^^^^^^^^

The following connection types are used by the open-source MOULa clients,
one for each server type that the client communicates with:

* CliToAuth = 10
* CliToGame = 11
* CliToFile = 16
* CliToGateKeeper = 22

The following connection types are present in the original open-source code
and their protocol format is at least partially known.
However,
the code is incomplete,
not useful in practice,
and has been removed entirely from the H'uru codebase:

* CliToCsr = 20
* SimpleNet = 21

Additionally,
the following connection types are defined,
but not used in any of the open-source code:

* Nil = 0 (apparently not a valid connection type)
* Debug = 1
* SrvToAgent = 12
* SrvToMcp = 13
* SrvToVault = 14
* SrvToDb = 15
* SrvToState = 17
* SrvToLog = 18
* SrvToScore = 19
* AdminInterface = 97 (ASCII code for the letter ``a``)

Connect packet data
^^^^^^^^^^^^^^^^^^^

Although the format of the connect packet data is completely type-specific,
in practice all connection types
(except for the mostly dead SimpleNet)
start the connect packet data with a 4-byte length field.
Here are the exact formats for all types
(where we know the protocol format at least):

* **CliToGatekeeper, CliToAuth:**
  
  * **Data byte count:** 4-byte unsigned int.
    Always 20.
  * **Token:** 16-byte UUID.
    Set to all zeroes by default.
    
    For auth server connections,
    the server may send the client a ``ServerAddr`` message containing a different token,
    which the client will send back to the server if it has to reconnect.
    Not sure if this is actually used in practice.
    
    For gatekeeper connections,
    there is no way to change the token,
    so the client always sends all zeroes.

* **CliToFile:**
  
  * **Data byte count:** 4-byte unsigned int.
    Always 12.
  * **Real build ID:** 4-byte unsigned int.
    Set to the client's :ref:`build ID <build_id>`.
    For file server connections,
    the generic header's build ID field is always set to 0,
    so this field is used as an alternative.
    The main client sends its real build ID here,
    but the patcher sets it to 0 (again).
  * **Server type:** 4-byte unsigned int.
    Always set to 0 by clients.
    Based on the open-sourced client code,
    it looks like other values might be used when a *server* is connecting to a file server (?).

* **CliToGame:**
  
  * **Data byte count:** 4-byte unsigned int.
    Always 36.
  * **Account UUID:** 16-byte UUID.
    Apparently unused and never initialized by the client.
  * **Age UUID:** 16-byte UUID.
    Apparently unused and never initialized by the client.

* **CliToCsr:**
  
  * **Data byte count:** 4-byte unsigned int.
    Always 4.

* **SimpleNet:**
  
  * **Channel ID:** 4-byte unsigned int.
    Apparently identifies the type of connection.
    The open-sourced client code defines the following SimpleNet channel IDs:
    
    * Nil = 0 (apparently not a valid channel ID)
    * Csr = 1
    * Max = 2 (based on comments, this probably stands for 3DS Max, not "maximum" --- although this is also the highest defined channel ID!)

.. note::
   
   After the connect packet,
   SimpleNet connections use a different protocol than all other connection types.
   I won't cover SimpleNet further here,
   because it's practically unused.

.. _connection_encryption:

Encryption
----------

Connections using the MOUL protocol are normally encrypted using RC4.
After sending the connect packet,
the client begins setting up encryption.

The main exception is the file server connection,
which is never encrypted.
When connecting to the file server,
the encryption setup is skipped
and the client begins sending unencrypted messages immediately after the connect packet.
For development and testing purposes,
encryption can also be disabled entirely --- see :ref:`disabling_connection_encryption`.

Every encrypted connection uses a new 56-bit key,
derived using Diffie-Hellman key exchange from :ref:`values generated by the shard admin <dh_keys>`.
The *g*, *n*, and *x* values are published and :doc:`configured in the client <server_config>`.
The key exchange process goes like this:

1. Client generates a new random 512-bit private key *b*.
2. Client calculates *kb = x*:sup:`b` *mod n* and *y = g*:sup:`b` *mod n*.
3. Client sends *y* to the server.
4. Server calculates *ka = y*:sup:`a` *mod n*.
5. Server generates a random 56-bit *seed*.
6. Server sends *seed* to the client.
7. Server calculates *key = seed xor* (*ka* truncated to 56 bits).
8. Client calculates *key = seed xor* (*kb* truncated to 56 bits).

Because Diffie-Hellman,
*ka* is equal to *kb*,
so both client and server now have the same 56-bit *key*.
Both sides now initialize standard RC4 encryption using this *key* in both directions.
All communication from this point on is transparently encrypted.

Encryption setup packets
^^^^^^^^^^^^^^^^^^^^^^^^

During the key exchange process,
client and server communicate using a minimal type-length-value packet format.
Every packet during encryption setup has this format:

* **Message type:** 1-byte unsigned int.
* **Packet byte count:** 1-byte unsigned int.
* **Packet data:** Varies depending on message type.

The open-source client code defines the following message types and contents:

* (client -> server) **Connect** = 0
  
  * **Value of y:** Variable-length integer (maximum 16 bytes).
    Length is implied by the packet byte count.
    *y* should always be 16 bytes long.
    The main exception is when a H'uru client :ref:`requests no encryption <disabling_connection_encryption>`,
    in which case it sends a 0-byte "value" for *y*.
  
* (server -> client) **Encrypt** = 1
  
  * **Seed:** 7 bytes ---
    except when replying to a H'uru client :ref:`requests no encryption <disabling_connection_encryption>`,
    in which case it must be 0 bytes.
  
* (server -> client) **Error** = 2
  
  * **Error code:** 4-byte unsigned int.

In practice,
only Connect and Encrypt messages are used.
Message type Error is mostly ignored by the client ---
it doesn't display the error in any way
and just continues waiting for an Encrypt message.
The client only considers encryption as failed
if the server closes the connection entirely
(resulting in a generic "Disconnected from Myst Online" error,
even if the server sent an error code before disconnecting).

.. _disabling_connection_encryption:

Disabling encryption
^^^^^^^^^^^^^^^^^^^^

For easier development/testing,
both OpenUru and H'uru clients support disabling encryption for all connections.
When a client with encryption disabled connects to a server that would normally use encryption,
it still exchanges encryption setup packets with the server,
but the contained data is ignored and both sides communicate unencrypted afterwards.
This is different from the always-unencrypted file server connection,
where the encryption setup step is skipped completely.

The exact process for disabling encryption varies between OpenUru and H'uru clients.
These differences also affect how the server must respond.

For OpenUru clients,
encryption can be disabled at compile time by defining the macro ``NO_ENCRYPTION`` in the file NucleusLib/pnNetCli/pnNcCli.cpp.
Doing so disables the network data encryption/decryption code and nothing else.
In particular,
client and server still perform key exchange as normal,
but the client ignores the resulting *key* and expects the server to do the same.
The server has no way of knowing that a client has been built with ``NO_ENCRYPTION``,
so this mode can only be handled correctly
by manually disabling encryption on the server side in a similar manner.
MOSS supports a ``NO_ENCRYPTION`` macro for this purpose,
but DIRTSAND does not.

For H'uru clients,
encryption can be disabled for any server type by omitting the respective keys from the server.ini.
In this case,
the client sends a Connect message with a 0-byte *y* value.
The server side must recognize this unencrypted connection request
and must reply accordingly with an Encrypt message with a 0-byte *seed* value.
This is supported by DIRTSAND,
but not MOSS or Cyan's server software.

.. _messages:

Messages
--------

Once the connection is fully set up,
client and server communicate using messages in the following format:

* **Message type:** 2-byte unsigned int.
* **Message data:** Varies depending on message type.

The meaning of the message type number depends on the connection type and communication direction
(client -> server or server -> client).
For each connection type,
client-to-server and server-to-client messages with the same type numbers often have related meanings ---
e. g. file server message type 20 is a manifest *request* when sent by the client and a manifest *reply* when sent by the server.
This is not required though ---
e. g. the auth server protocol uses different message type numbers for request and reply messages,
and some messages don't have any counterpart in the opposite direction.

Each connection type uses entirely different message type numbers.
The only exception is message type 0,
which stands for a ping request/reply for all known connection types
(gatekeeper, file, auth, game, CSR),
although the data format differs between connection types.

The format of the message data is completely different for each message type
(which in turn depends on the connection type and communication direction).
The overall message format doesn't contain any generic information about the structure of the message,
not even its length.
This means that if a message with an unknown type is received,
it's impossible to safely process that message and any further ones after it.

.. note::
   
   In the rest of this documentation,
   if I say "message type",
   assume that I mean the *logical* message type,
   i. e. the combination of message type number, communication direction, and connection type.

Handling of unknown message types
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the open-sourced client code,
when an unknown message type is received,
the client logs an error,
but it doesn't abort the connection and doesn't try to recover from the error in any way.
Instead,
the data following the unknown message type is treated as the start of the next message,
which is almost guaranteed to result in nonsense and unlikely to resynchronize the message stream correctly.

This (lack of) error handling is still present in both the OpenUru and H'uru codebases.
Cyan's MOULa server software probably behaves similarly.
The open-source MOSS and DIRTSAND servers handle this more safely
by closing the connection when an unknown message is received.

To avoid unpredictable behavior,
both client and server must be careful to only send message types that the other side understands.

H'uru clients and DIRTSAND implement a few new message types
that are not supported by OpenUru clients, MOSS, or Cyan's server software.
To avoid issues with non-DIRTSAND servers,
a H'uru client will never send any of these extended messages
unless the server has indicated that it supports them.
Unfortunately,
to inform clients about its features,
DIRTSAND sends a new message type (Auth2Cli_ServerCaps) to every client as soon as it connects to the auth server.
This makes current DIRTSAND versions (since 2018) incompatible with OpenUru clients (and old H'uru clients from before 2017),
because they don't understand the new message type sent by the server.
