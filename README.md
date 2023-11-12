# NAGUS - not a good Uru server

[![Documentation Status](https://readthedocs.org/projects/nagus/badge/?version=latest)](https://nagus.readthedocs.io/en/latest/?badge=latest)

<!-- Note: keep this in sync with docs/index.rst! -->

NAGUS is an experimental work-in-progress Uru Live/Myst Online server written in pure Python.
It is (currently) not very good.
See the [implementation status](https://nagus.readthedocs.io/en/latest/nagus/about.html#implementation-status) for details on what works and what doesn't yet.

For a proper MOULa server implementation,
check out OpenUru's [MOSS](https://wiki.openuru.org/index.php/MOSS) and H'uru's [DIRTSAND](https://guildofwriters.org/wiki/DIRTSAND).

I started writing this server while trying to understand how MOULa's networking works.
In [the docs](https://nagus.readthedocs.io/en/latest/),
I've written a detailed (but still incomplete) reference for MOULa's network protocol and other internals,
which haven't been properly documented elsewhere before.

Please be aware that I'm writing all of this while still figuring out the details myself,
so expect mistakes.
If you find any errors,
please tell me on the [issue tracker](https://github.com/dgelessus/NAGUS/issues)
and I'll try to fix the code and/or docs.

## Requirements

This pile of code has been developed using Python 3.10 on Windows.
It should also work on other OSes and down to Python 3.7.
No additional dependencies are required.

## Running

Quick and dirty setup:

```sh
$ cd src
$ python3 -m nagus
```

Proper installation:

```sh
$ python3 -m pip install .
$ nagus
```

## Documentation

Some documentation about the implementation,
as well as Uru's network architecture and protocols in general,
can be found in the [docs](./docs/) subdirectory.
A pre-built version can be found on [Read the Docs](https://nagus.readthedocs.io/en/latest/),
or you can build the docs yourself using Sphinx:

```sh
$ cd docs
$ python3 -m pip install -r requirements_docs.txt
$ make html
```

The built files can then be found at docs/_build/html.

## License

The code is licensed under AGPL 3.0 or later.
The documentation is licensed under CC BY-SA 4.0.

### Code

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
along with this program.  If not, see <https://www.gnu.org/licenses/>.

### Documentation

[![Creative Commons License](https://i.creativecommons.org/l/by-sa/4.0/88x31.png)](http://creativecommons.org/licenses/by-sa/4.0/)

This work is licensed under a [Creative Commons Attribution-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-sa/4.0/).
