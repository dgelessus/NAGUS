# This file is part of NAGUS, an Uru Live server that is not very good.
# Copyright (C) 2024 dgelessus
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import io
import typing
import unittest

from nagus import sdl


def _make_all_default_record(indices: typing.Iterable[int], explicit: bool) -> sdl.GuessedSDLRecord:
	simple_values = {}
	for i in indices:
		simple_values[i] = sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags.same_as_default, data=b"")
	return sdl.GuessedSDLRecord(simple_values_indices=explicit, simple_values=simple_values, nested_sdl_values_indices=True, nested_sdl_values={})


# Age SDL blobs.
# These only contain simple SDL variables and fixed-length arrays.

CITY_V43_HEADER = sdl.SDLStreamHeader(b"city", 43)

CITY_V43_DEFAULT_RECORD = _make_all_default_record(range(151), explicit=False)
CITY_V43_DEFAULT_DATA = b"\x00\x80\x04\xf0\x9c\x96\x8b\x86+\x00\x00\x00\x06\x97\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x00"

CLEFT_V24_HEADER = sdl.SDLStreamHeader(b"Cleft", 24)

CLEFT_V24_DEFAULT_RECORD = _make_all_default_record(range(31), explicit=False)
CLEFT_V24_DEFAULT_DATA = b"\x00\x80\x05\xf0\xbc\x93\x9a\x99\x8b\x18\x00\x00\x00\x06\x1f\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x02\x00\x00\xf0\x08\x00"

NEIGHBORHOOD_V35_HEADER = sdl.SDLStreamHeader(b"Neighborhood", 35)

NEIGHBORHOOD_V35_DEFAULT_RECORD = _make_all_default_record([*range(1, 48), *range(49, 101)], explicit=True)
NEIGHBORHOOD_V35_DEFAULT_DATA = b"\x00\x80\x0c\xf0\xb1\x9a\x96\x98\x97\x9d\x90\x8d\x97\x90\x90\x9b#\x00\x00\x00\x06c\x01\x02\x00\x00\xf0\x08\x02\x02\x00\x00\xf0\x08\x03\x02\x00\x00\xf0\x08\x04\x02\x00\x00\xf0\x08\x05\x02\x00\x00\xf0\x08\x06\x02\x00\x00\xf0\x08\x07\x02\x00\x00\xf0\x08\x08\x02\x00\x00\xf0\x08\t\x02\x00\x00\xf0\x08\n\x02\x00\x00\xf0\x08\x0b\x02\x00\x00\xf0\x08\x0c\x02\x00\x00\xf0\x08\r\x02\x00\x00\xf0\x08\x0e\x02\x00\x00\xf0\x08\x0f\x02\x00\x00\xf0\x08\x10\x02\x00\x00\xf0\x08\x11\x02\x00\x00\xf0\x08\x12\x02\x00\x00\xf0\x08\x13\x02\x00\x00\xf0\x08\x14\x02\x00\x00\xf0\x08\x15\x02\x00\x00\xf0\x08\x16\x02\x00\x00\xf0\x08\x17\x02\x00\x00\xf0\x08\x18\x02\x00\x00\xf0\x08\x19\x02\x00\x00\xf0\x08\x1a\x02\x00\x00\xf0\x08\x1b\x02\x00\x00\xf0\x08\x1c\x02\x00\x00\xf0\x08\x1d\x02\x00\x00\xf0\x08\x1e\x02\x00\x00\xf0\x08\x1f\x02\x00\x00\xf0\x08 \x02\x00\x00\xf0\x08!\x02\x00\x00\xf0\x08\"\x02\x00\x00\xf0\x08#\x02\x00\x00\xf0\x08$\x02\x00\x00\xf0\x08%\x02\x00\x00\xf0\x08&\x02\x00\x00\xf0\x08'\x02\x00\x00\xf0\x08(\x02\x00\x00\xf0\x08)\x02\x00\x00\xf0\x08*\x02\x00\x00\xf0\x08+\x02\x00\x00\xf0\x08,\x02\x00\x00\xf0\x08-\x02\x00\x00\xf0\x08.\x02\x00\x00\xf0\x08/\x02\x00\x00\xf0\x081\x02\x00\x00\xf0\x082\x02\x00\x00\xf0\x083\x02\x00\x00\xf0\x084\x02\x00\x00\xf0\x085\x02\x00\x00\xf0\x086\x02\x00\x00\xf0\x087\x02\x00\x00\xf0\x088\x02\x00\x00\xf0\x089\x02\x00\x00\xf0\x08:\x02\x00\x00\xf0\x08;\x02\x00\x00\xf0\x08<\x02\x00\x00\xf0\x08=\x02\x00\x00\xf0\x08>\x02\x00\x00\xf0\x08?\x02\x00\x00\xf0\x08@\x02\x00\x00\xf0\x08A\x02\x00\x00\xf0\x08B\x02\x00\x00\xf0\x08C\x02\x00\x00\xf0\x08D\x02\x00\x00\xf0\x08E\x02\x00\x00\xf0\x08F\x02\x00\x00\xf0\x08G\x02\x00\x00\xf0\x08H\x02\x00\x00\xf0\x08I\x02\x00\x00\xf0\x08J\x02\x00\x00\xf0\x08K\x02\x00\x00\xf0\x08L\x02\x00\x00\xf0\x08M\x02\x00\x00\xf0\x08N\x02\x00\x00\xf0\x08O\x02\x00\x00\xf0\x08P\x02\x00\x00\xf0\x08Q\x02\x00\x00\xf0\x08R\x02\x00\x00\xf0\x08S\x02\x00\x00\xf0\x08T\x02\x00\x00\xf0\x08U\x02\x00\x00\xf0\x08V\x02\x00\x00\xf0\x08W\x02\x00\x00\xf0\x08X\x02\x00\x00\xf0\x08Y\x02\x00\x00\xf0\x08Z\x02\x00\x00\xf0\x08[\x02\x00\x00\xf0\x08\\\x02\x00\x00\xf0\x08]\x02\x00\x00\xf0\x08^\x02\x00\x00\xf0\x08_\x02\x00\x00\xf0\x08`\x02\x00\x00\xf0\x08a\x02\x00\x00\xf0\x08b\x02\x00\x00\xf0\x08c\x02\x00\x00\xf0\x08d\x02\x00\x00\xf0\x08\x00"

PERSONAL_V41_HEADER = sdl.SDLStreamHeader(b"Personal", 41)

