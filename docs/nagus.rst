About NAGUS
===========

NAGUS is an Uru Live server.
It is currently a work in progress and still *very* incomplete.
Only the most essential functionality has been implemented so far,
so you'll probably be able to log in and create an avatar,
but most gameplay aspects aren't working yet.

If you're looking for a proper MOULa server implementation that you can actually play on,
check out OpenUru's `MOSS <https://wiki.openuru.org/index.php/MOSS>`__ and H'uru's `DIRTSAND <https://guildofwriters.org/wiki/DIRTSAND>`__.

Scope and goals
---------------

I'm calling this an "Uru Live server",
but it is specifically for Uru Live's latest iteration,
"Myst Online: Uru Live again" (MOULa),
and its derivatives.
NAGUS aims to fully support both the OpenUru and H'uru forks of the open-source MOULa client.
As the network protocol has changed very little since MOULa was first released,
older MOUL(a) clients may work too,
but this is not a primary goal.
NAGUS does *not* support pre-MOUL clients based on the original Uru Live,
as the MOUL(a) protocol differs from the original Uru Live in some significant ways.

A secondary goal is to keep this server self-contained and easy to set up.
All parts of the server run in a single process,
using an SQLite database instead of a separate database server.
The server is implemented in pure Python using only standard library modules ---
you don't need to install any third-party dependencies.
