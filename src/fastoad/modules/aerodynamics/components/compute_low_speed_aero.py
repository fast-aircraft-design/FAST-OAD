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

from math import sqrt, pi, tan

import numpy as np
from openmdao.core.explicitcomponent import ExplicitComponent


class ComputeAerodynamicsLowSpeed(ExplicitComponent):
    """
    Czalpha from Raymer Eq 12.6
    TODO: complete source
    """
    def setup(self):
        self.add_input('geometry:fuselage:maximum_width', val=np.nan, units='m')
        self.add_input('geometry:fuselage:maximum_height', val=np.nan, units='m')
        self.add_input('geometry:wing:span', val=np.nan, units='m')
        self.add_input('geometry:wing:aspect_ratio', val=np.nan)
        self.add_input('geometry:wing:tip:chord', val=np.nan, units='m')
        self.add_input('geometry:wing:sweep_25', val=np.nan, units='deg')
        self.add_input('geometry:wing:root:chord', val=np.nan, units='m')
        self.add_input('geometry:wing:area', val=np.nan, units='m**2')
        self.add_input('geometry:wing:tip:thickness_ratio', val=np.nan)

        self.add_output('aerodynamics:aircraft:takeoff:CL_alpha', units='1/rad')
        self.add_output('aerodynamics:aircraft:cruise:CL0')

    def compute(self, inputs, outputs):
        width_max = inputs['geometry:fuselage:maximum_width']
        height_max = inputs['geometry:fuselage:maximum_height']
        span = inputs['geometry:wing:span']
        lambda_wing = inputs['geometry:wing:aspect_ratio']
        l2_wing = inputs['geometry:wing:root:chord']
        l4_wing = inputs['geometry:wing:tip:chord']
        el_ext = inputs['geometry:wing:tip:thickness_ratio']
        sweep_25 = inputs['geometry:wing:sweep_25']
        wing_area = inputs['geometry:wing:area']

        mach = 0.2

        beta = sqrt(1 - mach ** 2)
        d_f = sqrt(width_max * height_max)
        fact_F = 1.07 * (1 + d_f / span) ** 2
        lambda_wing_eff = lambda_wing * (1 + 1.9 * l4_wing * el_ext / span)
        cl_alpha_wing_low = 2 * pi * lambda_wing_eff / \
                            (2 + sqrt(4 + lambda_wing_eff ** 2 * beta ** 2 / 0.95 ** 2 * (
                                    1 + (tan(sweep_25 / 180. * pi)) ** 2 / beta ** 2))) * \
                            (wing_area - l2_wing * width_max) / wing_area * fact_F

        outputs['aerodynamics:aircraft:takeoff:CL_alpha'] = cl_alpha_wing_low
        outputs['aerodynamics:aircraft:cruise:CL0'] = 0.2  # FIXME: hard-coded value
