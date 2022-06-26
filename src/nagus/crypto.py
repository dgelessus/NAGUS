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


"""Various hash functions and encryption methods.

These are too old, custom, or non-cryptographic to be included in the standard library,
so we have to implement them by hand ourselves.
"""


import array
import hashlib
import struct
import typing


SHA_0_1_CHUNK = struct.Struct(">16I")
SHA_0_1_MESSAGE_LENGTH = struct.Struct(">Q")
SHA_0_1_HASH = struct.Struct(">5I")

CHALLENGE_HASH_DATA = struct.Struct("<II20s")


def _slow_sha_0_1(data: bytes, *, sha_1: bool) -> bytes:
	"""Slow pure Python implementation of SHA-0 and SHA-1.
	
	We really only care about SHA-0,
	because SHA-1 is also provided by Python's :mod:`hashlib`.
	SHA-0 and SHA-1 are extremely similar though,
	so it's easy to implement both at once,
	and it allows testing our implementation against :func:`hashlib.sha1`.
	"""
	
	# Based on https://en.wikipedia.org/wiki/SHA-1#SHA-1_pseudocode
	
	h0 = 0x67452301
	h1 = 0xefcdab89
	h2 = 0x98badcfe
	h3 = 0x10325476
	h4 = 0xc3d2e1f0
	
	# Save original message length in bits.
	orig_message_length = len(data) * 8
	# Append a 1 bit.
	data += b"\x80"
	# Pad data with zero bytes so that it will be a multiple of 64 bytes long once we add the 8-byte message length.
	pad_count = (SHA_0_1_CHUNK.size - (len(data) + SHA_0_1_MESSAGE_LENGTH.size)) % SHA_0_1_CHUNK.size
	# Add message length suffix.
	data += bytes(pad_count) + SHA_0_1_MESSAGE_LENGTH.pack(orig_message_length)
	
	for offset in range(0, len(data), SHA_0_1_CHUNK.size):
		w: typing.List[int] = []
		# Parse each chunk into 16 32-byte integers.
		w += SHA_0_1_CHUNK.unpack_from(data, offset)
		for i in range(16, 80):
			x = w[i-3] ^ w[i-8] ^ w[i-14] ^ w[i-16]
			if sha_1:
				x = x << 1 & 0xffffffff | x >> 31
			w.append(x)
		
		a = h0
		b = h1
		c = h2
		d = h3
		e = h4
		
		# SHA magic!
		
		for i in range(0, 20):
			a, b, c, d, e = (
				((a << 5 & 0xffffffff | a >> 27) + (b & c | (~b & 0xffffffff) & d) + e + 0x5a827999 + w[i]) & 0xffffffff,
				a,
				b << 30 & 0xffffffff | b >> 2,
				c,
				d,
			)
		
		for i in range(20, 40):
			a, b, c, d, e = (
				((a << 5 & 0xffffffff | a >> 27) + (b ^ c ^ d) + e + 0x6ed9eba1 + w[i]) & 0xffffffff,
				a,
				b << 30 & 0xffffffff | b >> 2,
				c,
				d,
			)
		
		for i in range(40, 60):
			a, b, c, d, e = (
				((a << 5 & 0xffffffff | a >> 27) + (b & c | b & d | c & d) + e + 0x8f1bbcdc + w[i]) & 0xffffffff,
				a,
				b << 30 & 0xffffffff | b >> 2,
				c,
				d,
			)
		
		for i in range(60, 80):
			a, b, c, d, e = (
				((a << 5 & 0xffffffff | a >> 27) + (b ^ c ^ d) + e + 0xca62c1d6 + w[i]) & 0xffffffff,
				a,
				b << 30 & 0xffffffff | b >> 2,
				c,
				d,
			)
		
		# Update hash.
		h0 = (h0 + a) & 0xffffffff
		h1 = (h1 + b) & 0xffffffff
		h2 = (h2 + c) & 0xffffffff
		h3 = (h3 + d) & 0xffffffff
		h4 = (h4 + e) & 0xffffffff
	
	# Convert hash to standard 160-bit big-endian format.
	return SHA_0_1_HASH.pack(h0, h1, h2, h3, h4)


def slow_sha_0(data: bytes) -> bytes:
	"""Slow pure Python implementation of SHA-0."""
	
	return _slow_sha_0_1(data, sha_1=False)


def slow_sha_1(data: bytes) -> bytes:
	"""Slow pure Python implementation of SHA-1.
	
	You should never use this.
	Use :func:`hashlib.sha1` instead.
	"""
	
	return _slow_sha_0_1(data, sha_1=True)


def byte_swap_hash(hash: bytes) -> bytes:
	"""Byte-swap a SHA hash value as if it were an array of 4-byte integers."""
	
	hash_array = array.array("I", hash)
	hash_array.byteswap()
	return hash_array.tobytes()


def byte_swapped_sha_1(data: bytes) -> bytes:
	"""Standard SHA-1, except that the final digest is byte-swapped.
	
	This is needed for one of MOULa's password hashing methods.
	"""
	
	return byte_swap_hash(hashlib.sha1(data).digest())


def password_hash_sha_0(account_name: str, password: str) -> bytes:
	"""Implements the SHA-0-based version of MOULa's password hashing function."""
	
	# Convert all ASCII letters to lowercase.
	account_name = account_name.encode().lower().decode()
	# Replace last character of account name and password with U+0000
	# (to replicate an off-by-one error in the client code).
	if account_name:
		account_name = account_name[:-1] + "\x00"
	if password:
		password = password[:-1] + "\x00"
	return slow_sha_0((password + account_name).encode("utf-16-le"))


def challenge_hash(client_challenge: int, server_challenge: int, password_hash: bytes) -> bytes:
	"""Calculate the challenge hash from client and server challenge values and a password hash."""
	
	return slow_sha_0(CHALLENGE_HASH_DATA.pack(client_challenge, server_challenge, password_hash))
