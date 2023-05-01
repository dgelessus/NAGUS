.. index:: SDL
  :name: sdl

SDL
===

*The* mechanism for storing game state and sharing it between clients.
Anything that isn't stored in the :doc:`vault <vault>` is almost certainly handled via SDL
(and some SDL is even stored in the vault!).

.. note::
  
  Outside the context of Uru/Plasma,
  "SDL" usually refers to the `Simple DirectMedia Layer <https://www.libsdl.org/>`__ library.
  Uru's SDL mechanism has absolutely nothing to do with that library.

A few different kinds of states are stored using SDL:

* States of objects within an age instance,
  e. g. the position and movement of kickables.
  The client interacts with these states via the :ref:`game server <game_server>` SDL messages.
  They are stored persistently on the server side,
  but not as vault nodes.
* .. index:: AgeSDLHook
    :name: age_sdl_hook
  
  Age instance state that isn't tied to a specific object in the engine,
  e. g. whether a door is open or closed, a machine is on or off, and any kind of puzzle state.
  If a player can do something in an age
  that is stored persistently and/or visible to other players,
  it's probably reflected in the age instance SDL state.
  This SDL state is stored as an :ref:`vault_node_sdl` vault node under the respective :ref:`vault_node_age` node,
  but the client normally doesn't access or modify these vault nodes directly.
  Instead,
  it uses the same :ref:`game server <game_server>` SDL messages as for age instance object states,
  with a special :dfn:`AgeSDLHook` object
  that represents the age instance state.
* Shard-wide age settings,
  e. g. whether certain linking books, barriers, and other props are visible.
  When the general player community talks about "SDL" or "SDL settings",
  this is what they mean.
  Unlike all other SDL states,
  these can only be changed by shard admins on the server side.
  To clients,
  these SDL settings are completely read-only and only accessible indirectly,
  through the :ref:`AgeSDLHook <age_sdl_hook>` together with the age instance state.
  These settings are sometimes also called "vault settings" or similar,
  but the client never accesses them via the vault interface
  and the server side doesn't necessarily store them as vault nodes.
* Persistent avatar customization and clothing.
  These SDL states are stored as vault nodes under the respective :ref:`vault_node_player` node
  and the client accesses them directly through these nodes.

All SDL data must have a static structure,
which is declared using a :dfn:`state descriptor`.
The text format for state descriptors is called :dfn:`SDL`
(State Descriptor Language).
An instance of a state descriptor is called a :dfn:`state data record`.
When sent over the network and/or stored persistently,
state data records are serialized into a packed binary format,
which is sometimes called an :dfn:`SDL blob`.

Every state descriptor is uniquely identified by a name and version number.
The structure of SDL blobs depends on the state descriptor.
This allows the state to be represented more efficiently,
but also means that SDL blobs can only be read and written if the correct state descriptor is known.

Changing a state descriptor will break any existing SDL blobs that use that descriptor
(with some limited exceptions).
In practice,
this means that once a state descriptor has been published on a shard,
its structure cannot be changed in-place anymore ---
any major changes require creating a new version of the state descriptor.

.. index:: state descriptor
  double: SDL; descriptor
  single: STATEDESC
  :name: state_desc

State descriptors
-----------------

A simple typical SDL file might look like this:

.. code-block::
  
  # State Description Language for SomeAge
  
  STATEDESC SomeAge
  {
      VERSION 1
      # Boolean variables
      VAR BOOL someGlobalFlag[1] DEFAULT=false DEFAULTOPTION=VAULT
  }
  
  STATEDESC SomeAge
  {
      VERSION 2
      # Boolean variables
      VAR BOOL someGlobalFlag[1] DEFAULT=false DEFAULTOPTION=VAULT
      # Age Mechanics
      VAR INT someInstanceState[2] DEFAULT=0
  }

Line comments start with ``#``.
SDL doesn't support block comments.

Every ``STATEDESC`` block declares one version of a state descriptor.
The ``VERSION`` statement is required
and must be the first statement in the ``STATEDESC`` block.
Following the ``VERSION`` is a sequence of ``VAR`` statements
declaring all variables of the state descriptor.
The ``VAR`` syntax is explained in more detail under :ref:`state_var`.

By convention,
the first version of a state descriptor is version 1.
Version number 0 is technically valid,
but not used in practice.
Negative version numbers cannot be used reliably,
because they have special meanings in the open-sourced client code, MOSS, and DIRTSAND.

When declaring multiple versions of a state descriptor,
every version must declare *all* variables in the descriptor,
not just the ones that were newly added in that version.
If a variable is declared in an older version but not in a newer one,
it's deleted in the newer version.