PERSONAL_V41_DEFAULT_RECORD = _make_all_default_record([*range(10), *range(11, 72), 73, *range(75, 102)], explicit=True)
PERSONAL_V41_DEFAULT_DATA = b"\x00\x80\x08\xf0\xaf\x9a\x8d\x8c\x90\x91\x9e\x93)\x00\x00\x00\x06c\x00\x02\x00\x00\xf0\x08\x01\x02\x00\x00\xf0\x08\x02\x02\x00\x00\xf0\x08\x03\x02\x00\x00\xf0\x08\x04\x02\x00\x00\xf0\x08\x05\x02\x00\x00\xf0\x08\x06\x02\x00\x00\xf0\x08\x07\x02\x00\x00\xf0\x08\x08\x02\x00\x00\xf0\x08\t\x02\x00\x00\xf0\x08\x0b\x02\x00\x00\xf0\x08\x0c\x02\x00\x00\xf0\x08\r\x02\x00\x00\xf0\x08\x0e\x02\x00\x00\xf0\x08\x0f\x02\x00\x00\xf0\x08\x10\x02\x00\x00\xf0\x08\x11\x02\x00\x00\xf0\x08\x12\x02\x00\x00\xf0\x08\x13\x02\x00\x00\xf0\x08\x14\x02\x00\x00\xf0\x08\x15\x02\x00\x00\xf0\x08\x16\x02\x00\x00\xf0\x08\x17\x02\x00\x00\xf0\x08\x18\x02\x00\x00\xf0\x08\x19\x02\x00\x00\xf0\x08\x1a\x02\x00\x00\xf0\x08\x1b\x02\x00\x00\xf0\x08\x1c\x02\x00\x00\xf0\x08\x1d\x02\x00\x00\xf0\x08\x1e\x02\x00\x00\xf0\x08\x1f\x02\x00\x00\xf0\x08 \x02\x00\x00\xf0\x08!\x02\x00\x00\xf0\x08\"\x02\x00\x00\xf0\x08#\x02\x00\x00\xf0\x08$\x02\x00\x00\xf0\x08%\x02\x00\x00\xf0\x08&\x02\x00\x00\xf0\x08'\x02\x00\x00\xf0\x08(\x02\x00\x00\xf0\x08)\x02\x00\x00\xf0\x08*\x02\x00\x00\xf0\x08+\x02\x00\x00\xf0\x08,\x02\x00\x00\xf0\x08-\x02\x00\x00\xf0\x08.\x02\x00\x00\xf0\x08/\x02\x00\x00\xf0\x080\x02\x00\x00\xf0\x081\x02\x00\x00\xf0\x082\x02\x00\x00\xf0\x083\x02\x00\x00\xf0\x084\x02\x00\x00\xf0\x085\x02\x00\x00\xf0\x086\x02\x00\x00\xf0\x087\x02\x00\x00\xf0\x088\x02\x00\x00\xf0\x089\x02\x00\x00\xf0\x08:\x02\x00\x00\xf0\x08;\x02\x00\x00\xf0\x08<\x02\x00\x00\xf0\x08=\x02\x00\x00\xf0\x08>\x02\x00\x00\xf0\x08?\x02\x00\x00\xf0\x08@\x02\x00\x00\xf0\x08A\x02\x00\x00\xf0\x08B\x02\x00\x00\xf0\x08C\x02\x00\x00\xf0\x08D\x02\x00\x00\xf0\x08E\x02\x00\x00\xf0\x08F\x02\x00\x00\xf0\x08G\x02\x00\x00\xf0\x08I\x02\x00\x00\xf0\x08K\x02\x00\x00\xf0\x08L\x02\x00\x00\xf0\x08M\x02\x00\x00\xf0\x08N\x02\x00\x00\xf0\x08O\x02\x00\x00\xf0\x08P\x02\x00\x00\xf0\x08Q\x02\x00\x00\xf0\x08R\x02\x00\x00\xf0\x08S\x02\x00\x00\xf0\x08T\x02\x00\x00\xf0\x08U\x02\x00\x00\xf0\x08V\x02\x00\x00\xf0\x08W\x02\x00\x00\xf0\x08X\x02\x00\x00\xf0\x08Y\x02\x00\x00\xf0\x08Z\x02\x00\x00\xf0\x08[\x02\x00\x00\xf0\x08\\\x02\x00\x00\xf0\x08]\x02\x00\x00\xf0\x08^\x02\x00\x00\xf0\x08_\x02\x00\x00\xf0\x08`\x02\x00\x00\xf0\x08a\x02\x00\x00\xf0\x08b\x02\x00\x00\xf0\x08c\x02\x00\x00\xf0\x08d\x02\x00\x00\xf0\x08e\x02\x00\x00\xf0\x08\x00"


# Other SDL blobs in the vault.
# These contain variable-length arrays.

APPEARANCE_OPTIONS_V2_HEADER = sdl.SDLStreamHeader(b"appearanceOptions", 2)

APPEARANCE_OPTIONS_V2_FEMALE_DEFAULT_RECORD = sdl.GuessedSDLRecord(
	simple_values_indices=False,
	simple_values={
		# RGB8 skinTint[1]
		0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\xff\xd6\xb5"),
		# BYTE faceBlends[]
		1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00"),
	},
	nested_sdl_values_indices=True,
	nested_sdl_values={},
)
APPEARANCE_OPTIONS_V2_FEMALE_DEFAULT_DATA = b"\x00\x80\x11\xf0\x9e\x8f\x8f\x9a\x9e\x8d\x9e\x91\x9c\x9a\xb0\x8f\x8b\x96\x90\x91\x8c\x02\x00\x00\x00\x06\x02\x02\x00\x00\xf0\x10\xff\xd6\xb5\x02\x00\x00\xf0\x10\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"

CLOTHING_ITEM_V3_HEADER = sdl.SDLStreamHeader(b"clothingItem", 3)

CLOTHING_ITEM_V3_FEMALE_FACE_DEFAULT_RECORD = sdl.GuessedSDLRecord(
	simple_values_indices=False,
	simple_values={
		# PLKEY item[1]
		0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x00\x03\x00\x05\xff\x04\x00\xb5\x00\r\x00\x00\x00\n\xf0\xbc\xb6\x8b\x92\xa0\xb9\xb9\x9e\x9c\x9a"),
		# RGB8 tint[1]
		1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x7fL3"),
		# RGB8 tint2[1]
		2: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\xff\xff\xff"),
	},
	nested_sdl_values_indices=True,
	nested_sdl_values={},
)
CLOTHING_ITEM_V3_FEMALE_FACE_DEFAULT_DATA = b"\x00\x80\x0c\xf0\x9c\x93\x90\x8b\x97\x96\x91\x98\xb6\x8b\x9a\x92\x03\x00\x00\x00\x06\x03\x02\x00\x00\xf0\x10\x00\x03\x00\x05\xff\x04\x00\xb5\x00\r\x00\x00\x00\n\xf0\xbc\xb6\x8b\x92\xa0\xb9\xb9\x9e\x9c\x9a\x02\x00\x00\xf0\x10\x7fL3\x02\x00\x00\xf0\x10\xff\xff\xff\x00"

# Core engine SDL blobs attached to objects.
# These may contain complex nested SDL variables,
# sometimes with multiple levels of nesting.

AVATAR_V7_HEADER = sdl.SDLStreamHeader(b"avatar", 7)

