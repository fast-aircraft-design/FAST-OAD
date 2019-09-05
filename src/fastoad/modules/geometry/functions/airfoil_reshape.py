"""
    Airfoil reshape function
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

from math import fabs

def airfoil_reshape(toc_mean: float, f_path_ori: str, f_path_new: str):
    """
    Generates a new airfoil file based on the mean ToC (Thickness of Chord) and the original airfoil.

    :param toc_mean: value of mean ToC
    :param f_path_ori: path to original airfoil file.
    :param f_path_new: path to new airfoil file.

    :raise FileNotFoundError: if one of the files is not found
    """
    try:
        file = open(f_path_ori, "r")
    except:
        FileNotFoundError('The file ' + str(f_path_ori) + ' for the airfoil reshape has not been found')

    l1 = file.readlines()
    file.close()
    b = []
    for i, elem in enumerate(l1):
        if i >= 1:
            a = elem
            b.append(list(map(float, a.split("\t"))))
        else:
            pass
    t = []
    for i, elem in enumerate(b):
        for j in range(i + 1, len(b) - 1):
            if (b[j][0] <= elem[0] and b[j + 1][0] >= elem[0]
            ) or (b[j][0] >= elem[0] and b[j + 1][0] <= elem[0]):
                t_down = b[j][
                    1] + (elem[0] - b[j][0]) / (b[j + 1][0] - b[j][0]) * (b[j + 1][1] - b[j][1])
                t_up = elem[1]
                t.append(fabs(t_down) + fabs(t_up))
    toc = max(t)
    factor = toc_mean / toc

    try:
        file = open(f_path_new, "w")
    except:
        FileNotFoundError('The file ' + str(f_path_ori) + ' for the airfoil reshape has not been found')

    file.write("Wing\n")
    for i, elem in enumerate(l1):
        if i >= 1:
            a = elem
            b = a.split("\t")
            file.write(
                str(float(b[0])) + ' \t' + str((float(b[1])) * factor) + "\n")
        else:
            pass
    file.close()