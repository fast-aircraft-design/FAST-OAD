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

from math import fabs

import numpy as np


# TODO: decompose reading and writing into distinct functions
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

    toc = []
    for i, elem in enumerate(x_z):
        for j in range(i + 1, len(x_z) - 1):
            if (x_z[j][0] <= elem[0] <= x_z[j + 1][0]) or (
                    x_z[j][0] >= elem[0] >= x_z[j + 1][0]):
                t_down = x_z[j][1] + (elem[0] - x_z[j][0]) / (x_z[j + 1][0] - x_z[j][0]) * (
                        x_z[j + 1][1] - x_z[j][1])
                t_up = elem[1]
                toc.append(fabs(t_down) + fabs(t_up))
    toc = max(toc)
    factor = toc_mean / toc

    try:
        file = open(f_path_new, "w")
    except:
        raise FileNotFoundError('The file ' + str(f_path_new) +
                                ' for the airfoil reshape has not been found')

    file.write("Wing\n")
    for x, z in x_z:
        file.write(
            str(x) + ' \t' + str(z * factor) + "\n")
    file.close()
