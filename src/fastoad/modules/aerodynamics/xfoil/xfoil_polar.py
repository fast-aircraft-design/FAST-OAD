"""
This module launches XFOIL computations
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
import logging
import os
import os.path as pth

import numpy as np
from openmdao.utils.file_wrap import InputFileGenerator

from fastoad.modules.aerodynamics.xfoil.xfoil_computation import XfoilInputFileGenerator, \
    XfoilComputation

_INPUT_FILE_NAME = 'polar_input.txt'

_LOGGER = logging.getLogger(__name__)


class XfoilPolar(XfoilComputation):
    """
    Runs a polar computation with XFOIL and returns the max lift coefficient
    """

    def setup(self):
        super(XfoilPolar, self).setup()
        self.options['input_file_generator'] = PolarIFG()
        self.add_input('geometry:wing_sweep_25', val=np.nan)
        self.add_output('aerodynamics:Cl_max_2D')
        self.add_output('aerodynamics:Cl_max_clean')

    _xfoil_output_names = ['alpha', 'CL', 'CD', 'CDp', 'CM', 'Top_Xtr', 'Bot_Xtr']
    """Column names in XFOIL polar result"""

    def compute(self, inputs, outputs):

        super(XfoilPolar, self).compute(inputs, outputs)

        if 'xfoil:alpha' in outputs:
            cl_max_2d = self._get_max_cl(outputs['xfoil:alpha'], outputs['xfoil:CL'])
        else:
            cl_max_2d = 1.9

        sweep_25 = inputs['geometry:wing_sweep_25']
        outputs['aerodynamics:Cl_max_2D'] = cl_max_2d
        outputs['aerodynamics:Cl_max_clean'] = cl_max_2d * 0.9 * np.cos(np.radians(sweep_25))

    @staticmethod
    def _get_max_cl(alpha: np.ndarray, lift_coeff: np.ndarray) -> float:
        """

        :param alpha:
        :param lift_coeff: CL
        :return: max CL if enough alpha computed
        """
        if max(alpha) >= 5.0:
            return max(lift_coeff)

        _LOGGER.error('CL max not found!')
        return 1.9


# pylint: disable=too-few-public-methods
class PolarIFG(XfoilInputFileGenerator):
    """ Input file generator for a polar XFOIL computation """

    def __init__(self):
        super(PolarIFG, self).__init__(pth.join(os.path.dirname(__file__), _INPUT_FILE_NAME))

    def _transfer_vars(self, parser: InputFileGenerator, inputs: dict):
        parser.mark_anchor('RE')
        parser.transfer_var(inputs['profile:reynolds'], 1, 1)
        parser.mark_anchor('M')
        parser.transfer_var(inputs['profile:mach'], 1, 1)
