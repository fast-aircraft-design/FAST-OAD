"""
    Estimation of max fuel weight
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

class ComputeMFW(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Max fuel weight estimation """

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:wing_area', val=np.nan)
        self.add_input('geometry:wing_aspect_ratio', val=np.nan)
        self.add_input('geometry:wing_toc_root', val=np.nan)
        self.add_input('geometry:wing_toc_tip', val=np.nan)
        
        self.add_output('weight:MFW')
        
        self.declare_partials('weight:MFW', '*', method=deriv_method)
        
    def compute(self, inputs, outputs):
        wing_area = inputs['geometry:wing_area']
        lambda_wing = inputs['geometry:wing_aspect_ratio']
        el_emp = inputs['geometry:wing_toc_root']
        el_ext = inputs['geometry:wing_toc_tip']
        
        mfw = 224 * (wing_area ** 1.5 * lambda_wing ** (-0.4)
                     * (0.6 * el_emp + 0.4 * el_ext)) + 1570

        outputs['weight:MFW'] = mfw   
        