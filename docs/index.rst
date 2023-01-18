NAGUS --- not a good Uru server
===============================

This is NAGUS, an Uru Live server that is not very good.

I started writing this while trying to understand how MOULa's networking works.
`The code <https://github.com/dgelessus/NAGUS>`__ does nothing useful at this point,
but the documentation below contains some assorted information about MOULa's internals,
most of which isn't well-documented elsewhere
(though I'm hoping to change that soon-ish).

Please be aware that I actually don't know Uru's internals very well!
Most of this is written while I'm still figuring it all out myself,
so expect mistakes.
(If you find any errors,
tell me on the `issue tracker <https://github.com/dgelessus/NAGUS/issues>`__
and I'll try to fix the code and/or docs.)

.. seealso::
  
  If you're looking for a proper MOULa server implementation that you can actually play on,
  check out OpenUru's `MOSS <https://wiki.openuru.org/index.php/MOSS>`__ and H'uru's `DIRTSAND <https://guildofwriters.org/wiki/DIRTSAND>`__.
  
  A lot of Uru-related documentation can be found on the `Guild of Writers <https://www.guildofwriters.org/wiki/>`__ and `OpenUru <https://wiki.openuru.org/>`__ wikis.
  Most of the information there focuses on age creation and server administration,
  but especially the GoW wiki also has `some high-level docs <https://www.guildofwriters.org/wiki/Plasma>`__ about the :ref:`Plasma <plasma>` engine and its architecture.

Contents
--------

.. toctree::
  :maxdepth: 1
  :caption: MOUL internals
  
  uru/names
  uru/architecture
  uru/product_id
  uru/encryption_keys
  uru/server_config
  uru/protocol
  uru/vault
  uru/auth_server
  uru/game_server

.. toctree::
  :maxdepth: 1
  :caption: NAGUS
  
  nagus/about

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

License
-------

Documentation
^^^^^^^^^^^^^

.. image:: https://i.creativecommons.org/l/by-sa/4.0/88x31.png
  :target: http://creativecommons.org/licenses/by-sa/4.0/
  :alt: Creative Commons License

This work is licensed under a `Creative Commons Attribution-ShareAlike 4.0 International License <http://creativecommons.org/licenses/by-sa/4.0/>`__.

Code
^^^^

Copyright (C) 2022 dgelessus

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see `<https://www.gnu.org/licenses/>`__.
