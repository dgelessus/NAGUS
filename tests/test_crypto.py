# This file is part of NAGUS, an Uru Live server that is not very good.
# Copyright (C) 2022 dgelessus
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


import hashlib
import unittest

from nagus import crypto


# Test hashes stolen from DIRTSAND
SHA_0_TEST_HASHES = [
	(b"", "f96cea198ad1dd5617ac084a3d92c6107708c0ef"),
	(b"a", "37f297772fae4cb1ba39b6cf9cf0381180bd62f2"),
	(b"abc", "0164b8a914cd2a5e74c4f7ff082c4d97f1edf880"),
	(
		b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq",
		"d2516ee1acfa5baf33dfc1c471e438449ef134c8",
	),
	(
		(
			b"abcdefghbcdefghicdefghijdefghijkefghijklfghijklmghijklmn"
			b"hijklmnoijklmnopjklmnopqklmnopqrlmnopqrsmnopqrstnopqrstu"
		),
		"459f83b95db2dc87bb0f5b513a28f900ede83237",
	),
]
SHA_1_TEST_HASHES = [
	(b"", "da39a3ee5e6b4b0d3255bfef95601890afd80709"),
	(b"abc", "a9993e364706816aba3e25717850c26c9cd0d89d"),
]
BYTE_SWAPPED_SHA_1_TEST_HASHES = [
	(b"", "eea339da0d4b6b5eefbf5532901860950907d8af"),
	(b"abc", "363e99a96a81064771253eba6cc250789dd8d09c"),
]


class ShaTest(unittest.TestCase):
	def test_sha_0(self) -> None:
		for data, hex_hash in SHA_0_TEST_HASHES:
			with self.subTest(data=data, hash=hex_hash):
				self.assertEqual(crypto.slow_sha_0(data), bytes.fromhex(hex_hash))
	
	def test_sha_1(self) -> None:
		for data, hex_hash in SHA_1_TEST_HASHES:
			with self.subTest(data=data, hash=hex_hash):
				self.assertEqual(crypto.slow_sha_1(data), bytes.fromhex(hex_hash))
				self.assertEqual(hashlib.sha1(data).hexdigest(), hex_hash)
	
	def test_byte_swapped_sha_1(self) -> None:
		for data, hex_hash in BYTE_SWAPPED_SHA_1_TEST_HASHES:
			with self.subTest(data=data, hash=hex_hash):
				self.assertEqual(crypto.byte_swapped_sha_1(data), bytes.fromhex(hex_hash))


if __name__ == "__main__":
	unittest.main()
