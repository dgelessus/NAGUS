# This file is part of NAGUS, an Uru Live server that is not very good.
# Copyright (C) 2025 dgelessus
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

"""Reads object SDL blobs from MOSS .agestate files."""

import io
import typing

from .. import game_server
from .. import sdl
from ..sdl import guess
from .. import structs


def read_single_moss_agestate(stream: typing.BinaryIO) -> bytes:
	(length,) = structs.stream_unpack(stream, structs.UINT32)
	return structs.read_exact(stream, length)


def iter_moss_agestates(stream: typing.BinaryIO) -> typing.Iterable[bytes]:
	dat = stream.read(structs.UINT32.size)
	while dat:
		(length,) = structs.UINT32.unpack(dat)
		yield structs.read_exact(stream, length)
		dat = stream.read(structs.UINT32.size)


def unpack_single_moss_agestate(data: bytes) -> typing.Tuple[structs.Uoid, sdl.SDLStreamHeader, sdl.guess.GuessedSDLRecord]:
	# Add dummy message flags field,
	# which isn't included in the pseudo-game-server-message saved by MOSS.
	padded_data = bytes(4) + data
	with io.BytesIO(padded_data) as stream:
		msg = game_server.NetMessageStreamedObject()
		msg.read(stream)
		
		rest = stream.read()
		if rest:
			print(f"Extra data after stream message: {rest!r}")
	
	with io.BytesIO(msg.decompress_data()) as stream:
		header, record = sdl.guess.guess_parse_sdl_blob(stream)
		
		rest = stream.read()
		if rest:
			print(f"Extra data after SDL blob: {rest!r}")
	
	return msg.uoid, header, record


def iter_unpack_moss_agestates(stream: typing.BinaryIO) -> typing.Iterable[typing.Tuple[structs.Uoid, sdl.SDLStreamHeader, sdl.guess.GuessedSDLRecord]]:
	for dat in iter_moss_agestates(stream):
		yield unpack_single_moss_agestate(dat)


def format_moss_agestates(agestates: typing.Iterable[typing.Tuple[structs.Uoid, sdl.SDLStreamHeader, sdl.guess.GuessedSDLRecord]]) -> typing.Iterable[str]:
	for uoid, header, record in agestates:
		yield f"State for object {uoid}:"
		if header.uoid is not None:
			yield f"\tWarning: SDL header also contains a UOID! {header.uoid}"
		yield f"\t{header.descriptor_id}"
		for line in record.as_multiline_str():
			yield "\t" + line
