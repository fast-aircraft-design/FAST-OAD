"""CG calculation for load cases."""
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
import openmdao.api as om


class ComputeCGLoadCase(om.ExplicitComponent):
    """
    Base class for computing load cases for CG calculations.
    """

    @property
    def output_name(self):
        """Builds name of the unique output from option "case_number"."""
        return "data:weight:aircraft:load_case_%i:CG:MAC_position" % self.options["case_number"]

    def initialize(self):
        self.options.declare("case_number", 1, types=int)
        self.options.declare("mass_per_pax", 80.0, types=float)
        self.options.declare("mass_front_fret_per_pax", 0.0, types=float)
        self.options.declare("mass_rear_fret_per_pax", 0.0, types=float)
        self.options.declare("fuel_mass_variable", "", types=str, allow_none=True)

    def setup(self):
        self.add_input("data:geometry:wing:MAC:length", val=np.nan, units="m")
        self.add_input("data:geometry:wing:MAC:at25percent:x", val=np.nan, units="m")
        self.add_input("data:weight:payload:PAX:CG:x", val=np.nan, units="m")
        self.add_input("data:weight:payload:rear_fret:CG:x", val=np.nan, units="m")
        self.add_input("data:weight:payload:front_fret:CG:x", val=np.nan, units="m")
        self.add_input("data:TLAR:NPAX", val=np.nan)
        self.add_input("data:weight:aircraft_empty:CG:x", val=np.nan, units="m")
        self.add_input("data:weight:aircraft_empty:mass", val=np.nan, units="kg")

        if self.options["fuel_mass_variable"]:
            self.add_input(self.options["fuel_mass_variable"], val=np.nan, units="kg")
            self.add_input("data:weight:fuel_tank:CG:x", val=np.nan, units="m")

        self.add_output(self.output_name)

    def setup_partials(self):
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        l0_wing = inputs["data:geometry:wing:MAC:length"]
        fa_length = inputs["data:geometry:wing:MAC:at25percent:x"]
        x_cg_aircraft_empty = inputs["data:weight:aircraft_empty:CG:x"]
        mass_aircraft_empty = inputs["data:weight:aircraft_empty:mass"]

        mass_payload, x_cg_payload = self._get_payload_mass_and_cg(inputs)

        x_cg_aircraft_with_payload = (
            mass_aircraft_empty * x_cg_aircraft_empty + mass_payload * x_cg_payload
        ) / (mass_aircraft_empty + mass_payload)
        cg_ratio_aircraft_with_payload = (
            x_cg_aircraft_with_payload - fa_length + 0.25 * l0_wing
        ) / l0_wing
        outputs[self.output_name] = cg_ratio_aircraft_with_payload

    def _get_payload_mass_and_cg(self, inputs):
        """

        :param inputs:
        :return: tuple (payload mass, X-position of payload CG)
        """

        cg_pax = inputs["data:weight:payload:PAX:CG:x"]
        cg_rear_fret = inputs["data:weight:payload:rear_fret:CG:x"]
        cg_front_fret = inputs["data:weight:payload:front_fret:CG:x"]
        npax = inputs["data:TLAR:NPAX"]

        mass_pax = npax * self.options["mass_per_pax"]
        mass_front_fret = inputs["data:TLAR:NPAX"] * self.options["mass_front_fret_per_pax"]
        mass_rear_fret = inputs["data:TLAR:NPAX"] * self.options["mass_rear_fret_per_pax"]
        if self.options["fuel_mass_variable"]:
            mass_fuel = inputs[self.options["fuel_mass_variable"]]
            cg_fuel = inputs["data:weight:fuel_tank:CG:x"]
        else:
            mass_fuel = 0.0
            cg_fuel = 0.0

        mass_payload = mass_pax + mass_rear_fret + mass_front_fret + mass_fuel
        x_cg_payload = (
            mass_pax * cg_pax
            + mass_rear_fret * cg_rear_fret
            + mass_front_fret * cg_front_fret
            + mass_fuel * cg_fuel
        ) / mass_payload

        return mass_payload, x_cg_payload
