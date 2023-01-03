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


class GroundEffect:

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

    ground_effect_name = None
    use_ground_effect = False

    def __init__(self, input_dic=None):
        """
        Class for managing ground effects
        As many ground effect models can be derived, this class is intended to handle the different
        models

        The input variables names necessary for a specific model should be declared as attribute.
        At instantiation to be effectively used, the variables should be contained in the input
        dictionary.

        :param input_dic: a dictionary containing the ground effect model name under key
        'ground_effect' and variables for ground effect calculation.

        """

        self.ground_effect_name = input_dic["ground_effect"]

        list_var = self.get_gnd_effect_model()

        if bool(list_var) and {name for name, val in list_var.items()}.issubset(input_dic):
            self.init_ground_effect(input_dic)
            self.use_ground_effect = True
        else:
            self.use_ground_effect = False

    def get_gnd_effect_model(self):
        """Returns the input variables need to evaluate the gnd effect model"""
        if self.ground_effect_name == "Raymer":
            return self.gnd_effect_variables_raymer
        else:
            # return empty dictionnary
            return {}

    def init_ground_effect(self, input_arg):
        """
        Initialise the ground effect calculation

        Only Raymer model available
        """
        if input_arg["ground_effect"] == "Raymer":
            # TO DO : replace condition by keywords designating the ground effect model
            self._span = input_arg["span"]
            self._lg_height = input_arg["lg_height"]
            self._induced_drag_coef = input_arg["induced_drag_coef"]
            self._k_winglet = input_arg["k_winglet"]
            self._k_cd = input_arg["k_cd"]

    def cd_ground(self, cl, altitude: float = 0):

        """Evaluates the drag in ground effect, using Raymer's model:
        'Aircraft Design A conceptual approach', D. Raymer p304"""

        h_b = (self._span * 0.1 + self._lg_height + altitude) / self._span
        k_ground = 33.0 * h_b ** 1.5 / (1 + 33.0 * h_b ** 1.5)
        cd_ground = (
            self._induced_drag_coef * cl ** 2 * self._k_winglet * self._k_cd * (k_ground - 1)
        )

        return cd_ground