AVATAR_V7_FEMALE_WAVE_RECORD = sdl.GuessedSDLRecord(
	flags=sdl.SDLRecordBase.Flags.volatile,
	simple_values_indices=False,
	simple_values={
		# BYTE invisibilityLevel[1]
		0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x38), data=b""),
	},
	nested_sdl_values_indices=False,
	nested_sdl_values={
		# VAR $brainUnion VERSION 1 brainStack[]
		0: sdl.GuessedNestedSDLVariableValue(hint=b"", variable_array_length=1, values={
			0: sdl.GuessedSDLRecord(
				simple_values_indices=True,
				simple_values={},
				nested_sdl_values_indices=False,
				nested_sdl_values={
					# VAR $genericBrain VERSION 3 fGenericBrain[]
					0: sdl.GuessedNestedSDLVariableValue(hint=b"", variable_array_length=1, values={
						0: sdl.GuessedSDLRecord(
							simple_values_indices=True,
							simple_values={
								# BYTE currentStage[1]
								1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
								# PLKEY callbackRcvr[1]
								3: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
								# BOOL movingForward[1]
								4: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
								# BYTE exitFlags[1]
								5: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x07"),
								# BYTE type[1]
								6: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x04"),
								# BYTE mode[1]
								7: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x01"),
								# FLOAT fadeIn[1]
								8: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x00\x00\x00@"),
								# FLOAT fadeOut[1]
								9: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x00\x00\x00@"),
								# BYTE moveMode[1]
								10: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x03"),
								# BYTE bodyUsage[1]
								11: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x01"),
							},
							nested_sdl_values_indices=False,
							nested_sdl_values={
								# VAR $standardStage VERSION 3 stages[]
								0: sdl.GuessedNestedSDLVariableValue(hint=b"", variable_array_length=1, values={
									0: sdl.GuessedSDLRecord(
										simple_values_indices=True,
										simple_values={
											0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"Wave\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"),
											1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											2: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x02"),
											3: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											4: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x01"),
											5: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											6: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											7: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											8: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											9: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											11: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											12: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											13: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x01"),
										},
										nested_sdl_values_indices=False,
										nested_sdl_values={},
									),
								}),
							}),
					}),
					# VAR $climbBrain VERSION 1 fClimbBrain[]
					1: sdl.GuessedNestedSDLVariableValue(hint=b"", variable_array_length=0, values_indices=True, values={}),
					# VAR $driveBrain VERSION 1 fDriveBrain[]
					2: sdl.GuessedNestedSDLVariableValue(hint=b"", variable_array_length=0, values_indices=True, values={}),
				},
			),
		}),
	},
)
AVATAR_V7_FEMALE_WAVE_DATA = b"\x00\x80\x06\xf0\x9e\x89\x9e\x8b\x9e\x8d\x07\x00\x01\x00\x06\x01\x02\x00\x00\xf08\x01\x02\x00\x00\xf0\x00\x01\x00\x00\x00\x01\x00\x00\x06\x00\x03\x02\x00\x00\xf0\x00\x01\x00\x00\x00\x01\x00\x00\x06\n\x01\x02\x00\x00\xf0\x18\x03\x02\x00\x00\xf0\x18\x04\x02\x00\x00\xf0\x18\x05\x02\x00\x00\xf0\x10\x07\x06\x02\x00\x00\xf0\x10\x04\x07\x02\x00\x00\xf0\x10\x01\x08\x02\x00\x00\xf0\x10\x00\x00\x00@\t\x02\x00\x00\xf0\x10\x00\x00\x00@\n\x02\x00\x00\xf0\x10\x03\x0b\x02\x00\x00\xf0\x10\x01\x01\x02\x00\x00\xf0\x00\x01\x00\x00\x00\x01\x00\x00\x06\r\x00\x02\x00\x00\xf0\x10Wave\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x00\x00\xf0\x18\x02\x02\x00\x00\xf0\x10\x02\x03\x02\x00\x00\xf0\x18\x04\x02\x00\x00\xf0\x10\x01\x05\x02\x00\x00\xf0\x18\x06\x02\x00\x00\xf0\x18\x07\x02\x00\x00\xf0\x18\x08\x02\x00\x00\xf0\x18\t\x02\x00\x00\xf0\x18\x0b\x02\x00\x00\xf0\x18\x0c\x02\x00\x00\xf0\x18\r\x02\x00\x00\xf0\x10\x01\x00\x02\x00\x00\xf0\x00\x00\x00\x00\x00\x00\x02\x00\x00\xf0\x00\x00\x00\x00\x00\x00"

