"""
Simple module for performances
"""
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
import openmdao.api as om
from fastoad.constants import FlightPhase
from fastoad.utils.physics import Atmosphere
from scipy.constants import g

CLIMB_MASS_RATIO = 0.97  # = mass at end of climb / mass at start of climb
DESCENT_MASS_RATIO = 0.98  # = mass at end of descent / mass at start of descent
RESERVE_MASS_RATIO = 0.06  # = (weight of fuel reserve)/ZFW
CLIMB_DESCENT_DISTANCE = 500  # in km, distance of climb + descent


class BreguetFromMTOW(om.Group):
    """
    Estimation of fuel consumption through Breguet formula with a rough estimate
    of climb and descent phases.

    MTOW (Max TakeOff Weight) being an input, the model computes the ZFW (Zero Fuel
    Weight) considering that all fuel but the reserve has been consumed during the
    mission.
    This model does not ensure consistency with OWE (Operating Empty Weight)
    """

    # TODO: in a more general case, this module will link the starting mass to
    #   the ending mass. Could we make the module more generic ?
    def setup(self):
        self.add_subsystem("propulsion", _BreguetPropulsion(), promotes=["*"])
        self.add_subsystem("distances", _Distances(), promotes=["*"])
        self.add_subsystem("cruise_mass_ratio", _CruiseMassRatio(), promotes=["*"])
        self.add_subsystem("fuel_weights", _FuelWeightFromMTOW(), promotes=["*"])
        self.add_subsystem("consumption", _Consumption(), promotes=["*"])


class BreguetFromOWE(om.Group):
    """
    Estimation of fuel consumption through Breguet formula with a rough estimate
    of climb and descent phases.

    For the sizing mission, the Breguet formula links MTOW (Max TakeOff Weight) to
    ZFW (Zero Fuel Weight).
    OWE (Operating Weight Empty) being linked to ZFW and MTOW, a cycle is implemented
    to have consistency between these 3 values.
    """

    def setup(self):
        self.add_subsystem("propulsion", _BreguetPropulsion(), promotes=["*"])
        self.add_subsystem("distances", _Distances(), promotes=["*"])
        self.add_subsystem("cruise_mass_ratio", _CruiseMassRatio(), promotes=["*"])
        self.add_subsystem("mtow", _MTOWFromOWE(), promotes=["*"])
        self.add_subsystem("fuel_weights", _FuelWeightFromMTOW(), promotes=["*"])
        self.add_subsystem("consumption", _Consumption(), promotes=["*"])

        self.nonlinear_solver = om.NewtonSolver()
        self.nonlinear_solver.options["iprint"] = 0
        self.nonlinear_solver.options["solve_subsystems"] = False
        self.nonlinear_solver.linesearch = om.BoundsEnforceLS()
        self.linear_solver = om.DirectSolver()


class _Consumption(om.ExplicitComponent):
    """
    Adds a variable for consumption/passenger/km
    """

    def setup(self):
        self.add_input("data:mission:sizing:fuel", np.nan, units="kg")
        self.add_input("data:TLAR:range", np.nan, units="km")
        self.add_input("data:TLAR:NPAX", np.nan)

        self.add_output("data:mission:sizing:fuel:unitary", units="kg/km")
        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        fuel = inputs["data:mission:sizing:fuel"]
        npax = inputs["data:TLAR:NPAX"]
        distance = inputs["data:TLAR:range"]

        outputs["data:mission:sizing:fuel:unitary"] = fuel / npax / distance