By convention,
all versions of a state descriptor named :samp:`{DescName}` are declared in the file :file:`{DescName}.sdl`,
but this is not required.
The client and all server implementations parse all SDL files eagerly
and then use only the state descriptor names declared in the SDL code,
not the names of the files themselves.
Some SDL file names are capitalized differently than the state descriptor names,
and especially the core engine SDL files often contain descriptors with non-matching names
and/or multiple differently named descriptors per file.

In the case of age instance SDL,
the state descriptor name must be identical to the age file name
(and thus the SDL file name should also match the age file name).

.. index:: state variable
  double: SDL; variable
  single: VAR
  :name: state_var

State variables
---------------

All state variable declarations follow the format :samp:`VAR {TYPE} {name}[{n}] {ATTRS...}`.

:samp:`{TYPE}` is usually one of the simple :ref:`SDL data types <sdl_types>`.
It may also be a ``$``-prefixed state descriptor name to declare a :ref:`nested SDL variable <sdl_nested_types>`.
The second kind is rarely used
and practically only found in the core engine SDL files.

:samp:`{name}` is the human-readable identifier for the variable.
TODO Where exactly is the variable name used as opposed to its index?

:samp:`[{n}]` specifies the number of array elements in the variable.
:samp:`{n}` must be a positive integer,
or the brackets may be empty (:samp:`[]`) to declare a variable-length array variable.
All SDL variables are treated as arrays,
so this part is *required* for *all* variable declarations.
Simple one-element variables must be explicitly declared with ``[1]``.
In practice,
most variables have a single element.
Where arrays are used,
they are usually fixed-length.
Variable-length arrays are practically only used in the core engine SDL files.

:samp:`{ATTRS...}` is a sequence of attributes,
which may appear in any order,
separated by whitespace.
All attributes are optional
and it's also valid for a variable to have no attributes at all.
The following attributes are available:

* :samp:`DEFAULT={value}` defines a default value to be used when the variable is unset in a state data record.
  This attribute is only supported for variables with a simple SDL data type,
  not for nested SDL variables.
  The default value applies to *all* elements of array variables ---
  there is no way to set different default values for individual elements.
  The format of :samp:`{value}` depends on the variable type
  and is described in more detail in :ref:`sdl_types`.
* :samp:`DEFAULTOPTION={option}` sets options that affect the variable's behavior.
  :samp:`{option}` is case-insensitive.
  Unknown options are silently ignored by the open-sourced client code and DIRTSAND,
  but treated as an error by MOSS.
  Only one ``DEFAULTOPTION`` is defined:
  
  * ``DEFAULTOPTION=VAULT`` should be set for variables that are (mainly) meant to be set shard-wide rather than in a particular age instance.
    It is recognized by the open-sourced client code and MOSS,
    but has no effect.
    Unclear if Cyan's server software does anything with it.
  
  ``DEFAULTOPTION=hidden`` and ``DEFAULTOPTION=red`` are also used in some SDL files,
  but they have no effect and are typos of ``DISPLAYOPTION`` (see below).
  MOSS treats these invalid options as errors.
* :samp:`DISPLAYOPTION={option}` sets options that don't affect the variable's format or behavior.
  They are ignored by clients and servers and are meant for use by other tools that manipulate SDL blobs,
  although no currently available tools actually use these options.
  This attribute may be specified more than once to set multiple options.
  :samp:`{option}` is case-insensitive and unknown options are silently ignored.
  In practice,
  the following ``DISPLAYOPTION``\s are used:
  
  * ``DISPLAYOPTION=hidden`` is recognized by the open-sourced client code and MOSS,
    but has no effect.
  * ``DISPLAYOPTION=red`` is commonly used,
    but not recognized by any known code.
  * ``DISPLAYOPTION=VAULT`` has no effect and is a typo of ``DEFAULTOPTION=VAULT`` (see above).
* ``INTERNAL`` and ``PHASED`` are obsolete spellings of ``DISPLAYOPTION=hidden`` and ``DEFAULTOPTION=VAULT``,
  respectively.
  They are recognized by the open-sourced client code,
  but like their equivalent spellings,
  they have no effect.
  These obsolete spellings are not used in any current SDL files
  and are not supported by MOSS and DIRTSAND.

A variable declaration may be followed by a semicolon,
but this is not required and has no effect.

.. index:: SDL; data types
  single: SDL; simple types
  :name: sdl_types

SDL data types
--------------

There are three categories of SDL data types:

* :ref:`Atomic types <sdl_atomic_types>`: ``INT``, ``FLOAT``, ``BOOL``, etc.
* :ref:`Vector types <sdl_vector_types>`: ``VECTOR3``, ``POINT3``, ``QUATERNION``, etc.
* :ref:`Nested SDL types <sdl_nested_types>`: :samp:`${DescName}`

Atomic and vector types are collectively called :dfn:`simple types`
to distinguish them from nested state descriptors.

