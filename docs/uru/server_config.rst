Configuring servers in the client
=================================

Because MOUL was designed to be played on a single central server,
the client doesn't allow players to easily change what servers it connects to.
This continues to be the case even now that other MOULa shards exist ---
each shard requires a different client build and data files
(with very few exceptions),
so it's not feasible to use the same client installation for multiple different shards.
Instead,
every shard distributes its own version of the client
that is preconfigured with the appropriate server addresses and encryption keys.
The way this information is configured differs between OpenUru and H'uru clients.

.. seealso::
  
  :ref:`generating_dh_keys` for how to generate connection keys when setting up your own shard.

.. _compiled_server_config:

Compiled-in server information (OpenUru)
----------------------------------------

The original open-sourced client code and the current OpenUru code
has all server addresses and keys set at compile time.
Some server addresses can be :ref:`overridden at runtime <server_address_cli_options>`,
but to properly set up a client to connect to a different shard,
the addresses and keys must be changed in the source code.
(You can also patch the compiled executables,
but with the client being open source,
this is generally no longer worth the effort.)

The server addresses are all over the place in the source code.
Below is a list of the exact files, macros, variables, and functions containing server info.

.. note::
  
  Some of these have different values depending on the :ref:`build type <build_type>`.
  Build type Live corresponds to Cyan's public MOULa servers.
  Other build types use old Ubisoft/Cyan addresses that are no longer valid.
  When configuring your own server addresses,
  you can safely remove all the build type conditionals and set a single fixed value instead.

.. c:macro:: STATUS_PATH
  
  (in files :file:`Plasma/Apps/plClient/winmain.cpp`, :file:`Plasma/Apps/plUruLauncher/Main.cpp`)
  
  The host name or IP address of the status server,
  as a string literal.
  The macro name is misleading ---
  this string cannot contain a path!
  The location of the status page on the server is configured separately in :cpp:func:`BuildTypeServerStatusPath`.
  
  The status server port number is hardcoded to 80.
  To change it,
  locate the ``WinHttpConnect`` calls in the ``StatusCallback`` functions
  (in the same source files as :c:macro:`STATUS_PATH`)
  and replace ``INTERNET_DEFAULT_HTTP_PORT`` with the desired port number.

.. cpp:function:: const wchar *BuildTypeServerStatusPath()
  
  (in file :file:`Plasma/NucleusLib/pnProduct/Private/pnPrBuildType.cpp`)
  
  Returns the path of the status page on the status server.
  Can return ``nil``/``NULL``/``0``,
  in which case the status server is never contacted
  and the default status message "Welcome to URU" is displayed forever.

.. cpp:var::
  static const wchar *s_gateKeeperAddrs[]
  static const wchar *s_authAddrs[]
  static const wchar *s_csrAddrs[]
  
  (in file :file:`Plasma/NucleusLib/pnNetBase/Private/pnNbSrvs.cpp`)
  
  The address of the gatekeeper, auth, and CSR server,
  respectively.
  May include an explicit port number,
  otherwise the default port ``kNetDefaultClientPort`` (14617) is used.
  
  Although these are arrays that could contain multiple server addresses,
  this is not fully supported in the client code,
  and all addresses after the first one are ignored.

.. cpp:var:: static const wchar *s_fileAddrs[]
  
  (in file :file:`Plasma/NucleusLib/pnNetBase/Private/pnNbSrvs.cpp`)
  
  Not actually used.
  The file server address is obtained from the gatekeeper server instead.

Connection encryption keys are defined in the files :file:`Plasma/NucleusLib/pnNetBase/pnNb{TYPE}Key.hpp`,
where :file:`{TYPE}` is one of ``Auth``, ``Csr``, ``Game``, or ``GateKeeper``.
(There is no :file:`pnNbFileKey.hpp`,
because file server connections are never encrypted.)
Each of these files defines three variables
containing the Diffie-Hellman values for the respective server type:

.. cpp:var:: static const unsigned kDhGValue
  
  The value of *g*.
  Usually doesn't need to be changed,
  because almost all MOULa shards use the same *g* values for each server type.

.. cpp:var::
  static const byte kDhNData[64]
  static const byte kDhXData[64]
  
  The values of *n* and *x*,
  stored as a packed integer in *little-endian* byte order
  (least significant byte first).
  This is different from H'uru and OpenSSL,
  which use *big-endian* byte order instead.

.. _server_address_cli_options:

Overriding addresses on the command line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Most of the compiled-in server addresses can be selectively overridden using the following command-line options,
which are supported by the launcher and the main client,
in both :ref:`internal and external builds <internal_external_client>`.

.. option::
  /GateKeeperSrv=GATEKEEPER_ADDRESS
  /FileSrv=FILE_ADDRESS
  /AuthSrv=AUTH_ADDRESS
  
  Use the given address for the gatekeeper, file, or auth server,
  respectively,
  instead of the compiled-in address.
  
  Each address (including port number suffix, if any)
  may be at most 63 characters long,
  because the client stores them in fixed-size buffers.
  If for some reason your host name is longer than that,
  you need to write it as an IP address instead.