AVATAR_V7_ZANDI_RECORD = sdl.GuessedSDLRecord(
	flags=sdl.SDLRecordBase.Flags.volatile,
	simple_values_indices=False,
	simple_values={
		# BYTE invisibilityLevel[1]
		0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x38), data=b""),
	},
	nested_sdl_values_indices=False,
	nested_sdl_values={
		# VAR $brainUnion VERSION 1 brainStack[]
		0: sdl.GuessedNestedSDLVariableValue(hint=b"", variable_array_length=1, values={
			0: sdl.GuessedSDLRecord(
				simple_values_indices=True,
				simple_values={},
				nested_sdl_values_indices=False,
				nested_sdl_values={
					# VAR $genericBrain VERSION 3 fGenericBrain[]
					0: sdl.GuessedNestedSDLVariableValue(hint=b"", variable_array_length=1, values={
						0: sdl.GuessedSDLRecord(
							simple_values_indices=True,
							simple_values={
								# BYTE currentStage[1]
								1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
								# PLKEY callbackRcvr[1]
								3: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x00=\x00\x07\x00\x00\x00\xa2\x00\x01\x00\x00\x00\x11\xf0\x9c\xaf\x86\x8b\x97\xa5\x9e\x91\x9b\x96\xbc\x90\x91\x8b\x8d\x90\x93"),
								# BOOL movingForward[1]
								4: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
								# BYTE exitFlags[1]
								5: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
								# BYTE type[1]
								6: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
								# BYTE mode[1]
								7: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x03"),
								# FLOAT fadeIn[1]
								8: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x00\x00\xc0@"),
								# FLOAT fadeOut[1]
								9: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x00\x00\x00\x00"),
								# BYTE moveMode[1]
								10: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x01"),
								# BYTE bodyUsage[1]
								11: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
							},
							nested_sdl_values_indices=False,
							nested_sdl_values={
								# VAR $standardStage VERSION 3 stages[]
								0: sdl.GuessedNestedSDLVariableValue(hint=b"", variable_array_length=7, values={
									0: sdl.GuessedSDLRecord(
										simple_values_indices=True,
										simple_values={
											# STRING32 name[1]
											0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"ZandiIdle\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"),
											# SHORT numLoops[1]
											1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\xff\xff"),
											# BYTE forward[1]
											2: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x02"),
											# BYTE backward[1]
											3: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BYTE stageAdvance[1]
											4: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BYTE stageRegress[1]
											5: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL notifyEnter[1]
											6: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL notifyLoop[1]
											7: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL notifyStageAdvance[1]
											8: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL notifyStageRegress[1]
											9: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# FLOAT localTime[1]
											11: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# SHORT currentLoop[1]
											12: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL isAttached[1]
											13: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x01"),
										},
										nested_sdl_values_indices=True,
										nested_sdl_values={},
									),
									1: sdl.GuessedSDLRecord(
										simple_values_indices=True,
										simple_values={
											# STRING32 name[1]
											0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b'ZandiScratchHead\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'),
											# SHORT numLoops[1]
											1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BYTE forward[1]
											2: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x02"),
											# BYTE backward[1]
											3: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BYTE stageAdvance[1]
											4: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x02"),
											# BYTE stageRegress[1]
											5: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL notifyEnter[1]
											6: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL notifyLoop[1]
											7: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL notifyStageAdvance[1]
											8: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x01"),
											# BOOL notifyStageRegress[1]
											9: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x01"),
											# FLOAT localTime[1]
											11: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# SHORT currentLoop[1]
											12: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL isAttached[1]
											13: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
										},
										nested_sdl_values_indices=True,
										nested_sdl_values={},
									),
									2: sdl.GuessedSDLRecord(
										simple_values_indices=True,
										simple_values={
											# STRING32 name[1]
											0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"ZandiTurnPage\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"),
											# SHORT numLoops[1]
											1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BYTE forward[1]
											2: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x02"),
											# BYTE backward[1]
											3: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BYTE stageAdvance[1]
											4: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x02"),
											# BYTE stageRegress[1]
											5: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL notifyEnter[1]
											6: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL notifyLoop[1]
											7: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL notifyStageAdvance[1]
											8: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x01"),
											# BOOL notifyStageRegress[1]
											9: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x01"),
											# FLOAT localTime[1]
											11: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# SHORT currentLoop[1]
											12: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL isAttached[1]
											13: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
										},
										nested_sdl_values_indices=True,
										nested_sdl_values={},
									),
									3: sdl.GuessedSDLRecord(
										simple_values_indices=True,
										simple_values={
											# STRING32 name[1]
											0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"ZandiDirections\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"),
											# SHORT numLoops[1]
											1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BYTE forward[1]
											2: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x02"),
											# BYTE backward[1]
											3: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BYTE stageAdvance[1]
											4: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x02"),
											# BYTE stageRegress[1]
											5: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL notifyEnter[1]
											6: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL notifyLoop[1]
											7: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL notifyStageAdvance[1]
											8: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x01"),
											# BOOL notifyStageRegress[1]
											9: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x01"),
											# FLOAT localTime[1]
											11: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# SHORT currentLoop[1]
											12: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL isAttached[1]
											13: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
										},
										nested_sdl_values_indices=True,
										nested_sdl_values={},
									),
									4: sdl.GuessedSDLRecord(
										simple_values_indices=True,
										simple_values={
											# STRING32 name[1]
											0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"ZandiCrossLegs\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"),
											# SHORT numLoops[1]
											1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BYTE forward[1]
											2: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x02"),
											# BYTE backward[1]
											3: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BYTE stageAdvance[1]
											4: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x02"),
											# BYTE stageRegress[1]
											5: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL notifyEnter[1]
											6: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL notifyLoop[1]
											7: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL notifyStageAdvance[1]
											8: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x01"),
											# BOOL notifyStageRegress[1]
											9: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x01"),
											# FLOAT localTime[1]
											11: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# SHORT currentLoop[1]
											12: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL isAttached[1]
											13: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
										},
										nested_sdl_values_indices=True,
										nested_sdl_values={},
									),
									5: sdl.GuessedSDLRecord(
										simple_values_indices=True,
										simple_values={
											# STRING32 name[1]
											0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"ZandiRubNose\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"),
											# SHORT numLoops[1]
											1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BYTE forward[1]
											2: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x02"),
											# BYTE backward[1]
											3: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BYTE stageAdvance[1]
											4: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x02"),
											# BYTE stageRegress[1]
											5: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL notifyEnter[1]
											6: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL notifyLoop[1]
											7: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL notifyStageAdvance[1]
											8: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x01"),
											# BOOL notifyStageRegress[1]
											9: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x01"),
											# FLOAT localTime[1]
											11: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# SHORT currentLoop[1]
											12: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL isAttached[1]
											13: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
										},
										nested_sdl_values_indices=True,
										nested_sdl_values={},
									),
									6: sdl.GuessedSDLRecord(
										simple_values_indices=True,
										simple_values={
											# STRING32 name[1]
											0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"ZandiTurnPage\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"),
											# SHORT numLoops[1]
											1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BYTE forward[1]
											2: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x02"),
											# BYTE backward[1]
											3: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BYTE stageAdvance[1]
											4: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x02"),
											# BYTE stageRegress[1]
											5: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL notifyEnter[1]
											6: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL notifyLoop[1]
											7: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL notifyStageAdvance[1]
											8: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL notifyStageRegress[1]
											9: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# FLOAT localTime[1]
											11: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# SHORT currentLoop[1]
											12: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
											# BOOL isAttached[1]
											13: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
										},
										nested_sdl_values_indices=False,
										nested_sdl_values={},
									),
								}),
							},
						),
					}),
					# VAR $climbBrain VERSION 1 fClimbBrain[]
					1: sdl.GuessedNestedSDLVariableValue(hint=b"", variable_array_length=0, values_indices=True, values={}),
					# VAR $driveBrain VERSION 1 fDriveBrain[]
					2: sdl.GuessedNestedSDLVariableValue(hint=b"", variable_array_length=0, values_indices=True, values={}),
				},
			),
		}),
	},
)
AVATAR_V7_ZANDI_DATA = b"\x00\x80\x06\xf0\x9e\x89\x9e\x8b\x9e\x8d\x07\x00\x01\x00\x06\x01\x02\x00\x00\xf08\x01\x02\x00\x00\xf0\x00\x01\x00\x00\x00\x01\x00\x00\x06\x00\x03\x02\x00\x00\xf0\x00\x01\x00\x00\x00\x01\x00\x00\x06\n\x01\x02\x00\x00\xf0\x18\x03\x02\x00\x00\xf0\x10\x00=\x00\x07\x00\x00\x00\xa2\x00\x01\x00\x00\x00\x11\xf0\x9c\xaf\x86\x8b\x97\xa5\x9e\x91\x9b\x96\xbc\x90\x91\x8b\x8d\x90\x93\x04\x02\x00\x00\xf0\x18\x05\x02\x00\x00\xf0\x18\x06\x02\x00\x00\xf0\x18\x07\x02\x00\x00\xf0\x10\x03\x08\x02\x00\x00\xf0\x10\x00\x00\xc0@\t\x02\x00\x00\xf0\x10\x00\x00\x00\x00\n\x02\x00\x00\xf0\x10\x01\x0b\x02\x00\x00\xf0\x18\x01\x02\x00\x00\xf0\x00\x07\x00\x00\x00\x07\x00\x00\x06\r\x00\x02\x00\x00\xf0\x10ZandiIdle\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x00\x00\xf0\x10\xff\xff\x02\x02\x00\x00\xf0\x10\x02\x03\x02\x00\x00\xf0\x18\x04\x02\x00\x00\xf0\x18\x05\x02\x00\x00\xf0\x18\x06\x02\x00\x00\xf0\x18\x07\x02\x00\x00\xf0\x18\x08\x02\x00\x00\xf0\x18\t\x02\x00\x00\xf0\x18\x0b\x02\x00\x00\xf0\x18\x0c\x02\x00\x00\xf0\x18\r\x02\x00\x00\xf0\x10\x01\x00\x00\x00\x06\r\x00\x02\x00\x00\xf0\x10ZandiScratchHead\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x00\x00\xf0\x18\x02\x02\x00\x00\xf0\x10\x02\x03\x02\x00\x00\xf0\x18\x04\x02\x00\x00\xf0\x10\x02\x05\x02\x00\x00\xf0\x18\x06\x02\x00\x00\xf0\x18\x07\x02\x00\x00\xf0\x18\x08\x02\x00\x00\xf0\x10\x01\t\x02\x00\x00\xf0\x10\x01\x0b\x02\x00\x00\xf0\x18\x0c\x02\x00\x00\xf0\x18\r\x02\x00\x00\xf0\x18\x00\x00\x00\x06\r\x00\x02\x00\x00\xf0\x10ZandiTurnPage\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x00\x00\xf0\x18\x02\x02\x00\x00\xf0\x10\x02\x03\x02\x00\x00\xf0\x18\x04\x02\x00\x00\xf0\x10\x02\x05\x02\x00\x00\xf0\x18\x06\x02\x00\x00\xf0\x18\x07\x02\x00\x00\xf0\x18\x08\x02\x00\x00\xf0\x10\x01\t\x02\x00\x00\xf0\x10\x01\x0b\x02\x00\x00\xf0\x18\x0c\x02\x00\x00\xf0\x18\r\x02\x00\x00\xf0\x18\x00\x00\x00\x06\r\x00\x02\x00\x00\xf0\x10ZandiDirections\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x00\x00\xf0\x18\x02\x02\x00\x00\xf0\x10\x02\x03\x02\x00\x00\xf0\x18\x04\x02\x00\x00\xf0\x10\x02\x05\x02\x00\x00\xf0\x18\x06\x02\x00\x00\xf0\x18\x07\x02\x00\x00\xf0\x18\x08\x02\x00\x00\xf0\x10\x01\t\x02\x00\x00\xf0\x10\x01\x0b\x02\x00\x00\xf0\x18\x0c\x02\x00\x00\xf0\x18\r\x02\x00\x00\xf0\x18\x00\x00\x00\x06\r\x00\x02\x00\x00\xf0\x10ZandiCrossLegs\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x00\x00\xf0\x18\x02\x02\x00\x00\xf0\x10\x02\x03\x02\x00\x00\xf0\x18\x04\x02\x00\x00\xf0\x10\x02\x05\x02\x00\x00\xf0\x18\x06\x02\x00\x00\xf0\x18\x07\x02\x00\x00\xf0\x18\x08\x02\x00\x00\xf0\x10\x01\t\x02\x00\x00\xf0\x10\x01\x0b\x02\x00\x00\xf0\x18\x0c\x02\x00\x00\xf0\x18\r\x02\x00\x00\xf0\x18\x00\x00\x00\x06\r\x00\x02\x00\x00\xf0\x10ZandiRubNose\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x00\x00\xf0\x18\x02\x02\x00\x00\xf0\x10\x02\x03\x02\x00\x00\xf0\x18\x04\x02\x00\x00\xf0\x10\x02\x05\x02\x00\x00\xf0\x18\x06\x02\x00\x00\xf0\x18\x07\x02\x00\x00\xf0\x18\x08\x02\x00\x00\xf0\x10\x01\t\x02\x00\x00\xf0\x10\x01\x0b\x02\x00\x00\xf0\x18\x0c\x02\x00\x00\xf0\x18\r\x02\x00\x00\xf0\x18\x00\x00\x00\x06\r\x00\x02\x00\x00\xf0\x10ZandiTurnPage\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x00\x00\xf0\x18\x02\x02\x00\x00\xf0\x10\x02\x03\x02\x00\x00\xf0\x18\x04\x02\x00\x00\xf0\x10\x02\x05\x02\x00\x00\xf0\x18\x06\x02\x00\x00\xf0\x18\x07\x02\x00\x00\xf0\x18\x08\x02\x00\x00\xf0\x18\t\x02\x00\x00\xf0\x18\x0b\x02\x00\x00\xf0\x18\x0c\x02\x00\x00\xf0\x18\r\x02\x00\x00\xf0\x18\x00\x02\x00\x00\xf0\x00\x00\x00\x00\x00\x00\x02\x00\x00\xf0\x00\x00\x00\x00\x00\x00"

