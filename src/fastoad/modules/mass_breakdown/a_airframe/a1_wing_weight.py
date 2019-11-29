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
        self.add_input('geometry:wing:root:thickness_ratio', val=np.nan)
        self.add_input('geometry:wing:kink:thickness_ratio', val=np.nan)
        self.add_input('geometry:wing:tip:thickness_ratio', val=np.nan)
        self.add_input('geometry:wing:area', val=np.nan, units='m**2')
        self.add_input('geometry:wing:span', val=np.nan, units='m')
        self.add_input('geometry:wing:root:chord', val=np.nan, units='m')
        self.add_input('geometry:wing:sweep_25', val=np.nan, units='deg')  # TODO : as radians ?
        self.add_input('geometry:wing:cantilever_area', val=np.nan, units='m**2')
        self.add_input('weight:aircraft:MTOW', val=np.nan, units='kg')
        self.add_input('weight:aircraft:MLW', val=np.nan, units='kg')
        self.add_input('n1m1', val=np.nan, units='kg')
        self.add_input('n2m2', val=np.nan, units='kg')
        self.add_input('weight:airframe:wing:mass:k', val=1.)
        self.add_input('weight:airframe:wing:mass:offset', val=0., units='kg')
        self.add_input('weight:airframe:wing:bending_sizing:mass:k', val=1.)
        self.add_input('weight:airframe:wing:bending_sizing:mass:offset', val=0., units='kg')
        self.add_input('weight:airframe:wing:shear_sizing:mass:k', val=1.)
        self.add_input('weight:airframe:wing:shear_sizing:mass:offset', val=0., units='kg')
        self.add_input('weight:airframe:wing:ribs:mass:k', val=1.)
        self.add_input('weight:airframe:wing:ribs:mass:offset', val=0., units='kg')
        self.add_input('weight:airframe:wing:reinforcements:mass:k', val=1.)
        self.add_input('weight:airframe:wing:reinforcements:mass:offset', val=0., units='kg')
        self.add_input('weight:airframe:wing:secondary_parts:mass:k', val=1.)
        self.add_input('weight:airframe:wing:secondary_parts:mass:offset', val=0., units='kg')
        self.add_input('weight:airframe:wing:mass:k_voil', val=1.)
        self.add_input('weight:airframe:wing:mass:k_mvo', val=1.)

        self.add_output('weight:airframe:wing:mass', units='kg')

    # pylint: disable=too-many-locals
    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        toc_root = inputs['geometry:wing:root:thickness_ratio']
        toc_kink = inputs['geometry:wing:kink:thickness_ratio']
        toc_tip = inputs['geometry:wing:tip:thickness_ratio']
        wing_area = inputs['geometry:wing:area']
        span = inputs['geometry:wing:span']
        l2_wing = inputs['geometry:wing:root:chord']
        sweep_25 = inputs['geometry:wing:sweep_25']
        cantilevered_area = inputs['geometry:wing:cantilever_area']
        mtow = inputs['weight:aircraft:MTOW']
        mlw = inputs['weight:aircraft:MLW']
        max_nm = max(inputs['n1m1'], inputs['n2m2'])

        # K factors
        k_a1 = inputs['weight:airframe:wing:mass:k']
        offset_a1 = inputs['weight:airframe:wing:mass:offset']
        k_a11 = inputs['weight:airframe:wing:bending_sizing:mass:k']
        offset_a11 = inputs['weight:airframe:wing:bending_sizing:mass:offset']
        k_a12 = inputs['weight:airframe:wing:shear_sizing:mass:k']
        offset_a12 = inputs['weight:airframe:wing:shear_sizing:mass:offset']
        k_a13 = inputs['weight:airframe:wing:ribs:mass:k']
        offset_a13 = inputs['weight:airframe:wing:ribs:mass:offset']
        k_a14 = inputs['weight:airframe:wing:reinforcements:mass:k']
        offset_a14 = inputs['weight:airframe:wing:reinforcements:mass:offset']
        k_a15 = inputs['weight:airframe:wing:secondary_parts:mass:k']
        offset_a15 = inputs['weight:airframe:wing:secondary_parts:mass:offset']
        k_voil = inputs['weight:airframe:wing:mass:k_voil']
        k_mvo = inputs['weight:airframe:wing:mass:k_mvo']

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

        outputs['weight:airframe:wing:mass'] = k_a1 * temp_a1 + offset_a1
