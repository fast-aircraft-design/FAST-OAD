"""
    FAST - Copyright (c) 2016 ONERA
"""

#      This file is part of FAST : A framework for rapid Overall Aircraft Design
#      Copyright (C) 2019  ONERA/ISAE
#      FAST is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.
import numpy as np
from openmdao.core.explicitcomponent import ExplicitComponent

from fastoad.utils.physics.atmosphere import atmosphere


class Loads(ExplicitComponent):
    # --------------------------------------------------------------
    #                     LOADS CALCULATIONS
    # --------------------------------------------------------------
    def setup(self):
        self.add_input('geometry:wing_area', val=np.nan)
        self.add_input('geometry:wing_span', val=np.nan)
        self.add_input('weight:MZFW', val=np.nan)
        self.add_input('weight:MFW', val=np.nan)
        self.add_input('weight:MTOW', val=np.nan)
        self.add_input('aerodynamics:Cl_alpha', val=np.nan)
        self.add_input('loadcase1:U_gust', val=np.nan)
        self.add_input('loadcase1:altitude', val=np.nan)
        self.add_input('loadcase1:Vc_EAS', val=np.nan)
        self.add_input('loadcase2:U_gust', val=np.nan)
        self.add_input('loadcase2:altitude', val=np.nan)
        self.add_input('loadcase2:Vc_EAS', val=np.nan)

        self.add_output('n1m1')
        self.add_output('n2m2')

    def compute(self, inputs, outputs):
        DENSITY_SL = 1.225
        wing_area = inputs['geometry:wing_area']
        span = inputs['geometry:wing_span']
        MZFW = inputs['weight:MZFW']
        MFW = inputs['weight:MFW']
        MTOW = inputs['weight:MTOW']
        CL_alpha = inputs['aerodynamics:Cl_alpha']
        U_gust1 = inputs['loadcase1:U_gust']
        alt_1 = inputs['loadcase1:altitude']
        Vc_EAS1 = inputs['loadcase1:Vc_EAS']
        U_gust2 = inputs['loadcase2:U_gust']
        alt_2 = inputs['loadcase2:altitude']
        Vc_EAS2 = inputs['loadcase2:Vc_EAS']

        # calculation of mean geometric chord
        chord_geom = wing_area / span

        # load case #1
        m1 = 1.05 * MZFW
        n_gust_1 = self.__n_gust(m1, wing_area, atmosphere(alt_1)[1], DENSITY_SL, chord_geom,
                                 Vc_EAS1, CL_alpha,
                                 U_gust1)
        n1 = 1.5 * max(2.5, n_gust_1)
        n1m1 = n1 * m1

        # load case #2
        n_gust_2 = self.__n_gust(MTOW, wing_area, atmosphere(alt_2)[1], DENSITY_SL, chord_geom,
                                 Vc_EAS2, CL_alpha,
                                 U_gust2)
        n2 = 1.5 * max(2.5, n_gust_2)
        MCV = min(0.8 * MFW, MTOW - MZFW)
        n2m2 = n2 * (MTOW - 0.55 * MCV)

        outputs['n1m1'] = n1m1
        outputs['n2m2'] = n2m2

    @staticmethod
    def __n_gust(mass, wing_area, rho, rho_SL, chord_geom, vc_EAS, CL_alpha, U_gust):
        mu_g = 2 * mass / rho / wing_area / chord_geom / CL_alpha
        K_g = 0.88 * mu_g / (5.3 + mu_g)
        n_gust = 1 + (rho_SL / 2 / 9.81) * K_g * U_gust * \
                 (vc_EAS * 0.514444 * CL_alpha / mass / wing_area)

        return n_gust
