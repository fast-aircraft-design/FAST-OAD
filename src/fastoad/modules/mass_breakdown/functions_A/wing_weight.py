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
import math
import numpy as np
from openmdao.core.explicitcomponent import ExplicitComponent


class WingWeight(ExplicitComponent):
    # --------------------------------------------------------------
    #                     COMPONENTS WEIGHT ESTIMATION
    # ----------------------------------------------------------------
    #                                A1 - Wing
    # ----------------------------------------------------------------
    def setup(self):
        self.add_input('geometry:wing_toc_root', val=np.nan)
        self.add_input('geometry:wing_toc_kink', val=np.nan)
        self.add_input('geometry:wing_toc_tip', val=np.nan)
        self.add_input('geometry:wing_area', val=np.nan)
        self.add_input('geometry:wing_span', val=np.nan)
        self.add_input('geometry:wing_l2', val=np.nan)
        self.add_input('geometry:wing_sweep_25', val=np.nan)
        self.add_input('geometry:wing_area_pf', val=np.nan)
        self.add_input('weight:MTOW', val=np.nan)
        self.add_input('weight:MLW', val=np.nan)
        self.add_input('n1m1', val=np.nan)
        self.add_input('n2m2', val=np.nan)
        self.add_input('kfactors_a1:K_A1', val=1.)
        self.add_input('kfactors_a1:offset_A1', val=0.)
        self.add_input('kfactors_a1:K_A11', val=1.)
        self.add_input('kfactors_a1:offset_A11', val=0.)
        self.add_input('kfactors_a1:K_A12', val=1.)
        self.add_input('kfactors_a1:offset_A12', val=0.)
        self.add_input('kfactors_a1:K_A13', val=1.)
        self.add_input('kfactors_a1:offset_A13', val=0.)
        self.add_input('kfactors_a1:K_A14', val=1.)
        self.add_input('kfactors_a1:offset_A14', val=0.)
        self.add_input('kfactors_a1:K_A15', val=1.)
        self.add_input('kfactors_a1:offset_A15', val=0.)
        self.add_input('kfactors_a1:K_voil', val=1.)
        self.add_input('kfactors_a1:K_mvo', val=1.)

        self.add_output('weight_airframe:A1')

    def compute(self, inputs, outputs):
        toc_root = inputs['geometry:wing_toc_root']
        toc_kink = inputs['geometry:wing_toc_kink']
        toc_tip = inputs['geometry:wing_toc_tip']
        wing_area = inputs['geometry:wing_area']
        span = inputs['geometry:wing_span']
        l2_wing = inputs['geometry:wing_l2']
        sweep_25 = inputs['geometry:wing_sweep_25']
        S_pf = inputs['geometry:wing_area_pf']
        MTOW = inputs['weight:MTOW']
        MLW = inputs['weight:MLW']
        max_nm = max(inputs['n1m1'], inputs['n2m2'])

        # K factors
        K_A1 = inputs['kfactors_a1:K_A1']
        offset_A1 = inputs['kfactors_a1:offset_A1']
        K_A11 = inputs['kfactors_a1:K_A11']
        offset_A11 = inputs['kfactors_a1:offset_A11']
        K_A12 = inputs['kfactors_a1:K_A12']
        offset_A12 = inputs['kfactors_a1:offset_A12']
        K_A13 = inputs['kfactors_a1:K_A13']
        offset_A13 = inputs['kfactors_a1:offset_A13']
        K_A14 = inputs['kfactors_a1:K_A14']
        offset_A14 = inputs['kfactors_a1:offset_A14']
        K_A15 = inputs['kfactors_a1:K_A15']
        offset_A15 = inputs['kfactors_a1:offset_A15']
        K_voil = inputs['kfactors_a1:K_voil']
        K_mvo = inputs['kfactors_a1:K_mvo']

        toc_mean = (3 * toc_root + 2 * toc_kink + toc_tip) / 6

        temp_A11 = 5.922e-5 * K_voil * ((max_nm / (l2_wing * toc_mean)) \
                                        * (span / math.cos(
                    (sweep_25 / 180. * math.pi))) ** 2.0) ** 0.9
        weight_A11 = K_A11 * temp_A11 + offset_A11

        # A12=Mass of the wing due to shear
        temp_A12 = 5.184e-4 * K_voil * (max_nm * span / \
                                        math.cos((sweep_25 / 180. * math.pi))) ** 0.9
        weight_A12 = K_A12 * temp_A12 + offset_A12

        # A13=Mass of the wing due to the ribs
        temp_A13 = K_voil * (1.7009 * wing_area + 10 ** (-3) * max_nm)
        weight_A13 = K_A13 * temp_A13 + offset_A13

        # A14=Mass of the wing due to reinforcements
        temp_A14 = 4.4e-3 * K_voil * MLW ** 1.0169
        weight_A14 = K_A14 * temp_A14 + offset_A14

        # A15=Mass of the wing due to secondary parts
        temp_A15 = 0.3285 * K_voil * MTOW ** 0.35 * S_pf * K_mvo
        weight_A15 = K_A15 * temp_A15 + offset_A15

        temp_A1 = weight_A11 + weight_A12 + weight_A13 + weight_A14 + weight_A15

        A1 = K_A1 * temp_A1 + offset_A1

        outputs['weight_airframe:A1'] = A1
