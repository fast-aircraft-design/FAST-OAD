"""Computation of form drag for nacelles and pylons."""
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
from .utils.friction_drag import get_flat_plate_friction_drag_coefficient
from ..constants import SERVICE_CD0_NACELLES_PYLONS


@RegisterSubmodel(
    SERVICE_CD0_NACELLES_PYLONS, "fastoad.submodel.aerodynamics.CD0.nacelles_pylons.legacy"
)
class Cd0NacellesAndPylons(om.ExplicitComponent):
    """Computation of form drag for nacelles and pylons."""

    def initialize(self):
        self.options.declare("low_speed_aero", default=False, types=bool)

    def setup(self):
        if self.options["low_speed_aero"]:
            self.add_input("data:aerodynamics:wing:low_speed:reynolds", val=np.nan)
            self.add_input("data:aerodynamics:aircraft:takeoff:mach", val=np.nan)
            self.add_output("data:aerodynamics:nacelles:low_speed:CD0")
            self.add_output("data:aerodynamics:pylons:low_speed:CD0")
        else:
            self.add_input("data:aerodynamics:wing:cruise:reynolds", val=np.nan)
            self.add_input("data:TLAR:cruise_mach", val=np.nan)
            self.add_output("data:aerodynamics:nacelles:cruise:CD0")
            self.add_output("data:aerodynamics:pylons:cruise:CD0")

        self.add_input("data:geometry:propulsion:pylon:length", val=np.nan, units="m")
        self.add_input("data:geometry:propulsion:nacelle:length", val=np.nan, units="m")
        self.add_input("data:geometry:propulsion:pylon:wetted_area", val=np.nan, units="m**2")
        self.add_input("data:geometry:propulsion:nacelle:wetted_area", val=np.nan, units="m**2")
        self.add_input("data:geometry:propulsion:engine:count", val=np.nan)
        self.add_input("data:geometry:propulsion:fan:length", val=np.nan, units="m")
        self.add_input("data:geometry:wing:area", val=np.nan, units="m**2")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        n_engines = inputs["data:geometry:propulsion:engine:count"]
        wing_area = inputs["data:geometry:wing:area"]
        if self.options["low_speed_aero"]:
            mach = inputs["data:aerodynamics:aircraft:takeoff:mach"]
            reynolds = inputs["data:aerodynamics:wing:low_speed:reynolds"]
        else:
            mach = inputs["data:TLAR:cruise_mach"]
            reynolds = inputs["data:aerodynamics:wing:cruise:reynolds"]

        cd0_pylon = self._compute_cd0_for_pylons(inputs, n_engines, wing_area, mach, reynolds)
        cd0_nac = self._compute_cd0_for_nacelles(inputs, n_engines, wing_area, mach, reynolds)

        if self.options["low_speed_aero"]:
            outputs["data:aerodynamics:pylons:low_speed:CD0"] = cd0_pylon
            outputs["data:aerodynamics:nacelles:low_speed:CD0"] = cd0_nac
        else:
            outputs["data:aerodynamics:pylons:cruise:CD0"] = cd0_pylon
            outputs["data:aerodynamics:nacelles:cruise:CD0"] = cd0_nac

    @staticmethod
    def _compute_cd0_for_pylons(inputs, n_engines, wing_area, mach, reynolds):
        pylon_length = inputs["data:geometry:propulsion:pylon:length"]
        wet_area_pylon = inputs["data:geometry:propulsion:pylon:wetted_area"]

        cf_pylon = get_flat_plate_friction_drag_coefficient(pylon_length, mach, reynolds)
        el_pylon = 0.06
        ke_cd0_pylon = 4.688 * el_pylon ** 2 + 3.146 * el_pylon
        cd0_pylon = n_engines * (1 + ke_cd0_pylon) * cf_pylon * wet_area_pylon / wing_area
        return cd0_pylon

    @staticmethod
    def _compute_cd0_for_nacelles(inputs, n_engines, wing_area, mach, reynolds):
        nac_length = inputs["data:geometry:propulsion:nacelle:length"]
        wet_area_nac = inputs["data:geometry:propulsion:nacelle:wetted_area"]
        fan_length = inputs["data:geometry:propulsion:fan:length"]

        cf_nac = get_flat_plate_friction_drag_coefficient(nac_length, mach, reynolds)
        e_fan = 0.22
        kn_cd0_nac = 1 + 0.05 + 5.8 * e_fan / fan_length
        cd0_int_nac = 0.0002
        cd0_nac = n_engines * (kn_cd0_nac * cf_nac * wet_area_nac / wing_area + cd0_int_nac)
        return cd0_nac
