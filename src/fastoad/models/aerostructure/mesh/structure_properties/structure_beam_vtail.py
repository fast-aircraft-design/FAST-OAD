"""This module compute beam properties from VTP geometry"""
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
import numpy as np
from scipy.interpolate import interp1d as interp

from fastoad.models.aerostructure.mesh.structure_properties.beam_properties import Beam


class VtailBeamProps(om.ExplicitComponent):
    def initialize(self):
        self.options.declare("number_of_sections", types=int)

    def setup(self):
        n_secs = self.options["number_of_sections"]

        # Inputs -----------------------------------------------------------------------------------
        self.add_input("data:geometry:vertical_tail:root:chord", val=np.nan)
        self.add_input("data:geometry:vertical_tail:root:skin_thickness", val=0.005, units="m")
        self.add_input("data:geometry:vertical_tail:root:web_thickness", val=0.005, units="m")
        self.add_input("data:geometry:vertical_tail:tip:chord", val=np.nan)
        self.add_input("data:geometry:vertical_tail:tip:skin_thickness", val=0.005, units="m")
        self.add_input("data:geometry:vertical_tail:tip:web_thickness", val=0.005, units="m")
        self.add_input("data:geometry:vertical_tail:thickness_ratio", val=np.nan)
        self.add_input("data:geometry:vertical_tail:span", val=np.nan)

        self.add_input("data:geometry:fuselage:maximum_height", val=np.nan)

        self.add_input("data:geometry:vertical_tail:spar_area", val=0.0)
        self.add_input("data:aerostructural:structure:vertical_tail:nodes", shape_by_conn=True)
        self.add_input("settings:aerostructural:vertical_tail:n_spar", val=0.0)

        self.add_output(
            "data:aerostructural:structure:vertical_tail:beam_properties", shape=(n_secs, 4)
        )

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        n_secs = self.options["number_of_sections"]

        #  Characteristic lengths and points -------------------------------------------------------
        root_z = 0.5 * inputs["data:geometry:fuselage:maximum_height"][0]
        tip_z = inputs["data:geometry:vertical_tail:span"][0] + root_z
        root_chord = inputs["data:geometry:vertical_tail:root:chord"][0]
        root_skin_thickness = inputs["data:geometry:vertical_tail:root:skin_thickness"][0]
        root_web_thickness = inputs["data:geometry:vertical_tail:root:web_thickness"][0]
        tip_chord = inputs["data:geometry:vertical_tail:tip:chord"][0]
        tip_skin_thickness = inputs["data:geometry:vertical_tail:tip:skin_thickness"][0]
        tip_web_thickness = inputs["data:geometry:vertical_tail:tip:web_thickness"][0]
        thickness_ratio = inputs["data:geometry:vertical_tail:thickness_ratio"][0]

        z = inputs["data:aerostructural:structure:vertical_tail:nodes"][:n_secs, 2]

        n_spar = inputs["settings:aerostructural:vertical_tail:n_spar"][0]
        a_spar = inputs["data:geometry:vertical_tail:spar_area"][0]

        #  VTP Box chord and height computation ----------------------------------------------------
        c_box_root = 0.5 * root_chord  # Box is assumed to extend over 50% of the HTP chord
        c_box_tip = 0.5 * tip_chord
        h_box_root = root_chord * thickness_ratio
        h_box_tip = tip_chord * thickness_ratio

        #  Reference points for interpolation ------------------------------------------------------
        z_interp = [root_z, tip_z]
        c_interp = [c_box_root, c_box_tip]
        h_interp = [h_box_root, h_box_tip]
        t_skin_interp = [root_skin_thickness, tip_skin_thickness]
        t_web_interp = [root_web_thickness, tip_web_thickness]

        #  Box dimensions interpolation ------------------------------------------------------------
        f_c_box = interp(z_interp, c_interp)
        f_h_box = interp(z_interp, h_interp)
        f_t_skin = interp(z_interp, t_skin_interp)
        f_t_web = interp(z_interp, t_web_interp)

        c_box = f_c_box(z)
        h_box = f_h_box(z)
        t_skin = f_t_skin(z)
        t_web = f_t_web(z)

        #  Beam properties computation -------------------------------------------------------------
        beam_box = Beam(c_box, h_box, t_skin, t_web, n_spar, a_spar, type="box")
        beam_box.compute_section_properties()
        a_beam = beam_box.a.reshape((n_secs, 1))
        i1 = beam_box.i1.reshape((n_secs, 1))
        i2 = beam_box.i2.reshape((n_secs, 1))
        j = beam_box.j.reshape((n_secs, 1))
        props = np.hstack((a_beam, i1, i2, j))

        #  Outputs --------------------------------------------------------------------
        outputs["data:aerostructural:structure:vertical_tail:beam_properties"] = props
