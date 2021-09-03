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


class StrutBeamProps(om.ExplicitComponent):
    def initialize(self):
        self.options.declare("number_of_sections", types=int)

    def setup(self):
        n_secs = self.options["number_of_sections"]

        # Inputs -----------------------------------------------------------------------------------
        self.add_input("data:geometry:strut:tip:y", val=np.nan, units="m")
        self.add_input("data:geometry:strut:thickness_ratio", val=np.nan, units="m")
        self.add_input("data:geometry:strut:root:chord", val=np.nan, units="m")
        self.add_input("data:geometry:strut:tip:chord", val=np.nan, units="m")
        self.add_input("settings:geometry:strut:flange_ratio", val=0.1)
        self.add_input("data:geometry:strut:root:flange_thickness", val=0.002, units="m")
        self.add_input("data:geometry:strut:root:web_thickness", val=0.002, units="m")
        self.add_input("data:geometry:strut:tip:flange_thickness", val=0.002, units="m")
        self.add_input("data:geometry:strut:tip:web_thickness", val=0.002, units="m")
        self.add_input("data:aerostructural:structure:strut:nodes", shape_by_conn=True)

        self.add_output(
            "data:aerostructural:structure:strut:beam_properties", shape=(n_secs * 2, 6)
        )

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        n_secs = self.options["number_of_sections"]

        tip_y = inputs["data:geometry:strut:tip:y"]
        thickness_ratio = inputs["data:geometry:strut:thickness_ratio"]
        root_chord = inputs["data:geometry:strut:root:chord"]
        tip_chord = inputs["data:geometry:strut:tip:chord"]
        root_flange_thickness = inputs["data:geometry:strut:root:flange_thickness"]
        tip_flange_thickness = inputs["data:geometry:strut:tip:flange_thickness"]
        root_web_thickness = inputs["data:geometry:strut:root:web_thickness"]
        tip_web_thickness = inputs["data:geometry:strut:tip:web_thickness"]
        k_flange = inputs["settings:geometry:strut:flange_ratio"]

        # Beam properties are computed with geometric values corresponding to the inner point
        # This choice is conservative from a mass point of view.
        y_nodes = inputs["data:aerostructural:structure:strut:nodes"][:n_secs, 1]

        # Spar height
        pbarl_dim1 = (
            thickness_ratio * root_chord
            + y_nodes * thickness_ratio * (tip_chord - root_chord) / tip_y
        )

        # Spar flanges width
        pbarl_dim2 = k_flange * root_chord + y_nodes * k_flange * (tip_chord - root_chord) / tip_y
        pbarl_dim3 = pbarl_dim2

        # Spar web thickness
        pbarl_dim4 = root_web_thickness + y_nodes * (tip_web_thickness - root_web_thickness) / tip_y

        # Spar flanges thickness
        pbarl_dim5 = (
            root_flange_thickness + y_nodes * (tip_flange_thickness - root_flange_thickness) / tip_y
        )
        pbarl_dim6 = pbarl_dim5

        props = np.hstack(pbarl_dim1, pbarl_dim2, pbarl_dim3, pbarl_dim4, pbarl_dim5, pbarl_dim6)
        outputs["data:aerostructural:structure:strut:beam_properties"] = np.tile(props)