All SDL data types have an internal type number.
For completeness,
I've listed them in the *#* columns in the tables below,
although these type numbers are never sent over the network
and normally not stored persistently.

.. index:: SDL; atomic types
  :name: sdl_atomic_types

Atomic types
^^^^^^^^^^^^

The fundamental types from which the other SDL data types are constructed.
Some of these are relatively complex,
but still count as atomic from the perspective of SDL.

.. csv-table::
  :header: #,Name,``DEFAULT`` literal syntax,Type in memory,Blob data format,Notes
  :widths: auto
  
  0,``INT``,signed integer,``int``,4-byte signed int,
  1,``FLOAT``,floating-point number,``float``,4-byte floating-point number,
  2,``BOOL``,"``false``, ``true``, or integer",``bool``,1-byte boolean,1\.
  3,``STRING32``,unquoted text,``char [32]``,32-byte 8-bit string (zero-terminated),2\.
  4,``PLKEY``,``nil``,:class:`plUoid`,:class:`plUoid`,3\.
  6,``CREATABLE`` or ``MESSAGE``,(none),``plCreatable *``,(see notes),4\.
  7,``DOUBLE``,floating-point number,``double``,8-byte floating-point number,
  8,``TIME``,number,``double``,:class:`plUnifiedTime`,5\.
  9,``BYTE``,unsigned integer,``unsigned char``,1-byte unsigned int,
  10,``SHORT``,signed integer,``short``,2-byte signed int,
  11,``AGETIMEOFDAY``,(none),``float``,no data,6\.

Notes:

1.
  The boolean literals are case-insensitive.
  If an integer literal is used,
  0 is interpreted as false and all other values as true.
