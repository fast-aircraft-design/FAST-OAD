"""
Utility for generating subfolders in a unified manner
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

import os
import os.path as pth
from typing import List, Union


class SubfolderProvider:
    """
    Service for providing subfolders after having set once a unique root folder.
    """

    def __init__(self):
        self.root_result_folder = None

    def set_root_folder(self, absolute_path):
        """ Sets the root folder """
        self.root_result_folder = absolute_path

    def get_subfolder_path(self, relative_path_components: Union[str, List[str]] = None,
                           create: bool = True) -> str:
        """
        Returns a folder path in root folder with specified *relative_path*.

        :param relative_path_components: a list of strings that will be used to build the path
        :param create: if True and subfolder does not exists, it is created.
        :return: the absolute path of subfolder
        """

        if self.root_result_folder is None:
            raise AttributeError('Please define root folder path before asking for a result folder')

        if relative_path_components is None:
            return self.root_result_folder

        if isinstance(relative_path_components, str):
            result_folder = pth.join(self.root_result_folder, relative_path_components)
        else:
            result_folder = pth.join(self.root_result_folder, *relative_path_components)

        if create:
            os.makedirs(result_folder, exist_ok=True)

        return result_folder