Because there is no way to override the connection encryption keys along with the server addresses,
these options cannot be used to connect to arbitrary servers.
They are mainly useful for playing on alternative/testing servers operated by the same shard admin,
e. g. Cyan's MOULa and MOULa Staging,
or OpenUru's Minkata and Minkata-alpha.

.. index:: server.ini
  :name: server_ini

server.ini (H'uru)
------------------

H'uru clients load all server information at runtime from a configuration file.
This allows changing all server information without having to recompile the client.
By default,
the file is called :file:`server.ini` and located next to the client executable.
A different configuration file can be specified with a command line option
(supported by both the launcher and the main client):

.. option:: /ServerIni=INI_FILE
  
  Read server configuration from the given file path instead of the default :file:`server.ini`.

Without a server.ini,
a H'uru client will not run at all ---
there is no compiled-in default server information.

For details about the syntax and supported options in :file:`server.ini` files,
see `the corresponding H'uru documentation <https://github.com/H-uru/Plasma/blob/master/Docs/server.ini.md>`__.

.. _server_bypass:

Bypassing certain servers
-------------------------

With both the OpenUru and H'uru clients,
some server connections can be bypassed/skipped for development purposes.

When a file server address is set explicitly,
using the :option:`/FileSrv` option (OpenUru)
or the ``Server.File.Host`` server.ini command (H'uru),
then the client never asks the gatekeeper server for the file server address.
This does *not* work for the launcher though ---
it ignores any file server override and always goes through the gatekeeper server.
This makes overriding the file server only useful for internal clients,
which can be run directly without the launcher.

The file server connection can also be bypassed using one or more of the following options
(depending on the kind of client):

.. option:: /LocalData
  
  Skip all update checks
  and force using the local copies of all data and script files.
  
  .. warning::
    
    When using this option,
    make sure that your local data files are compatible with what the server expects!
    Especially SDL files **must** match the server very closely,
    or bad things will happen.
    
    To be safe,
    you should first let the launcher update all data files normally,
    then install current versions of the scripts (Python, SDL).
    Then you can use :option:`/LocalData` safely (until the shard updates anything)
    and make local modifications (carefully!).
  
  When enabling this option for OpenUru clients or older H'uru clients (before August 2023),
  the gatekeeper and file servers are never contacted
  and no "secure files" are downloaded from the auth server.
  Any files that are normally served as "secure files" (usually Python and SDL) must be manually placed into the game folder.
  
  With recent H'uru clients (since August 2023),
  this option does *not* affect SDL files ---
  they are still downloaded from the file or auth server by default
  to ensure that they always match what the server expects.
  To force the use of local SDL files,
  you have to enable :option:`/LocalSDL` separately.
  To prevent the client from downloading any files from the server,
  you have to enable both :option:`/LocalData` *and* :option:`/LocalSDL`.
  
  This option is only supported by :ref:`internal clients <internal_external_client>`
  (both OpenUru and H'uru).
  To use this option,
  you should launch :program:`plClient` directly ---
  the launcher ignores it and will update the data files anyway.

H'uru-only options
^^^^^^^^^^^^^^^^^^

The following options are only supported by H'uru :ref:`internal clients <internal_external_client>`.
With OpenUru clients,
you have to use the full :option:`/LocalData` option instead.

.. option:: /LocalPython
  
  Skip downloading Python scripts from the auth server and use local scripts instead,
  but update all other files as usual.
  This is a subset of :option:`/LocalData`,
  useful when you need to modify just the Python scripts and nothing else.

.. option:: /LocalSDL
  
  Skip downloading SDL files from the auth server and use local copies instead,
  but update all other files as usual.
  Unlike :option:`/LocalPython`,
  this option is *not* automatically enabled by :option:`/LocalData`.
  
  .. warning::
    
    Do not use this option when connecting to a public shard.
    You should only use it with certain testing shards
    that aren't set up to serve SDL files
    (e. g. the Destiny shard or other shards that use a minimal DIRTSAND configuration).
    
    When using this option,
    make sure that your local SDL files are compatible with what the server expects!
    SDL files **must** match the server very closely,
    or bad things will happen.
    To be safe,
    you should first let the launcher update the SDL files,
    if the server supports this.
  
  If both :option:`/LocalSDL` and :option:`/LocalData` are enabled,
  the gatekeeper and file servers are never contacted
  and no "secure files" are downloaded from the auth server.

.. option:: /SkipPreload
  
  Skip downloading "secure files" from the auth server and use local copies instead,
  but update all other data files from the file server as usual.
  This is a subset of :option:`/LocalData`,
  useful when you need to modify just the scripts and not any other data files.
  
  This option is obsolete and only supported by older H'uru :ref:`internal clients <internal_external_client>` (from 2013 to 2023).
  With newer H'uru clients (since August 2023),
  use :option:`/LocalPython` and/or :option:`/LocalSDL` instead.
