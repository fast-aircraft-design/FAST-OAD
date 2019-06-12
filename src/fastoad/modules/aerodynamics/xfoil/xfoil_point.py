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

_INPUT_FILE_NAME = 'point_input.txt'

_LOGGER = logging.getLogger(__name__)


class XfoilPoint(XfoilComputation):
    """
    Runs a point computation with XFOIL and returns the max lift coefficient
    """

    def setup(self):
        super(XfoilPoint, self).setup()
        self.options['input_file_generator'] = PointIFG()
        self.add_input('profile:alpha', val=np.nan)


# pylint: disable=too-few-public-methods
class PointIFG(XfoilInputFileGenerator):
    """ Input file generator for a single alpha XFOIL computation """

    def __init__(self):
        super(PointIFG, self).__init__(pth.join(os.path.dirname(__file__), _INPUT_FILE_NAME))

    def _transfer_vars(self, parser: InputFileGenerator, inputs: dict):
        parser.mark_anchor('RE')
        parser.transfer_var(inputs['profile:reynolds'], 1, 1)
        parser.mark_anchor('M')
        parser.transfer_var(inputs['profile:mach'], 1, 1)
        parser.mark_anchor('ALFA')
        parser.transfer_var(inputs['profile:alpha'], 1, 1)
