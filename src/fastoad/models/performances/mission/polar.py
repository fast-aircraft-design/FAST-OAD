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
from scipy.interpolate import interp1d
from scipy.optimize import fmin

from .ground_effect import GroundEffect


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

    def __init__(self, input_dic=None):
        """
        Class for managing aerodynamic polar data.

        Links drag coefficient (CD) to lift coefficient (CL).
        It is defined by two vectors with CL and CD values.

        Once defined, for any CL value, CD can be obtained using :meth:`cd`.

        :param input_dic: a dictionary containing the CL and CD N-elements
        array and additional variables for ground effect calculation.
        For ground segments the 'CL vs alpha curve' is required and the dictionary
        must contain 'CL0_clean', 'CL_alpha' and 'CL_high_lift'

        """

        if {"CL", "CD"}.issubset(input_dic):
            self._definition_CL = input_dic["CL"]
            self._cd = interp1d(
                input_dic["CL"], input_dic["CD"], kind="quadratic", fill_value="extrapolate"
            )
        else:
            # default initialisation for instanciation without argument
            self._definition_CL = np.array([0.2, 0.5, 1.0])
            self._definition_CD = np.array([0.01, 0.02, 0.1])

            self._cd = interp1d(
                self._definition_CL, self._definition_CD, kind="quadratic", fill_value="extrapolate"
            )

        # Additional arguments for takeoff segments
        if {"CL0_clean", "CL_alpha", "CL_high_lift"}.issubset(input_dic):
            self.init_takeoff_polar(input_dic)
            self._use_CL_alpha = True

        # Additional arguments for ground effect
        if "ground_effect" in input_dic:
            self.ground_effect = GroundEffect(input_dic)
            self._use_ground_effect = self.ground_effect.use_ground_effect

        def _negated_lift_drag_ratio(lift_coeff):
            """Returns -CL/CD."""
            return -lift_coeff / self.cd(lift_coeff)

        self._optimal_CL = fmin(_negated_lift_drag_ratio, self._definition_CL[0], disp=0)

    def init_takeoff_polar(self, input_arg):
        """
        Builds the CL vs alpha vector for ground manoeuvres.
        """
        self._CL_alpha_0 = input_arg["CL0_clean"]
        self._CL_alpha = input_arg["CL_alpha"]
        self._CL_high_lift = input_arg["CL_high_lift"]
        alpha_vector = (
            self._definition_CL - self._CL_alpha_0 - self._CL_high_lift
        ) / self._CL_alpha
        self._clvsalpha = interp1d(alpha_vector, self._definition_CL)

    def get_gnd_effect_model(self):
        return self.ground_effect.get_gnd_effect_model()

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

        """Evaluates the drag in ground effect, using Raymer's model:
        'Aircraft Design A conceptual approach', D. Raymer p304"""

        if cl is None:
            if self._use_ground_effect:
                cd_ground = self.ground_effect.cd_ground(self._definition_CL, altitude)
                return self._cd(self._definition_CL) + cd_ground
            else:
                return self._cd(self._definition_CL)

        if self._use_ground_effect:
            cd_ground = self.ground_effect.cd_ground(cl, altitude)
            return cd_ground + self._cd(cl)
        else:
            return self._cd(cl)

    def cl(self, alpha):
        """
        The lift coefficient corresponding to alpha (rad)
        """
        if self._use_CL_alpha:
            return self._clvsalpha(alpha)
        else:
            raise ValueError(
                "CL vs alpha curve not available, provide 'CL0_clean', 'CL_alpha' and"
                "'CL_high_lift' to polar in mission definition."
            )
