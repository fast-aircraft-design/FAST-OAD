"""
Defines classes for dynamic call of nodes and chords classes for aerodynamic mesh
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
from fastoad.models.aerostructure.mesh.components.aerodynamic_nodes_wing import AerodynamicNodesWing
from .aerodynamic_nodes_htail import AerodynamicNodesHtail
from .aerodynamic_nodes_vtail import AerodynamicNodesVtail
from .aerodynamic_nodes_fuselage import AerodynamicNodesFuselage
from .aerodynamic_chords_wing import AerodynamicChordsWing
from .aerodynamic_chords_htail import AerodynamicChordsHtail
from .aerodynamic_chords_vtail import AerodynamicChordsVtail
from .aerodynamic_chords_fuselage import AerodynamicChordsFuselage


class AerodynamicNodesClasses(Enum):
    WING = AerodynamicNodesWing
    HORIZONTAL_TAIL = AerodynamicNodesHtail
    VERTICAL_TAIL = AerodynamicNodesVtail
    FUSELAGE = AerodynamicNodesFuselage


class AerodynamicChordsClasses(Enum):
    WING = AerodynamicChordsWing
    HORIZONTAL_TAIL = AerodynamicChordsHtail
    VERTICAL_TAIL = AerodynamicChordsVtail
    FUSELAGE = AerodynamicChordsFuselage
