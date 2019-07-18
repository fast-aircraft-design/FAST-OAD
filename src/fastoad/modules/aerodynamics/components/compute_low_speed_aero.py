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
from math import sqrt, pi, tan
from openmdao.core.explicitcomponent import ExplicitComponent


class ComputeAerodynamicsLowSpeed(ExplicitComponent):
    """
    Czalpha from Raymer Eq 12.6
    TODO: complete source
    """
    def setup(self):
        self.add_input('geometry:fuselage_width_max', val=np.nan, units='m')
        self.add_input('geometry:fuselage_height_max', val=np.nan, units='m')
        self.add_input('geometry:wing_span', val=np.nan, units='m')
        self.add_input('geometry:wing_aspect_ratio', val=np.nan)
        self.add_input('geometry:wing_l4', val=np.nan, units='m')
        self.add_input('geometry:wing_sweep_25', val=np.nan, units='deg')
        self.add_input('geometry:wing_l2', val=np.nan, units='m')
        self.add_input('geometry:wing_area', val=np.nan, units='m**2')
        self.add_input('geometry:wing_toc_tip', val=np.nan)

        self.add_output('aerodynamics:Cl_alpha_low', val=np.nan, units='1/rad')
        self.add_output('aerodynamics:Cl_0_AoA', val=np.nan)

    def compute(self, inputs, outputs):
        width_max = inputs['geometry:fuselage_width_max']
        height_max = inputs['geometry:fuselage_height_max']
        span = inputs['geometry:wing_span']
        lambda_wing = inputs['geometry:wing_aspect_ratio']
        l2_wing = inputs['geometry:wing_l2']
        l4_wing = inputs['geometry:wing_l4']
        el_ext = inputs['geometry:wing_toc_tip']
        sweep_25 = inputs['geometry:wing_sweep_25']
        wing_area = inputs['geometry:wing_area']

        mach = 0.2

        beta = sqrt(1 - mach ** 2)
        d_f = sqrt(width_max * height_max)
        fact_F = 1.07 * (1 + d_f / span) ** 2
        lambda_wing_eff = lambda_wing * (1 + 1.9 * l4_wing * el_ext / span)
        cl_alpha_wing_low = 2 * pi * lambda_wing_eff / \
                            (2 + sqrt(4 + lambda_wing_eff ** 2 * beta ** 2 / 0.95 ** 2 * (
                                    1 + (tan(sweep_25 / 180. * pi)) ** 2 / beta ** 2))) * \
                            (wing_area - l2_wing * width_max) / wing_area * fact_F

        outputs['aerodynamics:Cl_alpha_low'] = cl_alpha_wing_low
        outputs['aerodynamics:Cl_0_AoA'] = 0.02  # FIXME: hard-coded value
