Encryption keys
===============

This is a short overview of all the different kinds of encryption and keys used by MOUL clients and servers.
I'm explaining this here,
because some of these are used during network communication
and some of the keys vary between shards.

.. index::
  single: encryption; data file
  single: encryption; whatdoyousee
  single: encryption; WDYS
  single: encryption; XTEA
  single: whatdoyousee
  single: WDYS
  single: XTEA
  :name: whatdoyousee

Data file encryption: whatdoyousee (XTEA)
-----------------------------------------

Most plain-text data files (.age, .csv, .fni, sometimes server.ini)
and config files (.ini and login.dat in user data folder)
are encrypted using `XTEA <https://en.wikipedia.org/wiki/XTEA>`__.
The encrypted files use this simple format:

* **Magic signature:** 12 bytes.
  Set to ASCII ``whatdoyousee``.
  The client also accepts ``BriceIsSmart`` instead,
  but in practice nothing uses this alternative signature.
* **Original data length:** 4-byte unsigned integer (little-endian).
* **Encrypted data:** Remainder of file.

Almost all whatdoyousee-encrypted files use the default key ``{0x6c0a5452, 0x3827d0f, 0x3a170b92, 0x16db7fc2}``.
The only exception is the login.dat,
which uses a different key generated from the volume serial numbers of the computer's non-removable disks
(to ensure that the login.dat cannot be easily copied to a different computer).

OpenUru-based :ref:`external clients <internal_external_client>` *require* all of the file types listed above to be encrypted
and will not read them if unencrypted.
OpenUru-based :ref:`internal clients <internal_external_client>` and all H'uru clients accept both encrypted and unencrypted files.

.. index::
  single: encryption; secure file
  single: encryption; notthedroids
  single: encryption; droid
  single: encryption; NTD
  single: encryption; XXTEA
  single: notthedroids
  single: droid
  single: NTD
  single: XXTEA
  :name: notthedroids

"Secure" file encryption: notthedroids (XXTEA)
----------------------------------------------

Some script files (.sdl, Python.pak)
are encrypted using `XXTEA <https://en.wikipedia.org/wiki/XXTEA>`__ instead.
The format is identical to the :ref:`whatdoyousee <whatdoyousee>` files,
except that the magic signature is ``notthedroids`` and the encryption algorithm is different.

The default notthedroids encryption key is the same as for whatdoyousee,
but most of the time this default key is not used.
Most notthedroids-encrypted files instead use a different key sent by the auth server.
For Cyan's MOULa shard,
this key is ``{0x7096e12d, 0x44e089c0, 0xc26984d2, 0x537aa6f4}``.
DIRTSAND's default notthedroids key is ``{0x31415926, 0x53589793, 0x23846264, 0x33832795}``.

As with whatdoyousee-encrypted files,
OpenUru-based external clients *require* the file types listed above to be encrypted,
whereas OpenUru internal clients and all H'uru clients also accept them unencrypted.

.. index::
  single: encryption; connection
  single: encryption; RC4
  single: RC4
  single: Diffie-Hellman
  single: server keys
  :name: dh_keys

Connection encryption (Diffie-Hellman, RC4)
-------------------------------------------

.. warning::
  
  I don't know much about cryptography.
  Everything in this section should be taken with a grain of salt
  (even more than the rest of this documentation).
  
  .. note::
    
    Har har, `salt <https://en.wikipedia.org/wiki/Salt_(cryptography)>`__, geddit?

The MOUL network protocol uses RC4 encryption for most connections.
Every encrypted connection uses a different RC4 key,
generated by the client and server using Diffie-Hellman key exchange.

The following values are used in the key exchange:

* A small integer base/generator *g*
* A 512-bit public modulus *n* (known as *p* in some literature)
* A 512-bit server private key *a* (DIRTSAND calls it *k*)
* A 512-bit server public key *x* (known as capital *A* in some literature)
* A 512-bit client private key *b*
* A 512-bit client public key *y* (known as capital *B* in some literature)

Each :ref:`server type <server_types>` uses a separate set of Diffie-Hellman values.
The *g* value for each server type is the same across almost all MOULa-based shards
(although e. g. Minkata changes them).
The *n*, *a*, and *x* values are unique for every shard.
When setting up a shard,
for each server type,
the shard admin generates a random prime *n* and random *a*,
calculates *x = g*:sup:`a` *% n*,
and publishes *n* and *x*
(usually as part of a pre-packaged client).
The *b* and *y* values are newly generated by the client for every connection ---
see :ref:`connection_encryption` for details.

The following *g*, *n*, and *x* values are used by Cyan's MOULa shard.
As mentioned above,
other MOULa-based shards use the same *g* values (usually),
but different *n* and *x* values.
The private keys *a* are not publicly known,
for obvious reasons.

