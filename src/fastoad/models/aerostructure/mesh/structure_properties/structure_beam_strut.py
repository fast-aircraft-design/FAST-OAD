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

import numpy as np
import openmdao.api as om

from fastoad.models.aerostructure.mesh.structure_properties.beam_properties import Beam


class StrutBeamProps(om.ExplicitComponent):
    def initialize(self):
        self.options.declare("number_of_sections", types=int)
        self.options.declare("has_vertical_strut", types=bool, default=False)

    def setup(self):
        n_secs = self.options["number_of_sections"]

        # Inputs -----------------------------------------------------------------------------------
        self.add_input("data:geometry:strut:tip:y", val=np.nan, units="m")
        self.add_input("data:geometry:strut:thickness_ratio", val=np.nan, units="m")
        self.add_input("data:geometry:strut:root:chord", val=np.nan, units="m")
        self.add_input("data:geometry:strut:tip:chord", val=np.nan, units="m")
        self.add_input("settings:geometry:strut:box_ratio", val=0.5)
        self.add_input("data:geometry:strut:root:flange_thickness", val=0.002, units="m")
        self.add_input("data:geometry:strut:root:web_thickness", val=0.002, units="m")
        self.add_input("data:geometry:strut:tip:flange_thickness", val=0.002, units="m")
        self.add_input("data:geometry:strut:tip:web_thickness", val=0.002, units="m")
        self.add_input("data:aerostructural:structure:strut:nodes", shape_by_conn=True)

        if self.options["has_vertical_strut"]:
            self.add_output(
                "data:aerostructural:structure:strut:beam_properties", shape=((n_secs + 1) * 2, 12)
            )
        else:
            self.add_output(
                "data:aerostructural:structure:strut:beam_properties", shape=(n_secs * 2, 12)
            )

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        n_secs = self.options["number_of_sections"]

        tip_y = inputs["data:geometry:strut:tip:y"][0]
        thickness_ratio = inputs["data:geometry:strut:thickness_ratio"][0]
        root_chord = inputs["data:geometry:strut:root:chord"][0]
        tip_chord = inputs["data:geometry:strut:tip:chord"][0]
        root_flange_thickness = inputs["data:geometry:strut:root:flange_thickness"][0]
        tip_flange_thickness = inputs["data:geometry:strut:tip:flange_thickness"][0]
        root_web_thickness = inputs["data:geometry:strut:root:web_thickness"][0]
        tip_web_thickness = inputs["data:geometry:strut:tip:web_thickness"][0]
        box_ratio = inputs["settings:geometry:strut:box_ratio"][0]

        # Beam properties are computed with geometric values corresponding to the inner point
        # This choice is conservative from a mass point of view.
        if not self.options["has_vertical_strut"]:
            y_nodes = inputs["data:aerostructural:structure:strut:nodes"][:n_secs, 1]
        else:
            y_nodes = inputs["data:aerostructural:structure:strut:nodes"][: n_secs + 1, 1]

        # Spar height
        box_height = (
            thickness_ratio * root_chord
            + y_nodes * thickness_ratio * (tip_chord - root_chord) / tip_y
        )

        # Spar flanges width
        box_chord = box_ratio * root_chord + y_nodes * box_ratio * (tip_chord - root_chord) / tip_y

        # Spar web thickness
        web_thickness = (
            root_web_thickness + y_nodes * (tip_web_thickness - root_web_thickness) / tip_y
        )

        # Spar flanges thickness
        flange_thickness = (
            root_flange_thickness + y_nodes * (tip_flange_thickness - root_flange_thickness) / tip_y
        )
        beam_box = Beam(
            box_chord, box_height, flange_thickness, web_thickness, 0.0, 0.0, type="box"
        )
        beam_box.compute_section_properties()
        a_beam = beam_box.a.reshape((n_secs, 1))
        i1 = beam_box.i1.reshape((n_secs, 1))
        i2 = beam_box.i2.reshape((n_secs, 1))
        j = beam_box.j.reshape((n_secs, 1))
        y1 = beam_box.y1.reshape((n_secs, 1))
        y2 = beam_box.y2.reshape((n_secs, 1))
        y3 = beam_box.y3.reshape((n_secs, 1))
        y4 = beam_box.y4.reshape((n_secs, 1))
        z1 = beam_box.z1.reshape((n_secs, 1))
        z2 = beam_box.z2.reshape((n_secs, 1))
        z3 = beam_box.z3.reshape((n_secs, 1))
        z4 = beam_box.z4.reshape((n_secs, 1))

        props = np.hstack((a_beam, i1, i2, j, y1, z1, y2, z2, y3, z3, y4, z4))
        outputs["data:aerostructural:structure:strut:beam_properties"] = np.tile(props, (2, 1))
