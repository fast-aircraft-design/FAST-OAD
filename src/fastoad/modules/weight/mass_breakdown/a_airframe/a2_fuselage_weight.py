"""
Estimation of fuselage weight
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA/ISAE
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


class FuselageWeight(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Fuselage weight estimation (A2) """

    def setup(self):
        self.add_input('data:geometry:fuselage:wetted_area', val=np.nan, units='m**2')
        self.add_input('data:geometry:fuselage:maximum_width', val=np.nan, units='m')
        self.add_input('data:geometry:fuselage:maximum_height', val=np.nan, units='m')
        self.add_input('data:mission:sizing:cs25:sizing_load_1', val=np.nan, units='kg')
        self.add_input('tuning:weight:airframe:fuselage:mass:k', val=1.)
        self.add_input('tuning:weight:airframe:fuselage:mass:offset', val=0., units='kg')
        self.add_input('settings:weight:airframe:fuselage:mass:k_lg', val=1.05)
        self.add_input('settings:weight:airframe:fuselage:mass:k_fus', val=1.)

        self.add_output('data:weight:airframe:fuselage:mass', units='kg')

    def compute(self, inputs, outputs
                , discrete_inputs=None, discrete_outputs=None):
        fuselage_wet_area = inputs['data:geometry:fuselage:wetted_area']
        width_max = inputs['data:geometry:fuselage:maximum_width']
        height_max = inputs['data:geometry:fuselage:maximum_height']
        n1m1 = inputs['data:mission:sizing:cs25:sizing_load_1']
        k_a2 = inputs['tuning:weight:airframe:fuselage:mass:k']
        offset_a2 = inputs['tuning:weight:airframe:fuselage:mass:offset']
        k_lg = inputs['settings:weight:airframe:fuselage:mass:k_lg']
        k_fus = inputs['settings:weight:airframe:fuselage:mass:k_fus']

        temp_a2 = fuselage_wet_area * (10 + 1.2 * np.sqrt(width_max * height_max)
                                       + 0.00019 * n1m1 / height_max ** 1.7) * k_lg * k_fus
        outputs['data:weight:airframe:fuselage:mass'] = k_a2 * temp_a2 + offset_a2
