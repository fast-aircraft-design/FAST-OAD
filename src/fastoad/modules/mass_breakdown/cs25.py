"""
Load case computation
"""

#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2019  ONERA/ISAE
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

from fastoad.utils.physics.atmosphere import atmosphere


class Loads(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """
    Computes gust load cases

    Load case 1: with wings with almost no fuel
    Load case 2: at maximum take-off width
    """

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

    # pylint: disable=too-many-locals
    # pylint: disable=invalid-name
    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        sea_level_density = 1.225
        wing_area = inputs['geometry:wing_area']
        span = inputs['geometry:wing_span']
        mzfw = inputs['weight:MZFW']
        mfw = inputs['weight:MFW']
        mtow = inputs['weight:MTOW']
        cl_alpha = inputs['aerodynamics:Cl_alpha']
        u_gust1 = inputs['loadcase1:U_gust']
        alt_1 = inputs['loadcase1:altitude']
        vc_eas1 = inputs['loadcase1:Vc_EAS']
        u_gust2 = inputs['loadcase2:U_gust']
        alt_2 = inputs['loadcase2:altitude']
        vc_eas2 = inputs['loadcase2:Vc_EAS']

        # calculation of mean geometric chord
        chord_geom = wing_area / span

        # load case #1
        m1 = 1.05 * mzfw
        n_gust_1 = self.__n_gust(m1, wing_area, atmosphere(alt_1)[1],
                                 sea_level_density, chord_geom, vc_eas1,
                                 cl_alpha, u_gust1)
        n1 = 1.5 * max(2.5, n_gust_1)
        n1m1 = n1 * m1

        # load case #2
        n_gust_2 = self.__n_gust(mtow, wing_area, atmosphere(alt_2)[1],
                                 sea_level_density, chord_geom, vc_eas2,
                                 cl_alpha, u_gust2)
        n2 = 1.5 * max(2.5, n_gust_2)
        mcv = min(0.8 * mfw, mtow - mzfw)
        n2m2 = n2 * (mtow - 0.55 * mcv)

        outputs['n1m1'] = n1m1
        outputs['n2m2'] = n2m2

    @staticmethod
    def __n_gust(mass, wing_area, rho, sea_level_density, chord_geom,
                 vc_eas, cl_alpha, u_gust):
        # TODO: better dosctring
        """

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
                vc_eas * 0.514444 * cl_alpha / mass / wing_area)

        return n_gust
