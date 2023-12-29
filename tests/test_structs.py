# This file is part of NAGUS, an Uru Live server that is not very good.
# Copyright (C) 2023 dgelessus
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


import unittest

from nagus import structs


TEST_SEQUENCE_NUMBERS = [
	# GlobalAvatars
	(0xff060002, (-6, 1)), # Male
	(0xff060003, (-6, 2)), # Female
	(0xff060004, (-6, 3)), # Audio
	# GlobalMarkers
	(0xff040002, (-4, 1)), # Markers
	# GlobalAnimations
	(0xff010002, (-1, 1)), # MaleSitStand
	(0xff010032, (-1, 49)), # FemaleSitStand
	(0xff010063, (-1, 98)), # MaleAFKEnter
	(0xff010066, (-1, 101)), # FemaleAFKEnter
	(0xff010113, (-1, 274)), # FemaleThumbsUp
	(0xff010115, (-1, 276)), # MaleThumbsUp
	(0xff0101b4, (-1, 435)), # FemaleSwimDockExit
	(0xff0101e3, (-1, 482)), # MaleSwimDockExit
	# Garden
	(0x10022, (1, 1)), # trailerCamPage
	(0x10024, (1, 3)), # ItinerantBugCloud
	(0x10025, (1, 4)), # kemoGarden
	(0x10026, (1, 5)), # kemoStorm
	(0x2001f, (1, 0xfffe)), # BuiltIn
	(0x20020, (1, 0xffff)), # Textures
	# Personal
	(0xd0022, (13, 1)), # psnlMYSTII
	(0xd0023, (13, 2)), # psnlFanYeeshaPages01
	(0xd0024, (13, 3)), # trailerCamPage
	(0xe001f, (13, 0xfffe)), # BuiltIn
	(0xe0020, (13, 0xffff)), # Textures
	# StartUp
	(0xf0022, (15, 1)), # GUIDialog04c
	# philRelto
	(0x320022, (50, 1)), # PhilsRelto
	(0x33001f, (50, 0xfffe)), # BuiltIn
	(0x330020, (50, 0xffff)), # Textures
	# GoMePubNew
	(0x4d20022, (1234, 1)), # StoreRoom
	(0x4d20023, (1234, 2)), # GoMePub
	(0x4d20024, (1234, 3)), # Alcoves
	(0x4d20025, (1234, 4)), # GoMeConfRoom
	(0x4d20026, (1234, 5)), # Entry
	(0x4d20027, (1234, 6)), # Holidays
	(0x4d20028, (1234, 7)), # gmpnCones
	(0x4d20029, (1234, 8)), # Mysterium
	(0x4d3001f, (1234, 0xfffe)), # BuiltIn
	(0x4d30020, (1234, 0xffff)), # Textures
	# FahetsHighgarden
	(0x28ce0021, (10446, 0)), # Default
	(0x28cf001f, (10446, 0xfffe)), # BuiltIn
	(0x28cf0020, (10446, 0xffff)), # Textures
	# VeeTsah
	(0x9c440022, (40004, 1)), # Temple
	(0x9c45001f, (40004, 0xfffe)), # BuiltIn
	(0x9c450020, (40004, 0xffff)), # Textures
]

SPECIAL_TEST_SEQUENCE_NUMBERS = [
	0,
	1,
	2,
	3,
	31,
	32,
	0xff000000,
	0xff000001,
	0xff00ffff,
	0xff010000,
	0xffffffff,
]


class SequenceNumberTest(unittest.TestCase):
	def test_split_sequence_number(self) -> None:
		for seqnum, (age, page) in TEST_SEQUENCE_NUMBERS:
			with self.subTest(seqnum=f"0x{seqnum:08x}", age=age, page=page):
				self.assertEqual(structs.split_sequence_number(seqnum), (age, page))
	
	def test_split_special_sequence_number(self) -> None:
		for seqnum in SPECIAL_TEST_SEQUENCE_NUMBERS:
			with self.subTest(seqnum=f"0x{seqnum:08x}"):
				with self.assertRaises(ValueError):
					structs.split_sequence_number(seqnum)
	
	def test_make_sequence_number(self) -> None:
		for seqnum, (age, page) in TEST_SEQUENCE_NUMBERS:
			with self.subTest(seqnum=f"0x{seqnum:08x}", age=age, page=page):
				self.assertEqual(structs.make_sequence_number(age, page), seqnum)


if __name__ == "__main__":
	unittest.main()
