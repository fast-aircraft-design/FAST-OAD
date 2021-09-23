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

from abc import ABC, abstractmethod

import numpy as np
import openmdao.api as om


class AbstractComputeCGLoadCase(om.ExplicitComponent, ABC):
    def initialize(self):
        self.options.declare("case_number", 1, types=int)

    def setup(self):
        self.output_name = (
            "data:weight:aircraft:load_case_%i:CG:MAC_position" % self.options["case_number"]
        )

        self.add_input("data:geometry:wing:MAC:length", val=np.nan, units="m")
        self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan, units="m")
        self.add_input("data:weight:payload:PAX:CG:x", val=np.nan, units="m")
        self.add_input("data:weight:payload:rear_fret:CG:x", val=np.nan, units="m")
        self.add_input("data:weight:payload:front_fret:CG:x", val=np.nan, units="m")
        self.add_input("data:TLAR:NPAX", val=np.nan)
        self.add_input("data:weight:aircraft_empty:CG:x", val=np.nan, units="m")
        self.add_input("data:weight:aircraft_empty:mass", val=np.nan, units="kg")

        self.add_output(self.output_name)

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    @abstractmethod
    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        """
        This method is expected to set the value of output with name provided by
        :attr:`output_name`.

        Hence it should end with::

            outputs[self.output_name] = self.compute_cg_ratio(...)
        """

    @staticmethod
    def compute_cg_ratio(
        inputs, weight_per_pax, weight_front_fret, weight_rear_fret, weight_fuel=0.0, cg_fuel=0.0,
    ):
        """
        Will compute the CG ratio according to provided inputs

        :param inputs: input vector from OpenMDAO
        :param weight_per_pax: in kg/passenger
        :param weight_front_fret: in kg
        :param weight_rear_fret: in kg
        :param weight_fuel: in kg
        :param cg_fuel: in meters
        :return: CG ratio with respect to 25% MAC
        """
        l0_wing = inputs["data:geometry:wing:MAC:length"]
        fa_length = inputs["data:geometry:wing:MAC:at25percent:x"]
        cg_pax = inputs["data:weight:payload:PAX:CG:x"]
        cg_rear_fret = inputs["data:weight:payload:rear_fret:CG:x"]
        cg_front_fret = inputs["data:weight:payload:front_fret:CG:x"]
        npax = inputs["data:TLAR:NPAX"]
        x_cg_plane_aft = inputs["data:weight:aircraft_empty:CG:x"]
        x_cg_plane_down = inputs["data:weight:aircraft_empty:mass"]
        x_cg_plane_up = x_cg_plane_aft * x_cg_plane_down
        weight_pax = npax * weight_per_pax
        weight_pl = weight_pax + weight_rear_fret + weight_front_fret + weight_fuel
        x_cg_pl = (
            weight_pax * cg_pax
            + weight_rear_fret * cg_rear_fret
            + weight_front_fret * cg_front_fret
            + weight_fuel * cg_fuel
        ) / weight_pl
        x_cg_plane_pl = (x_cg_plane_up + weight_pl * x_cg_pl) / (x_cg_plane_down + weight_pl)
        cg_ratio_pl = (x_cg_plane_pl - fa_length + 0.25 * l0_wing) / l0_wing
        return cg_ratio_pl
