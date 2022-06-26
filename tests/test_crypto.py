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


# The SHA-0 test hashes are stolen from DIRTSAND's tests.
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
	(b"hunter2", "f3bbbd66a63d4bf1747940578ec3d0103530e21d")
]
BYTE_SWAP_TEST_HASHES = [
	("da39a3ee5e6b4b0d3255bfef95601890afd80709", "eea339da0d4b6b5eefbf5532901860950907d8af"),
	("a9993e364706816aba3e25717850c26c9cd0d89d", "363e99a96a81064771253eba6cc250789dd8d09c"),
	("f3bbbd66a63d4bf1747940578ec3d0103530e21d", "66bdbbf3f14b3da65740797410d0c38e1de23035"),
]
BYTE_SWAPPED_SHA_1_TEST_HASHES = [
	(b"", "eea339da0d4b6b5eefbf5532901860950907d8af"),
	(b"abc", "363e99a96a81064771253eba6cc250789dd8d09c"),
	(b"hunter2", "66bdbbf3f14b3da65740797410d0c38e1de23035"),
]
SHA_0_PASSWORD_TEST_HASHES = [
	("AzureDiamond", "", "b7e516f93d18cdc186aa269d34e2a8702c41f3ae"),
	("AzureDiamond", "hunter2", "8598c0ad2f51fb1605c7433654baca9bdc589212"),
	("AzureDiamond@example.com", "", "803305d66ba54db37424794b341fb32795ff5223"),
	("AzureDiamond@example.com", "hunter2", "0ee474a4a95caf724b52e4931434108176860b25"),
]
CHALLENGE_TEST_HASHES = [
	(0, 0, "eea339da0d4b6b5eefbf5532901860950907d8af", "78e1389e938b12d4c8e97bb3b3eb4b1e2b40cc85"),
	(0, 0, "803305d66ba54db37424794b341fb32795ff5223", "afc6922c6c837f7204b9b0f905456d29d341104f"),
	(0, 0, "66bdbbf3f14b3da65740797410d0c38e1de23035", "475df2fc21a36ede01bf381ea10a5a8121a11c81"),
	(0, 0, "0ee474a4a95caf724b52e4931434108176860b25", "72650da5e84e37994acd3e07da5658915bf588fe"),
	(0xbd6683e0, 0xdeadbeef, "eea339da0d4b6b5eefbf5532901860950907d8af", "81c6a159c836c8c00668924ebde2b400b9fe0875"),
	(0x2af74e54, 0xdeadbeef, "803305d66ba54db37424794b341fb32795ff5223", "2a6ab7af77955cf801044a9cc85adb52c068fbc1"),
	(0xfceff512, 0xdeadbeef, "66bdbbf3f14b3da65740797410d0c38e1de23035", "e386750a474f85840681fa8f97cec02bcf84238b"),
	(0x5d94ee7c, 0xdeadbeef, "0ee474a4a95caf724b52e4931434108176860b25", "70f281bfb415c4753c4c18b29f27dd089bafe0bd"),
	(0xc5e1d167, 0x441d9a53, "eea339da0d4b6b5eefbf5532901860950907d8af", "1d645398de2d0ce89c9aa23d0ed376616e5df4eb"),
	(0x8fb97218, 0x441d9a53, "803305d66ba54db37424794b341fb32795ff5223", "3552c2ec040aee2bc5ba269fede109628f8c3a5e"),
	(0xfc46f7a9, 0x441d9a53, "66bdbbf3f14b3da65740797410d0c38e1de23035", "a579c026624cfd60530c87f6f57d56586ce36cb4"),
	(0xf5d41122, 0x441d9a53, "0ee474a4a95caf724b52e4931434108176860b25", "e52ddb60b73319815f801044b91cdcbb933343e8"),
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
	
	def test_byte_swap(self) -> None:
		for hex_hash, hex_hash_swapped in BYTE_SWAP_TEST_HASHES:
			with self.subTest(hash=hex_hash, hsah=hex_hash_swapped):
				self.assertEqual(crypto.byte_swap_hash(bytes.fromhex(hex_hash)), bytes.fromhex(hex_hash_swapped))
				self.assertEqual(crypto.byte_swap_hash(bytes.fromhex(hex_hash_swapped)), bytes.fromhex(hex_hash))
	
	def test_byte_swapped_sha_1(self) -> None:
		for data, hex_hash in BYTE_SWAPPED_SHA_1_TEST_HASHES:
			with self.subTest(data=data, hash=hex_hash):
				self.assertEqual(crypto.byte_swapped_sha_1(data), bytes.fromhex(hex_hash))
	
	def test_password_sha_0(self) -> None:
		for account_name, password, hex_hash in SHA_0_PASSWORD_TEST_HASHES:
			with self.subTest(account_name=account_name, password=password, hash=hex_hash):
				self.assertEqual(crypto.password_hash_sha_0(account_name, password), bytes.fromhex(hex_hash))
	
	def test_challenge(self) -> None:
		for client_challenge, server_challenge, password_hash, hex_hash in CHALLENGE_TEST_HASHES:
			with self.subTest(client_challenge=client_challenge, server_challenge=server_challenge, password_hash=password_hash, hash=hex_hash):
				self.assertEqual(crypto.challenge_hash(client_challenge, server_challenge, bytes.fromhex(password_hash)), bytes.fromhex(hex_hash))


if __name__ == "__main__":
	unittest.main()