class _BreguetPropulsion(om.ExplicitComponent):
    """
    Link with engine computation
    """

    def setup(self):
        self.add_input("data:mission:sizing:cruise:altitude", np.nan, units="m")
        self.add_input("data:TLAR:cruise_mach", np.nan)
        self.add_input("data:weight:aircraft:MTOW", np.nan, units="kg")
        self.add_input("data:aerodynamics:aircraft:cruise:L_D_max", np.nan)
        self.add_input("data:geometry:propulsion:engine:count", 2)

        self.add_output("data:propulsion:phase", FlightPhase.CRUISE)
        self.add_output("data:propulsion:use_thrust_rate", False)
        self.add_output("data:propulsion:required_thrust_rate", 0.0, lower=0.0, upper=1.0)
        self.add_output("data:propulsion:required_thrust", units="N", ref=1e5)
        self.add_output("data:propulsion:altitude", units="m", ref=1e4)
        self.add_output("data:propulsion:mach")

        self.declare_partials("data:propulsion:phase", "*", method="fd")
        self.declare_partials("data:propulsion:use_thrust_rate", "*", method="fd")
        self.declare_partials("data:propulsion:required_thrust_rate", "*", method="fd")
        self.declare_partials("data:propulsion:required_thrust", "*", method="fd")
        self.declare_partials(
            "data:propulsion:altitude", "data:mission:sizing:cruise:altitude", method="fd"
        )
        self.declare_partials("data:propulsion:mach", "data:TLAR:cruise_mach", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        engine_count = inputs["data:geometry:propulsion:engine:count"]
        ld_ratio = inputs["data:aerodynamics:aircraft:cruise:L_D_max"]
        mtow = inputs["data:weight:aircraft:MTOW"]
        initial_cruise_mass = mtow * CLIMB_MASS_RATIO

        # Variables for propulsion
        outputs["data:propulsion:altitude"] = inputs["data:mission:sizing:cruise:altitude"]
        outputs["data:propulsion:mach"] = inputs["data:TLAR:cruise_mach"]

        outputs["data:propulsion:required_thrust"] = (
            initial_cruise_mass / ld_ratio * g / engine_count
        )


class _FuelWeightFromMTOW(om.ExplicitComponent):
    """
    Estimation of fuel consumption through Breguet formula with a rough estimate
    of climb and descent phases
    """

    def setup(self):
        self.add_input("data:TLAR:cruise_mach", np.nan)
        self.add_input("data:TLAR:range", np.nan, units="m")
        self.add_input("data:aerodynamics:aircraft:cruise:L_D_max", np.nan)
        self.add_input("data:propulsion:SFC", np.nan, units="kg/N/s")
        self.add_input("data:weight:aircraft:MTOW", np.nan, units="kg")
        self.add_input("data:mission:sizing:cruise:mass_ratio", np.nan)
        self.add_input("data:mission:sizing:cruise:altitude", np.nan, units="m")

        self.add_output("data:mission:sizing:ZFW", units="kg", ref=1e4)
        self.add_output("data:mission:sizing:fuel", units="kg", ref=1e4)
        self.add_output("data:mission:sizing:trip:fuel", units="kg", ref=1e4)
        self.add_output("data:mission:sizing:climb:fuel", units="kg", ref=1e4)
        self.add_output("data:mission:sizing:cruise:fuel", units="kg", ref=1e4)
        self.add_output("data:mission:sizing:descent:fuel", units="kg", ref=1e4)
        self.add_output("data:mission:sizing:fuel_reserve", units="kg", ref=1e4)

        self.declare_partials("data:mission:sizing:ZFW", "*", method="fd")
        self.declare_partials("data:mission:sizing:fuel", "*", method="fd")
        self.declare_partials("data:mission:sizing:trip:fuel", "*", method="fd")
        self.declare_partials("data:mission:sizing:climb:fuel", "*", method="fd")
        self.declare_partials("data:mission:sizing:cruise:fuel", "*", method="fd")
        self.declare_partials("data:mission:sizing:descent:fuel", "*", method="fd")
        self.declare_partials("data:mission:sizing:fuel_reserve", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        mtow = inputs["data:weight:aircraft:MTOW"]
        cruise_mass_ratio = inputs["data:mission:sizing:cruise:mass_ratio"]

        flight_mass_ratio = cruise_mass_ratio * CLIMB_MASS_RATIO * DESCENT_MASS_RATIO
        zfw = mtow * flight_mass_ratio / (1.0 + RESERVE_MASS_RATIO)
        mission_fuel = mtow - zfw

        outputs["data:mission:sizing:ZFW"] = zfw

        outputs["data:mission:sizing:fuel"] = mission_fuel
        outputs["data:mission:sizing:trip:fuel"] = mtow * (1.0 - flight_mass_ratio)
        outputs["data:mission:sizing:climb:fuel"] = mtow * (1.0 - CLIMB_MASS_RATIO)
        outputs["data:mission:sizing:cruise:fuel"] = (
            mtow * CLIMB_MASS_RATIO * (1.0 - cruise_mass_ratio)
        )
        outputs["data:mission:sizing:descent:fuel"] = (
            mtow * CLIMB_MASS_RATIO * cruise_mass_ratio * (1.0 - DESCENT_MASS_RATIO)
        )
        outputs["data:mission:sizing:fuel_reserve"] = zfw * RESERVE_MASS_RATIO


class _MTOWFromOWE(om.ImplicitComponent):
    """
    Estimation of fuel consumption through Breguet formula with a rough estimate
    of climb and descent phases
    """

    def setup(self):
        self.add_input("data:mission:sizing:cruise:mass_ratio", np.nan)
        self.add_input("data:TLAR:range", np.nan, units="m")
        self.add_input("data:weight:aircraft:OWE", np.nan, units="kg")
        self.add_input("data:weight:aircraft:payload", np.nan, units="kg")

        self.add_output("data:weight:aircraft:MTOW", units="kg", ref=1e5)

        self.declare_partials("data:weight:aircraft:MTOW", "*", method="fd")

    def apply_nonlinear(self, inputs, outputs, residuals):
        owe = inputs["data:weight:aircraft:OWE"]
        payload_weight = inputs["data:weight:aircraft:payload"]
        cruise_mass_ratio = inputs["data:mission:sizing:cruise:mass_ratio"]

        mtow = outputs["data:weight:aircraft:MTOW"]

        flight_mass_ratio = cruise_mass_ratio * CLIMB_MASS_RATIO * DESCENT_MASS_RATIO
        zfw = mtow * flight_mass_ratio / (1.0 + RESERVE_MASS_RATIO)
        mission_owe = zfw - payload_weight

        residuals["data:weight:aircraft:MTOW"] = owe - mission_owe

    def guess_nonlinear(
        self, inputs, outputs, residuals, discrete_inputs=None, discrete_outputs=None
    ):
        # pylint: disable=too-many-arguments # It's OpenMDAO's fault :)
        outputs["data:weight:aircraft:MTOW"] = inputs["data:weight:aircraft:OWE"] * 1.5


class _Distances(om.ExplicitComponent):
    """ Rough estimation of distances for each flight phase"""

    def setup(self):
        self.add_input("data:TLAR:range", np.nan, units="m")

        self.add_output("data:mission:sizing:climb:distance", units="m", ref=1e3)
        self.add_output("data:mission:sizing:cruise:distance", units="m", ref=1e3)
        self.add_output("data:mission:sizing:descent:distance", units="m", ref=1e3)

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        flight_range = inputs["data:TLAR:range"]

        outputs["data:mission:sizing:cruise:distance"] = (
            flight_range - CLIMB_DESCENT_DISTANCE * 1000.0
        )
        outputs["data:mission:sizing:climb:distance"] = CLIMB_DESCENT_DISTANCE * 500.0
        outputs["data:mission:sizing:descent:distance"] = CLIMB_DESCENT_DISTANCE * 500.0


class _CruiseMassRatio(om.ExplicitComponent):
    """
    Estimation of fuel consumption through Breguet formula for a given cruise distance
    """

    def setup(self):
        self.add_input("data:aerodynamics:aircraft:cruise:L_D_max", np.nan)
        self.add_input("data:propulsion:SFC", np.nan, units="kg/N/s")
        self.add_input("data:TLAR:cruise_mach", np.nan)
        self.add_input("data:mission:sizing:cruise:altitude", np.nan, units="m")
        self.add_input("data:mission:sizing:cruise:distance", np.nan, units="m")

        self.add_output("data:mission:sizing:cruise:mass_ratio")

        self.declare_partials("data:mission:sizing:cruise:mass_ratio", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        atmosphere = Atmosphere(
            inputs["data:mission:sizing:cruise:altitude"], altitude_in_feet=False
        )
        cruise_speed = atmosphere.speed_of_sound * inputs["data:TLAR:cruise_mach"]

        cruise_distance = inputs["data:mission:sizing:cruise:distance"]
        ld_ratio = inputs["data:aerodynamics:aircraft:cruise:L_D_max"]
        sfc = inputs["data:propulsion:SFC"]

        range_factor = cruise_speed * ld_ratio / g / sfc
        # During first iterations, SFC will be incorrect and range_factor may be too low,
        # resulting in null or too small cruise_mass_ratio.
        # Forcing cruise_mass_ratio to a minimum of 0.3 avoids problems and should not
        # harm (no airplane loses 70% of its weight from fuel consumption)
        cruise_mass_ratio = np.maximum(0.3, 1.0 / np.exp(cruise_distance / range_factor))

        outputs["data:mission:sizing:cruise:mass_ratio"] = cruise_mass_ratio
