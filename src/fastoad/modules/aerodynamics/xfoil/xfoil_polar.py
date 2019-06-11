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
import shutil
import tempfile

import numpy as np
from openmdao.components.external_code_comp import ExternalCodeComp
from openmdao.utils.file_wrap import InputFileGenerator

_INPUT_FILE_NAME = 'polar_input.txt'
_STDOUT_FILE_NAME = 'polar_calc.log'
_PROFILE_FILE_NAME = 'profile.txt'  # as specified in input file
_RESULT_FILE_NAME = 'polar_result.txt'  # as specified in input file

_LOGGER = logging.getLogger(__name__)


class XfoilPolar(ExternalCodeComp):
    """
    Runs a polar computation with XFOIL and returns the max lift coefficient
    """

    def initialize(self):
        self.options.declare('xfoil_exe_path', types=str)
        self.options.declare('profile_path',
                             default=os.path.join(os.path.dirname(__file__), 'BACJ.txt'), types=str)
        self.options.declare('result_folder_path', types=str)
        self.options.declare('result_polar_file_name', default=_RESULT_FILE_NAME, types=str)

    def setup(self):
        self.options['external_input_files'] = [_INPUT_FILE_NAME, _PROFILE_FILE_NAME]
        self.options['external_output_files'] = [_RESULT_FILE_NAME]
        self.stdin = _INPUT_FILE_NAME
        self.stdout = _STDOUT_FILE_NAME
        self.options['command'] = [self.options['xfoil_exe_path']]

        self.add_input('xfoil:reynolds', val=np.nan)
        self.add_input('xfoil:mach', val=np.nan)
        self.add_input('geometry:wing_sweep_25', val=np.nan)

        self.add_output('aerodynamics:Cl_max_2D')
        self.add_output('aerodynamics:Cl_max_clean')

    def compute(self, inputs, outputs):

        # Create result folder first (if it must fail, let it fail as soon as possible)
        result_folder_path = self.options['result_folder_path']
        os.makedirs(result_folder_path, exist_ok=True)
        stdout_file_path = pth.join(result_folder_path, _STDOUT_FILE_NAME)
        polar_file_path = pth.join(result_folder_path, self.options['result_polar_file_name'])

        # Get inputs
        reynolds = inputs['xfoil:reynolds']
        mach = inputs['xfoil:mach']
        sweep_25 = inputs['geometry:wing_sweep_25']

        # Pre-processing
        tmp_directory = tempfile.TemporaryDirectory()

        # profile file
        tmp_profile_file_path = pth.join(tmp_directory.name, _PROFILE_FILE_NAME)
        shutil.copy(self.options['profile_path'], tmp_profile_file_path)

        # input file
        parser = InputFileGenerator()
        parser.set_template_file(pth.join(os.path.dirname(__file__), _INPUT_FILE_NAME))
        parser.set_generated_file(pth.join(tmp_directory.name, _INPUT_FILE_NAME))
        parser.mark_anchor('RE')
        parser.transfer_var(reynolds, 1, 1)
        parser.mark_anchor('M')
        parser.transfer_var(mach, 1, 1)
        parser.generate()

        # Run XFOIL
        current_working_directory = os.getcwd()
        os.chdir(tmp_directory.name)
        super(XfoilPolar, self).compute(inputs, outputs)
        shutil.move(_STDOUT_FILE_NAME, stdout_file_path)
        os.chdir(current_working_directory)

        # Post-process
        tmp_result_file_path = pth.join(tmp_directory.name, _RESULT_FILE_NAME)
        cl_max_2d = self._get_max_cl(tmp_result_file_path)

        outputs['aerodynamics:Cl_max_2D'] = cl_max_2d
        outputs['aerodynamics:Cl_max_clean'] = cl_max_2d * 0.9 * np.cos(np.radians(sweep_25))

        shutil.move(tmp_result_file_path, polar_file_path)
        tmp_directory.cleanup()

    @staticmethod
    def _get_max_cl(xfoil_result_file_path):
        """
            :param xfoil_result_file_path:
            :return: maximum lift coefficient Cl value.
        """
        if os.path.isfile(xfoil_result_file_path):
            result_array = np.genfromtxt(xfoil_result_file_path, skip_header=12,
                                         dtype=[('alpha', 'f8'), ('CL', 'f8'), ('CD', 'f8'),
                                                ('CDp', 'f8'), ('CM', 'f8'), ('Top_Xtr', 'f8'),
                                                ('Bot_Xtr', 'f8')])
            alpha = result_array['alpha']
            lift_coeff = result_array['CL']

            if max(alpha) >= 5.0:
                max_cl = max(lift_coeff)
            else:
                max_cl = 1.9
                _LOGGER.error('CL max not found!')
        else:
            max_cl = 1.9
            _LOGGER.error('XFOIL results file not found')

        return max_cl
