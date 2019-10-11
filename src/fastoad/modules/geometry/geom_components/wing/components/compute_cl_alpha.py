"""
    Estimation of wing lift coefficient
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
import math
import numpy as np

from openmdao.core.explicitcomponent import ExplicitComponent


class ComputeCLalpha(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Wing lift coefficient estimation """

    def setup(self):

        self.add_input('tlar:cruise_Mach', val=np.nan)
        self.add_input('geometry:fuselage_width_max', val=np.nan, units='m')
        self.add_input('geometry:fuselage_height_max', val=np.nan, units='m')
        self.add_input('geometry:wing_area', val=np.nan, units='m**2')
        self.add_input('geometry:wing_l2', val=np.nan, units='m')
        self.add_input('geometry:wing_l4', val=np.nan, units='m')
        self.add_input('geometry:wing_toc_tip', val=np.nan)
        self.add_input('geometry:wing_sweep_25', val=np.nan, units='deg')
        self.add_input('geometry:wing_aspect_ratio', val=np.nan)
        self.add_input('geometry:wing_span', val=np.nan, units='m')

        self.add_output('aerodynamics:Cl_alpha')

        self.declare_partials('aerodynamics:Cl_alpha', '*', method='fd')

    def compute(self, inputs, outputs):
        cruise_mach = inputs['tlar:cruise_Mach']
        width_max = inputs['geometry:fuselage_width_max']
        height_max = inputs['geometry:fuselage_height_max']
        span = inputs['geometry:wing_span']
        lambda_wing = inputs['geometry:wing_aspect_ratio']
        el_ext = inputs['geometry:wing_toc_tip']
        wing_area = inputs['geometry:wing_area']
        l2_wing = inputs['geometry:wing_l2']
        l4_wing = inputs['geometry:wing_l4']
        sweep_25 = inputs['geometry:wing_sweep_25']

        beta = math.sqrt(1 - cruise_mach ** 2)
        d_f = math.sqrt(width_max * height_max)
        fact_f = 1.07 * (1 + d_f / span) ** 2
        lambda_wing_eff = lambda_wing * (1 + 1.9 * l4_wing * el_ext / span)
        cl_alpha_wing = 2 * math.pi * lambda_wing_eff / \
                        (2 + math.sqrt(4 + lambda_wing_eff ** 2 * beta ** 2 / 0.95 ** 2 * (
                                1 + (math.tan(sweep_25 / 180. * math.pi)) ** 2 / beta ** 2))) * \
                        (wing_area - l2_wing * width_max) / wing_area * fact_f

        outputs['aerodynamics:Cl_alpha'] = cl_alpha_wing