.. note::
  
  Each *n* and *x* value below is a single hex integer
  (i. e. in big-endian order).
  Ignore the spaces/line breaks, they are only for layout.
  The *g* values are given in decimal.

.. seealso::
  
  :doc:`server_config` for details on the different key formats used by OpenUru and H'uru clients.

.. csv-table:: Encryption keys (Cyan MOULa)
  :name: encryption_keys_cyan
  :header: Server,*g*,*n*,*x*
  :widths: auto
  
  GateKeeper,4,``b523446ba38021d7 c36f2f29fa55bc60 ec6a0d92f5554c15 1cf1dbc74d4cb8dc 50d549fcb6559816 2e66ab340f219aa3 237ad7d1814b25ab 50507af8e635fa8d``,``1af3b71960d06969 caf99489c5328268 47ce8d6c09c4cb7c e47f6fbea0be9c0f 389b0f61a6a95ecd fcb3f3a93935fa39 050f9d839862bc07 2e2b70900bff88b3``
  Auth,41,``8f56a6a397be203f c5873812126dab6b 349b66385711610a 1a54c266cb5b314d e4b7780cc8035e47 b98ec3431b45fe72 eee5754388617c29 918f71eb4219172d``,``1be9d855f3036ffa bccd3d6ab3bbb2da 3f758cb99eb143ea ef64d52e5501ece5 eb5b23fbee9a2720 f9590df48fbbc105 55b9dd2561ce3653 ad23c008c61dcf21``
  Game,73,``904b28d049d224d9 20c90b55c943bc20 6033cbd71582d119 1b70f2fecd2eadd6 20bbea2650fd3fde c42284de44389aaa 5d09766a123b7227 c7a6d74369f7a438``,``3ddb3d8fb358584f 68e9657aa3cf0484 6733cf147f369362 9879fdc8bab65fdc 6801d8841f5c7647 5c3f3b99f05afdc2 3e65443e09bd21a9 4872bd02bd93b2f9``
  Csr,97,``6dd6cdd805e7c6f0 99420062b173477c 03fa6c86f170df97 44f7919828e50b97 69b3c950ee22daf8 75aebc4b8f3773d7 deeceb888c7a8e76 0d7427ed1703f8bd``,``34c3782cd45ee434 2c5759bb6d593658 061276a4492d2a37 db5f73e911e974f3 215168066a87275e 96b70e13813a9886 e6c24228be3166a8 a663923662831d03``

Connections to the file server are never encrypted (see :ref:`connection_encryption`),
so it has no corresponding Diffie-Hellman values.
The CSR server is practically unused and not implemented by open-source server software,
so fan shards don't generate any Diffie-Hellman values for it.

.. _generating_dh_keys:

Generating connection encryption keys
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When setting up your own shard,
you need to generate your own connection keys.
Both OpenUru's MOSS and H'uru's DIRTSAND have included tools for this purpose.

MOSS comes with a standalone tool :program:`make_cyan_dh`
that generates a single server key pair.
The tool needs to be run once for each server type,
using the ``-g``/``--generator`` option to specify the correct *g* value for each type. 
The server key is written in ASN.1 DER format,
as expected by MOSS itself.
The corresponding values for the client may be output as either C++ source code
(for :ref:`compiling into an OpenUru client <compiled_server_config>`)
or packed little-endian binary data
(for patching into an existing client executable).
Additionally,
there is an option ``-t``/``-text`` to display all values (for both client and server) as big-endian hex.

DIRTSAND has key generation built-in,
invoked using :program:`dirtsand --generate-keys` or the server console command ``keygen new``.
The console command ``keygen show`` re-calculates and displays the client values for an existing set of server keys.
The keys for all server types (gatekeeper, auth, game) are generated at once,
automatically using the standard *g* values for each type.
There is no support for other server types (CSR) or non-standard *g* values,
except by modifying the code.
Server and client keys are output as base-64 in big-endian byte order,
in an appropriate format for the dirtsand.ini and :ref:`server.ini <server_ini>` files.

MOSS cannot output client keys in the H'uru server.ini format,
and similarly DIRTSAND cannot output C++ source code for OpenUru client builds.
If necessary,
you can manually convert between the two formats:
for each key,
convert the base-64 data from/to hex
and change the endianness by reversing all bytes.

OpenSSL's standard :program:`openssl dhparam` command *cannot* be used here,
because it only supports generator values 2 and 5,
and not the custom *g* values that MOULa uses by default.

According to comments in the open-sourced client code,
Cyan generated their Diffie-Hellman values using a tool called :program:`plDhKeyGen`,
but it is not publicly available.
