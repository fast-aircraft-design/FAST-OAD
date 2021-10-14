"""
    Estimation of geometry of vertical tail
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2021 ONERA & ISAE-SUPAERO
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


import openmdao.api as om

import fastoad.api as oad
from fastoad.models.geometry.geom_components.vt.components import ComputeVTChords
from fastoad.models.geometry.geom_components.vt.components import ComputeVTClalpha
from fastoad.models.geometry.geom_components.vt.components import ComputeVTDistance
from fastoad.models.geometry.geom_components.vt.components import ComputeVTMAC
from fastoad.models.geometry.geom_components.vt.components import ComputeVTSweep
from fastoad.module_management.service_registry import RegisterSubmodel
from ...constants import SERVICE_FUSELAGE_CNBETA, SERVICE_VERTICAL_TAIL_GEOMETRY


@oad.RegisterSubmodel(
    SERVICE_VERTICAL_TAIL_GEOMETRY, "fastoad.submodel.geometry.vertical_tail.legacy"
)
class ComputeVerticalTailGeometry(om.Group):
    """Vertical tail geometry estimation"""

    def setup(self):
        self.add_subsystem(
            "fuselage_cnbeta",
            RegisterSubmodel.get_submodel(SERVICE_FUSELAGE_CNBETA),
            promotes=["*"],
        )
        self.add_subsystem("vt_aspect_ratio", ComputeVTDistance(), promotes=["*"])
        self.add_subsystem("vt_clalpha", ComputeVTClalpha(), promotes=["*"])
        self.add_subsystem("vt_chords", ComputeVTChords(), promotes=["*"])
        self.add_subsystem("vt_mac", ComputeVTMAC(), promotes=["*"])
        self.add_subsystem("vt_sweep", ComputeVTSweep(), promotes=["*"])
