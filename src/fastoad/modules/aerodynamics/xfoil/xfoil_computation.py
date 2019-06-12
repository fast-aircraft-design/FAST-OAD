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
from abc import ABC, abstractmethod
from typing import TypeVar

import numpy as np
from openmdao.components.external_code_comp import ExternalCodeComp
from openmdao.utils.file_wrap import InputFileGenerator

IFGSubclass = TypeVar('IFGSubclass', bound=InputFileGenerator)

_INPUT_FILE_NAME = 'input.txt'
_STDOUT_FILE_NAME = 'xfoil_calc.log'
_PROFILE_FILE_NAME = 'profile.txt'  # as specified in input file
_RESULT_FILE_NAME = 'result.txt'  # as specified in input file

_LOGGER = logging.getLogger(__name__)


class XfoilComputation(ExternalCodeComp):
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
        self.options.declare('input_file_generator', types=object)  # types=IFGSubclass

    def setup(self):
        self.options['external_input_files'] = [_INPUT_FILE_NAME, _PROFILE_FILE_NAME]
        self.options['external_output_files'] = [_RESULT_FILE_NAME]
        self.stdin = _INPUT_FILE_NAME
        self.stdout = _STDOUT_FILE_NAME
        self.options['command'] = [self.options['xfoil_exe_path']]

        self.add_input('profile:reynolds', val=np.nan)
        self.add_input('profile:mach', val=np.nan)

        for name in self._xfoil_output_names:
            self.add_output('xfoil:%s' % name)

    def compute(self, inputs, outputs):

        # Create result folder first (if it must fail, let it fail as soon as possible)
        if self.options['result_folder_path'] != '':
            result_folder_path = self.options['result_folder_path']
            os.makedirs(result_folder_path, exist_ok=True)
            stdout_file_path = pth.join(result_folder_path, _STDOUT_FILE_NAME)
            polar_file_path = pth.join(result_folder_path, self.options['result_polar_file_name'])

        # Pre-processing
        tmp_directory = tempfile.TemporaryDirectory()

        # profile file
        tmp_profile_file_path = pth.join(tmp_directory.name, _PROFILE_FILE_NAME)
        shutil.copy(self.options['profile_path'], tmp_profile_file_path)

        # input file
        parser = self.options['input_file_generator']
        parser.inputs = inputs
        parser.set_generated_file(pth.join(tmp_directory.name, _INPUT_FILE_NAME))
        parser.generate()

        # Run XFOIL
        current_working_directory = os.getcwd()
        os.chdir(tmp_directory.name)
        super(XfoilComputation, self).compute(inputs, outputs)
        os.chdir(current_working_directory)

        # Post-process
        tmp_stdout_file_path = pth.join(tmp_directory.name, _STDOUT_FILE_NAME)
        tmp_result_file_path = pth.join(tmp_directory.name, _RESULT_FILE_NAME)
        result_array = self._read_polar(tmp_result_file_path)
        if result_array is not None:
            for name in self._xfoil_output_names:
                outputs['xfoil:%s' % name] = result_array[name]

        if self.options['result_folder_path'] != '':
            shutil.move(tmp_stdout_file_path, stdout_file_path)
            shutil.move(tmp_result_file_path, polar_file_path)
        tmp_directory.cleanup()

    @staticmethod
    def _read_polar(xfoil_result_file_path: str) -> np.ndarray:
        """
        :param xfoil_result_file_path:
        :return: numpy array with XFoil polar results
        """
        if os.path.isfile(xfoil_result_file_path):
            dtypes = [(name, 'f8') for name in XfoilComputation._xfoil_output_names]
            result_array = np.genfromtxt(xfoil_result_file_path, skip_header=12,
                                         dtype=dtypes)
            return result_array
        else:
            _LOGGER.error('XFOIL results file not found')


class XfoilInputFileGenerator(InputFileGenerator, ABC):
    """ Abstract class for generating XFOIL standard input """

    @abstractmethod
    def get_template(self):
        """  :return: the path of template file """

    @abstractmethod
    def transfer_vars(self):
        """ The place where to apply self.mark_anchor() and self.transfer_var() """

    def __init__(self):
        super(XfoilInputFileGenerator, self).__init__()
        self.set_template_file(pth.join(os.path.dirname(__file__), self.get_template()))

    def generate(self, return_data=False):
        self.transfer_vars()
        super(XfoilInputFileGenerator, self).generate()
