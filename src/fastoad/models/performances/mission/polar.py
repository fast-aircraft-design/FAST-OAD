"""Aerodynamic polar data."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2021 ONERA & ISAE-SUPAERO
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
from numpy import ndarray
from scipy.interpolate import interp1d
from scipy.optimize import fmin


class Polar:
    def __init__(self, cl: ndarray, cd: ndarray, span: float = None, lg_height: float = None,
                 induced_drag_coef: float = None, k_winglet: float = None, k_cd: float = None,
                 CL_alpha: float = None, CL_alpha0: float = None, CL_high_lift: float = None):

        """
        Class for managing aerodynamic polar data.

        Links drag coefficient (CD) to lift coefficient (CL).
        It is defined by two vectors with CL and CD values.

        Once defined, for any CL value, CD can be obtained using :meth:`cd`.

        :param cl: a N-elements array with CL values
        :param cd: a N-elements array with CD values that match CL
        """
        self._definition_CL = cl
        self._cd = interp1d(cl, cd, kind="quadratic", fill_value="extrapolate")

        #Add terms for ground effect if provided
        if None not in [span, lg_height, induced_drag_coef, k_winglet, k_cd] and not isinstance(span, str):
            self._span = span
            self._lg_height = lg_height
            self._induced_drag_coef = induced_drag_coef
            self._k_winglet = k_winglet
            self._k_cd = k_cd
            self._use_ground_effect = True
        else:
            self._use_ground_effect = False

        #Add CL vs alpha curve with provided CL (containing high lift terms if any)
        if None not in [CL_alpha0, CL_alpha, CL_high_lift]:
            if not isinstance(CL_alpha0, str):
                self._CL_alpha_0 = CL_alpha0
                self._CL_alpha = CL_alpha
                self._CL_high_lift = CL_high_lift
                alpha_vector = (self._definition_CL - self._CL_alpha_0 - self._CL_high_lift)/self._CL_alpha
                self._clvsalpha = interp1d( alpha_vector, self._definition_CL)

        def _negated_lift_drag_ratio(lift_coeff):
            """Returns -CL/CD."""
            return -lift_coeff / self.cd(lift_coeff)

        self._optimal_CL = fmin(_negated_lift_drag_ratio, cl[0], disp=0)

    @property
    def definition_cl(self):
        """The vector that has been used for defining lift coefficient."""
        return self._definition_CL

    @property
    def optimal_cl(self):
        """The CL value that provides larger lift/drag ratio."""
        return self._optimal_CL

    def cd(self, cl=None):
        """
        Computes drag coefficient (CD) by interpolation in definition data.

        :param cl: lift coefficient (CL) values. If not provided, the CL definition vector will be
                   used (i.e. CD definition vector will be returned)
        :return: CD values for each provide CL values
        """
        if cl is None:
            return self._cd(self._definition_CL)
        return self._cd(cl)

    def cd_ground(self, cl=None, altitude: float = 0):
        # TO DO : document the model
        if cl is None:
            return self._cd(self._definition_CL)
        elif self._use_ground_effect:
            h_b = (self._span * 0.1 + self._lg_height + altitude) / self._span
            k_ground = 33. * h_b**1.5 / (1+ 33. * h_b**1.5)
            cd_ground = self._induced_drag_coef * cl**2 * self._k_winglet * self._k_cd * (k_ground-1) + self._cd(cl)
            return cd_ground
        else:
            return self._cd(cl)

    def cl(self, alpha):
        """
        The lift coefficient corresponding to alpha (rad)
        """
        return self._clvsalpha(alpha)
