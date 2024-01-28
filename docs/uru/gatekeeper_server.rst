.. index:: gatekeeper server
  single: server; gatekeeper
  single: GateKeeperSrv
  :name: gatekeeper_server

Gatekeeper server
=================

Tells the client the addresses of the other servers
(file server and auth server).

Theoretically,
the gatekeeper server can dynamically send different clients to different instances of the file and auth servers.
This can be used for load balancing and providing geographically distributed mirrors,
especially for the file server.
In practice,
all MOULa shards use only one instance of the file and auth server though,
so the gatekeeper server always sends the same addresses to all clients.

The use of the gatekeeper server is mostly optional,
because the addresses sent by the gatekeeper server can also be set statically on the client side.
It's only strictly required for the launcher,
which unconditionally asks the gatekeeper server for the file server address,
even if a static file server address is set on the client side.
See :doc:`server_config` for details.

Messages
--------

.. csv-table:: Gatekeeper server messages
  :name: gatekeeper_messages
  :header: #,Cli2GateKeeper,GateKeeper2Cli,#
  :widths: auto
  
  0,:ref:`PingRequest <cli2gatekeeper_ping_request>`,:ref:`PingReply <gatekeeper2cli_ping_reply>`,0
  1,:ref:`FileSrvIpAddressRequest <cli2gatekeeper_file_srv_ip_address_request>`,:ref:`FileSrvIpAddressReply <gatekeeper2cli_file_srv_ip_address_reply>`,1
  2,:ref:`AuthSrvIpAddressRequest <cli2gatekeeper_auth_srv_ip_address_request>`,:ref:`AuthSrvIpAddressReply <gatekeeper2cli_auth_srv_ip_address_reply>`,2

.. _cli2gatekeeper_ping_request:

Cli2GateKeeper_PingRequest
^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 0
* **Ping time:** 4-byte unsigned int.
* **Transaction ID:** 4-byte unsigned int.
* **Payload byte count:** 4-byte unsigned int.
* **Payload:** Variable-length.

See :ref:`ping` for details.

.. _gatekeeper2cli_ping_reply:

GateKeeper2Cli_PingReply
^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 0
* **Ping time:** 4-byte unsigned int.
* **Transaction ID:** 4-byte unsigned int.
* **Payload byte count:** 4-byte unsigned int.
* **Payload:** Variable-length.

See :ref:`ping` for details.

.. _cli2gatekeeper_file_srv_ip_address_request:

Cli2GateKeeper_FileSrvIpAddressRequest
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 1
* **Transaction ID:** 4-byte unsigned int.
* **Is patcher:** 1-byte boolean.
  1 if the request is coming from the launcher/patcher
  or 0 if it's from the main game client.
  Seems to be ignored by all servers in practice.

Request the address of a file server.

.. _gatekeeper2cli_file_srv_ip_address_reply:

GateKeeper2Cli_FileSrvIpAddressReply
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 1
* **Transaction ID:** 4-byte unsigned int.
* **File server address:** :c:macro:`NET_MSG_FIELD_STRING`\(24).
  Although the open-sourced client code specifically calls this an "IP address",
  the client also correctly handles domain names in this field.
  Domain names may include a port number,
  but plain IP addresses must not
  (the client will always use the default port).

Reply to a :ref:`FileSrvIpAddressRequest <cli2gatekeeper_file_srv_ip_address_request>` message.

.. _cli2gatekeeper_auth_srv_ip_address_request:

Cli2GateKeeper_AuthSrvIpAddressRequest
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 2
* **Transaction ID:** 4-byte unsigned int.

Request the address of the auth server.

.. _gatekeeper2cli_auth_srv_ip_address_reply:

GateKeeper2Cli_AuthSrvIpAddressReply
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* *Message type* = 1
* **Transaction ID:** 4-byte unsigned int.
* **Auth server address:** :c:macro:`NET_MSG_FIELD_STRING`\(24).
  Although the open-sourced client code specifically calls this an "IP address",
  the client also correctly handles domain names in this field.
  Domain names may include a port number,
  but plain IP addresses must not
  (the client will always use the default port).

Reply to an :ref:`AuthSrvIpAddressRequest <cli2gatekeeper_auth_srv_ip_address_request>` message.
