"""
This module computes nodal forces from aerodynamic forces from AVL
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

import numpy as np
import openmdao.api as om


class ComponentForces(om.ExplicitComponent):
    """
    This component transfers the aerodynamic forces to the structural nodes
    """

    def initialize(self):
        self.options.declare("component", types=str)
        self.options.declare("number_of_structural_sections", types=int)

    def setup(self):
        comp = self.options["component"]
        sect = self.options["number_of_structural_sections"]
        self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan)
        self.add_input(
            "data:aerostructural:aerodynamic:" + comp + ":nodes", val=np.nan, shape_by_conn=True
        )
        self.add_input(
            "data:aerostructural:structure:" + comp + ":nodes", val=np.nan, shape_by_conn=True
        )
        self.add_input(
            "data:aerostructural:aerodynamic:" + comp + ":forces", val=0.0, shape_by_conn=True
        )
        size = sect + 1
        if comp in ("wing", "horizontal_tail", "strut"):
            size = (sect + 1) * 2
        self.add_output(
            "data:aerostructural:structure:" + comp + ":forces", val=0.0, shape=(size, 6)
        )

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs):
        comp = self.options["component"]
        aero_nodes = inputs["data:aerostructural:aerodynamic:" + comp + ":nodes"]
        struct_nodes = inputs["data:aerostructural:structure:" + comp + ":nodes"]
        aero_forces = inputs["data:aerostructural:aerodynamic:" + comp + ":forces"]
        x_ref = inputs["data:geometry:wing:MAC:at25percent:x"]
        if comp in ("wing", "horizontal_tail", "strut"):
            pressure_centers = _compute_pressure_centers(
                aero_nodes, aero_forces, x_ref, sym_comp=True
            )
            # Split nodes into right and left parts
            struct_nodes_right, struct_nodes_left = (
                np.split(struct_nodes, 2)[0],
                np.split(struct_nodes, 2)[1],
            )
            pressure_centers_right, pressure_centers_left = (
                np.split(pressure_centers, 2)[0],
                np.split(pressure_centers, 2)[1],
            )
            aero_forces_right, aero_forces_left = (
                np.split(aero_forces, 2)[0],
                np.split(aero_forces, 2)[1],
            )
            struct_forces_right = self._nearest_neighbour_force_transfer(
                struct_nodes_right, pressure_centers_right, aero_forces_right
            )
            struct_forces_left = self._nearest_neighbour_force_transfer(
                struct_nodes_left, pressure_centers_left, aero_forces_left
            )
            outputs["data:aerostructural:structure:" + comp + ":forces"] = np.vstack(
                (struct_forces_right, struct_forces_left)
            )
            # outputs[
            #     "data:aerostructural:structure:" + comp + ":forces_alternative"
            # ] = self._transpose_forces_moments(
            #     struct_nodes, aero_nodes, aero_forces, x_ref, sym_comp=True
            # )
        else:
            pressure_centers = _compute_pressure_centers(
                aero_nodes, aero_forces, x_ref, sym_comp=False
            )
            struct_forces = self._nearest_neighbour_force_transfer(
                struct_nodes, pressure_centers, aero_forces
            )
            outputs["data:aerostructural:structure:" + comp + ":forces"] = struct_forces
            # outputs[
            #     "data:aerostructural:structure:" + comp + ":forces_alternative"
            # ] = self._transpose_forces_moments(
            #     struct_nodes, aero_nodes, aero_forces, x_ref, sym_comp=False
            # )

    @staticmethod
    def _transpose_forces_moments(n_s, n_a, f_a, x_ref, sym_comp=False):
        """

        :param n_s: structural nodes
        :param n_a: aerodynamic nodes
        :param f_a: aerodynamic forces and moment respect to n_ref
        :param x_ref: reference node for aerodynamic moments computation
        :param sym_comp: True if the component is geometrically symmetric e.g. wing
        :return f_s: structural nodal forces and moments
        """
        f_s = np.zeros((np.size(n_s, axis=0), 6))
        n_cp = _compute_pressure_centers(n_a, f_a, x_ref, sym_comp=sym_comp)

        for idx, f in enumerate(f_a):
            r_s1 = n_cp[idx] - n_s[idx, :]
            r_s2 = n_cp[idx] - n_s[idx + 1]
            f_s[idx, :3] += f[:3] * 0.5
            f_s[idx + 1, :3] += f[:3] * 0.5
            f_s[idx, 3:] += np.cross(r_s1, 0.5 * f[:3])
            f_s[idx + 1, 3:] += np.cross(r_s2, 0.5 * f[:3])

        return f_s

    @staticmethod
    def _nearest_neighbour_force_transfer(strut_nodes, aero_nodes, aero_forces):

        f_s = np.zeros((np.size(strut_nodes, axis=0), 6))
        nearest_sets = _nearest_set(strut_nodes, aero_nodes)
        for idx, n_strut in enumerate(strut_nodes):
            idx_nn = nearest_sets[idx]
            f_s[idx, :3] = np.sum(aero_forces[idx_nn, :3], axis=0)
            lever_arms = aero_nodes[idx_nn] - n_strut
            f_s[idx, 3:] = np.sum(np.cross(lever_arms, aero_forces[idx_nn, :3]), axis=0)
        return f_s


def _compute_pressure_centers(n_a, f_a, x_ref, sym_comp=False):
    """
    :param n_a: aerodynamic nodes
    :param f_a: aerodynamic forces and moment respect to n_ref
    :param x_ref: reference node for aerodynamic moments computation
    :param sym_comp: True if the component is geometrically symmetric e.g. wing
    :return n_cp: pressure centers coordinates
    """
    n_cp = []
    for idx, f in enumerate(f_a):
        if idx >= 0.5 * np.size(f_a, axis=0) and sym_comp:
            idx = idx + 1
        n_a1 = n_a[idx, :]
        n_a2 = n_a[idx + 1, :]
        if f[2] != 0.0:
            n_cp.append(
                [x_ref[0] - f[4] / f[2], 0.5 * (n_a1[1] + n_a2[1]), 0.5 * (n_a1[2] + n_a2[2]),]
            )

        else:
            n_cp.append([x_ref[0], 0.5 * (n_a1[1] + n_a2[1]), 0.5 * (n_a1[2] + n_a2[2])])

    return np.array(n_cp)


def _nearest_neighbour(ref_point, set_points):
    i_nearest = 0
    distance = np.linalg.norm(ref_point - set_points[0, :])
    for idx, point in enumerate(set_points):
        distance_tmp = np.linalg.norm(ref_point - point)
        if distance_tmp < distance:
            distance = distance_tmp
            i_nearest = idx
        else:
            continue
    return set_points[i_nearest], i_nearest


def _nearest_set(ref_set, neighbour_set):
    """
    For each ref point in ref_set returns indices of points in neighbour_set
     the ref point for which is the nearest neighbour
    :param ref_set: reference set of points
    :param neighbour_set: set of points in which to search nearest neighbours
    :return:
    """
    idx_nearest_neighbours = []
    for idx, neighbour in enumerate(neighbour_set):
        idx_nearest_neighbours.append(_nearest_neighbour(neighbour, ref_set)[1])

    nearest_sets = []
    for idx_ref, ref_point in enumerate(ref_set):
        nearest_set = []
        for idx, idx_nn in enumerate(idx_nearest_neighbours):
            if idx_nn == idx_ref:
                nearest_set.append(idx)
        nearest_sets.append(nearest_set)

    return nearest_sets
