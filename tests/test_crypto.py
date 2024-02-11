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


SHA_0_TEST_HASHES = [
	# Stolen from DIRTSAND's test code:
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
	# Stolen from the H'uru Plasma tests:
	(b"Hello World", "45d579c3582a30e6ec0cc15e7ebd586838b0f7fb"),
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
SHA_1_PASSWORD_TEST_HASHES = [
	("", "ascii", "eea339da0d4b6b5eefbf5532901860950907d8af"),
	("abc", "ascii", "363e99a96a81064771253eba6cc250789dd8d09c"),
	("hunter2", "ascii", "66bdbbf3f14b3da65740797410d0c38e1de23035"),
	("correct horse battery staple", "ascii", "b573145737d1d3c92e707801a017edff0d260ded"),
	("correct horse b", "ascii", "b573145737d1d3c92e707801a017edff0d260ded"),
	("pässwörd", "cp1252", "1d488c79086cc08e96b05e9110c2f939bfa41f13"),
	("pässwörd", "utf-8", "f1dd17f52f112ad3c655adf1cb121b6df7e8e738"),
]
SHA_0_PASSWORD_TEST_HASHES = [
	("AzureDiamond", "", "b7e516f93d18cdc186aa269d34e2a8702c41f3ae"),
	("AzureDiamond", "hunter2", "8598c0ad2f51fb1605c7433654baca9bdc589212"),
	("AzureDiamond@example.com", "", "803305d66ba54db37424794b341fb32795ff5223"),
	("AzureDiamond@example.com", "hunter2", "0ee474a4a95caf724b52e4931434108176860b25"),
	("longassaccountnamegoingpastthelimitof63utf16codeunits@example.com", "correct horse battery staple", "e48b7292626f71ee9398b72025031cce4b178fa9"),
	("longassaccountnamegoingpastthelimitof63utf16codeunits@example.c", "correct horse b", "e48b7292626f71ee9398b72025031cce4b178fa9"),
	("ünicöde@example.com", "pässwörd", "469f82acd0b514293cfd31c19f7703000b36eca2"),
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
	(0x96993700, 0xdeadbeef, "e48b7292626f71ee9398b72025031cce4b178fa9", "1a503639541a29bc709dacbcf8588369d0da6db3"),
	(0x3a41474b, 0xdeadbeef, "469f82acd0b514293cfd31c19f7703000b36eca2", "f929aeed5d5a9390452b9f8b8c344b1a37c465c5"),
	(0xb30d7f53, 0xdeadbeef, "469f82acd0b514293cfd31c19f7703000b36eca2", "d9930d4f26a2e58da91df760243a94a101950d30"),
]

RC4_TEST_DATA = [
	# Stolen from Wikipedia:
	# https://en.wikipedia.org/wiki/RC4#Test_vectors
	(b"Key", b"Plaintext", b"\xbb\xf3\x16\xe8\xd9@\xaf\n\xd3"),
	(b"Wiki", b"pedia", b"\x10!\xbf\x04 "),
	(b"Secret", b"Attack at dawn", b"E\xa0\x1fd_\xc3[85RTK\x9b\xf5"),
]


class ShaTest(unittest.TestCase):
	def test_sha_0(self) -> None:
		for data, hex_hash in SHA_0_TEST_HASHES:
			with self.subTest(data=data, hash=hex_hash):
				self.assertEqual(crypto.slow_sha_0(data), bytes.fromhex(hex_hash))
	
	@unittest.skip("slow") # Takes about 2.7 sec on an AMD Ryzen 5 3400G.
	def test_sha_0_long(self) -> None:
		# Stolen from the H'uru Plasma tests.
		self.assertEqual(
			crypto.slow_sha_0(b"a" * 1000000),
			bytes.fromhex("3232affa48628a26653b5aaa44541fd90d690603"),
		)
	
	@unittest.skip("extremely slow") # Would take about 48 minutes, based on the above time.
	def test_sha_0_very_long(self) -> None:
		# Stolen from the H'uru Plasma tests.
		self.assertEqual(
			crypto.slow_sha_0(b"abcdefghbcdefghicdefghijdefghijkefghijklfghijklmghijklmnhijklmno" * 16777216),
			bytes.fromhex("bd18f2e7736c8e6de8b5abdfdeab948f5171210c"),
		)
	
	def test_sha_1(self) -> None:
		for data, hex_hash in SHA_1_TEST_HASHES:
			with self.subTest(data=data, hash=hex_hash):
				self.assertEqual(crypto.slow_sha_1(data), bytes.fromhex(hex_hash))
				self.assertEqual(hashlib.sha1(data).hexdigest(), hex_hash)
	
	@unittest.skip("slow") # Takes about 3.0 sec on an AMD Ryzen 5 3400G.
	def test_sha_1_long(self) -> None:
		# Stolen from the H'uru Plasma tests.
		self.assertEqual(
			crypto.slow_sha_1(b"a" * 1000000),
			bytes.fromhex("34aa973cd4c4daa4f61eeb2bdbad27316534016f"),
		)
	
	@unittest.skip("extremely slow") # Would take about 54 minutes, based on the above time.
	def test_sha_1_very_long(self) -> None:
		# Stolen from the H'uru Plasma tests.
		self.assertEqual(
			crypto.slow_sha_1(b"abcdefghbcdefghicdefghijdefghijkefghijklfghijklmghijklmnhijklmno" * 16777216),
			bytes.fromhex("7789f0c9ef7bfc40d93311143dfbe69e2017f592"),
		)
	
	def test_byte_swap(self) -> None:
		for hex_hash, hex_hash_swapped in BYTE_SWAP_TEST_HASHES:
			with self.subTest(hash=hex_hash, hsah=hex_hash_swapped):
				self.assertEqual(crypto.byte_swap_hash(bytes.fromhex(hex_hash)), bytes.fromhex(hex_hash_swapped))
				self.assertEqual(crypto.byte_swap_hash(bytes.fromhex(hex_hash_swapped)), bytes.fromhex(hex_hash))
	
	def test_password_sha_1(self) -> None:
		for password, encoding, hex_hash in SHA_1_PASSWORD_TEST_HASHES:
			with self.subTest(password=password, encoding=encoding, hash=hex_hash):
				self.assertEqual(crypto.password_hash_sha_1(password, encoding=encoding), bytes.fromhex(hex_hash))
	
	def test_password_sha_0(self) -> None:
		for account_name, password, hex_hash in SHA_0_PASSWORD_TEST_HASHES:
			with self.subTest(account_name=account_name, password=password, hash=hex_hash):
				self.assertEqual(crypto.password_hash_sha_0(account_name, password), bytes.fromhex(hex_hash))
	
	def test_challenge(self) -> None:
		for client_challenge, server_challenge, password_hash, hex_hash in CHALLENGE_TEST_HASHES:
			with self.subTest(client_challenge=client_challenge, server_challenge=server_challenge, password_hash=password_hash, hash=hex_hash):
				self.assertEqual(crypto.challenge_hash(client_challenge, server_challenge, bytes.fromhex(password_hash)), bytes.fromhex(hex_hash))


class Rc4Test(unittest.TestCase):
	def test_rc4_batch(self) -> None:
		for key, plaintext, ciphertext in RC4_TEST_DATA:
			with self.subTest(key=key, plaintext=plaintext):
				state_encrypt = crypto.Rc4State(key)
				state_decrypt = crypto.Rc4State(key)
				self.assertEqual(state_encrypt.crypt(plaintext), ciphertext)
				self.assertEqual(state_decrypt.crypt(ciphertext), plaintext)
	
	def test_rc4_bytewise(self) -> None:
		for key, plaintext, ciphertext in RC4_TEST_DATA:
			with self.subTest(key=key, plaintext=plaintext):
				state_encrypt = crypto.Rc4State(key)
				state_decrypt = crypto.Rc4State(key)
				for p, c in zip(plaintext, ciphertext):
					self.assertEqual(state_encrypt.crypt(bytes([p])), bytes([c]))
					self.assertEqual(state_decrypt.crypt(bytes([c])), bytes([p]))


if __name__ == "__main__":
	unittest.main()
