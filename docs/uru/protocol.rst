The MOUL network protocol
=========================

MOUL clients communicate with the server side over TCP,
on port 14617 by default.
All the different server types use the same basic protocol,
although a few server types
(:ref:`file server <file_server>` and :ref:`SimpleNet <simplenet>`)
modify the protocol somewhat.
Finally,
the :ref:`status server <status_server>` uses standard HTTP on the conventional port 80
instead of the MOUL protocol.

.. seealso::
   
   :doc:`architecture` for a high-level overview of the different MOUL server types.

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

IPv4 addresses are sometimes represented in packed integer form
instead of a string in the more common "dotted quad" format.
Like all other integers,
they are transmitted in little-endian byte order,
so they will be in reverse order compared to the "network byte order" (big-endian) used in IPv4 packets.
For example,
the address 184.73.198.22 would be represented as the integer 0xb849c616 (= 3091842582 in decimal)
and transmitted as bytes ``16 c6 49 b8``.

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
    the server may send the client an :ref:`auth2cli_server_addr` message containing a different token,
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

The file server connection uses a slightly different message header,
but otherwise behaves like all the others:

* **Message byte count:** 4-byte unsigned int.
* **Message type:** 4-byte unsigned int.
* **Message data:** Varies dependning on the message type.

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
The overall message format doesn't contain any generic information about the structure of the message ---
there isn't even a length field,
except in the file server protocol.
For all other connection types,
if a message with an unknown type is received,
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

For the file server protocol,
the situation is slightly different ---
because the file server message header contains a length field,
it's theoretically possible to safely skip unknown messages.
However,
the open-sourced client code triggers a debug assertion failure when an unknown message type is received.
Even worse,
in :ref:`release builds <debug_release_build>` the assertion is replaced by an unreachable code statement,
leading to unpredictable behavior if a release client is sent an unknown file server message.

This (lack of) error handling is still present in both the OpenUru and H'uru codebases.
Cyan's MOULa server software probably behaves similarly to the open-source client.
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

Message descriptions in the client code
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For all connection types except the file server,
the structure of each message type is declaratively specified in global variables,
which are used by the client code to convert between network and in-memory representations of the message data.
The file server client code doesn't use this mechanism
and instead directly reads/writes structs in memory,
so this section *doesn't* apply there.

The infrastructure for declaring message structures is found in :file:`Plasma/NucleusLib/pnNetCli/pnNetCli.h`.
The actual message definitions are found under :file:`Plasma/NucleusLib/pnNetProtocol/Private/Protocols`,
with each connection type having its own subdirectory.
Message types are declared with the following macro:

.. c:macro:: NET_MSG(msgId, msgFields)
   
   Initializer for a ``NetMsg`` struct.
   
   :param msgId: Name of the integer constant for the message type number.
       By convention,
       this constant should be named :samp:`k{Sender}2{Receiver}_{MessageName}`,
       e.g. ``kCli2Auth_PingRequest`` or ``kAuth2Cli_PingReply``.
   :param msgFields: Name of a ``NetMsgField []`` variable describing the types of all fields in the message.

A simple message type declaration might look like this:

.. code-block:: cpp
   
   // header file
   enum {
       kCli2Whatever_SomeMessage,
   };
   extern const NetMsg kNetMsg_Cli2Whatever_SomeMessage;
   
   // source file
   static const NetMsgField kSomeMessageFields[] = {
       NET_MSG_FIELD_DWORD(),
       NET_MSG_FIELD_STRING(64),
   };
   const NetMsg kNetMsg_Cli2Whatever_SomeMessage =
       NET_MSG(kCli2Whatever_SomeMessage, kSomeMessageFields);

The following basic message field types are defined:

.. c:macro::
   NET_MSG_FIELD_BYTE()
   NET_MSG_FIELD_WORD()
   NET_MSG_FIELD_DWORD()
   NET_MSG_FIELD_QWORD()
   
   A single integer,
   1, 2, 4, or 8 bytes large,
   respectively.
   Only :c:macro:`NET_MSG_FIELD_BYTE` and :c:macro:`NET_MSG_FIELD_DWORD` are actively used.

