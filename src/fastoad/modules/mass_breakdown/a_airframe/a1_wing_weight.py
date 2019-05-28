"""
Estimation of wing weight
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


class WingWeight(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Wing weight estimation (A1) """

    def setup(self):
        self.add_input('geometry:wing_toc_root', val=np.nan)
        self.add_input('geometry:wing_toc_kink', val=np.nan)
        self.add_input('geometry:wing_toc_tip', val=np.nan)
        self.add_input('geometry:wing_area', val=np.nan, units='m**2')
        self.add_input('geometry:wing_span', val=np.nan, units='m')
        self.add_input('geometry:wing_l2', val=np.nan, units='m')
        self.add_input('geometry:wing_sweep_25', val=np.nan, units='deg')  # TODO : as radians ?
        self.add_input('geometry:wing_area_pf', val=np.nan, units='m**2')
        self.add_input('weight:MTOW', val=np.nan, units='kg')
        self.add_input('weight:MLW', val=np.nan, units='kg')
        self.add_input('n1m1', val=np.nan, units='kg')
        self.add_input('n2m2', val=np.nan, units='kg')
        self.add_input('kfactors_a1:K_A1', val=1.)
        self.add_input('kfactors_a1:offset_A1', val=0., units='kg')
        self.add_input('kfactors_a1:K_A11', val=1.)
        self.add_input('kfactors_a1:offset_A11', val=0., units='kg')
        self.add_input('kfactors_a1:K_A12', val=1.)
        self.add_input('kfactors_a1:offset_A12', val=0., units='kg')
        self.add_input('kfactors_a1:K_A13', val=1.)
        self.add_input('kfactors_a1:offset_A13', val=0., units='kg')
        self.add_input('kfactors_a1:K_A14', val=1.)
        self.add_input('kfactors_a1:offset_A14', val=0., units='kg')
        self.add_input('kfactors_a1:K_A15', val=1.)
        self.add_input('kfactors_a1:offset_A15', val=0., units='kg')
        self.add_input('kfactors_a1:K_voil', val=1.)
        self.add_input('kfactors_a1:K_mvo', val=1.)

        self.add_output('weight_airframe:A1', units='kg')

    # pylint: disable=too-many-locals
    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        toc_root = inputs['geometry:wing_toc_root']
        toc_kink = inputs['geometry:wing_toc_kink']
        toc_tip = inputs['geometry:wing_toc_tip']
        wing_area = inputs['geometry:wing_area']
        span = inputs['geometry:wing_span']
        l2_wing = inputs['geometry:wing_l2']
        sweep_25 = inputs['geometry:wing_sweep_25']
        cantilevered_area = inputs['geometry:wing_area_pf']
        mtow = inputs['weight:MTOW']
        mlw = inputs['weight:MLW']
        max_nm = max(inputs['n1m1'], inputs['n2m2'])

        # K factors
        k_a1 = inputs['kfactors_a1:K_A1']
        offset_a1 = inputs['kfactors_a1:offset_A1']
        k_a11 = inputs['kfactors_a1:K_A11']
        offset_a11 = inputs['kfactors_a1:offset_A11']
        k_a12 = inputs['kfactors_a1:K_A12']
        offset_a12 = inputs['kfactors_a1:offset_A12']
        k_a13 = inputs['kfactors_a1:K_A13']
        offset_a13 = inputs['kfactors_a1:offset_A13']
        k_a14 = inputs['kfactors_a1:K_A14']
        offset_a14 = inputs['kfactors_a1:offset_A14']
        k_a15 = inputs['kfactors_a1:K_A15']
        offset_a15 = inputs['kfactors_a1:offset_A15']
        k_voil = inputs['kfactors_a1:K_voil']
        k_mvo = inputs['kfactors_a1:K_mvo']

        toc_mean = (3 * toc_root + 2 * toc_kink + toc_tip) / 6

        # A11=Mass of the wing due to flexion
        temp_a11 = 5.922e-5 * k_voil * ((max_nm / (l2_wing * toc_mean)) * (
                span / np.cos(np.radians(sweep_25))) ** 2.0) ** 0.9
        weight_a11 = k_a11 * temp_a11 + offset_a11

        # A12=Mass of the wing due to shear
        temp_a12 = 5.184e-4 * k_voil * (
                max_nm * span / np.cos((np.radians(sweep_25)))) ** 0.9
        weight_a12 = k_a12 * temp_a12 + offset_a12

        # A13=Mass of the wing due to the ribs
        temp_a13 = k_voil * (1.7009 * wing_area + 10 ** (-3) * max_nm)
        weight_a13 = k_a13 * temp_a13 + offset_a13

        # A14=Mass of the wing due to reinforcements
        temp_a14 = 4.4e-3 * k_voil * mlw ** 1.0169
        weight_a14 = k_a14 * temp_a14 + offset_a14

        # A15=Mass of the wing due to secondary parts
        temp_a15 = 0.3285 * k_voil * mtow ** 0.35 * cantilevered_area * k_mvo
        weight_a15 = k_a15 * temp_a15 + offset_a15

        temp_a1 = weight_a11 + weight_a12 + weight_a13 \
                  + weight_a14 + weight_a15

        outputs['weight_airframe:A1'] = k_a1 * temp_a1 + offset_a1
