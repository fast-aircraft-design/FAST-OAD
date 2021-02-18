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


from openmdao.core.group import Group
from .nodes.nodes_classes import StructureNodesClasses
from .structure_properties.properties_classes import BeamPropertiesClass


class StructureMesh(Group):
    def initialize(self):
        self.options.declare("components_sections", types=list)
        self.options.declare("components", types=list)

    def setup(self):
        comps = self.options["components"]
        n_sections = self.options["components_sections"]
        if n_sections is not None and len(n_sections) != len(comps):
            msg = "Number of components and number of associated sections must correspond"
            raise ValueError(msg)
        for comp, n_section in zip(comps, n_sections):
            nodes_class = StructureNodesClasses[comp.upper()].value
            props_class = BeamPropertiesClass[comp.upper()].value

            self.add_subsystem(
                comp + "_nodes", nodes_class(number_of_sections=n_section), promotes=["*"],
            )
            self.add_subsystem(
                comp + "_prop", props_class(number_of_sections=n_section), promotes=["*"]
            )
