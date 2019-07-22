"""
    FAST - Copyright (c) 2016 ONERA ISAE
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

from fastoad.modules.aerodynamics.constants import ARRAY_SIZE


class ComputePolar(ExplicitComponent):
    def initialize(self):
        self.options.declare('low_speed_aero', default=False, types=bool)

    def setup(self):
        self.low_speed_aero = self.options['low_speed_aero']

        self.add_input('kfactors_aero:K_Cd', val=np.nan)
        self.add_input('kfactors_aero:Offset_Cd', val=np.nan)
        self.add_input('kfactors_aero:K_winglet_Cd', val=np.nan)
        self.add_input('kfactors_aero:Offset_winglet_Cd', val=np.nan)

        nans_array = np.full(ARRAY_SIZE, np.nan)
        if self.low_speed_aero:
            self.add_input('cl_low_speed', val=nans_array)
            self.add_input('cd0_total_low_speed', val=nans_array)
            self.add_input('cd_eq_low_speed', val=nans_array)
            self.add_input('cd_comp_low_speed', val=nans_array)
            self.add_input('oswald_coeff', val=np.nan)
            cl = []
            cd = []
            for i in range(ARRAY_SIZE):
                cl.append(i / 100)
                cd.append(0.033)
            self.add_output('aerodynamics:ClCd_low_speed', val=[cd, cl], shape=(2, ARRAY_SIZE))
        else:
            self.add_input('cl_high_speed', val=nans_array)
            self.add_input('cd0_total_high_speed', val=nans_array)
            self.add_input('cd_eq_high_speed', val=nans_array)
            self.add_input('cd_comp_high_speed', val=nans_array)
            self.add_input('oswald_coeff', val=np.nan)
            cl = []
            cd = []
            for i in range(ARRAY_SIZE):
                cl.append(i / 100)
                cd.append(0.033)
            self.add_output('aerodynamics:ClCd', val=[cd, cl], shape=(2, ARRAY_SIZE))
            self.add_output('aerodynamics:L_D_max')
            self.add_output('aerodynamics:Cl_opt', val=np.nan)
            self.add_output('aerodynamics:Cd_opt', val=np.nan)

    def compute(self, inputs, outputs):
        coef_k = inputs['oswald_coeff']
        k_cd = inputs['kfactors_aero:K_Cd']
        offset_cd = inputs['kfactors_aero:Offset_Cd']
        k_winglet_cd = inputs['kfactors_aero:K_winglet_Cd']
        offset_winglet_cd = inputs['kfactors_aero:Offset_winglet_Cd']
        if self.low_speed_aero:
            cl = inputs['cl_low_speed']
            cd0 = inputs['cd0_total_low_speed']
            cd_equilibrium = inputs['cd_eq_low_speed']
            cd_c = inputs['cd_comp_low_speed']
        else:
            cl = inputs['cl_high_speed']
            cd0 = inputs['cd0_total_high_speed']
            cd_equilibrium = inputs['cd_eq_high_speed']
            cd_c = inputs['cd_comp_high_speed']

        cd = []
        for i, cl_val in enumerate(cl):
            cd.append((cd0[i] + cd_c[i] + cd_equilibrium[i] +
                       coef_k * (
                           cl_val) ** 2 * k_winglet_cd + offset_winglet_cd) * k_cd + offset_cd)

        if self.low_speed_aero:
            outputs['aerodynamics:ClCd_low_speed'] = [cd, cl]
        else:
            outputs['aerodynamics:ClCd'] = [cd, cl]

            Cl_opt, Cd_opt = optimum_ClCd(outputs['aerodynamics:ClCd'])[0:2]
            outputs['aerodynamics:L_D_max'] = Cl_opt / Cd_opt
            outputs['aerodynamics:Cl_opt'] = Cl_opt
            outputs['aerodynamics:Cd_opt'] = Cd_opt


def optimum_ClCd(ClCd):
    optimum_ld = 0
    for i, elem in enumerate(ClCd[1]):
        if ClCd[1][i] / ClCd[0][i] > optimum_ld:
            optimum_ld = ClCd[1][i] / ClCd[0][i]
            optimum_index = i

    optimum_Cz = ClCd[1][optimum_index]
    optimum_Cd = ClCd[0][optimum_index]

    return optimum_Cz, optimum_Cd
