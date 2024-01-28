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
it stops the connection process,
but doesn't actually display the error in any way.
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
DIRTSAND sends a new message type (:ref:`Auth2Cli_ServerCaps <auth2cli_server_caps>`) to every client as soon as it connects to the auth server.
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

The client regularly sends ping requests to the server
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

.. _common_data_types:

Common data types
-----------------

These data types/structures are used in multiple different parts of the protocol.

.. index:: SafeString
  single: safe string
  :name: safe_string

.. object:: SafeString
  
  * **Count:** 2-byte unsigned int.
    Number of 8-bit characters in the string.
    The high 4 bits of this field are masked out when reading and should always be set when writing.
    As a result,
    a single SafeString can contain at most 4095 characters.
  * **Ignored:** 2-byte unsigned int.
    Only present if the count field has none of its high 4 bits set.
    The open-sourced client code calls this a "backward compat hack" that should have been removed in July 2003.
  * **String:** Variable-length string of 8-bit characters.
    If the first character has its high bit set,
    then the string is obfuscated by bitwise negating every character,
    otherwise the string is stored literally.
    When writing,
    the open-sourced client code always uses this obfuscation.
    None of the characters should be 0.

.. index:: SafeWString
  single: safe string; wide
  :name: safe_w_string

.. object:: SafeWString
  
  * **Count:** 2-byte unsigned int.
    Number of UTF-16 code units in the string.
    The high 4 bits of this field are masked out when reading and should always be set when writing.
    As a result,
    a single SafeWString can contain at most 4095 UTF-16 code units.
  * **String:** Variable-length string of UTF-16 code units.
    The string is obfuscated by bitwise negating every code unit.
    (Unlike with non-wide SafeStrings,
    there is no support for un-obfuscated SafeWStrings.)
    None of the characters should be 0.
  * **Terminator:** 2-byte unsigned int.
    Should always be 0.
    This string terminator is stored in the data,
    but not counted in the count field.

.. cpp:class:: hsBitVector
  
  * **Count:** 4-byte unsigned int.
    Element count for the following array.
  * **Bit vector:** Variable-length array of 4-byte unsigned ints.
    The contents of the bit vector,
    grouped into 4-byte units,
    with the first element containing the least significant bits
    and the last one the most significant bits.

.. cpp:class:: plUnifiedTime
  
  * **Seconds:** 4-byte unsigned int.
    Unix timestamp (seconds since 1970).
  * **Microseconds:** 4-byte unsigned int.
    Fractional part of the timestamp for sub-second precision.

.. index:: sequence number
  single: sequence prefix
  single: age number
  double: age; sequence prefix
  single: sequence suffix
  single: page number
  double: page; sequence suffix
  :name: sequence_number

