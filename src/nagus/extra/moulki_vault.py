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

"""Reads vault nodes and refs from MoulKI .vault files."""

import collections
import typing

from .. import state
from .. import structs


class MoulKIVault(structs.FieldBasedRepr):
	view_root_node_ids: typing.List[int]
	node_refs: typing.List[state.VaultNodeRef]
	nodes: typing.List[state.VaultNodeData]
	
	def __init__(
		self,
		view_root_node_ids: typing.List[int],
		node_refs: typing.List[state.VaultNodeRef],
		nodes: typing.List[state.VaultNodeData],
	) -> None:
		super().__init__()
		
		self.view_root_node_ids = view_root_node_ids
		self.node_refs = node_refs
		self.nodes = nodes
	
	def repr_fields(self) -> "collections.OrderedDict[str, str]":
		fields = super().repr_fields()
		fields["view_root_node_ids"] = repr(self.view_root_node_ids)
		fields["node_refs"] = repr(self.node_refs)
		fields["nodes"] = repr(self.nodes)
		return fields
	
	def as_multiline_str(self) -> typing.Iterable[str]:
		yield f"{len(self.view_root_node_ids)} root nodes in the view: {self.view_root_node_ids!r}"
		yield ""
		yield f"{len(self.node_refs)} vault node refs:"
		for ref in self.node_refs:
			yield f"\t{ref}"
		yield ""
		yield f"{len(self.nodes)} vault nodes:"
		for node in self.nodes:
			yield f"\t{node}"
	
	@classmethod
	def from_stream(cls, stream: typing.BinaryIO) -> "MoulKIVault":
		(view_root_node_id_count,) = structs.stream_unpack(stream, structs.UINT32)
		view_root_node_ids = []
		for _ in range(view_root_node_id_count):
			(root_node_id,) = structs.stream_unpack(stream, structs.UINT32)
			view_root_node_ids.append(root_node_id)
		
		(node_ref_count,) = structs.stream_unpack(stream, structs.UINT32)
		node_refs = []
		for _ in range(node_ref_count):
			# MoulKI pads node refs to the next 4-byte boundary...
			node_ref_buffer = structs.read_exact(stream, 16)
			node_ref_data = node_ref_buffer[:state.VAULT_NODE_REF.size]
			node_refs.append(state.VaultNodeRef.unpack(node_ref_data))
		
		(node_count,) = structs.stream_unpack(stream, structs.UINT32)
		nodes = []
		for _ in range(node_count):
			(packed_node_data_length,) = structs.stream_unpack(stream, structs.UINT32)
			packed_node_data = structs.read_exact(stream, packed_node_data_length)
			nodes.append(state.VaultNodeData.unpack(packed_node_data))
		
		return cls(
			view_root_node_ids=view_root_node_ids,
			node_refs=node_refs,
			nodes=nodes,
		)