.. c:macro::
   NET_MSG_FIELD_FLOAT()
   NET_MSG_FIELD_DOUBLE()
   
   A single floating-point number,
   4 or 8 bytes large,
   respectively.
   Not actively used.

.. c:macro::
   NET_MSG_FIELD_BYTE_ARRAY(maxCount)
   NET_MSG_FIELD_WORD_ARRAY(maxCount)
   NET_MSG_FIELD_DWORD_ARRAY(maxCount)
   NET_MSG_FIELD_QWORD_ARRAY(maxCount)
   NET_MSG_FIELD_FLOAT_ARRAY(maxCount)
   NET_MSG_FIELD_DOUBLE_ARRAY(maxCount)
   
   A fixed-length array of any of the above types.
   Only :c:macro:`NET_MSG_FIELD_DWORD_ARRAY` is actively used.
   
   :param maxCount: Number of elements in the array.
       Contrary to the *max* in the name,
       the array must always have *exactly* this many elements and not fewer.

.. c:macro:: NET_MSG_FIELD_STRING(maxLength)
   
   A little-endian UTF-16 string,
   prefixed with a 16-bit unsigned int length field
   (counted in 16-bit code units, not bytes).
   
   :param maxCount: Maximum length of the string in code units **plus one**.
       The extra code unit is reserved for the zero terminator,
       which is not transmitted over the network,
       but is implicitly added by the client when it receives the string.

.. c:macro::
   NET_MSG_FIELD_DATA(maxBytes)    
   NET_MSG_FIELD_PTR(maxBytes)     
   NET_MSG_FIELD_RAW_DATA(maxBytes)
   NET_MSG_FIELD_RAW_PTR(maxBytes)
   
   A fixed-length field of bytes with no declared structure.
   There is no functional difference between these four types.
   Only :c:macro:`NET_MSG_FIELD_DATA` and :c:macro:`NET_MSG_FIELD_RAW_DATA` are actively used ---
   in fact,
   the open-sourced client code doesn't implement reading for :c:macro:`NET_MSG_FIELD_PTR` and :c:macro:`NET_MSG_FIELD_RAW_PTR`,
   only writing.
   
   :param maxCount: Size in bytes of the field.
       Contrary to the *max* in the name,
       the data must be *exactly* this long and not shorter.

.. c:macro:: NET_MSG_FIELD_VAR_COUNT(elemSize, maxCount)
   
   A 4-byte unsigned integer indicating the number of elements in the following variable-length array field
   (:c:macro:`NET_MSG_FIELD_VAR_PTR` or :c:macro:`NET_MSG_FIELD_RAW_VAR_PTR`).
   
   :param elemSize: Size in bytes of each array element.
   :param maxCount: Maximum number of elements in the array.

.. c:macro::
   NET_MSG_FIELD_VAR_PTR()    
   NET_MSG_FIELD_RAW_VAR_PTR()
   
   A variable-length array of fixed-size elements.
   The structure of the individual elements isn't declared further.
   There is no functional difference between these two types.
   
   There can be at most one variable-length array field per message.
   If there is one,
   it must be the last field in the message
   and it must be directly preceded by a :c:macro:`NET_MSG_FIELD_VAR_COUNT` field.

A few higher-level aliases for some field types are defined in :file:`Plasma/NucleusLib/pnNetProtocol/Private/pnNpCommon.h`.
They are not always used consistently ---
e.g. some ``transId`` fields are declared as :c:macro:`NET_MSG_FIELD_DWORD` instead of :cpp:var:`kNetMsgFieldTransId`.

