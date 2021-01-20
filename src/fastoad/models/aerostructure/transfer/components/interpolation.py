"""
Module to generate transfer matrices between aerodynamic and structural meshes
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
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


def find_closest(n1: np.ndarray, nodes2: np.ndarray) -> (np.ndarray, np.ndarray):
    """
    Find the two closest mesh nodes from a given location and retruns their indices
    :param n1: location
    :param nodes2: mesh nodes matrix
    :return: indices, closest: arrays of indices and closest nodes coordinates
    """
    dist = np.zeros((np.size(nodes2, axis=0)))
    for idx, node in enumerate(nodes2):
        dist[idx] = np.linalg.norm(n1 - node)
    id1 = np.argsort(dist)[0]
    id2 = np.argsort(dist)[1]

    # Prevent to consider twice the same point for components starting on the symmetry axis
    if np.array_equal(nodes2[id1, :], nodes2[id2, :]):
        id2 = np.argsort(dist)[2]
    indices = np.array([id1, id2])
    closest = np.array([nodes2[id1, :], nodes2[id2, :]])
    return indices, closest


def _symmetry_test(array: np.ndarray) -> bool:
    n = np.size(array, axis=0)
    sym = False
    if n % 2 == 0:
        if np.array_equal(array[: int(n / 2), 1], -array[int(n / 2) :, 1]) or np.array_equal(
            array[: int(n / 2), 2], -array[int(n / 2) :, 2]
        ):
            sym = True
    return sym


class InterpolationMatrix:
    """
    Class that generates transfer matrix for displacements transfer between structural nodes to
    aerodynamic ones
    :param aero_nodes: initial aerodynamic mesh nodes
    :param struct_nodes: Initial structural mesh nodes
    :param methode: interpolation method between structural and aerodynamic displacements could be
    'rigid': no displacements transferred, 'linear': displacements linearly transferred.
    """

    def __init__(self, aero_nodes, struct_nodes, methode="linear"):
        self._a_n = aero_nodes
        self._s_n = struct_nodes
        self._meth = methode
        self._t_mat = np.zeros((3 * np.size(self._a_n, axis=0), 6 * np.size(self._s_n, axis=0)))

    def get_interpolation_matrix(self):
        if self._meth == "linear":
            self._t_mat = self.get_linear_interpolation(self._a_n, self._s_n)
        return self._t_mat

    @staticmethod
    def get_linear_interpolation(nodes1: np.ndarray, nodes2: np.ndarray) -> np.ndarray:
        """
        Computes linear interpolation matrix from a set of nodes to the other
        :param nodes1: First set of nodes
        :param nodes2: Second set of nodes
        :return: linear_mat: linear interpolation matrix
        """
        linear_mat = np.zeros((3 * np.size(nodes1, axis=0), 6 * np.size(nodes2, axis=0)))
        sym = _symmetry_test(nodes1)
        for i, n1 in enumerate(nodes1):
            if sym and i >= np.size(nodes1, axis=0) / 2:
                idx, clst = (
                    find_closest(n1, nodes2[int(np.size(nodes1, axis=0) / 2) :, :])[0]
                    + int(np.size(nodes1, axis=0) / 2),
                    find_closest(n1, nodes2[int(np.size(nodes1, axis=0) / 2) :, :])[1],
                )
            else:
                idx, clst = find_closest(n1, nodes2)
            n21 = clst[0]
            n22 = clst[1]
            direct = n22 - n21
            vect = n1 - n21
            # normalised distance on the director vector
            k_p = np.dot(vect, direct) / np.linalg.norm(direct) ** 2
            # projected vector
            n_p = n21 + k_p * direct
            # distance between projected vector and node
            d_p = n1 - n_p
            proj_mat = np.hstack((np.identity(6) * (1 - k_p), np.identity(6) * k_p))
            rot_mat = np.hstack((np.identity(3), np.cross(np.identity(3), d_p)))

            linear_mat[3 * i : 3 * i + 3, 6 * idx[0] : 6 * idx[0] + 6] = np.dot(rot_mat, proj_mat)[
                :, :6
            ]
            linear_mat[3 * i : 3 * i + 3, 6 * idx[1] : 6 * idx[1] + 6] = np.dot(rot_mat, proj_mat)[
                :, 6:
            ]
        return linear_mat
