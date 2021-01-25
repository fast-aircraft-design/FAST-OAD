"""
Defines classes for dynamic call of structure properties classes for structure mesh
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
#  FAST is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.


from enum import Enum
from fastoad.models.aerostructure.mesh.structure_properties.structure_beam_wing import WingBeamProps
from fastoad.models.aerostructure.mesh.structure_properties.structure_beam_htail import (
    HtailBeamProps,
)
from fastoad.models.aerostructure.mesh.structure_properties.structure_beam_vtail import (
    VtailBeamProps,
)


class BeamPropertiesClass(Enum):
    WING = WingBeamProps
    HORIZONTAL_TAIL = HtailBeamProps
    VERTICAL_TAIL = VtailBeamProps
