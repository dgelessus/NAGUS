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

.. _connect_packet:

Connect packet
--------------

.. index:: connect packet

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

.. _connection_types:

Connection types
^^^^^^^^^^^^^^^^

The following connection types are used by the open-source MOULa clients,
one for each server type that the client communicates with:

* CliToAuth = 10
* CliToGame = 11
* CliToFile = 16
* CliToGateKeeper = 22

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
* CliToCsr = 20 (only used in CsrSrv communication code, which is unused)
* SimpleNet = 21 (only used in SimpleNet protocol code, which is unused)
* AdminInterface = 97 (ASCII code for the letter ``a``)
