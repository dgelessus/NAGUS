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

.. c:macro:: SERVER_PATH
   
   (in files :file:`Plasma/Apps/plClient/winmain.cpp`, :file:`Plasma/Apps/plUruLauncher/Main.cpp`)
   
   The host name or IP address of the status server,
   as a string literal.
   The macro name is misleading ---
   this string cannot contain a path!
   The location of the status page on the server is configured separately in :cpp:func:`BuildTypeServerStatusPath`.
   
   The status server port number is hardcoded to 80.
   To change it,
   locate the ``WinHttpConnect`` calls in the ``StatusCallback`` functions
   (in the same source files as :c:macro:`SERVER_PATH`)
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
   Shouldn't need to be changed,
   because all MOULa shards use the same *g* values for each server.

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
An different configuration file can be specified with a command line option
(supported by both the launcher and the main client):

.. option:: /ServerIni=INI_FILE
   
   Read server configuration from the given file path instead of the default :file:`server.ini`.

Without a server.ini,
a H'uru client will not run at all ---
there is no compiled-in default server information.

The server.ini is actually a Plasma console script,
in the same basic format as .ini files in the user data folder or .fni files in the dat folder.
Unless indicated otherwise,
the argument/value of every command should be surrounded with double quotes,
to avoid parsing issues with spaces or other symbols.
The following commands are supported:

.. object:: Server.DispName "Example Shard"
   
   A human-readable name for the shard.
   Despite the command name,
   this value is currently never displayed to the user.
   It is actually used as an identifier for the shard when saving login information.
   Can be omitted,
   but this causes slightly odd naming in the registry
   (last username is stored one key higher than it should be).

.. object:: Server.Status "https://moula.example.net/status"
   
   The full URL of the status page on the status server.
   Can be omitted,
   in which case the default status message "Welcome to URU" is displayed forever.

.. object:: Server.Signup "https://moula.example.net/signup"
   
   The URL that is opened by the "Need an account?" button in the login window.
   Can be omitted,
   but this causes slightly odd behavior when the button is clicked
   (login window gets sent to background and nothing else happens).

.. object:: Server.Port 14617
   
   (integer, not quoted)
   
   The default port number for server addresses,
   used for server addresses that don't contain an explicit port number.
   If omitted,
   defaults to the standard MOUL server port 14617.

.. object::
   Server.Gate.Host "moula.example.net"
   Server.File.Host "moula.example.net"
   Server.Auth.Host "moula.example.net"
   
   The addresses of the gatekeeper, file, and auth servers,
   respectively.
   May include an explicit port number,
   otherwise the default port from ``Server.Port`` is used.
   
   The file server address is normally obtained via the gatekeeper server
   and doesn't need to be set in the server.ini.

.. object::
   Server.Gate.N "..."
   Server.Gate.X "..."
   Server.Auth.N "..."
   Server.Auth.X "..."
   Server.Game.N "..."
   Server.Game.X "..."
   
   The Diffie-Hellman *n* and *x* values for the gatekeeper, auth, and game server connections,
   respectively.
   The values are packed big-endian integers encoded as base-64.
   There are no corresponding commands for the file server,
   because file server connections are never encrypted.
   
   Any pair of ``N``/``X`` commands may be omitted to disable encryption for that server type ---
   see :ref:`disabling_connection_encryption`.
   This is only supported when connecting to a server based on DIRTSAND,
   not MOSS or Cyan's server software.

.. object::
   Server.Gate.G 4
   Server.Auth.G 41
   Server.Game.G 73
   
   (integers, not quoted)
   
   The Diffie-Hellman *g* values for the gatekeeper, auth, and game server connections,
   respectively.
   There is no corresponding command for the file server,
   because file server connections are never encrypted.
   
   If any of these commands is omitted,
   the standard *g* value for that server type is used.
   Because all MOULa shards (that I know of) use these standard values,
   there should never be any need to set these explicitly.

.. _server_bypass:

Bypassing certain servers
-------------------------

With both the OpenUru and H'uru clients,
some server connections can be bypassed/skipped for development purposes.

When a file server address is set explicitly,
using the :option:`/FileSrv` option (OpenUru)
or the ``Server.File.Host`` server.ini command (H'uru),
then the client never contacts the gatekeeper server.
This does *not* work for the launcher though ---
it ignores any file server override and always goes through the gatekeeper server.
This makes overriding the file server only useful in combination with :option:`/LocalData`:

.. option:: /LocalData
   
   Skip all update checks
   and force using the local copies of all data and script files.
   With this option enabled,
   the gatekeeper and file servers are never contacted
   and no "secure files" are downloaded from the auth server.
   Any files that are normally served as "secure files" (usually Python and SDL) must be manually placed into the game folder.
   
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
   
   This option is only supported by :ref:`internal clients <internal_external_client>`
   (both OpenUru and H'uru).
   To use this option,
   you should launch :program:`plClient` directly ---
   the launcher ignores it and will update the data files anyway.

.. option:: /SkipPreload
   
   Skip downloading "secure files" from the auth server and use local copies instead,
   but update all other data files from the file server as usual.
   This is a subset of :option:`/LocalData`,
   useful when you need to modify just the scripts and not any other data files.
   
   This option is only supported by H'uru :ref:`internal clients <internal_external_client>`.
   With OpenUru clients,
   you have to use the full :option:`/LocalData` option instead.
