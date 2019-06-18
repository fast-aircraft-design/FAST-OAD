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
_STDERR_FILE_NAME = 'polar_calc.err'
_PROFILE_FILE_NAME = 'profile.txt'  # as specified in input file
_RESULT_FILE_NAME = 'polar_result.txt'  # as specified in input file

_LOGGER = logging.getLogger(__name__)


class XfoilPolar(ExternalCodeComp):
    """
    Runs a polar computation with XFOIL and returns the max lift coefficient
    """

    _xfoil_output_names = ['alpha', 'CL', 'CD', 'CDp', 'CM', 'Top_Xtr', 'Bot_Xtr']
    """Column names in XFOIL polar result"""

    def initialize(self):
        self.options.declare('xfoil_exe_path', types=str)
        self.options.declare('profile_path',
                             default=os.path.join(os.path.dirname(__file__), 'BACJ.txt'), types=str)
        self.options.declare('result_folder_path', default='', types=str)
        self.options.declare('result_polar_file_name', default=_RESULT_FILE_NAME, types=str)

    def setup(self):
        self.options['command'] = [self.options['xfoil_exe_path']]

        self.add_input('xfoil:reynolds', val=np.nan)
        self.add_input('xfoil:mach', val=np.nan)
        self.add_input('geometry:wing_sweep_25', val=np.nan)

        self.add_output('aerodynamics:Cl_max_2D')
        self.add_output('aerodynamics:Cl_max_clean')

        for name in self._xfoil_output_names:
            self.add_output('xfoil:%s' % name)

    def compute(self, inputs, outputs):

        # Create result folder first (if it must fail, let it fail as soon as possible)
        result_folder_path = self.options['result_folder_path']
        if result_folder_path != '':
            os.makedirs(result_folder_path, exist_ok=True)

        # Get inputs
        reynolds = inputs['xfoil:reynolds']
        mach = inputs['xfoil:mach']
        sweep_25 = inputs['geometry:wing_sweep_25']

        # Pre-processing (populating temp directory)
        tmp_directory = tempfile.TemporaryDirectory(prefix='xfl')
        tmp_profile_file_path = pth.join(tmp_directory.name, _PROFILE_FILE_NAME)
        self.stdin = pth.join(tmp_directory.name, _INPUT_FILE_NAME)
        self.stdout = pth.join(tmp_directory.name, _STDOUT_FILE_NAME)
        self.stderr = pth.join(tmp_directory.name, _STDERR_FILE_NAME)
        tmp_result_file_path = pth.join(tmp_directory.name, _RESULT_FILE_NAME)

        # profile file
        shutil.copy(self.options['profile_path'], tmp_profile_file_path)

        # standard input file
        parser = InputFileGenerator()
        parser.set_template_file(pth.join(os.path.dirname(__file__), _INPUT_FILE_NAME))
        parser.set_generated_file(self.stdin)
        parser.mark_anchor('LOAD')
        parser.transfer_var(tmp_profile_file_path, 1, 1)
        parser.mark_anchor('RE')
        parser.transfer_var(float(reynolds), 1, 1)
        parser.mark_anchor('M')
        parser.transfer_var(float(mach), 1, 1)
        parser.mark_anchor(_RESULT_FILE_NAME)
        parser.transfer_var(tmp_result_file_path, 0, 1)
        parser.generate()

        # Run XFOIL
        self.options['external_input_files'] = [self.stdin, tmp_profile_file_path]
        self.options['external_output_files'] = [tmp_result_file_path]
        super(XfoilPolar, self).compute(inputs, outputs)

        # Post-processing
        result_array = self._read_polar(tmp_result_file_path)
        if result_array is not None:
            for name in self._xfoil_output_names:
                outputs['xfoil:%s' % name] = result_array[name]
            cl_max_2d = self._get_max_cl(result_array['alpha'], result_array['CL'])
        else:
            cl_max_2d = 1.9

        outputs['aerodynamics:Cl_max_2D'] = cl_max_2d
        outputs['aerodynamics:Cl_max_clean'] = cl_max_2d * 0.9 * np.cos(np.radians(sweep_25))

        # Getting output files if needed
        if self.options['result_folder_path'] != '':
            if pth.exists(tmp_result_file_path):
                polar_file_path = pth.join(result_folder_path,
                                           self.options['result_polar_file_name'])
                shutil.move(tmp_result_file_path, polar_file_path)

            if pth.exists(self.stdout):
                stdout_file_path = pth.join(result_folder_path, _STDOUT_FILE_NAME)
                shutil.move(self.stdout, stdout_file_path)

            if pth.exists(self.stderr):
                stderr_file_path = pth.join(result_folder_path, _STDERR_FILE_NAME)
                shutil.move(self.stderr, stderr_file_path)

        tmp_directory.cleanup()

    @staticmethod
    def _read_polar(xfoil_result_file_path: str) -> np.ndarray:
        """
        :param xfoil_result_file_path:
        :return: numpy array with XFoil polar results
        """
        if os.path.isfile(xfoil_result_file_path):
            dtypes = [(name, 'f8') for name in XfoilPolar._xfoil_output_names]
            result_array = np.genfromtxt(xfoil_result_file_path, skip_header=12,
                                         dtype=dtypes)
            return result_array

        _LOGGER.error('XFOIL results file not found')
        return None

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
