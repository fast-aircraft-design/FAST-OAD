"""
    Estimation of vertical tail volume coefficient
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

class ComputeVTVolCoeff(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Vertical tail volume coefficient estimation """

    def initialize(self):
        self.options.declare('deriv_method', default='fd')

    def setup(self):
        deriv_method = self.options['deriv_method']

        self.add_input('geometry:vt_area', val=np.nan, units='m**2')
        self.add_input('geometry:vt_lp', val=np.nan, units='m')
        self.add_input('geometry:wing_area', val=np.nan, units='m**2')
        self.add_input('geometry:wing_span', val=np.nan, units='m')
        
        self.add_output('geometry:vt_vol_coeff')
        
        self.declare_partials('geometry:vt_vol_coeff', '*', method=deriv_method)
        
    def compute(self, inputs, outputs):
        outputs['geometry:vt_vol_coeff'] = inputs['geometry:vt_area'] * inputs['geometry:vt_lp'] / \
            (inputs['geometry:wing_area'] * inputs['geometry:wing_span'])