AVATAR_PHYSICAL_V1_HEADER = sdl.SDLStreamHeader(b"avatarPhysical", 1)

AVATAR_PHYSICAL_V1_TEST_RECORD = sdl.GuessedSDLRecord(
	flags=sdl.SDLRecordBase.Flags.volatile,
	simple_values_indices=False,
	simple_values={
		# POINT3 position[1]
		0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x30), data=b"\x16\xdc\xeaC!\xf2E\xc2\x8d\x8e\xad?"),
		# FLOAT rotation[1]
		1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x30), data=b"\xf3f\xdf>"),
		# PLKEY subworld[1]
		2: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x38), data=b""),
	},
	nested_sdl_values_indices=True,
	nested_sdl_values={},
)
AVATAR_PHYSICAL_V1_TEST_DATA = b"\x00\x80\x0e\xf0\x9e\x89\x9e\x8b\x9e\x8d\xaf\x97\x86\x8c\x96\x9c\x9e\x93\x01\x00\x01\x00\x06\x03\x02\x00\x00\xf00\x16\xdc\xeaC!\xf2E\xc2\x8d\x8e\xad?\x02\x00\x00\xf00\xf3f\xdf>\x02\x00\x00\xf08\x00"

CLOTHING_V4_HEADER = sdl.SDLStreamHeader(b"clothing", 4)

