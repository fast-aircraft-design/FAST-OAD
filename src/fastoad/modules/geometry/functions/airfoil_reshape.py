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

import numpy as np
import pandas as pd

from .profile import Profile


def airfoil_reshape(toc_mean: float, f_path_ori: str, f_path_new: str):
    """
    Generates a new airfoil file based on the mean ToC (Thickness of Chord)
    and the original airfoil.

    :param toc_mean: value of mean ToC
    :param f_path_ori: path to original airfoil file.
    :param f_path_new: path to new airfoil file.

    :raise FileNotFoundError: if one of the files is not found
    """

    x_z = np.genfromtxt(f_path_ori, skip_header=1, delimiter='\t', names='x, z')

    profile = Profile()
    profile.set_points(x_z['x'], x_z['z'])

    profile.max_relative_thickness = toc_mean

    file = open(f_path_new, "w")
    file.write("Wing\n")
    points = pd.concat([profile.get_upper_side().sort_index(ascending=False),
                        profile.get_lower_side()[1:]])
    for x, z in points.values:
        file.write('%s\t%s\n' % (x, z))
    file.close()
