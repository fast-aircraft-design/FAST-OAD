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


from fastoad.models.aerostructure.mesh.structure_mesh import StructureMesh
from fastoad.models.aerostructure.structure.external.mystran.mystran_static import MystranStatic
from fastoad.models.options import OpenMdaoOptionDispatcherGroup as OmOptGrp


class StructureSolver(OmOptGrp):
    def initialize(self):
        self.options.declare("components", types=list)
        self.options.declare("components_sections", types=list)

    def setup(self):
        self.add_subsystem(
            "structure_mesh",
            StructureMesh(
                components=self.options["components"],
                components_sections=self.options["components_sections"],
            ),
            promotes=["*"],
        )
        self.add_subsystem(
            "static_structure_solver",
            MystranStatic(
                components=self.options["components"],
                components_sections=self.options["components_sections"],
            ),
            promotes=["*"],
        )