CLOTHING_V4_FEMALE_DEFAULT_RECORD = sdl.GuessedSDLRecord(
	flags=sdl.SDLRecordBase.Flags.volatile,
	simple_values={
		# PLKEY linkInAnim[1]
		0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x38), data=b""),
	},
	nested_sdl_values={
		# $clothingItem VERSION 3 wardrobe[]
		0: sdl.GuessedNestedSDLVariableValue(hint=b"", variable_array_length=8, values={
			0: sdl.GuessedSDLRecord(
				simple_values={
					# PLKEY item[1]
					0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x00\x03\x00\x05\xff\x04\x00\xb5\x00\r\x00\x00\x00\n\xf0\xbc\xb6\x8b\x92\xa0\xb9\xb9\x9e\x9c\x9a"),
					# RGB8 tint[1]
					1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x7fL3"),
					# RGB8 tint2[1]
					2: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\xff\xff\xff"),
				},
				nested_sdl_values_indices=True,
				nested_sdl_values={},
			),
			1: sdl.GuessedSDLRecord(
				simple_values={
					# PLKEY item[1]
					0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x00\x03\x00\x05\xff\x04\x00\xb5\x00\x10\x00\x00\x00\x12\xf0\xbc\xb6\x8b\x92\xa0\xcf\xce\xa0\xb9\xb3\x9a\x98\x8c\xcf\xce\xa0\xcf\xce"),
					# RGB8 tint[1]
					1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"`s\xb0"),
					# RGB8 tint2[1]
					2: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x00\x00\x00"),
				},
				nested_sdl_values_indices=True,
				nested_sdl_values={},
			),
			2: sdl.GuessedSDLRecord(
				simple_values={
					# PLKEY item[1]
					0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x00\x05\x00\x05\xff\x04\x00\xb5\x00(\x00\x00\x00\x13\xf0\xbc\xb6\x8b\x92\xa0\xcf\xcd\xa0\xb9\xab\x90\x8d\x8c\x90\xce\xcd\xa0\xcf\xce"),
					# RGB8 tint[1]
					1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"a\x89\xb3"),
					# RGB8 tint2[1]
					2: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\xff\xff\xff"),
				},
				nested_sdl_values_indices=True,
				nested_sdl_values={},
			),
			3: sdl.GuessedSDLRecord(
				simple_values={
					# PLKEY item[1]
					0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x00\x03\x00\x05\xff\x04\x00\xb5\x00\x13\x00\x00\x00\x13\xf0\xbc\xb6\x8b\x92\xa0\xcf\xce\xa0\xb9\xb3\xb7\x9e\x91\x9b\xcf\xce\xa0\xcf\xce"),
					# RGB8 tint[1]
					1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\xff\xff\xff"),
					# RGB8 tint2[1]
					2: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\xff\xff\xff"),
				},
				nested_sdl_values_indices=True,
				nested_sdl_values={},
			),
			4: sdl.GuessedSDLRecord(
				simple_values={
					# PLKEY item[1]
					0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x00\x03\x00\x05\xff\x04\x00\xb5\x00\x12\x00\x00\x00\x13\xf0\xbc\xb6\x8b\x92\xa0\xcf\xce\xa0\xb9\xad\xb7\x9e\x91\x9b\xcf\xce\xa0\xcf\xce"),
					# RGB8 tint[1]
					1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\xff\xff\xff"),
					# RGB8 tint2[1]
					2: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\xff\xff\xff"),
				},
				nested_sdl_values_indices=True,
				nested_sdl_values={},
			),
			5: sdl.GuessedSDLRecord(
				simple_values={
					# PLKEY item[1]
					0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x00\x05\x00\x05\xff\x04\x00\xb5\x00\t\x00\x00\x00\x12\xf0\xbc\xb6\x8b\x92\xa0\xcf\xcd\xa0\xb9\xb7\x9e\x96\x8d\xcf\xcc\xa0\xcf\xce"),
					# RGB8 tint[1]
					1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x7fL3"),
					# RGB8 tint2[1]
					2: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\xff\xff\xff"),
				},
				nested_sdl_values_indices=True,
				nested_sdl_values={},
			),
			6: sdl.GuessedSDLRecord(
				simple_values={
					# PLKEY item[1]
					0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x00\x05\x00\x05\xff\x04\x00\xb5\x00!\x00\x00\x00\x13\xf0\xbc\xb6\x8b\x92\xa0\xcf\xcd\xa0\xb9\xb3\xb9\x90\x90\x8b\xcf\xcc\xa0\xcf\xce"),
					# RGB8 tint[1]
					1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\xff\xff\xff"),
					# RGB8 tint2[1]
					2: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\xff\xff\xff"),
				},
				nested_sdl_values_indices=True,
				nested_sdl_values={},
			),
			7: sdl.GuessedSDLRecord(
				simple_values={
					# PLKEY item[1]
					0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x00\x05\x00\x05\xff\x04\x00\xb5\x00#\x00\x00\x00\x13\xf0\xbc\xb6\x8b\x92\xa0\xcf\xcd\xa0\xb9\xad\xb9\x90\x90\x8b\xcf\xcc\xa0\xcf\xce"),
					# RGB8 tint[1]
					1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\xff\xff\xff"),
					# RGB8 tint2[1]
					2: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\xff\xff\xff"),
				},
				nested_sdl_values={},
			),
		}),
		# appearanceOptions VERSION 2 appearance[1]
		1: sdl.GuessedNestedSDLVariableValue(hint=b"", values={
			0: sdl.GuessedSDLRecord(
				simple_values={
					# RGB8 skinTint[1]
					0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\xff\xd6\xb5"),
					# BYTE faceBlends[]
					1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00"),
				},
				nested_sdl_values_indices=True,
				nested_sdl_values={},
			),
		}),
	},
)
CLOTHING_V4_FEMALE_DEFAULT_DATA = b"\x00\x80\x08\xf0\x9c\x93\x90\x8b\x97\x96\x91\x98\x04\x00\x01\x00\x06\x01\x02\x00\x00\xf08\x02\x02\x00\x00\xf0\x00\x08\x00\x00\x00\x08\x00\x00\x06\x03\x02\x00\x00\xf0\x10\x00\x03\x00\x05\xff\x04\x00\xb5\x00\r\x00\x00\x00\n\xf0\xbc\xb6\x8b\x92\xa0\xb9\xb9\x9e\x9c\x9a\x02\x00\x00\xf0\x10\x7fL3\x02\x00\x00\xf0\x10\xff\xff\xff\x00\x00\x00\x06\x03\x02\x00\x00\xf0\x10\x00\x03\x00\x05\xff\x04\x00\xb5\x00\x10\x00\x00\x00\x12\xf0\xbc\xb6\x8b\x92\xa0\xcf\xce\xa0\xb9\xb3\x9a\x98\x8c\xcf\xce\xa0\xcf\xce\x02\x00\x00\xf0\x10`s\xb0\x02\x00\x00\xf0\x10\x00\x00\x00\x00\x00\x00\x06\x03\x02\x00\x00\xf0\x10\x00\x05\x00\x05\xff\x04\x00\xb5\x00(\x00\x00\x00\x13\xf0\xbc\xb6\x8b\x92\xa0\xcf\xcd\xa0\xb9\xab\x90\x8d\x8c\x90\xce\xcd\xa0\xcf\xce\x02\x00\x00\xf0\x10a\x89\xb3\x02\x00\x00\xf0\x10\xff\xff\xff\x00\x00\x00\x06\x03\x02\x00\x00\xf0\x10\x00\x03\x00\x05\xff\x04\x00\xb5\x00\x13\x00\x00\x00\x13\xf0\xbc\xb6\x8b\x92\xa0\xcf\xce\xa0\xb9\xb3\xb7\x9e\x91\x9b\xcf\xce\xa0\xcf\xce\x02\x00\x00\xf0\x10\xff\xff\xff\x02\x00\x00\xf0\x10\xff\xff\xff\x00\x00\x00\x06\x03\x02\x00\x00\xf0\x10\x00\x03\x00\x05\xff\x04\x00\xb5\x00\x12\x00\x00\x00\x13\xf0\xbc\xb6\x8b\x92\xa0\xcf\xce\xa0\xb9\xad\xb7\x9e\x91\x9b\xcf\xce\xa0\xcf\xce\x02\x00\x00\xf0\x10\xff\xff\xff\x02\x00\x00\xf0\x10\xff\xff\xff\x00\x00\x00\x06\x03\x02\x00\x00\xf0\x10\x00\x05\x00\x05\xff\x04\x00\xb5\x00\t\x00\x00\x00\x12\xf0\xbc\xb6\x8b\x92\xa0\xcf\xcd\xa0\xb9\xb7\x9e\x96\x8d\xcf\xcc\xa0\xcf\xce\x02\x00\x00\xf0\x10\x7fL3\x02\x00\x00\xf0\x10\xff\xff\xff\x00\x00\x00\x06\x03\x02\x00\x00\xf0\x10\x00\x05\x00\x05\xff\x04\x00\xb5\x00!\x00\x00\x00\x13\xf0\xbc\xb6\x8b\x92\xa0\xcf\xcd\xa0\xb9\xb3\xb9\x90\x90\x8b\xcf\xcc\xa0\xcf\xce\x02\x00\x00\xf0\x10\xff\xff\xff\x02\x00\x00\xf0\x10\xff\xff\xff\x00\x00\x00\x06\x03\x02\x00\x00\xf0\x10\x00\x05\x00\x05\xff\x04\x00\xb5\x00#\x00\x00\x00\x13\xf0\xbc\xb6\x8b\x92\xa0\xcf\xcd\xa0\xb9\xad\xb9\x90\x90\x8b\xcf\xcc\xa0\xcf\xce\x02\x00\x00\xf0\x10\xff\xff\xff\x02\x00\x00\xf0\x10\xff\xff\xff\x00\x02\x00\x00\xf0\x00\x01\x00\x00\x06\x02\x02\x00\x00\xf0\x10\xff\xd6\xb5\x02\x00\x00\xf0\x10\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"

LAYER_V6_HEADER = sdl.SDLStreamHeader(b"Layer", 6)

