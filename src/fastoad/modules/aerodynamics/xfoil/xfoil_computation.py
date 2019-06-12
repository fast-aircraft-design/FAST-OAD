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
from typing import TypeVar, Optional

import numpy as np
from openmdao.components.external_code_comp import ExternalCodeComp
from openmdao.utils.file_wrap import InputFileGenerator

IFGSubclass = TypeVar('IFGSubclass', bound='XfoilInputFileGenerator')

_INPUT_FILE_NAME = 'input.txt'
_STDOUT_FILE_NAME = 'xfoil_calc.log'
_PROFILE_FILE_NAME = 'profile.txt'
_RESULT_FILE_NAME = 'result.txt'
_RESULT_PLACE_FOLDER = 'result_file'  # as specified in input file

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

        self.add_input('profile:reynolds', val=np.nan)
        self.add_input('profile:mach', val=np.nan)

        for name in self._xfoil_output_names:
            self.add_output('xfoil:%s' % name)

        self.declare_partials(of='xfoil:CL', wrt='profile:alpha', method='fd', step=0.4)

    def compute(self, inputs, outputs):

        # Create result folder first (if it must fail, let it fail as soon as possible)
        if self.options['result_folder_path'] != '':
            result_folder_path = self.options['result_folder_path']
            os.makedirs(result_folder_path, exist_ok=True)
            stdout_file_path = pth.join(result_folder_path, _STDOUT_FILE_NAME)
            polar_file_path = pth.join(result_folder_path, self.options['result_polar_file_name'])

        # Pre-processing
        tmp_directory = tempfile.TemporaryDirectory(prefix='xfl')
        tmp_profile_file_path = pth.join(tmp_directory.name, _PROFILE_FILE_NAME)
        tmp_stdin_file_path = pth.join(tmp_directory.name, _INPUT_FILE_NAME)
        tmp_stdout_file_path = pth.join(tmp_directory.name, _STDOUT_FILE_NAME)
        tmp_result_file_path = pth.join(tmp_directory.name, _RESULT_FILE_NAME)

        # profile file
        shutil.copy(self.options['profile_path'], tmp_profile_file_path)

        # input file
        parser: IFGSubclass = self.options['input_file_generator']
        parser.generate(tmp_stdin_file_path, tmp_result_file_path, inputs)
        self.stdin = tmp_stdin_file_path
        self.stdout = tmp_stdout_file_path

        self.options['external_input_files'] = [tmp_stdin_file_path, tmp_profile_file_path]
        self.options['external_output_files'] = [tmp_result_file_path]
        self.options['command'] = [self.options['xfoil_exe_path'], tmp_profile_file_path]

        # Run XFOIL
        super(XfoilComputation, self).compute(inputs, outputs)

        # Post-process
        result_array = self._read_polar(tmp_result_file_path)
        if result_array is not None and result_array.size > 0:
            for name in self._xfoil_output_names:
                outputs['xfoil:%s' % name] = result_array[name]

        if self.options['result_folder_path'] != '':
            shutil.move(tmp_stdout_file_path, stdout_file_path)
            shutil.move(tmp_result_file_path, polar_file_path)
        tmp_directory.cleanup()

    @staticmethod
    def _read_polar(xfoil_result_file_path: str) -> Optional[np.ndarray]:
        """
        :param xfoil_result_file_path:
        :return: numpy array with XFoil polar results
        """
        if os.path.isfile(xfoil_result_file_path):
            dtypes = [(name, 'f8') for name in XfoilComputation._xfoil_output_names]
            result_array = np.genfromtxt(xfoil_result_file_path, skip_header=12,
                                         dtype=dtypes)
            return result_array

        _LOGGER.error('XFOIL results file not found')
        return None


# pylint: disable=too-few-public-methods
class XfoilInputFileGenerator(ABC):
    """
    Abstract class for generating XFOIL standard input

    To be used with:

    .. code-block:: python

        parser = MyXfoilInputFileGenerator(my_template_file_path)
        parser.apply_values(my_target_file_path, my_openmdao_inputs)

    """

    @abstractmethod
    def _transfer_vars(self, parser: InputFileGenerator, inputs: dict):
        """
        The place where to apply self.mark_anchor() and self.transfer_var()
        :param parser:
        :param inputs:
        """

    def __init__(self, template_path: str):
        super(XfoilInputFileGenerator, self).__init__()
        self._template_path = template_path

    def generate(self, target_file_path: str, result_file_path: str, inputs: dict):
        """
        Generates target file using provided inputs
        :param target_file_path:
        :param result_file_path:
        :param inputs:
        """
        parser = InputFileGenerator()
        parser.set_template_file(self._template_path)
        parser.set_generated_file(target_file_path)
        self._transfer_vars(parser, inputs)
        parser.reset_anchor()
        parser.mark_anchor(_RESULT_PLACE_FOLDER)
        parser.transfer_var(result_file_path, 0, 1)
        parser.generate()
