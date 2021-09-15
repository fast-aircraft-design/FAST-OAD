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


import openmdao.api as om

from fastoad.models.aerostructure.transfer.components.component_displacements import (
    ComponentDisplacements,
)
from fastoad.models.aerostructure.transfer.components.component_rotations import ComponentRotations


class DisplacementsTransfer(om.Group):
    def initialize(self):
        self.options.declare("coupled_components", types=list)
        self.options.declare("aerodynamic_components_sections", types=list)

    def setup(self):
        comps = self.options["coupled_components"]
        aerodynamic_sections = self.options["aerodynamic_components_sections"]

        for aero_sections, comp in zip(aerodynamic_sections, comps):
            self.add_subsystem(
                comp + "_Displacements_Transfer",
                ComponentDisplacements(component=comp),
                promotes=["*"],
            )
            self.add_subsystem(
                comp + "_Rotations_Transfer",
                ComponentRotations(component=comp, number_of_aerodynamic_sections=aero_sections),
                promotes=["*"],
            )