LAYER_V6_CLEFT_IMAGER_NOISE_RECORD = sdl.GuessedSDLRecord(
	flags=sdl.SDLRecordBase.Flags.volatile,
	simple_values_indices=True,
	simple_values={
		# FLOAT transform[]
		1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x30), data=b"\x10\x00\x00\x00\x00\x00\x80?\x00\x00\x00\x00\x00\x00\x00\x00\xa5Y\x92\xc1\x00\x00\x00\x00\x00\x00\x80?\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80?\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80?"),
	},
	nested_sdl_values_indices=False,
	nested_sdl_values={
		# $AnimTimeConvert VERSION 6 atc[1]
		0: sdl.GuessedNestedSDLVariableValue(hint=b"", values={
			0: sdl.GuessedSDLRecord(
				simple_values_indices=False,
				simple_values={
					# INT flags[1]
					0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\"\x00\x00\x00"),
					# FLOAT lastStateAnimTime[1]
					1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
					# FLOAT loopEnd[1]
					2: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\xab\xaajA"),
					# FLOAT loopBegin[1]
					3: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
					# FLOAT speed[1]
					4: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
					# BYTE currentEaseCurve[1]
					5: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
					# TIME currentEaseBeginWorldTime[1]
					6: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\xe1\x00\xd2eu\xf9\x05\x00"),
					# TIME lastStateChange[1]
					7: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x16\x01\xd2ev\x18\x0b\x00"),
				},
				nested_sdl_values_indices=True,
				nested_sdl_values={},
			),
		}),
	},
)
LAYER_V6_CLEFT_IMAGER_NOISE_DATA = b"\x00\x80\x05\xf0\xb3\x9e\x86\x9a\x8d\x06\x00\x01\x00\x06\x01\x01\x02\x00\x00\xf00\x10\x00\x00\x00\x00\x00\x80?\x00\x00\x00\x00\x00\x00\x00\x00\xa5Y\x92\xc1\x00\x00\x00\x00\x00\x00\x80?\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80?\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80?\x01\x02\x00\x00\xf0\x00\x01\x00\x00\x06\x08\x02\x00\x00\xf0\x10\"\x00\x00\x00\x02\x00\x00\xf0\x18\x02\x00\x00\xf0\x10\xab\xaajA\x02\x00\x00\xf0\x18\x02\x00\x00\xf0\x18\x02\x00\x00\xf0\x18\x02\x00\x00\xf0\x10\xe1\x00\xd2eu\xf9\x05\x00\x02\x00\x00\xf0\x10\x16\x01\xd2ev\x18\x0b\x00\x00"

LAYER_V6_FEMALE_KI_LIGHT_RECORD = sdl.GuessedSDLRecord(
	simple_values_indices=True,
	simple_values={
		# BYTE channelData[]
		2: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x30), data=b"\t\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"),
	},
	nested_sdl_values={
		# $AnimTimeConvert VERSION 6 atc[1]
		0: sdl.GuessedNestedSDLVariableValue(hint=b"", values={
			0: sdl.GuessedSDLRecord(
				simple_values_indices=False,
				simple_values={
					# INT flags[1]
					0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x01\x00\x00\x00"),
					# FLOAT lastStateAnimTime[1]
					1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
					# FLOAT loopEnd[1]
					2: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"ww\xf7?"),
					# FLOAT loopBegin[1]
					3: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
					# FLOAT speed[1]
					4: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
					# BYTE currentEaseCurve[1]
					5: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x18), data=b""),
					# TIME currentEaseBeginWorldTime[1]
					6: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\xe1\x00\xd2eu\xf9\x05\x00"),
					# TIME lastStateChange[1]
					7: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\xe1\x00\xd2eu\xf9\x05\x00"),
				},
				nested_sdl_values_indices=True,
				nested_sdl_values={},
			),
		}),
	},
)
LAYER_V6_FEMALE_KI_LIGHT_DATA = b"\x00\x80\x05\xf0\xb3\x9e\x86\x9a\x8d\x06\x00\x00\x00\x06\x01\x02\x02\x00\x00\xf00\t\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x00\x00\xf0\x00\x01\x00\x00\x06\x08\x02\x00\x00\xf0\x10\x01\x00\x00\x00\x02\x00\x00\xf0\x18\x02\x00\x00\xf0\x10ww\xf7?\x02\x00\x00\xf0\x18\x02\x00\x00\xf0\x18\x02\x00\x00\xf0\x18\x02\x00\x00\xf0\x10\xe1\x00\xd2eu\xf9\x05\x00\x02\x00\x00\xf0\x10\xe1\x00\xd2eu\xf9\x05\x00\x00"

MORPH_SEQUENCE_V2_HEADER = sdl.SDLStreamHeader(b"MorphSequence", 2)

MORPH_SEQUENCE_V2_FEMALE_HIGH_DEFAULT_RECORD = sdl.GuessedSDLRecord(
	flags=sdl.GuessedSDLRecord.Flags.volatile,
	simple_values_indices=True,
	simple_values={},
	nested_sdl_values_indices=False,
	nested_sdl_values={
		# $MorphSet VERSION 2 morphs[]
		0: sdl.GuessedNestedSDLVariableValue(hint=b"", variable_array_length=1, values={
			0: sdl.GuessedSDLRecord(
				simple_values={
					# PLKEY mesh[1]
					0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\x00\x03\x00\x05\xff\x04\x00\xcc\x00\x07\x00\x00\x00\x0b\xf0\xb9\xb7\xb9\x9e\x9c\x9a\xa0\xac\xb2\x8c\x97"),
					# BYTE weights[]
					1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x10), data=b"\t\x00\x00\x00\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f"),
				},
				nested_sdl_values_indices=True,
				nested_sdl_values={},
			),
		}),
	},
)
MORPH_SEQUENCE_V2_FEMALE_HIGH_DEFAULT_DATA = b"\x00\x80\r\xf0\xb2\x90\x8d\x8f\x97\xac\x9a\x8e\x8a\x9a\x91\x9c\x9a\x02\x00\x01\x00\x06\x00\x01\x02\x00\x00\xf0\x00\x01\x00\x00\x00\x01\x00\x00\x06\x02\x02\x00\x00\xf0\x10\x00\x03\x00\x05\xff\x04\x00\xcc\x00\x07\x00\x00\x00\x0b\xf0\xb9\xb7\xb9\x9e\x9c\x9a\xa0\xac\xb2\x8c\x97\x02\x00\x00\xf0\x10\t\x00\x00\x00\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x7f\x00"

PHYSICAL_V2_HEADER = sdl.SDLStreamHeader(b"physical", 2)

PHYSICAL_V2_TEST_RECORD = sdl.GuessedSDLRecord(
	simple_values_indices=True,
	simple_values={
		# POINT3 position[1]
		0: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x30), data=b"\x1c\x88\xc0C\xc8n\x95B\x13\xc83\xc1"),
		# QUATERNION orientation[1]
		1: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x30), data=b"\xa9\xb4\xda\xbeh\xfd\x11?\x99\xb4\x0f?\x8a\x88\xd7\xbe"),
		# VECTOR3 linear[1]
		2: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x30), data=b"\x1c\x94\xe6\xbb\x92\xe0\x06<p\x1d\x98\xbd"),
		# VECTOR3 angular[1]
		3: sdl.GuessedSimpleVariableValue(hint=b"", flags=sdl.SimpleVariableValueBase.Flags(0x30), data=b"9\xefc\xbd\xd8j\xef\xbc\xb6\xbe\x1c\xbb"),
	},
	nested_sdl_values_indices=True,
	nested_sdl_values={},
)
PHYSICAL_V2_TEST_DATA = b"\x00\x80\x08\xf0\x8f\x97\x86\x8c\x96\x9c\x9e\x93\x02\x00\x00\x00\x06\x04\x00\x02\x00\x00\xf00\x1c\x88\xc0C\xc8n\x95B\x13\xc83\xc1\x01\x02\x00\x00\xf00\xa9\xb4\xda\xbeh\xfd\x11?\x99\xb4\x0f?\x8a\x88\xd7\xbe\x02\x02\x00\x00\xf00\x1c\x94\xe6\xbb\x92\xe0\x06<p\x1d\x98\xbd\x03\x02\x00\x00\xf009\xefc\xbd\xd8j\xef\xbc\xb6\xbe\x1c\xbb\x00"

