"""Computation of form drag for Vertical Tail Plane."""
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

from fastoad.module_management.service_registry import RegisterSubmodel
from .utils.cd0_lifting_surface import LiftingSurfaceGeometry, compute_cd0_lifting_surface
from ..constants import SERVICE_CD0_VERTICAL_TAIL


@RegisterSubmodel(
    SERVICE_CD0_VERTICAL_TAIL, "fastoad.submodel.aerodynamics.CD0.vertical_tail.legacy"
)
class Cd0VerticalTail(om.ExplicitComponent):
    """
    Computation of form drag for Vertical Tail Plane.

    See :meth:`~fastoad.models.aerodynamics.components.utils.cd0_lifting_surface` for used method.
    """

    def initialize(self):
        self.options.declare("low_speed_aero", default=False, types=bool)

    def setup(self):
        self.add_input("data:geometry:vertical_tail:MAC:length", val=np.nan, units="m")
        self.add_input("data:geometry:vertical_tail:thickness_ratio", val=np.nan)
        self.add_input("data:geometry:vertical_tail:sweep_25", val=np.nan, units="deg")
        self.add_input("data:geometry:vertical_tail:wetted_area", val=np.nan, units="m**2")
        self.add_input("data:geometry:wing:area", val=np.nan, units="m**2")
        if self.options["low_speed_aero"]:
            self.add_input("data:aerodynamics:wing:low_speed:reynolds", val=np.nan)
            self.add_input("data:aerodynamics:aircraft:takeoff:mach", val=np.nan)
            self.add_output("data:aerodynamics:vertical_tail:low_speed:CD0")
        else:
            self.add_input("data:aerodynamics:wing:cruise:reynolds", val=np.nan)
            self.add_input("data:TLAR:cruise_mach", val=np.nan)
            self.add_output("data:aerodynamics:vertical_tail:cruise:CD0")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        vt_geometry = LiftingSurfaceGeometry(
            thickness_ratio=inputs["data:geometry:vertical_tail:thickness_ratio"],
            MAC_length=inputs["data:geometry:vertical_tail:MAC:length"],
            sweep_angle_25=inputs["data:geometry:vertical_tail:sweep_25"],
            wet_area=inputs["data:geometry:vertical_tail:wetted_area"],
            cambered=False,
            interaction_coeff=0.005,
        )
        wing_area = inputs["data:geometry:wing:area"]
        if self.options["low_speed_aero"]:
            mach = inputs["data:aerodynamics:aircraft:takeoff:mach"]
            reynolds = inputs["data:aerodynamics:wing:low_speed:reynolds"]
        else:
            mach = inputs["data:TLAR:cruise_mach"]
            reynolds = inputs["data:aerodynamics:wing:cruise:reynolds"]

        cd0_vt = compute_cd0_lifting_surface(vt_geometry, mach, reynolds, wing_area)

        if self.options["low_speed_aero"]:
            outputs["data:aerodynamics:vertical_tail:low_speed:CD0"] = cd0_vt
        else:
            outputs["data:aerodynamics:vertical_tail:cruise:CD0"] = cd0_vt
