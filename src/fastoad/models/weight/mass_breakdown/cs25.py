"""
Computation of load cases
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

import numpy as np
from openmdao.core.explicitcomponent import ExplicitComponent
from stdatm import Atmosphere

from fastoad.module_management.service_registry import RegisterSubmodel
from .constants import SERVICE_GUST_LOADS


@RegisterSubmodel(SERVICE_GUST_LOADS, "fastoad.submodel.gust_loads")
class Loads(ExplicitComponent):
    """
    Computes gust load cases

    Load case 1: with wings with almost no fuel
    Load case 2: at maximum take-off weight

    Based on formulas in :cite:`supaero:2014`, §6.3

    """

    def setup(self):
        self.add_input("data:geometry:wing:area", val=np.nan, units="m**2")
        self.add_input("data:geometry:wing:span", val=np.nan, units="m")
        self.add_input("data:weight:aircraft:MZFW", val=np.nan, units="kg")
        self.add_input("data:weight:aircraft:MFW", val=np.nan, units="kg")
        self.add_input("data:weight:aircraft:MTOW", val=np.nan, units="kg")
        self.add_input("data:aerodynamics:aircraft:cruise:CL_alpha", val=np.nan)
        self.add_input("data:load_case:lc1:U_gust", val=np.nan, units="m/s")
        self.add_input("data:load_case:lc1:altitude", val=np.nan, units="ft")
        self.add_input("data:load_case:lc1:Vc_EAS", val=np.nan, units="m/s")
        self.add_input("data:load_case:lc2:U_gust", val=np.nan, units="m/s")
        self.add_input("data:load_case:lc2:altitude", val=np.nan, units="ft")
        self.add_input("data:load_case:lc2:Vc_EAS", val=np.nan, units="kn")

        self.add_output("data:mission:sizing:cs25:sizing_load_1", units="kg")
        self.add_output("data:mission:sizing:cs25:sizing_load_2", units="kg")

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    # pylint: disable=too-many-locals
    # pylint: disable=invalid-name
    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        sea_level_density = Atmosphere(0).density
        wing_area = inputs["data:geometry:wing:area"]
        span = inputs["data:geometry:wing:span"]
        mzfw = inputs["data:weight:aircraft:MZFW"]
        mfw = inputs["data:weight:aircraft:MFW"]
        mtow = inputs["data:weight:aircraft:MTOW"]
        cl_alpha = inputs["data:aerodynamics:aircraft:cruise:CL_alpha"]
        u_gust1 = inputs["data:load_case:lc1:U_gust"]
        alt_1 = inputs["data:load_case:lc1:altitude"]
        vc_eas1 = inputs["data:load_case:lc1:Vc_EAS"]
        u_gust2 = inputs["data:load_case:lc2:U_gust"]
        alt_2 = inputs["data:load_case:lc2:altitude"]
        vc_eas2 = inputs["data:load_case:lc2:Vc_EAS"]

        # calculation of mean geometric chord
        chord_geom = wing_area / span

        # load case #1
        m1 = 1.05 * mzfw
        n_gust_1 = self.__n_gust(
            m1,
            wing_area,
            Atmosphere(alt_1).density,
            sea_level_density,
            chord_geom,
            vc_eas1,
            cl_alpha,
            u_gust1,
        )
        n1 = 1.5 * max(2.5, n_gust_1)
        n1m1 = n1 * m1

        # load case #2
        n_gust_2 = self.__n_gust(
            mtow,
            wing_area,
            Atmosphere(alt_2).density,
            sea_level_density,
            chord_geom,
            vc_eas2,
            cl_alpha,
            u_gust2,
        )
        n2 = 1.5 * max(2.5, n_gust_2)
        mcv = min(0.8 * mfw, mtow - mzfw)
        n2m2 = n2 * (mtow - 0.55 * mcv)

        outputs["data:mission:sizing:cs25:sizing_load_1"] = n1m1
        outputs["data:mission:sizing:cs25:sizing_load_2"] = n2m2

    @staticmethod
    def __n_gust(mass, wing_area, rho, sea_level_density, chord_geom, vc_eas, cl_alpha, u_gust):
        """
        Computes a reference gust load.

        :param mass:
        :param wing_area:
        :param rho:
        :param sea_level_density:
        :param chord_geom:
        :param vc_eas: Vc (Equivalent AirSpeed)
        :param cl_alpha:
        :param u_gust:
        :return:
        """
        mu_g = 2 * mass / rho / wing_area / chord_geom / cl_alpha
        k_g = 0.88 * mu_g / (5.3 + mu_g)  # attenuation factor
        n_gust = 1 + (sea_level_density / 2 / 9.81) * k_g * u_gust * (
            vc_eas * cl_alpha / mass / wing_area
        )

        return n_gust
