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
        self.k_c = 1.0

    @abstractmethod
    def get_component_geom(self):
        """
        Method to creates lines of the AVL geometry file (.avl) for each component
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

    def get_component_geom(self):
        if (len(self.twist) and len(self.thickness_ratios)) != np.size(self.nodes, axis=0):
            msg = "Wing twist and thickness ratios lists are not of the same size as nodes"
            raise ValueError(msg)
        c_space = 12 * self.k_c
        comp_lines = ["# Wing Sections:\n"]
        comp_lines += self._get_wings(c_space)
        comp_lines += self._get_wings(c_space, right=False)
        return comp_lines

    def _get_wings(self, c_space, right=True):
        comp_lines = []
        if right:
            surf_name = "Wing Right"
            order = [0, 1]
            nodes = np.split(self.nodes, 2)[0]
        else:
            surf_name = "Wing Left"
            order = [1, 0]
            nodes = np.split(self.nodes, 2)[1]
        comp_lines = self._get_wing_surface(c_space, comp_lines, nodes, order, surf_name)
        return comp_lines

    def _get_wing_surface(self, c_space, comp_lines, nodes, order, surf_name):
        for idx, node in enumerate(nodes):
            if idx == np.size(nodes, axis=0) - 1:  # exclude extreme point
                continue
            comp_lines += [
                "SURFACE \n",
                surf_name + "\n",
                str(c_space) + " 1.0 " + "1 0.0 \n",
                "COMPONENT\n",
                str(self.index) + "\n",
            ]
            for i in order:
                comp_lines += [
                    "SECTION\n"
                    + str(nodes[idx + i, 0])
                    + " "
                    + str(nodes[idx + i, 1])
                    + " "
                    + str(nodes[idx + i, 2])
                    + " "
                    + str(self.chords[idx + i])
                    + " "
                    + str(self.twist[idx + i])
                    + "\n",
                ]
                profile = get_profile(
                    file_name=self.profile, thickness_ratio=self.thickness_ratios[idx + i]
                )
                comp_lines += ["AIRFOIL X1 X2 \n"]
                for point in profile.to_numpy():
                    comp_lines += [str(point[0]) + " " + str(point[1]) + "\n"]
        return comp_lines


class AvlHtailGeom(IAvlComponentGenerator):
    def get_component_geom(self):
        c_space = 12 * self.k_c
        comp_lines = ["# Horizontal Tail sections \n"]
        comp_lines += self._get_tails(c_space, right=True)
        comp_lines += self._get_tails(c_space, right=False)
        return comp_lines

    def _get_tails(self, c_space, right=True):
        comp_lines = []
        if right:
            surf_name = "HTP Right"
            order = [0, 1]
            nodes = np.split(self.nodes, 2)[0]
        else:
            surf_name = "HTP Left"
            order = [1, 0]
            nodes = np.split(self.nodes, 2)[1]
        comp_lines = self._get_tail_surface(c_space, comp_lines, nodes, order, surf_name)
        return comp_lines

    def _get_tail_surface(self, c_space, comp_lines, nodes, order, surf_name):
        for idx, node in enumerate(nodes):
            if idx == np.size(nodes, axis=0) - 1:  # exclude extreme point
                continue
            comp_lines += [
                "SURFACE \n",
                surf_name + "\n",
                str(c_space) + " 1.0 " + "1 0.0 \n",
                "COMPONENT\n",
                str(self.index) + "\n",
            ]
            for i in order:
                comp_lines += [
                    "SECTION\n"
                    + str(nodes[idx + i, 0])
                    + " "
                    + str(nodes[idx + i, 1])
                    + " "
                    + str(nodes[idx + i, 2])
                    + " "
                    + str(self.chords[idx + i])
                    + " "
                    + "0.0"
                    + "\n",
                ]
        return comp_lines


class AvlVtailGeom(IAvlComponentGenerator):
    def get_component_geom(self):
        c_space = 12 * self.k_c
        comp_lines = ["# Vertical Tail Sections \n"]
        for idx, node in enumerate(self.nodes):
            if idx == np.size(self.nodes, axis=0) - 1:  # exclude extreme point
                continue
            comp_lines += [
                "SURFACE \n",
                "VTP" + "\n",
                str(c_space) + " 1.0 " + "1 0.0 \n",
                "COMPONENT\n",
                str(self.index) + "\n",
            ]
            for i in [0, 1]:
                comp_lines += [
                    "SECTION\n"
                    + str(self.nodes[idx + i, 0])
                    + " "
                    + str(self.nodes[idx + i, 1])
                    + " "
                    + str(self.nodes[idx + i, 2])
                    + " "
                    + str(self.chords[idx + i])
                    + " 0.0 \n",
                ]
        return comp_lines


class AvlFuseGeom(IAvlComponentGenerator):
    def get_component_geom(self):
        c_space = 12 * self.k_c
        comp_lines = ["# Fuselage Sections \n"]
        for idx, node in enumerate(self.nodes):
            if idx <= 2:
                x_le = str(node[0])
                y_le = str(node[1])
                z_le = str(node[2])
                chord = str(self.chords[idx])
                ainc = str(0.0)
                if idx == 0:
                    comp_lines += [
                        "SURFACE \n",
                        "Fuselage H" + "\n",
                        str(c_space) + " 1.0 " + "\n",
                        "COMPONENT\n",
                        str(self.index) + "\n",
                        "YDUPLICATE \n",
                        "0.0 \n",
                    ]
                comp_lines += [
                    "SECTION\n",
                    x_le + " " + y_le + " " + z_le + " " + chord + " " + ainc + " 1 0.0\n",
                ]
            elif 2 < idx <= 5:
                continue

            elif 5 < idx <= 8:
                x_le = str(node[0])
                y_le = str(node[1])
                z_le = str(node[2])
                chord = str(self.chords[idx])
                ainc = str(0.0)
                if idx == 6:
                    comp_lines += [
                        "SURFACE \n",
                        "Fuselage T" + "\n",
                        str(c_space) + " 1.0 " + "\n",
                        "COMPONENT\n",
                        str(self.index) + "\n",
                        "NOWAKE\n",
                    ]
                comp_lines += [
                    "SECTION\n",
                    x_le + " " + y_le + " " + z_le + " " + chord + " " + ainc + " 1 0.0 \n",
                ]
            else:
                x_le = str(node[0])
                y_le = str(node[1])
                z_le = str(node[2])
                chord = str(self.chords[idx])
                ainc = str(0.0)
                if idx == 9:
                    comp_lines += [
                        "SURFACE \n",
                        "Fuselage B" + "\n",
                        str(c_space) + " 1.0 " + "\n",
                        "COMPONENT\n",
                        str(self.index) + "\n",
                        "NOWAKE\n",
                    ]
                comp_lines += [
                    "SECTION\n",
                    x_le + " " + y_le + " " + z_le + " " + chord + " " + ainc + " 1 0.0\n",
                ]
        return comp_lines
