"""Aerodynamic polar data."""
import numpy as np

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
from scipy.interpolate import interp1d
from scipy.optimize import fmin


class Polar:
    def __init__(self, cl, cd, alpha=None):
        """
        Class for managing aerodynamic polar data.

        Links drag coefficient (CD) to lift coefficient (CL).
        It is defined by two vectors with CL and CD values.
        If a vector of angle of attack (alpha) is given, it links alpha and CL

        Once defined, for any CL value, CD can be obtained using :meth:`cd`.
        For any alpha given, CL is obtained using :meth:'cl'.

        :param cl: the lift coefficient vector
        :param cd: the drag coefficient vector
        :param alpha: the angle of attack corresponding to lift coefficient

        """

        self._definition_CL = cl
        self._definition_CD = cd

        # Interpolate cd
        self._cd = interp1d(cl, cd, kind="quadratic", fill_value="extrapolate")

        # CL as a function of AoA
        if alpha is None:
            # Define dummy AoA vector
            # Or force to give alpha
            alpha = np.linspace(-2, 20, np.size(cl))

        self._definition_alpha = alpha
        self._clvsalpha = interp1d( alpha, cl, kind="linear", fill_value="extrapolate")

        def _negated_lift_drag_ratio(lift_coeff):
            """Returns -CL/CD."""
            return -lift_coeff / self.cd(lift_coeff)

        self._optimal_CL = fmin(_negated_lift_drag_ratio, self._definition_CL[0], disp=0)

    @property
    def definition_cl(self):
        """The vector that has been used for defining lift coefficient."""
        return self._definition_CL

    @property
    def definition_cd(self):
        """The vector that has been used for defining drag coefficient."""
        return self._definition_CD

    @property
    def definition_alpha(self):
        """The vector that has been used for defining AoA."""
        return self._definition_alpha

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

    def cl(self, alpha):
        """
        The lift coefficient corresponding to alpha (rad)

        :param alpha: the angle of attack at which CL is evaluated
        :return: CL value for each alpha.
        """
        return self._clvsalpha(alpha)
