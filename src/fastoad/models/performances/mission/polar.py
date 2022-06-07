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
from dataclasses import is_dataclass


class Polar:

    _use_ground_effect = False

    takeoff_variables = {
        "CL_alpha0": "data:aerodynamics:aircraft:takeoff:CL0_clean",
        "CL_alpha": "data:aerodynamics:aircraft:takeoff:CL_alpha",
        "CL_high_lift": "data:aerodynamics:high_lift_devices:takeoff:CL"
    }
    gnd_effect_variables_raymer = {
        "span": "data:geometry:wing:span",
        "lg_height": "data:geometry:landing_gear:height",
        "induced_drag_coef": "data:aerodynamics:aircraft:low_speed:induced_drag_coefficient",
        "k_winglet": "tuning:aerodynamics:aircraft:cruise:CD:winglet_effect:k",
        "k_cd": "tuning:aerodynamics:aircraft:cruise:CD:k",
    }

    def __init__(self, input_dic=None):
        """
        Class for managing aerodynamic polar data.

        Links drag coefficient (CD) to lift coefficient (CL).
        It is defined by two vectors with CL and CD values.

        Once defined, for any CL value, CD can be obtained using :meth:`cd`.

        :param cl: a N-elements array with CL values
        :param cd: a N-elements array with CD values that match CL
        """
        if input_dic is not None: # try to test for dataclass and dictionary to fix mission_component breguet test
            key = list(input_dic.keys())
            if 'CL' and 'CD' in key:
                self._definition_CL = input_dic['CL']
                self._cd = interp1d(input_dic['CL'], input_dic['CD'], kind="quadratic", fill_value="extrapolate")
                if "ground_effect" in key:
                    self.init_takeoff_polar(input_dic)
                    self.init_ground_effect(input_dic)
            else:
                # default initialisation for instanciation without argument
                self._definition_CL = np.array([0.2,0.5,1.0])
                self._definition_CD = np.array([0.01,0.02,0.1])

                self._cd = interp1d(self._definition_CL, self._definition_CD, kind="quadratic",
                                            fill_value="extrapolate")

            def _negated_lift_drag_ratio(lift_coeff):
                """Returns -CL/CD."""
                return -lift_coeff / self.cd(lift_coeff)

            self._optimal_CL = fmin(_negated_lift_drag_ratio, self._definition_CL[0], disp=0)

    def init_ground_effect(self, input_dic):
        """
        Initialise the ground effect calculation

        Assumes only Raymer model
        """
        if input_dic["ground_effect"] == "Raymer":
            # TO DO : replace condition by keywords designating the ground effect model
            self._span = input_dic['span']
            self._lg_height = input_dic['lg_height']
            self._induced_drag_coef = input_dic['induced_drag_coef']
            self._k_winglet = input_dic['k_winglet']
            self._k_cd = input_dic['k_cd']
            self._use_ground_effect = True
        else:
            self._use_ground_effect = False

    def init_takeoff_polar(self, input_dic):
        """
        Builds the CL vs alpha vector for ground manoeuvres.
        """
        self._CL_alpha_0 = input_dic['CL_alpha0']
        self._CL_alpha = input_dic['CL_alpha']
        self._CL_high_lift = input_dic['CL_high_lift']
        alpha_vector = (self._definition_CL - self._CL_alpha_0 - self._CL_high_lift) / self._CL_alpha
        self._clvsalpha = interp1d(alpha_vector, self._definition_CL)


    def get_gnd_effect_model(self, model_name):
        """ Returns the input variables need to evaluated gnd effect using Raymer model"""
        if model_name == 'Raymer':
            return self.gnd_effect_variables_raymer

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

        """ Evaluates the drag in ground effect, using Raymer's model: 'Aircraft Design A conceptual approach', D. Raymer p304"""

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
