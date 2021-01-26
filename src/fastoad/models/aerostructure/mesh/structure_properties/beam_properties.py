"""This module computes section beam properties for classical section shapes"""
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


class Beam:
    def __init__(
        self,
        length: (float, np.ndarray),
        height: (float, np.ndarray),
        t_flange: (float, np.ndarray),
        t_web: (float, np.ndarray),
        spars: (int, np.ndarray),
        a_spars: (float, np.ndarray),
        type="box",
    ):
        self.length = length
        self.height = height
        self.t_flange = t_flange
        self.t_web = t_web
        self.type = type
        self.spars = int(spars)
        self.a_spars = a_spars

    def compute_section_properties(self):
        if self.type == "box":
            self._box_properties()
        if self.type == "tube":
            self._tube_properties()
        if self.type == "I":
            self._i_properties()

    def _box_properties(self):
        s2 = np.zeros((np.size(self.length)))
        if self.spars > 1:
            for idx, length in enumerate(self.length):
                d_spar = length / (self.spars - 1)
                d2 = np.zeros(self.spars)
                for k in range(self.spars):
                    d2[k] = (d_spar * k - length / 2) ** 2
                s2[idx] = np.sum(d2)

        self.a = 2 * (
            (self.length * self.t_flange + self.height * self.t_web) + self.spars * self.a_spars
        )
        self.i1 = 2 * (
            (self.t_web * self.height ** 3) / 12
            + (self.t_flange * self.length * self.height ** 2) / 4
            + (self.spars * self.a_spars * self.height ** 2) / 4
        )
        self.i2 = 2 * (
            (self.t_flange * self.length ** 3) / 12
            + (self.t_web * self.height * self.length ** 2) / 4
            + s2 * self.a_spars * self.spars
        )
        self.j = (
            2
            * (self.length ** 2 * self.height ** 2 * self.t_flange * self.t_web)
            / (self.length * self.t_web + self.height * self.t_flange)
        )

    def _tube_properties(self):
        pass

    def _i_properties(self):
        pass
