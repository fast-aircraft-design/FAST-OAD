"""
    Estimation of nacelle and pylon geometry
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

from math import sqrt

import numpy as np
import openmdao.api as om

import fastoad.api as oad
from ...constants import SERVICE_NACELLE_PYLON_GEOMETRY


@oad.RegisterSubmodel(
    SERVICE_NACELLE_PYLON_GEOMETRY, "fastoad.submodel.geometry.nacelle_and_pylon.legacy"
)
class ComputeNacelleAndPylonsGeometry(om.ExplicitComponent):
    # TODO: Document equations. Cite sources
    """Nacelle and pylon geometry estimation"""

    def setup(self):

        self.add_input("data:propulsion:MTO_thrust", val=np.nan, units="N")
        self.add_input("data:geometry:propulsion:engine:y_ratio", val=np.nan)
        self.add_input("data:geometry:propulsion:layout", val=np.nan)
        self.add_input("data:geometry:wing:span", val=np.nan, units="m")
        self.add_input("data:geometry:wing:MAC:length", val=np.nan, units="m")
        self.add_input("data:geometry:wing:MAC:leading_edge:x:local", val=np.nan, units="m")
        self.add_input("data:geometry:wing:root:chord", val=np.nan, units="m")
        self.add_input("data:geometry:wing:root:y", val=np.nan, units="m")
        self.add_input("data:geometry:wing:kink:chord", val=np.nan, units="m")
        self.add_input("data:geometry:wing:kink:y", val=np.nan, units="m")
        self.add_input("data:geometry:wing:kink:leading_edge:x:local", val=np.nan, units="m")
        self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan, units="m")
        self.add_input("data:geometry:fuselage:length", val=np.nan, units="m")
        self.add_input("data:geometry:fuselage:maximum_width", val=np.nan, units="m")

        self.add_output("data:geometry:propulsion:pylon:length", units="m")
        self.add_output("data:geometry:propulsion:fan:length", units="m")
        self.add_output("data:geometry:propulsion:nacelle:length", units="m")
        self.add_output("data:geometry:propulsion:nacelle:diameter", units="m")
        self.add_output("data:geometry:landing_gear:height", units="m")
        self.add_output("data:geometry:propulsion:nacelle:y", units="m")
        self.add_output("data:geometry:propulsion:pylon:wetted_area", units="m**2")
        self.add_output("data:geometry:propulsion:nacelle:wetted_area", units="m**2")
        self.add_output("data:weight:propulsion:engine:CG:x", units="m")

    def setup_partials(self):
        self.declare_partials(
            "data:geometry:propulsion:nacelle:diameter", "data:propulsion:MTO_thrust", method="fd"
        )
        self.declare_partials(
            "data:geometry:propulsion:nacelle:length", "data:propulsion:MTO_thrust", method="fd"
        )
        self.declare_partials(
            "data:geometry:landing_gear:height", "data:propulsion:MTO_thrust", method="fd"
        )
        self.declare_partials(
            "data:geometry:propulsion:fan:length", "data:propulsion:MTO_thrust", method="fd"
        )
        self.declare_partials(
            "data:geometry:propulsion:pylon:length", "data:propulsion:MTO_thrust", method="fd"
        )
        self.declare_partials(
            "data:geometry:propulsion:nacelle:y",
            [
                "data:propulsion:MTO_thrust",
                "data:geometry:fuselage:maximum_width",
                "data:geometry:propulsion:engine:y_ratio",
                "data:geometry:wing:span",
            ],
            method="fd",
        )
        self.declare_partials(
            "data:weight:propulsion:engine:CG:x",
            [
                "data:geometry:wing:MAC:at25percent:x",
                "data:geometry:wing:MAC:length",
                "data:geometry:wing:MAC:leading_edge:x:local",
                "data:geometry:wing:kink:leading_edge:x:local",
                "data:geometry:wing:root:y",
                "data:geometry:wing:kink:y",
                "data:geometry:wing:root:chord",
                "data:geometry:wing:kink:chord",
                "data:geometry:fuselage:length",
                "data:propulsion:MTO_thrust",
                "data:geometry:fuselage:maximum_width",
                "data:geometry:propulsion:engine:y_ratio",
                "data:geometry:wing:span",
            ],
            method="fd",
        )
        self.declare_partials(
            "data:geometry:propulsion:nacelle:wetted_area",
            "data:propulsion:MTO_thrust",
            method="fd",
        )
        self.declare_partials(
            "data:geometry:propulsion:pylon:wetted_area", "data:propulsion:MTO_thrust", method="fd"
        )

    def compute(self, inputs, outputs):
        thrust_sl = inputs["data:propulsion:MTO_thrust"]
        y_ratio_engine = inputs["data:geometry:propulsion:engine:y_ratio"]
        propulsion_layout = np.round(inputs["data:geometry:propulsion:layout"])
        span = inputs["data:geometry:wing:span"]
        l0_wing = inputs["data:geometry:wing:MAC:length"]
        x0_wing = inputs["data:geometry:wing:MAC:leading_edge:x:local"]
        l2_wing = inputs["data:geometry:wing:root:chord"]
        y2_wing = inputs["data:geometry:wing:root:y"]
        l3_wing = inputs["data:geometry:wing:kink:chord"]
        x3_wing = inputs["data:geometry:wing:kink:leading_edge:x:local"]
        y3_wing = inputs["data:geometry:wing:kink:y"]
        fa_length = inputs["data:geometry:wing:MAC:at25percent:x"]
        fus_length = inputs["data:geometry:fuselage:length"]
        b_f = inputs["data:geometry:fuselage:maximum_width"]

        nac_dia = 0.00904 * sqrt(thrust_sl * 0.225) + 0.7  # FIXME: use output of engine module
        lg_height = 1.4 * nac_dia
        # The nominal thrust must be used in lbf
        nac_length = 0.032 * sqrt(thrust_sl * 0.225)  # FIXME: use output of engine module

        outputs["data:geometry:propulsion:nacelle:length"] = nac_length
        outputs["data:geometry:propulsion:nacelle:diameter"] = nac_dia
        outputs["data:geometry:landing_gear:height"] = lg_height

        fan_length = 0.60 * nac_length
        pylon_length = 1.1 * nac_length

        if propulsion_layout == 1:
            y_nacell = y_ratio_engine * span / 2
        elif propulsion_layout == 2:
            y_nacell = b_f / 2.0 + 0.5 * nac_dia
        else:
            raise ValueError("Value of data:geometry:propulsion:layout can only be 1 or 2")

        l_wing_nac = l3_wing + (l2_wing - l3_wing) * (y3_wing - y_nacell) / (y3_wing - y2_wing)

        if propulsion_layout == 1:
            delta_x_nacell = 0.05 * l_wing_nac
            x_nacell_cg = (
                x3_wing * (y_nacell - y2_wing) / (y3_wing - y2_wing)
                - delta_x_nacell
                - 0.2 * nac_length
            )
            x_nacell_cg_absolute = fa_length - 0.25 * l0_wing - (x0_wing - x_nacell_cg)
        elif propulsion_layout == 2:
            x_nacell_cg_absolute = 0.8 * fus_length
        else:
            raise ValueError("Value of data:geometry:propulsion:layout can only be 1 or 2")

        outputs["data:geometry:propulsion:pylon:length"] = pylon_length
        outputs["data:geometry:propulsion:fan:length"] = fan_length
        outputs["data:geometry:propulsion:nacelle:y"] = y_nacell
        outputs["data:weight:propulsion:engine:CG:x"] = x_nacell_cg_absolute

        # Wet surfaces
        wet_area_nac = 0.0004 * thrust_sl * 0.225 + 11  # By engine
        wet_area_pylon = 0.35 * wet_area_nac

        outputs["data:geometry:propulsion:nacelle:wetted_area"] = wet_area_nac
        outputs["data:geometry:propulsion:pylon:wetted_area"] = wet_area_pylon