.. cpp:var::
   const NetMsgField kNetMsgFieldAccountName = NET_MSG_FIELD_STRING(64)
   const NetMsgField kNetMsgFieldPlayerName = NET_MSG_FIELD_STRING(40)
   const NetMsgField kNetMsgFieldShaDigest = NET_MSG_FIELD_RAW_DATA(20)
   const NetMsgField kNetMsgFieldUuid = NET_MSG_FIELD_DATA(16)
   const NetMsgField kNetMsgFieldTransId = NET_MSG_FIELD_DWORD()
   const NetMsgField kNetMsgFieldTimeMs = NET_MSG_FIELD_DWORD()
   const NetMsgField kNetMsgFieldENetError = NET_MSG_FIELD_DWORD()
   const NetMsgField kNetMsgFieldEAgeId = NET_MSG_FIELD_DWORD()
   const NetMsgField kNetMsgFieldNetNode = NET_MSG_FIELD_DWORD()
   const NetMsgField kNetMsgFieldBuildId = NET_MSG_FIELD_DWORD()

.. index:: ping
   :name: ping

Ping messages
-------------

All server types implement a pair of ping messages.
When the client sends a ping request,
the server replies as soon as possible with a ping response.
(The server cannot initiate pings,
only reply to requests from the client.)

For all types except the game server,
the client regularly sends ping requests to the server
to tell it that the connection is still alive.
MOSS automatically disconnects clients that haven't sent pings for a while.
DIRTSAND also times out inactive clients similarly,
but it understands any client message as a keepalive
and doesn't require ping messages specifically.
(TODO: What does Cyan's server software do?)

All ping request/reply messages use message type number 0.
The exact format of the messages differs between server types,
but the ping request and reply messages for each server type are always structured identically.

All variants of the ping message contain a ping time field,
which the client sets to a timestamp indicating when the ping was sent.
This timestamp is not absolute,
has no well-defined format,
and cannot be interpreted by the server ---
it's expected to be sent unmodified back to the client.
(OpenUru clients set the ping time field based on `GetTickCount <https://docs.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-gettickcount>`__,
whereas H'uru clients use a custom relative clock that is reset for every run of the client.)

The gatekeeper, auth, and CSR ping messages contain two additional fields:
a transaction ID,
and a payload of up to 64 KiB.
Like the ping time,
they are set by the client
and sent back unmodified without being interpreted by the server.
In practice,
clients always send transaction ID 0 and an empty payload.

Transactions
------------

TODO!

Error codes
-----------

Many reply messages report success or failure using a common set of error codes.
They are often displayed to the user ---
usually as their associated text description,
but sometimes also with their numeric code,
which is why e. g. "Net 6" is well-known in the player community.

.. cpp:enum:: ENetError : dword
   
   .. cpp:enumerator:: kNetPending = -1
      
      "Pending"
   
   .. cpp:enumerator:: kNetSuccess = 0
      
      "Success"
   
   .. cpp:enumerator:: kNetErrInternalError = 1
      
      "Internal Error"
   
   .. cpp:enumerator:: kNetErrTimeout = 2
      
      "No Response From Server"
   
   .. cpp:enumerator:: kNetErrBadServerData = 3
      
      "Invalid Server Data"
   
   .. cpp:enumerator:: kNetErrAgeNotFound = 4
      
      "Age Not Found"
   
   .. cpp:enumerator:: kNetErrConnectFailed = 5
      
      "Network Connection Failed"
   
   .. cpp:enumerator:: kNetErrDisconnected = 6
      
      "Disconnected From Server"
   
   .. cpp:enumerator:: kNetErrFileNotFound = 7
      
      "File Not Found"
   
   .. cpp:enumerator:: kNetErrOldBuildId = 8
      
      "Old Build"
   
   .. cpp:enumerator:: kNetErrRemoteShutdown = 9
      
      "Remote Shutdown"
   
   .. cpp:enumerator:: kNetErrTimeoutOdbc = 10
      
      "Database Timeout"
   
   .. cpp:enumerator:: kNetErrAccountAlreadyExists = 11
      
      "Account Already Exists"
   
   .. cpp:enumerator:: kNetErrPlayerAlreadyExists = 12
      
      "Player Already Exists"
   
   .. cpp:enumerator:: kNetErrAccountNotFound = 13
      
      "Account Not Found"
   
   .. cpp:enumerator:: kNetErrPlayerNotFound = 14
      
      "Player Not Found"
   
   .. cpp:enumerator:: kNetErrInvalidParameter = 15
      
      "Invalid Parameter"
   
   .. cpp:enumerator:: kNetErrNameLookupFailed = 16
      
      "Name Lookup Failed"
   
   .. cpp:enumerator:: kNetErrLoggedInElsewhere = 17
      
      "Logged In Elsewhere"
   
   .. cpp:enumerator:: kNetErrVaultNodeNotFound = 18
      
      "Vault Node Not Found"
   
   .. cpp:enumerator:: kNetErrMaxPlayersOnAcct = 19
      
      "Max Players On Account"
   
   .. cpp:enumerator:: kNetErrAuthenticationFailed = 20
      
      "Authentication Failed"
   
   .. cpp:enumerator:: kNetErrStateObjectNotFound = 21
      
      "State Object Not Found"
   
   .. cpp:enumerator:: kNetErrLoginDenied = 22
      
      "Login Denied"
   
   .. cpp:enumerator:: kNetErrCircularReference = 23
      
      "Circular Reference"
   
   .. cpp:enumerator:: kNetErrAccountNotActivated = 24
      
      "Account Not Activated"
   
   .. cpp:enumerator:: kNetErrKeyAlreadyUsed = 25
      
      "Key Already Used"
   
   .. cpp:enumerator:: kNetErrKeyNotFound = 26
      
      "Key Not Found"
   
   .. cpp:enumerator:: kNetErrActivationCodeNotFound = 27
      
      "Activation Code Not Found"
   
   .. cpp:enumerator:: kNetErrPlayerNameInvalid = 28
      
      "Player Name Invalid"
   
   .. cpp:enumerator:: kNetErrNotSupported = 29
      
      "Not Supported"
   
   .. cpp:enumerator:: kNetErrServiceForbidden = 30
      
      "Service Forbidden"
   
   .. cpp:enumerator:: kNetErrAuthTokenTooOld = 31
      
      "Auth Token Too Old"
   
   .. cpp:enumerator:: kNetErrMustUseGameTapClient = 32
      
      "Must Use GameTap Client"
   
   .. cpp:enumerator:: kNetErrTooManyFailedLogins = 33
      
      "Too Many Failed Logins"
   
   .. cpp:enumerator:: kNetErrGameTapConnectionFailed = 34
      
      "GameTap: Connection Failed"
   
   .. cpp:enumerator:: kNetErrGTTooManyAuthOptions = 35
      
      "GameTap: Too Many Auth Options"
   
   .. cpp:enumerator:: kNetErrGTMissingParameter = 36
      
      "GameTap: Missing Parameter"
   
   .. cpp:enumerator:: kNetErrGTServerError = 37
      
      "GameTap: Server Error"
   
   .. cpp:enumerator:: kNetErrAccountBanned = 38
      
      "Account has been banned"
   
   .. cpp:enumerator:: kNetErrKickedByCCR = 39
      
      "Account kicked by CCR"
   
   .. cpp:enumerator:: kNetErrScoreWrongType = 40
      
      "Wrong score type for operation"
   
   .. cpp:enumerator:: kNetErrScoreNotEnoughPoints = 41
      
      "Not enough points"
   
   .. cpp:enumerator:: kNetErrScoreAlreadyExists = 42
      
      "Non-fixed score already exists"
   
   .. cpp:enumerator:: kNetErrScoreNoDataFound = 43
      
      "No score data found"
   
   .. cpp:enumerator:: kNetErrInviteNoMatchingPlayer = 44
      
      "Invite: Couldn't find player"
   
   .. cpp:enumerator:: kNetErrInviteTooManyHoods = 45
      
      "Invite: Too many hoods"
   
   .. cpp:enumerator:: kNetErrNeedToPay = 46
      
      "Payments not up to date"
   
   .. cpp:enumerator:: kNetErrServerBusy = 47
      
      "Server Busy"
   
   .. cpp:enumerator:: kNetErrVaultNodeAccessViolation = 48
      
      "Vault Node Access Violation"
