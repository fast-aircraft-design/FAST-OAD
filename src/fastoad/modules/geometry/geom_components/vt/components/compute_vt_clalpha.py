"""
    Estimation of vertical tail lift coefficient
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


# TODO: This belongs more to aerodynamics than geometry
class ComputeVTClalpha(ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Vertical tail lift coefficient estimation """

    def setup(self):

        self.add_input('tlar:cruise_Mach', val=np.nan)
        self.add_input('geometry:vt_aspect_ratio', val=np.nan)
        self.add_input('geometry:vt_sweep_25', val=np.nan, units='deg')
        self.add_input('k_ar_effective', val=np.nan)

        self.add_output('aerodynamics:Cl_alpha_vt')

        self.declare_partials('aerodynamics:Cl_alpha_vt', '*', method='fd')

    def compute(self, inputs, outputs):
        cruise_mach = inputs['tlar:cruise_Mach']
        k_ar_effective = inputs['k_ar_effective']
        sweep_25_vt = inputs['geometry:vt_sweep_25']
        lambda_vt = inputs['geometry:vt_aspect_ratio']

        beta = math.sqrt(1 - cruise_mach ** 2)
        lambda_vt *= k_ar_effective
        cl_alpha_vt = 0.8 * 2 * math.pi * lambda_vt / \
                      (2 + math.sqrt(4 + lambda_vt ** 2 * beta ** 2 / 0.95 ** \
                       2 * (1 + (math.tan(sweep_25_vt / 180. * math.pi)) ** 2 \
                       / beta ** 2)))

        outputs['aerodynamics:Cl_alpha_vt'] = cl_alpha_vt
