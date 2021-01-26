"""This module compute beam properties from wing geometry"""
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


class WingBeamProps(om.ExplicitComponent):
    def initialize(self):
        self.options.declare("number_of_sections", types=int)

    def setup(self):
        n_secs = self.options["number_of_sections"]
        # Inputs -----------------------------------------------------------------------------------
        self.add_input("data:geometry:wing:root:y", val=np.nan)
        self.add_input("data:geometry:wing:root:chord", val=np.nan)
        self.add_input("data:geometry:wing:root:thickness_ratio", val=np.nan)
        self.add_input("data:geometry:wing:spar_ratio:front:root", val=np.nan)
        self.add_input("data:geometry:wing:spar_ratio:rear:root", val=np.nan)
        self.add_input("data:geometry:wing:root:skin_thickness", val=0.005, units="m")
        self.add_input("data:geometry:wing:root:web_thickness", val=0.005, units="m")

        self.add_input("data:geometry:wing:kink:y", val=np.nan)
        self.add_input("data:geometry:wing:kink:chord", val=np.nan)
        self.add_input("data:geometry:wing:kink:thickness_ratio", val=np.nan)
        self.add_input("data:geometry:wing:spar_ratio:front:kink", val=np.nan)
        self.add_input("data:geometry:wing:spar_ratio:rear:kink", val=np.nan)
        self.add_input("data:geometry:wing:kink:skin_thickness", val=0.005, units="m")
        self.add_input("data:geometry:wing:kink:web_thickness", val=0.005, units="m")

        self.add_input("data:geometry:wing:tip:y", val=np.nan)
        self.add_input("data:geometry:wing:tip:chord", val=np.nan)
        self.add_input("data:geometry:wing:tip:thickness_ratio", val=np.nan)
        self.add_input("data:geometry:wing:spar_ratio:front:tip", val=np.nan)
        self.add_input("data:geometry:wing:spar_ratio:rear:tip", val=np.nan)
        self.add_input("data:geometry:wing:tip:skin_thickness", val=0.005, units="m")
        self.add_input("data:geometry:wing:tip:web_thickness", val=0.005, units="m")

        self.add_input("data:geometry:wing:spar_area", val=0.0)
        self.add_input("data:aerostructural:structure:wing:nodes", shape_by_conn=True)
        self.add_input("settings:aerostructural:wing:n_spar", val=0.0)

        # Outputs ----------------------------------------------------------------------------------
        self.add_output("data:aerostructural:structure:wing:beam_properties", shape=(n_secs * 2, 4))

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        n_secs = self.options["number_of_sections"]
        #  Characteristic lengths and points -------------------------------------------------------
        root_y = inputs["data:geometry:wing:root:y"][0]
        kink_y = inputs["data:geometry:wing:kink:y"][0]
        tip_y = inputs["data:geometry:wing:tip:y"][0]
        root_front_spar_ratio = inputs["data:geometry:wing:spar_ratio:front:root"][0]
        root_rear_spar_ratio = inputs["data:geometry:wing:spar_ratio:rear:root"][0]
        root_skin_thickness = inputs["data:geometry:wing:root:skin_thickness"][0]
        root_web_thickness = inputs["data:geometry:wing:root:web_thickness"][0]
        kink_front_spar_ratio = inputs["data:geometry:wing:spar_ratio:front:kink"][0]
        kink_rear_spar_ratio = inputs["data:geometry:wing:spar_ratio:rear:kink"][0]
        kink_skin_thickness = inputs["data:geometry:wing:kink:skin_thickness"][0]
        kink_web_thickness = inputs["data:geometry:wing:kink:web_thickness"][0]
        tip_front_spar_ratio = inputs["data:geometry:wing:spar_ratio:front:tip"][0]
        tip_rear_spar_ratio = inputs["data:geometry:wing:spar_ratio:rear:tip"][0]
        tip_skin_thickness = inputs["data:geometry:wing:tip:skin_thickness"][0]
        tip_web_thickness = inputs["data:geometry:wing:tip:web_thickness"][0]
        root_thickness_ratio = inputs["data:geometry:wing:root:thickness_ratio"][0]
        kink_thickness_ratio = inputs["data:geometry:wing:kink:thickness_ratio"][0]
        tip_thickness_ratio = inputs["data:geometry:wing:tip:thickness_ratio"][0]
        root_chord = inputs["data:geometry:wing:root:chord"][0]
        kink_chord = inputs["data:geometry:wing:kink:chord"][0]
        tip_chord = inputs["data:geometry:wing:tip:chord"][0]

        # Beam properties are computed with geometric values corresponding to the inner point
        # This choice is conservative from a mass point of view.
        y = inputs["data:aerostructural:structure:wing:nodes"][:n_secs, 1]

        n_spar = inputs["settings:aerostructural:wing:n_spar"][0]
        a_spar = inputs["data:geometry:wing:spar_area"][0]

        #  Wing Box chord and height computation ---------------------------------------------------
        c_box_root = root_chord * (root_rear_spar_ratio - root_front_spar_ratio)
        h_box_root = root_chord * root_thickness_ratio

        c_box_kink = kink_chord * (kink_rear_spar_ratio - kink_front_spar_ratio)
        h_box_kink = kink_chord * kink_thickness_ratio

        c_box_tip = tip_chord * (tip_rear_spar_ratio - tip_front_spar_ratio)
        h_box_tip = tip_chord * tip_thickness_ratio

        #  Reference points for interpolation ------------------------------------------------------
        y_interp = [0.0, root_y, kink_y, tip_y]
        c_box_interp = [c_box_root, c_box_root, c_box_kink, c_box_tip]
        h_box_interp = [h_box_root, h_box_root, h_box_kink, h_box_tip]
        t_skin_interp = [
            root_skin_thickness,
            root_skin_thickness,
            kink_skin_thickness,
            tip_skin_thickness,
        ]
        t_web_interp = [
            root_web_thickness,
            root_web_thickness,
            kink_web_thickness,
            tip_web_thickness,
        ]

        #  Box dimensions interpolation ------------------------------------------------------------
        f_c_box = interp(y_interp, c_box_interp, "linear")
        f_h_box = interp(y_interp, h_box_interp, "linear")
        f_t_skin = interp(y_interp, t_skin_interp, "linear")
        f_t_web = interp(y_interp, t_web_interp, "linear")

        c_box = f_c_box(y)
        h_box = f_h_box(y)
        t_skin = f_t_skin(y)
        t_web = f_t_web(y)

        #  Beam properties computation -------------------------------------------------------------
        beam_box = Beam(c_box, h_box, t_skin, t_web, n_spar, a_spar, type="box")
        beam_box.compute_section_properties()
        a_beam = beam_box.a.reshape((n_secs, 1))
        i1 = beam_box.i1.reshape((n_secs, 1))
        i2 = beam_box.i2.reshape((n_secs, 1))
        j = beam_box.j.reshape((n_secs, 1))
        props = np.hstack((a_beam, i1, i2, j))

        #  Symmetry --------------------------------------------------------------------------------
        outputs["data:aerostructural:structure:wing:beam_properties"] = np.tile(props, (2, 1))