2.
  String literal syntax is very inconsistent across implementations.
  Only *unquoted identifiers* can be used reliably as string values.
  
  The open-sourced client code and MOSS treat quotes as a literal part of the string value,
  so e. g. ``""`` is not parsed as an empty string,
  but as a string containing two double-quote characters.
  DIRTSAND supports quoted identifiers that may contain whitespace and symbols (except ``"``),
  but this isn't useful in practice,
  because nothing else supports this syntax.
  
  As a special case,
  MOSS interprets the literal value ``empty`` (case-insensitive) as an empty string,
  whereas all other implementations treat it as a normal string value.
  
  Both ``""`` and ``empty`` are used as string default values in some SDL files,
  but the inconsistent parsing doesn't seem to cause any problems in practice.
3.
  There is no literal syntax for ``PLKEY`` values.
  The only supported default value is ``nil`` (case-sensitive),
  which behaves the same as setting no default value at all.
4.
  This type is not used in practice on the client side.
  It only appears in a single state descriptor,
  ``CloneMessage``,
  which is used internally by Cyan's server software and MOSS
  to store ``plLoadCloneMsg`` objects as SDL blobs.
  No other state descriptors should use this type
  and it should never be sent over the network or appear in the vault.
  
  DIRTSAND doesn't use the ``CloneMessage`` state descriptor,
  but nonetheless fully supports ``CREATABLE`` variables.
  The alternate spelling ``MESSAGE`` is not supported by DIRTSAND
  and unused in practice.
  
  The blob data format for ``CREATABLE`` values is:
  
  * **Class index:** 2-byte unsigned int.
    Class index of the ``plCreatable`` stored in the following buffer,
    or 0x8000 to represent a ``nullptr`` value.
  * **Buffer length:** 4-byte unsigned int.
    Byte length of the following buffer field.
    Only present if the class index is not 0x8000 (``nullptr``).
  * **Buffer:** Variable-length byte array.
    The serialized ``plCreatable``,
    in the format produced by ``plCreatable::Write`` and understood by ``plCreatable::Read``.
    Only present if the class index is not 0x8000 (``nullptr``).
5.
  Default values for ``TIME`` variables are handled inconsistently.
  The open-sourced client code interprets it as a local game time value
  (parsed as a floating-point value).
  MOSS and DIRTSAND interpret it as the seconds part of a :cpp:class:`plUnifiedTime`
  (parsed as an integer).
6.
  ``AGETIMEOFDAY`` variables are not stored in SDL blobs.
  In the client,
  such a variable is treated like a read-only ``FLOAT`` variable
  whose value is always the current time of day in the current age instance
  (ranging from 0 to 1).
  The open-sourced client code and MOSS allow specifying a default value for ``AGETIMEOFDAY`` variables,
  but this has no effect,
  is not used in practice,
  and not supported by DIRTSAND.

.. index:: SDL; vector types
  :name: sdl_vector_types

Vector types
^^^^^^^^^^^^

There is no official term for these types.
I'm calling them "vector" types,
in the mathematical sense that they consist of a fixed number of elements of the same atomic type.
Most of these are not vectors in the physics sense though.

Although vector types consist of multiple elements,
they are mostly treated as a single unit.
For example,
a variable declaration ``VAR POINT3 points[2]`` declares an array of 2 ``POINT3`` values,
both consisting of 3 ``FLOAT`` values each.

.. csv-table::
  :header: #,Name,Element type,Count
  :widths: auto
  
  50,``VECTOR3``,``FLOAT``,3
  51,``POINT3``,``FLOAT``,3
  52,``RGB``,``FLOAT``,3
  53,``RGBA``,``FLOAT``,4
  54,``QUATERNION``,``FLOAT``,4
  55,``RGB8``,``BYTE``,3
  56,``RGBA8``,``BYTE``,4

For all vector types,
the ``DEFAULT`` literal syntax is :samp:`({x},{y},{z})` or :samp:`({x},{y},{z},{w})`,
where each value follows the ``DEFAULT`` literal syntax of the atomic element type.
For example,
a ``POINT3`` variable might be declared with ``DEFAULT=(0.0,-5,12.34)``.

The blob data format of a vector type is that of its atomic element type,
repeated for each element.

.. index:: SDL; nested SDL types
  :name: sdl_nested_types

Nested SDL types
^^^^^^^^^^^^^^^^

TODO

.. csv-table::
  :header: #,Name
  :widths: auto
  
  5,:samp:`${DescName}`

.. _sdl_syntax_mess:

Gnarly SDL syntax details
-------------------------

There's no proper description or specification for the SDL syntax.
The original SDL parser in the open-sourced client code is very loose in some places ---
it ignores various errors and accidentally allows some syntax that makes no sense.
MOSS and DIRTSAND both have their own parsers,
which are stricter and more robust,
but as a result don't support some weird syntax that Cyan's original code accepts.
In a few cases,
the three parsers also interpret the same syntax differently.
This section covers most of the differences between the three parsers,
but I can't promise that I've found every weird corner case.

The open-sourced client code and MOSS use very simple tokenizers.
MOSS splits tokens only on whitespace in many cases,
so it *requires* whitespace in some places where one would expect it to be optional,
e. g. before ``#`` comments and around braces.
The open-sourced client code uses whitespace, ``,``, and ``=`` as the basic token separators
and sometimes allows them to be used interchangeably.
In both cases,
any symbols that are *not* token separators are handled in a second step after tokenization.
Most symbols are only recognized in their intended context and have no special meaning otherwise.

DIRTSAND uses a more traditional lexer and parser.
The lexer recognizes all tokens consistently regardless of context
and immediately reports unexpected symbols as errors.
The parser doesn't recognize any symbols on its own
and operates only on the tokens returned by the lexer.

Identifiers,
i. e. the names of state descriptors and variables,
*should* only consist of ASCII identifier characters:
the first character should be a letter or ``_``
and the remaining characters should be letters, digits, or ``_``.
DIRTSAND also allows ``-`` in variable names,
but not state descriptor names.
The open-sourced client code and MOSS allow arbitrary tokens as identifiers.
In practice,
all identifiers consist only of letters and digits.

OpenUru clients, MOSS, and DIRTSAND only allow base-10 integer literals.
H'uru clients also accept other bases as supported by ``strtol``,
but this isn't used in practice.

For floating-point literals,
DIRTSAND only allows simple decimal literals.
If a decimal point is present,
there must be at least one digit before it.
The open-sourced client code and MOSS also accept other floating-point literal formats,
such as scientific/exponential notation,
hexadecimal literals,
and infinity/NaN values.
In practice,
only simple decimal literals are used,
with digits on both sides of the decimal point.

The open-sourced client code, MOSS, and DIRTSAND all silently allow floating-point literals where integers are expected,
in which case the value is truncated at the decimal point.
In practice,
nothing relies on this.

:ref:`Simple type <sdl_types>` names are parsed case-insensitively by the open-sourced client code and MOSS,
but DIRTSAND requires them to be all uppercase,
which is how they are always spelled in practice.

The open-sourced client code interprets any type name starting with ``QUAT`` as ``QUATERNION``.
MOSS and DIRTSAND require the exact spelling ``QUATERNION``,
which is the only spelling used in practice.

DIRTSAND allows whitespace before and/or between the array length brackets,
but the open-sourced client code and MOSS don't.

The open-sourced client code is *very* loose when parsing ``DEFAULT`` values.
Invalid values are silently ignored.
Parentheses can be mismatched,
because they are treated as token separators and thus mostly ignored.
In default values of vector types,
parentheses are not required
and any token separator can be used between values in place of commas.
MOSS and DIRTSAND are stricter when parsing default values.
Additionally,
MOSS doesn't allow spaces between the parentheses in vector default values.
