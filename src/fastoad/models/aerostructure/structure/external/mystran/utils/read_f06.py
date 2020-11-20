#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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


def readf06(file):
    """
    :param file: Nastran f06 result file complete path
    :return: nodal displacements (numpy.array) and element stresses (numpy.array)
    """
    with open(file, "r") as f06_file:
        lines = f06_file.readlines()
        disp = False
        disp_mat = []
        nodes = []
        stress = False
        stresses = []
        elems = []
        for i in range(0, len(lines)):
            if "D I S P L A C E M E N T S" in lines[i]:
                disp = True
                ind_disp = i
            if disp:
                if i < ind_disp + 4:
                    continue
                if "-------------" not in lines[i]:
                    line = lines[i].split()
                    nodes.append(int(line[0]))
                    d6tmp = []
                    for j in range(2, 8):
                        d6tmp.append(float(line[j]))
                    disp_mat.append(d6tmp)
                else:
                    disp = False
            if "S T R E S S E S" in lines[i]:
                stress = True
                ind_stress = i
            if stress:
                if i < ind_stress + 5:
                    continue
                if "-------------" not in lines[i + 1]:
                    if lines[i] != "\n" and lines[i + 1] != "\n":
                        line1 = lines[i].split()
                        line2 = lines[i + 1].split()
                        elems.append(int(line1[0]))
                        stresses.append(
                            [float(line1[6]), float(line1[7]), float(line2[4]), float(line2[5])]
                        )
                    else:
                        continue
                else:
                    stress = False
    return np.array(disp_mat), np.array(stresses)
