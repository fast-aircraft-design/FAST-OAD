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

from fastoad.models.aerostructure.transfer.components.component_matrix import ComponentMatrix


class TransferMatrices(om.Group):
    def initialize(self):
        self.options.declare("coupled_components", types=list)
        self.options.declare("structural_components_sections", types=list)
        self.options.declare("aerodynamic_components_sections", types=list)
        self.options.declare("coupled_components_interpolations", types=list)

    def setup(self):
        comps = self.options["coupled_components"]
        struct_sections = self.options["structural_components_sections"][: len(comps)]
        aero_sections = self.options["aerodynamic_components_sections"][: len(comps)]
        methods = self.options["coupled_components_interpolations"]

        for comp, aero_s, struct_s, meth in zip(comps, aero_sections, struct_sections, methods):
            self.add_subsystem(
                comp + "Matrix",
                ComponentMatrix(
                    component=comp,
                    interpolation_method=meth,
                    number_of_aerodynamic_sections=aero_s,
                    number_of_structural_sections=struct_s,
                ),
                promotes=["*"],
            )