TEST_SDL_STREAM_HEADERS = [
	# Age SDL blobs:
	(b"\x00\x80\x04\xf0\x9c\x96\x8b\x86+\x00", CITY_V43_HEADER),
	(b"\x00\x80\x05\xf0\xbc\x93\x9a\x99\x8b\x18\x00", CLEFT_V24_HEADER),
	(b"\x00\x80\x0c\xf0\xb1\x9a\x96\x98\x97\x9d\x90\x8d\x97\x90\x90\x9b#\x00", NEIGHBORHOOD_V35_HEADER),
	(b"\x00\x80\x08\xf0\xaf\x9a\x8d\x8c\x90\x91\x9e\x93)\x00", PERSONAL_V41_HEADER),
	# Other SDL blobs in the vault:
	(b"\x00\x80\x11\xf0\x9e\x8f\x8f\x9a\x9e\x8d\x9e\x91\x9c\x9a\xb0\x8f\x8b\x96\x90\x91\x8c\x02\x00", APPEARANCE_OPTIONS_V2_HEADER),
	(b"\x00\x80\x0c\xf0\x9c\x93\x90\x8b\x97\x96\x91\x98\xb6\x8b\x9a\x92\x03\x00", CLOTHING_ITEM_V3_HEADER),
	# Core engine SDL blobs attached to objects:
	(b"\x00\x80\x06\xf0\x9e\x89\x9e\x8b\x9e\x8d\x07\x00", AVATAR_V7_HEADER),
	(b"\x00\x80\x0e\xf0\x9e\x89\x9e\x8b\x9e\x8d\xaf\x97\x86\x8c\x96\x9c\x9e\x93\x01\x00", AVATAR_PHYSICAL_V1_HEADER),
	(b"\x00\x80\x08\xf0\x9c\x93\x90\x8b\x97\x96\x91\x98\x04\x00", CLOTHING_V4_HEADER),
	(b"\x00\x80\x05\xf0\xb3\x9e\x86\x9a\x8d\x06\x00", LAYER_V6_HEADER),
	(b"\x00\x80\r\xf0\xb2\x90\x8d\x8f\x97\xac\x9a\x8e\x8a\x9a\x91\x9c\x9a\x02\x00", MORPH_SEQUENCE_V2_HEADER),
	(b"\x00\x80\x08\xf0\x8f\x97\x86\x8c\x96\x9c\x9e\x93\x02\x00", PHYSICAL_V2_HEADER),
]

TEST_SDL_BLOBS = [
	# Age SDL blobs:
	(CITY_V43_DEFAULT_DATA, CITY_V43_HEADER, CITY_V43_DEFAULT_RECORD),
	(CLEFT_V24_DEFAULT_DATA, CLEFT_V24_HEADER, CLEFT_V24_DEFAULT_RECORD),
	(NEIGHBORHOOD_V35_DEFAULT_DATA, NEIGHBORHOOD_V35_HEADER, NEIGHBORHOOD_V35_DEFAULT_RECORD),
	(PERSONAL_V41_DEFAULT_DATA, PERSONAL_V41_HEADER, PERSONAL_V41_DEFAULT_RECORD),
	# Other SDL blobs in the vault:
	(APPEARANCE_OPTIONS_V2_FEMALE_DEFAULT_DATA, APPEARANCE_OPTIONS_V2_HEADER, APPEARANCE_OPTIONS_V2_FEMALE_DEFAULT_RECORD),
	(CLOTHING_ITEM_V3_FEMALE_FACE_DEFAULT_DATA, CLOTHING_ITEM_V3_HEADER, CLOTHING_ITEM_V3_FEMALE_FACE_DEFAULT_RECORD),
	# Core engine SDL blobs attached to objects:
	(AVATAR_V7_FEMALE_WAVE_DATA, AVATAR_V7_HEADER, AVATAR_V7_FEMALE_WAVE_RECORD),
	(AVATAR_V7_ZANDI_DATA, AVATAR_V7_HEADER, AVATAR_V7_ZANDI_RECORD),
	(AVATAR_PHYSICAL_V1_TEST_DATA, AVATAR_PHYSICAL_V1_HEADER, AVATAR_PHYSICAL_V1_TEST_RECORD),
	(CLOTHING_V4_FEMALE_DEFAULT_DATA, CLOTHING_V4_HEADER, CLOTHING_V4_FEMALE_DEFAULT_RECORD),
	(LAYER_V6_CLEFT_IMAGER_NOISE_DATA, LAYER_V6_HEADER, LAYER_V6_CLEFT_IMAGER_NOISE_RECORD),
	(LAYER_V6_FEMALE_KI_LIGHT_DATA, LAYER_V6_HEADER, LAYER_V6_FEMALE_KI_LIGHT_RECORD),
	(MORPH_SEQUENCE_V2_FEMALE_HIGH_DEFAULT_DATA, MORPH_SEQUENCE_V2_HEADER, MORPH_SEQUENCE_V2_FEMALE_HIGH_DEFAULT_RECORD),
	(PHYSICAL_V2_TEST_DATA, PHYSICAL_V2_HEADER, PHYSICAL_V2_TEST_RECORD),
]


class SDLStreamHeaderTest(unittest.TestCase):
	def test_read_sdl_stream_header(self) -> None:
		for data, header in TEST_SDL_STREAM_HEADERS:
			with self.subTest(header=header):
				with io.BytesIO(data) as stream:
					self.assertEqual(sdl.SDLStreamHeader.from_stream(stream), header)
	
	def test_write_sdl_stream_header(self) -> None:
		for data, header in TEST_SDL_STREAM_HEADERS:
			with self.subTest(header=header):
				with io.BytesIO() as stream:
					header.write(stream)
					self.assertEqual(stream.getvalue(), data)


class GuessedSimpleVariableValueTest(unittest.TestCase):
	def test_eq_copy(self) -> None:
		for _, header, record in TEST_SDL_BLOBS:
			with self.subTest(header=header):
				for var in record.simple_values.values():
					copy = var.copy()
					self.assertIsNot(copy, var)
					self.assertEqual(copy, var)


class GuessedNestedSDLVariableValueTest(unittest.TestCase):
	def test_eq_copy(self) -> None:
		for _, header, record in TEST_SDL_BLOBS:
			with self.subTest(header=header):
				for i, var in record.nested_sdl_values.items():
					copy = var.copy()
					self.assertIsNot(copy, var)
					self.assertEqual(copy, var)


class GuessedSDLRecordTest(unittest.TestCase):
	def test_read_sdl_record(self) -> None:
		for data, header, record in TEST_SDL_BLOBS:
			with self.subTest(header=header):
				with io.BytesIO(data) as stream:
					parsed_header, parsed_record = sdl.guess_parse_sdl_blob(stream)
					self.assertEqual(parsed_header, header)
					self.assertEqual(parsed_record, record)
	
	def test_write_sdl_record(self) -> None:
		for data, header, record in TEST_SDL_BLOBS:
			with self.subTest(header=header):
				with io.BytesIO() as stream:
					header.write(stream)
					record.write(stream)
					self.assertEqual(stream.getvalue(), data)
	
	def test_eq_copy(self) -> None:
		for _, header, record in TEST_SDL_BLOBS:
			with self.subTest(header=header):
				copy = record.copy()
				self.assertIsNot(copy, record)
				self.assertEqual(copy, record)


if __name__ == "__main__":
	unittest.main()
