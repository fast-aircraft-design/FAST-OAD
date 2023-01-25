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
from scipy.interpolate import interp1d
from scipy.optimize import fmin


class Polar:

    _use_ground_effect = False
    _use_CL_alpha = False

    gnd_effect_variables_raymer = {
        "span": {"name": "data:geometry:wing:span", "unit": "m"},
        "lg_height": {"name": "data:geometry:landing_gear:height", "unit": "m"},
        "induced_drag_coef": {
            "name": "data:aerodynamics:aircraft:low_speed:induced_drag_coefficient",
            "unit": None,
        },
        "k_winglet": {
            "name": "tuning:aerodynamics:aircraft:cruise:CD:winglet_effect:k",
            "unit": None,
        },
        "k_cd": {"name": "tuning:aerodynamics:aircraft:cruise:CD:k", "unit": None},
    }

    def __init__(self, cl, cd, cl_alpha=5.0, cl0_clean=0.0, cl_high_lift=0.0):
        """
        Class for managing aerodynamic polar data.

        Links drag coefficient (CD) to lift coefficient (CL).
        It is defined by two vectors with CL and CD values.

        Once defined, for any CL value, CD can be obtained using :meth:`cd`.

        :param cl: the lift coefficient vector
        :param cd: the drag coefficient vector
        :param cl_alpha: the lift slope coefficient
        :param cl0_clean: the zero angle of attack(relative to aircraft) lift coefficient
        :param cl_high_lift: the lift increase due to high lift systems

        For ground segments the 'CL vs alpha curve' is required and the vairables
        'CL0_clean', 'CL_alpha' and 'CL_high_lift' should be provided through mission file

        """

        self._definition_CL = cl
        self._definition_CD = cd

        # Interpolate cd
        self.interpolate_cd(self._definition_CL, self._definition_CD)

        # Additional arguments for ground segments
        self._CL_alpha_0 = cl0_clean
        self._CL_alpha = cl_alpha
        self._CL_high_lift = cl_high_lift
        alpha_vector = (
            self._definition_CL - self._CL_alpha_0 - self._CL_high_lift
        ) / self._CL_alpha
        self._clvsalpha = interp1d(alpha_vector, self._definition_CL)

        def _negated_lift_drag_ratio(lift_coeff):
            """Returns -CL/CD."""
            return -lift_coeff / self.cd(lift_coeff)

        self._optimal_CL = fmin(_negated_lift_drag_ratio, self._definition_CL[0], disp=0)

    def interpolate_cd(self, cl, cd):
        self._cd = interp1d(cl, cd, kind="quadratic", fill_value="extrapolate")

    def get_gnd_effect_model(self):
        return self.ground_effect.get_gnd_effect_model()

    @property
    def definition_cl(self):
        """The vector that has been used for defining lift coefficient."""
        return self._definition_CL

    @property
    def definition_cd(self):
        """The vector that has been used for defining drag coefficient."""
        return self._definition_CD

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