.. object:: Sequence number
  
  A 4-byte unsigned int that identifies a :dfn:`location` in the engine
  (sometimes also called a "room"),
  which is a namespace for ``hsKeyedObject``\s.
  Used mainly as part of :cpp:class:`plLocation` and only rarely on its own.
  
  Most sequence numbers encode an age number (sequence prefix) and a page number (sequence suffix) within that age.
  A sequence number can be constructed from an *age* and *page* number as follows:
  
  * If *age* >= 0: (*age* << 16) + *page* + 0x21
  * If *age* < 0: (-*age* << 16) + *page* + 0xff000001
  
  The age and page numbers can be extracted from a sequence number *seqnum* as follows:
  
  * If *seqnum* is in the range from 0x21 through 0xfeff0020:
    
    * **Age** = (*seqnum* - 0x21) >> 16
    * **Page** = (*seqnum* - 0x21) & 0xffff
  * If *seqnum* is in the range from 0xff010001 through 0xfffffffe:
    
    * **Age** = -((*seqnum* - 0xff000001) >> 16)
    * **Page** = (*seqnum* - 0xff000001) & 0xffff
  * If *seqnum* isn't in either of these ranges,
    then it doesn't encode an age and page number.
    Such sequence numbers don't correspond to a .prp file ---
    they have a special meaning or are reserved or invalid.
  
  .. note::
    
    Age numbers are signed integers,
    but it's less clear whether page numbers are supposed to be signed or unsigned.
    This documentation considers page numbers to be unsigned,
    because it makes the calculations simpler
    and matches what the open-sourced client code does internally.
    Some other code,
    such as libHSPlasma,
    treats page numbers as signed though,
    because that gives a nicer representation for "common" page numbers
    (see the :cpp:enumerator:`~plLocation::LocFlags::kBuiltIn` flag of :cpp:class:`plLocation`).
  
  .. seealso::
    
    The `Myst Online Uru Live Again Sequence Prefix List <https://wiki.openuru.org/index.php/Myst_Online_Uru_Live_Again_Sequence_Prefix_List>`__
    on the OpenUru Wiki lists all age numbers that are currently used on Cyan's MOULa shard and the Minkata shards.
    It's also used to coordinate future age number assignments to avoid conflicts.
    
    Other MOULa shards may not follow these age number assignments exactly.
    For example,
    the Gehn and TOC-MOUL shards use different age numbers for fan ages,
    even for ones that were also later released on Cyan's shard.
  
  The full range of sequence numbers is structured as follows:
  
  * 0x0 is a special sequence number used for fixed keyed objects
    (singletons basically).
  * 0x1 through 0x20 are reserved for local use by clients and other tools.
    They should never appear in :cpp:class:`plLocation`\s sent to a server.
  * 0x21 through 0x10020 are regular sequence numbers for age 0.
  * 0x10021 through 0x20020 are regular sequence numbers for age 1.
  * (ditto for ages 2 through 32766)
  * 0x7fff0021 through 0x80000020 are regular sequence numbers for age 32767.
    This range may not work as expected with all tools,
    because some code (e. g. libHSPlasma) treats sequence numbers 0x80000000 and higher as if they had a negative age number.
  * 0x80000021 through 0x80010020 are regular sequence numbers for age 32768.
    This range may not work as expected with all tools,
    because some code (e. g. libHSPlasma) treats these sequence numbers as if they had a negative age number.
  * (ditto for ages 32769 through 65278,
    which may not work as expected with all tools)
  * 0xfeff0021 through 0xfeffffff can't be used properly.
    They theoretically correspond to age 65279,
    but there's no way to encode pages 0xffe0 through 0xffff with that age number,
    because the sequence numbers would conflict with the ranges below.
  * 0xff000000 is reserved for use by the server.
    The client also uses it (TODO only internally?) for ``plNetGroupId::kNetGroupUnknown``.
  * 0xff000000 through 0xff010000 are reserved.
    They theoretically fit the format for global sequence numbers,
    but would correspond to age 0,
    which isn't a global age and must be encoded using the regular sequence number format.
    The client uses this range for a few more ``plNetGroupId`` constants.
  * 0xff010001 through 0xff020000 are global sequence numbers for age -1.
  * 0xff020001 through 0xff030000 are global sequence numbers for age -2.
  * (ditto for ages -3 through -254)
  * 0xffff0001 through 0xfffffffe are global sequence numbers for age -255.
    There's no way to encode pages 0xfffe and 0xffff with this age number.
  * 0xffffffff is reserved as an invalid sequence number.

.. cpp:class:: plLocation
  
  * **Sequence number:** 4-byte :ref:`sequence number <sequence_number>`.
  * **Flags:** 2-byte unsigned int.
    See :cpp:enum:`LocFlags` for details.
    These flags are considered part of the location's identity.
    To prevent possible issues,
    two :cpp:class:`plLocation`\s with the same sequence number should always have the same flags.
  
  Identifies a "location" in the engine ---
  usually a page loaded from a .prp file.
  
  .. cpp:enum:: LocFlags
    
    .. cpp:enumerator:: kLocalOnly = 1 << 0
      
      According to its comment:
      "Set if nothing in the room saves state."
      Not used by the open-sourced client code
      and also seems to be never used in any .prp files.
    
    .. cpp:enumerator:: kVolatile = 1 << 1
      
      According to its comment:
      "Set is nothing in the room persists when the server exits."
      Not actually used by the open-sourced client code
      and also seems to be never used in any .prp files.
    
    .. cpp:enumerator:: kReserved = 1 << 2
      
      The sequence number refers to a page in a global age
      or one of the reserved pages.
      Should be set iff the sequence number is 0xff000000 or higher.
      (For sequence numbers that encode an age and page number,
      this is the case iff the age nuber is negative.)
    
    .. cpp:enumerator:: kBuiltIn = 1 << 3
      
      The sequence number refers to one of the "common" pages:
      Textures (0xffff/-1) or BuiltIn (0xfffe/-2).
    
    .. cpp:enumerator:: kItinerant = 1 << 4
      
      The page is expected to be used outside of its age.
      Not used by the open-sourced client code,
      except that unlike all other flags,
      it's ignored when comparing :cpp:class:`plLocation`\s for equality.
      Only rarely used in the .prp files,
      e. g. for the Eder Kemo fireflies page
      (Garden_District_ItinerantBugCloud.prp --- age 1, page 3).

