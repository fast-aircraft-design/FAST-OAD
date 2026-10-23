"""Aerodynamic polar data."""

#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2023 ONERA & ISAE-SUPAERO
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
from numpy import ndarray
from scipy.interpolate import interp1d
from scipy.optimize import fmin


class Polar:
    """Aerodynamic polar linking lift coefficient (CL) to drag coefficient (CD).

    This class manages aerodynamic polar data, providing an interpolation-based
    relation between CL and CD. It is defined by two vectors of equal size: one
    for CL values and one for the corresponding CD values.

    If a vector of angle of attack (alpha) is provided, the polar also provides
    CL as a function of alpha.

    Once defined, for any CL value, CD can be obtained using :meth:`cd`.
    For any alpha value, CL can be obtained using :meth:`cl`.

    :param cl: a N-elements array with lift coefficient (CL) values, unitless
    :param cd: a N-elements array with drag coefficient (CD) values, matching CL
    :param alpha: a N-elements array with angle of attack (alpha) in radians,
        corresponding to the CL values

    """

    def __init__(self, cl, cd, alpha=None):
        self._definition_CL = cl
        self._definition_CD = cd

        # Interpolate cd
        self._cd_vs_cl = interp1d(cl, cd, kind="quadratic", fill_value="extrapolate")

        # CL as a function of AoA
        self._definition_alpha = alpha
        if alpha is not None:
            self._cl_vs_alpha = interp1d(alpha, cl, kind="linear", fill_value="extrapolate")

        def _negated_lift_drag_ratio(lift_coeff):
            """Returns -CL/CD."""
            return -lift_coeff / self.cd(lift_coeff)

        self._optimal_CL = fmin(_negated_lift_drag_ratio, cl[0], disp=0)

    @property
    def definition_cl(self):
        """The CL vector used for defining the polar (unitless)."""
        return self._definition_CL

    @property
    def definition_cd(self):
        """The CD vector used for defining the polar (unitless)."""
        return self._definition_CD

    @property
    def definition_alpha(self):
        """The angle of attack (alpha) vector used for defining the polar (rad), or None if not provided."""
        return self._definition_alpha

    @property
    def optimal_cl(self):
        """The CL value providing the best lift/drag ratio (unitless)."""
        return self._optimal_CL

    def cd(self, cl=None):
        """Compute drag coefficient (CD) by interpolation in definition data.

        :param cl: lift coefficient (CL) value(s). If None, the CD values for the
            definition CL vector are returned.
        :return: drag coefficient (CD) value(s), unitless
        """
        if cl is None:
            return self._cd_vs_cl(self._definition_CL)
        return self._cd_vs_cl(cl)

    def cl(self, alpha):
        """Compute lift coefficient (CL) from angle of attack (alpha).

        :param alpha: angle of attack in radians
        :return: lift coefficient (CL) value(s), unitless
        :raises ValueError: if the polar was instantiated without an alpha vector
        """
        if self._definition_alpha is None:
            raise ValueError("Polar was instantiated without alpha vector.")

        return self._cl_vs_alpha(alpha)
