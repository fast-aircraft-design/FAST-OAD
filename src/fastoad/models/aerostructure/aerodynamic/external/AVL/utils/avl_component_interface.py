"""
Interface for AVL geometry generation
"""
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

from abc import ABC, abstractmethod
import numpy as np
from fastoad.models.geometry.profiles.get_profile import get_profile


class IAvlComponentGenerator(ABC):
    """
    Interface to generate components lines for AVL geom file
    """

    def __init__(self):
        self.index = 1
        self.nodes = np.zeros(3)
        self.chords = np.zeros(1)

    @abstractmethod
    def get_component_geom(self, nodes, chords, k_c):
        """
        Method to creates lines of the AVL geometry file (.avl) for each component
        :param nodes: component's Leading edge nodes coordinates
        :param chords: component's sections length
        :param k_c: coefficient to change chordwise spacing
        :return: comp_lines: component's lines for AVL geometry file
        """


class AvlWingGeom(IAvlComponentGenerator):
    """
    ALV wing geometry description for geometry input file
    """

    def __init__(self):
        super().__init__()
        self.twist = np.zeros(1)
        self.profile = "BACJ.txt"
        self.thickness_ratios = np.zeros(1)

    def get_component_geom(self, nodes, chords, k_c):
        if (len(self.twist) and len(self.thickness_ratios)) != np.size(nodes, axis=0):
            msg = "Wing twist and thickness ratios lists are not of the same size as nodes"
            raise ValueError(msg)
        c_space = 12 * k_c
        comp_lines = ["# Wing Sections:\n"]
        for idx, node in enumerate(nodes):
            if idx in (
                0.5 * np.size(nodes, axis=0) - 1,
                np.size(nodes, axis=0) - 1,
            ):  # exclude extreme points
                continue
            comp_lines += [
                "SURFACE \n",
                "WING" + "\n",
                str(c_space) + " 1.0 " + "1 0.0 \n",
                "COMPONENT\n",
                str(self.index) + "\n",
                "SECTION\n",
            ]
            for i in [0, 1]:
                comp_lines += [
                    str(nodes[idx + i, 0])
                    + " "
                    + str(nodes[idx + i, 1])
                    + " "
                    + nodes[idx + i, 2]
                    + " "
                    + str(chords[idx + i])
                    + " "
                    + str(self.twist[idx + i])
                    + "\n",
                ]
                profile = get_profile(
                    file_name=self.profile,
                    thickness_ratio=self.thickness_ratios[idx + i],
                    chord_length=chords[idx + i],
                )
                comp_lines += ["AIRFOIL X1 X2 \n"]
                for point in profile.to_numpy():
                    comp_lines += [str(point[0]) + " " + point[1] + "\n"]
        return comp_lines


class AvlHtailGeom(IAvlComponentGenerator):
    def get_component_geom(self, nodes, chords, k_c):
        c_space = 12 * k_c
        comp_lines = ["# Horizontal Tail sections \n"]
        for idx, node in enumerate(nodes):
            comp_lines += [
                "SURFACE \n",
                "HTP" + "\n",
                str(c_space) + " 1.0 " + "1 0.0 \n",
                "COMPONENT\n",
                str(self.index) + "\n",
            ]
            for i in [0, 1]:
                comp_lines += [
                    str(nodes[idx + i, 0])
                    + " "
                    + str(nodes[idx + i, 1])
                    + " "
                    + nodes[idx + i, 2]
                    + " "
                    + str(chords[idx + i])
                    + " 0.0 \n",
                ]

        return comp_lines


class AvlVtailGeom(IAvlComponentGenerator):
    def get_component_geom(self, nodes, chords, k_c):
        c_space = 12 * k_c
        comp_lines = ["# Vertical Tail Sections \n"]
        for idx, node in enumerate(nodes):
            comp_lines += [
                "SURFACE \n",
                "VTP" + "\n",
                str(c_space) + " 1.0 " + "1 0.0 \n",
                "COMPONENT\n",
                str(self.index) + "\n",
            ]
            for i in [0, 1]:
                comp_lines += [
                    str(nodes[idx + i, 0])
                    + " "
                    + str(nodes[idx + i, 1])
                    + " "
                    + nodes[idx + i, 2]
                    + " "
                    + str(chords[idx + i])
                    + " 0.0 \n",
                ]

        return comp_lines


class AvlFuseGeom(IAvlComponentGenerator):
    def get_component_geom(self, nodes, chords, k_c):
        c_space = 12 * k_c
        comp_lines = ["# Fuselage Sections \n"]
        for idx, node in enumerate(nodes):
            if idx <= 2:
                x_le = str(node[0])
                y_le = str(node[1])
                z_le = str(node[2])
                chord = str(chords[idx])
                ainc = str(0.0)
                if idx == 0:
                    comp_lines = [
                        "SURFACE \n",
                        "Fuse H" + "\n",
                        str(c_space) + " 1.0 " + "1 0.0 \n",
                        "COMPONENT\n",
                        str(self.index) + "\n",
                    ]
                comp_lines += [
                    "SECTION\n",
                    x_le + " " + y_le + " " + z_le + " " + chord + " " + ainc + "\n",
                ]
            elif 2 < idx <= 5:
                continue

            elif 5 < idx <= 8:
                x_le = str(node[0])
                y_le = str(node[1])
                z_le = str(node[2])
                chord = str(chord)
                ainc = str(0.0)
                if idx == 6:
                    comp_lines = [
                        "SURFACE \n",
                        "Fuse T" + "\n",
                        str(c_space) + " 1.0 " + "1 0.0 \n",
                        "COMPONENT\n",
                        str(self.index) + "\n",
                        "NOWAKE\n",
                    ]
                comp_lines += [
                    "SECTION\n",
                    x_le + " " + y_le + " " + z_le + " " + chord + " " + ainc + "\n",
                ]
            else:
                x_le = str(node[0])
                y_le = str(node[1])
                z_le = str(node[2])
                chord = str(chord)
                ainc = str(0.0)
                if idx == 9:
                    comp_lines = [
                        "SURFACE \n",
                        "Fuse B" + "\n",
                        str(c_space) + " 1.0 " + "1 0.0 \n",
                        "COMPONENT\n",
                        str(self.index) + "\n",
                        "NOWAKE\n",
                    ]
                comp_lines += [
                    "SECTION\n",
                    x_le + " " + y_le + " " + z_le + " " + chord + " " + ainc + "\n",
                ]