.. cpp:class:: plLoadMask
  
  * **Quality and capability:** 1-byte unsigned int.
    Decoded as follows
    (where *qc* is the value of this field)
    into separate quality and capability fields,
    each of which is a 1-byte unsigned int after decoding:
    
    * **Quality** = (*qc* >> 4 & 0xf) | 0xf0
    * **Capability** = (*qc* >> 0 & 0xf) | 0xf0
  
  .. cpp:var:: static const plLoadMask kAlways
    
    Has both quality and capability set to 0xff.

.. index:: UOID
  single: key
  single: keyed object
  single: hsKeyedObject
  single: clone

.. cpp:class:: plUoid
  
  * **Flags:** 1-byte unsigned int.
    See :cpp:enum:`ContentsFlags` for details.
  * **Location:** 6-byte :cpp:class:`plLocation`.
    This usually identifies the .prp file where the object is stored on disk.
  * **Load mask:** 1-byte :cpp:class:`plLoadMask`.
    Only present if the :cpp:enumerator:`~ContentsFlags::kHasLoadMask` flag is set,
    otherwise defaults to :cpp:var:`plLoadMask::kAlways`.
    If present,
    it should never be :cpp:var:`plLoadMask::kAlways`.
    Only rarely present.
    Used by the client to decide which objects to load depending on the graphics quality settings.
    Not relevant for the identity of the referenced object.
  * **Class index:** 2-byte unsigned int.
    The referenced object's class.
    Should be less than 0x0200
    (the end of the class index space for keyed objects).
  * **Object ID:** 4-byte unsigned int.
    Numeric identifier for the referenced object.
    The object ID is unique only in combination with the location and class index.
    Object ID 0 is a special value used for UOIDs that must be looked up by their name instead.
    If the object ID is not 0,
    then looking up the object by its ID *should* have the same effect as looking it up by name,
    but this isn't always the case.
    Object IDs aren't stable ---
    for example,
    libHSPlasma will often reassign object IDs when modifying a .prp file.
  * **Object name:** :ref:`SafeString <safe_string>`.
    String identifier for the referenced object.
    The object name is unique only in combination with the location and class index.
    Object names are less likely to change than object IDs,
    but slower to look up.
  * **Clone ID:** 2-byte unsigned int.
    Only present if the :cpp:enumerator:`~ContentsFlags::kHasCloneIDs` flag is set,
    otherwise defaults to 0.
    If present,
    it should never be 0.
    If not 0,
    the cloner KI number should also not be 0,
    and this UOID refers to a clone of a template object.
    If 0 (not present),
    the cloner KI number should also be 0 (not present),
    and this UOID refers to a non-clone object.
  * **Ignored:** 2-byte unsigned int.
    Only present if the :cpp:enumerator:`~ContentsFlags::kHasCloneIDs` flag is set.
    Should always be 0.
    Seems to exist only for backwards compatibility.
  * **Cloner KI number:** 4-byte unsigned int.
    Only present if the :cpp:enumerator:`~ContentsFlags::kHasCloneIDs` flag is set,
    otherwise defaults to 0.
    If present,
    should never be 0.
    KI number of the avatar that created this clone of the object.
    Prevents clone ID conflicts between multiple clients.
  
  Every ``hsKeyedObject`` is uniquely identified by a UOID.
  The structure of a UOID is a bit complex.
  
  * The location and class index act as a namespace.
    Two objects with different locations or different class indices are never identical.
    Different locations can (and do) contain objects with the same class, ID, and name.
    Similarly,
    objects of different classes in the same location can (and do) have the same ID and name.
  * Within this namespace,
    an object can be identified using either its object ID (if it has one) or its name.
    Both ways *should* work the same,
    but because object IDs are less stable than names,
    looking up by ID can fail if a .prp file is changed without updating all UOIDs that reference it.
    In those cases,
    the game has to fall back to looking up by name.
  * If a UOID has clone fields (clone ID and cloner KI number),
    it refers to a :dfn:`clone` of another (non-clone) object.
    Both clone fields are used together to identify the clone.
    Every clone is distinct from its template
    (which has the same UOID,
    but without the clone fields)
    and from any other clone of the same object with different clone fields.
  * The load mask isn't really part of the object's identity.
    To avoid problems,
    there should never be two objects whose UOID differs only in the load mask field.
  
  .. cpp:enum:: ContentsFlags
    
    .. cpp:enumerator:: kHasCloneIDs = 1 << 0
      
      Whether the clone fields (clone ID, ignored, cloner KI number) are present.
    
    .. cpp:enumerator:: kHasLoadMask = 1 << 1
      
      Whether the load mask field is present.

