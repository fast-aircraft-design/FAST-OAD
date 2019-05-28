"""
    Estimation of horizontal tail lift coefficient
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
import math 

from openmdao.core.explicitcomponent import ExplicitComponent

class ComputeHTClalpha(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Horizontal tail lift coefficient estimation """

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:ht_aspect_ratio', val=np.nan)
        self.add_input('tlar:cruise_Mach', val=npn.nan)
        self.add_input('geometry:ht_sweep_25', val=np.nan)
        
        self.add_output('aerodynamics:Cl_alpha_ht')
        
        self.declare_partials('aerodynamics:Cl_alpha_ht', '*', method=deriv_method)
        
    def compute(self, inputs, outputs):
        cruise_Mach = inputs['tlar:cruise_Mach']
        lambda_ht = inputs['geometry:ht_aspect_ratio']
        sweep_25_ht = inputs['geometry:ht_sweep_25']
        
        beta = math.sqrt(1 - cruise_Mach**2)
        cl_alpha_ht = 0.8 * 2 * math.pi * lambda_ht / \
            (2 + math.sqrt(4 + lambda_ht**2 * beta**2 / 0.95 **
                           2 * (1 + (math.tan(sweep_25_ht / 180. * math.pi))**2 / beta**2)))
            
        outputs['aerodynamics:Cl_alpha_ht'] = cl_alpha_ht