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


"""Handles reading and writing of SDL blobs.

This package contains two variants of SDL de-/serialization:
a "standard" version that works based on state descriptors
and a "guessed" version that tries to parse blobs *without* knowing the state descriptor.

The "guessed" version is currently more developed,
because I want to use it to get basic SDL functionality working
without having to implement the complexity of the full SDL system yet.
It may also be useful as a debugging tool for inspecting unknown SDL blobs.
The normal version will be finished later.
"""


from .common import (
	NestedSDLVariableValueBase,
	SDLRecordBase,
	SDLStreamHeader,
	SimpleVariableValueBase,
	StateDescriptorId,
	VariableValueBase,
)