.. cpp:class:: plKey
  
  .. note::
    
    :cpp:class:`plKey` itself can't actually be read or written directly.
    The structure described here is used by ``hsResMgr::ReadKey``/``hsResMgr::WriteKey``.
  
  * **Non-null:** 1-byte boolean.
    False if this key is actually ``nullptr``,
    true otherwise.
  * **UOID:** :cpp:class:`plUoid`.
    The UOID of the object identified by this key.
    Only present if the non-null field is true.
  
  In the data formats,
  :cpp:class:`plKey` is just a nullable variant of :cpp:class:`plUoid` ---
  although :cpp:class:`plKey` is also used in many places where it should never be ``nullptr``.
  
  In the open-sourced client code,
  :cpp:class:`plKey` acts as a smart pointer/handle to the object identified by its :cpp:class:`plUoid`.
  It holds a pointer to the actual ``hsKeyedObject`` along with a reference count,
  manages loading the object from its .prp file
  (and unloading it once it's no longer used),
  links clone keys with their template ("owner") keys,
  and a few more things.

.. index:: creatable
  double: creatable; index
  double: class; index
  :name: class_index

.. cpp:class:: plCreatable
  
  The abstract base class of many Plasma data types that can be read/written as a byte stream.
  Every :cpp:class:`plCreatable` subclass is identified by a unique 16-bit :dfn:`class index`,
  which Plasma uses to dynamically create objects of variable classes at runtime ---
  hence the name "creatable".
  
  .. note::
    
    For a list of :cpp:class:`plCreatable` subclasses and class indices
    that are relevant to the network protocol,
    see the :ref:`game server <game_server>` documentation, 
    particularly :cpp:class:`plNetMessage` and :cpp:class:`plMessage`.
    I'm not going to list every class index in existence,
    because there are *a lot* of them.
    If you need a complete list,
    have a look at:
    
    * plCreatableIndex.h in the `H'uru <https://github.com/H-uru/Plasma/blob/master/Sources/Plasma/NucleusLib/inc/plCreatableIndex.h>`__ and `OpenUru <https://foundry.openuru.org/gitblit/blob/?r=CWE-ou-minkata.git&f=Sources/Plasma/NucleusLib/inc/plCreatableIndex.h&h=master>`__ client source code
    * `typecodes.h <https://foundry.openuru.org/gitblit/blob/?r=MOSS-minkata.git&f=typecodes.h&h=master>`__ in the MOSS source code
    * `TypeMap.txt <https://github.com/H-uru/libhsplasma/blob/master/Misc/TypeMap.txt>`__ in the libHSPlasma source code
      (also lists class indices for other Plasma games outside the MOUL family)
  
  :cpp:class:`plCreatable` itself doesn't specify the actual data format.
  Although it defines generic ``Read`` and ``Write`` methods,
  every subclass implements its own data format in these methods.
  Notably,
  ``Write`` usually doesn't include the object's class index,
  so the serialized data can only be parsed if the class is already known from context.
  
  To allow reading/writing objects whose class can vary,
  ``hsResMgr``/``plResManager`` defines two helper methods ``ReadCreatable`` and ``WriteCreatable``,
  which add the following short header before the main ``Read``/``Write`` data:
  
  * **Class index:** 2-byte unsigned int.
    Class index of the :cpp:class:`plCreatable` subclass that wrote the following data.
    May also be the special value 0x8000 (32768),
    which indicates a ``nullptr`` value.
  
  .. note::
    
    :cpp:class:`plCreatable` also defines another pair of serialization methods,
    ``ReadVersion`` and ``WriteVersion``,
    which are designed for long-term compatibility ---
    ``ReadVersion`` should be able to parse data produced by any current or past implementation of ``WriteVersion``.
    Like ``Read`` and ``Write``,
    their data format is completely class-specific,
    but there are ``plResManager`` methods ``ReadCreatableVersion`` and ``WriteCreatableVersion``
    that add a class index header.
    
    The ``ReadVersion``/``WriteVersion`` data format is only used by ``plNetClientStreamRecorder`` and is never sent over the network or used in any data files,
    so I won't cover it in detail in the rest of this documentation.
    In short:
    ``WriteVersion`` usually uses the same format as ``Write``,
    but with a :cpp:class:`hsBitVector` added at the beginning
    that indicates which fields are present in the data.
    This information is used by ``ReadVersion`` to skip reading fields that didn't exist yet when the data was written.
