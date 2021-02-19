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

import openmdao.api as om
import numpy as np


class ComponentForces(om.ExplicitComponent):
    """
    This component transfers the aerodynamic forces to the structural nodes
    """

    def initialize(self):
        self.options.declare("component", types=str)
        self.options.declare("number_of_sections", types=int)

    def setup(self):
        comp = self.options["component"]
        sect = self.options["number_of_sections"]
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
        n_a = inputs["data:aerostructural:aerodynamic:" + comp + ":nodes"]
        n_s = inputs["data:aerostructural:structure:" + comp + ":nodes"]
        f_a = inputs["data:aerostructural:aerodynamic:" + comp + ":forces"]
        x_ref = inputs["data:geometry:wing:MAC:at25percent:x"]
        if comp in ("wing", "horizontal_tail", "strut"):
            outputs[
                "data:aerostructural:structure:" + comp + ":forces"
            ] = self._transpose_forces_moments(n_s, n_a, f_a, x_ref, sym_comp=True)
        else:
            outputs[
                "data:aerostructural:structure:" + comp + ":forces"
            ] = self._transpose_forces_moments(n_s, n_a, f_a, x_ref, sym_comp=False)

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
        for idx, f in enumerate(f_a):
            if idx >= 0.5 * np.size(f_a, axis=0) and sym_comp:
                idx = idx + 1
            n_a1 = n_a[idx, :]
            n_a2 = n_a[idx + 1, :]
            n_cp = np.array(
                [x_ref[0] - f[4] / f[2], 0.5 * (n_a1[1] + n_a2[1]), 0.5 * (n_a1[2] + n_a2[2])]
            )
            r_s1 = n_cp - n_s[idx, :]
            r_s2 = n_cp - n_s[idx + 1]
            f_s[idx, :3] += f[:3] * 0.5
            f_s[idx + 1, :3] += f[:3] * 0.5
            f_s[idx, 3:] += np.cross(r_s1, 0.5 * f[:3])
            f_s[idx + 1, 3:] += np.cross(r_s2, 0.5 * f[:3])

        return f_s
