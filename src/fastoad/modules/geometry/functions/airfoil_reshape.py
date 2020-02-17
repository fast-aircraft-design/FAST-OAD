"""
    Airfoil reshape function
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

import os
import os.path as pth

import numpy as np
import pandas as pd

from .profile import Profile


def get_profile(file_name: str = 'BACJ.txt',
                relative_thickness=None,
                chord_length=None) -> pd.DataFrame:
    """
    Reads profile from indicated resource file and returns it after resize

    :param file_name: name of resource (only "BACJ.txt" for now)
    :param relative_thickness:
    :param chord_length:
    :return: Nx2 pandas.DataFrame with x in 1st column and z in 2nd column
    """
    f_path_resources = pth.join(pth.abspath(pth.dirname(__file__)), os.pardir, 'resources')
    f_path_ori = pth.join(f_path_resources, file_name)
    x_z = np.genfromtxt(f_path_ori, skip_header=1, delimiter='\t', names='x, z')
    profile = Profile()
    profile.set_points(x_z['x'], x_z['z'])

    if relative_thickness:
        profile.max_relative_thickness = relative_thickness

    if chord_length:
        profile.chord_length = chord_length

    return profile.get_sides()
