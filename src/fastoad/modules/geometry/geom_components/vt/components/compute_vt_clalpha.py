"""
    Estimation of vertical tail lift coefficient
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

import math

import numpy as np
import openmdao.api as om

# TODO: This belongs more to aerodynamics than geometry
from fastoad.modules.geometry.options import TAIL_TYPE_OPTION


class ComputeVTClalpha(om.ExplicitComponent):
    # TODO: Document equations. Cite sources
    """ Vertical tail lift coefficient estimation """

    def initialize(self):
        self.options.declare(TAIL_TYPE_OPTION, types=float, default=0.)

    def setup(self):
        self.add_input('TLAR:cruise_mach', val=np.nan)
        self.add_input('geometry:vertical_tail:aspect_ratio', val=np.nan)
        self.add_input('geometry:vertical_tail:sweep_25', val=np.nan, units='deg')

        self.add_output('aerodynamics:vertical_tail:cruise:CL_alpha')

        self.declare_partials('aerodynamics:vertical_tail:cruise:CL_alpha', '*', method='fd')

    def compute(self, inputs, outputs):
        cruise_mach = inputs['TLAR:cruise_mach']
        sweep_25_vt = inputs['geometry:vertical_tail:sweep_25']
        k_ar_effective = 2.9 if self.options[TAIL_TYPE_OPTION] == 1.0 else 1.55
        lambda_vt = inputs['geometry:vertical_tail:aspect_ratio'] * k_ar_effective

        beta = math.sqrt(1 - cruise_mach ** 2)
        cl_alpha_vt = 0.8 * 2 * math.pi * lambda_vt / \
                      (2 + math.sqrt(4 + lambda_vt ** 2 * beta ** 2 / 0.95 ** \
                                     2 * (1 + (math.tan(sweep_25_vt / 180. * math.pi)) ** 2 \
                                          / beta ** 2)))

        outputs['aerodynamics:vertical_tail:cruise:CL_alpha'] = cl_alpha_vt
