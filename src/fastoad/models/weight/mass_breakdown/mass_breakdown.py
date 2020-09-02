"""Main components for mass breakdown."""
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

import openmdao.api as om

from fastoad.models.options import PAYLOAD_FROM_NPAX
from .a_airframe import (
    WingWeight,
    FuselageWeight,
    EmpennageWeight,
    FlightControlsWeight,
    LandingGearWeight,
    PylonsWeight,
    PaintWeight,
)
from .b_propulsion import (
    EngineWeight,
    FuelLinesWeight,
    UnconsumablesWeight,
)
from .c_systems import (
    PowerSystemsWeight,
    LifeSupportSystemsWeight,
    NavigationSystemsWeight,
    TransmissionSystemsWeight,
    FixedOperationalSystemsWeight,
    FlightKitWeight,
)
from .cs25 import Loads
from .d_furniture import (
    PassengerSeatsWeight,
    FoodWaterWeight,
    SecurityKitWeight,
    ToiletsWeight,
)
from .e_crew import CrewWeight
from .payload import ComputePayload
from .update_mlw_and_mzfw import UpdateMLWandMZFW


class MTOWComputation(om.AddSubtractComp):
    """
    Computes MTOW from OWE, design payload and consumed fuel in sizing mission.
    """

    def setup(self):
        self.add_equation(
            "data:weight:aircraft:MTOW",
            [
                "data:weight:aircraft:OWE",
                "data:weight:aircraft:payload",
                "data:mission:sizing:fuel",
            ],
            units="kg",
        )


class MassBreakdown(om.Group):
    """
    Computes analytically the mass of each part of the aircraft, and the resulting sum,
    the Overall Weight Empty (OWE).

    Some models depend on MZFW (Max Zero Fuel Weight), MLW (Max Landing Weight) and
    MTOW (Max TakeOff Weight), which depend on OWE.

    This model cycles for having consistent OWE, MZFW and MLW.

    Options:
    - payload_from_npax: If True (default), payload masses will be computed from NPAX, if False
                         design payload mass and maximum payload mass must be provided.
    """

    def initialize(self):
        self.options.declare(PAYLOAD_FROM_NPAX, types=bool, default=True)

    def setup(self):
        if self.options[PAYLOAD_FROM_NPAX]:
            self.add_subsystem("payload", ComputePayload(), promotes=["*"])
        self.add_subsystem("owe", OperatingWeightEmpty(), promotes=["*"])
        self.add_subsystem("update_mzfw_and_mlw", UpdateMLWandMZFW(), promotes=["*"])

        # Solvers setup
        self.nonlinear_solver = om.NonlinearBlockGS()
        self.nonlinear_solver.options["iprint"] = 0
        self.nonlinear_solver.options["maxiter"] = 50

        self.linear_solver = om.LinearBlockGS()
        self.linear_solver.options["iprint"] = 0


class AirframeWeight(om.Group):
    """
    Computes mass of airframe.
    """

    def setup(self):
        # Airframe
        self.add_subsystem("loads", Loads(), promotes=["*"])
        self.add_subsystem("wing_weight", WingWeight(), promotes=["*"])
        self.add_subsystem("fuselage_weight", FuselageWeight(), promotes=["*"])
        self.add_subsystem("empennage_weight", EmpennageWeight(), promotes=["*"])
        self.add_subsystem("flight_controls_weight", FlightControlsWeight(), promotes=["*"])
        self.add_subsystem("landing_gear_weight", LandingGearWeight(), promotes=["*"])
        self.add_subsystem("pylons_weight", PylonsWeight(), promotes=["*"])
        self.add_subsystem("paint_weight", PaintWeight(), promotes=["*"])

        weight_sum = om.AddSubtractComp()
        weight_sum.add_equation(
            "data:weight:airframe:mass",
            [
                "data:weight:airframe:wing:mass",
                "data:weight:airframe:fuselage:mass",
                "data:weight:airframe:horizontal_tail:mass",
                "data:weight:airframe:vertical_tail:mass",
                "data:weight:airframe:flight_controls:mass",
                "data:weight:airframe:landing_gear:main:mass",
                "data:weight:airframe:landing_gear:front:mass",
                "data:weight:airframe:pylon:mass",
                "data:weight:airframe:paint:mass",
            ],
            units="kg",
            desc="Mass of airframe",
        )

        self.add_subsystem(
            "airframe_weight_sum", weight_sum, promotes=["*"],
        )


class PropulsionWeight(om.Group):
    """
    Computes mass of propulsion.
    """

    def setup(self):
        # Engine have to be computed before pylons
        self.add_subsystem("engines_weight", EngineWeight(), promotes=["*"])
        self.add_subsystem("fuel_lines_weight", FuelLinesWeight(), promotes=["*"])
        self.add_subsystem("unconsumables_weight", UnconsumablesWeight(), promotes=["*"])

        weight_sum = om.AddSubtractComp()
        weight_sum.add_equation(
            "data:weight:propulsion:mass",
            [
                "data:weight:propulsion:engine:mass",
                "data:weight:propulsion:fuel_lines:mass",
                "data:weight:propulsion:unconsumables:mass",
            ],
            units="kg",
            desc="Mass of the propulsion system",
        )

        self.add_subsystem(
            "propulsion_weight_sum", weight_sum, promotes=["*"],
        )


class SystemsWeight(om.Group):
    """
    Computes mass of systems.
    """

    def setup(self):
        self.add_subsystem("power_systems_weight", PowerSystemsWeight(), promotes=["*"])
        self.add_subsystem(
            "life_support_systems_weight", LifeSupportSystemsWeight(), promotes=["*"]
        )
        self.add_subsystem("navigation_systems_weight", NavigationSystemsWeight(), promotes=["*"])
        self.add_subsystem(
            "transmission_systems_weight", TransmissionSystemsWeight(), promotes=["*"]
        )
        self.add_subsystem(
            "fixed_operational_systems_weight", FixedOperationalSystemsWeight(), promotes=["*"]
        )
        self.add_subsystem("flight_kit_weight", FlightKitWeight(), promotes=["*"])

        weight_sum = om.AddSubtractComp()
        weight_sum.add_equation(
            "data:weight:systems:mass",
            [
                "data:weight:systems:power:auxiliary_power_unit:mass",
                "data:weight:systems:power:electric_systems:mass",
                "data:weight:systems:power:hydraulic_systems:mass",
                "data:weight:systems:life_support:insulation:mass",
                "data:weight:systems:life_support:air_conditioning:mass",
                "data:weight:systems:life_support:de-icing:mass",
                "data:weight:systems:life_support:cabin_lighting:mass",
                "data:weight:systems:life_support:seats_crew_accommodation:mass",
                "data:weight:systems:life_support:oxygen:mass",
                "data:weight:systems:life_support:safety_equipment:mass",
                "data:weight:systems:navigation:mass",
                "data:weight:systems:transmission:mass",
                "data:weight:systems:operational:radar:mass",
                "data:weight:systems:operational:cargo_hold:mass",
                "data:weight:systems:flight_kit:mass",
            ],
            units="kg",
            desc="Mass of aircraft systems",
        )

        self.add_subsystem(
            "systems_weight_sum", weight_sum, promotes=["*"],
        )


class FurnitureWeight(om.Group):
    """
    Computes mass of furniture.
    """

    def setup(self):
        self.add_subsystem("passenger_seats_weight", PassengerSeatsWeight(), promotes=["*"])
        self.add_subsystem("food_water_weight", FoodWaterWeight(), promotes=["*"])
        self.add_subsystem("security_kit_weight", SecurityKitWeight(), promotes=["*"])
        self.add_subsystem("toilets_weight", ToiletsWeight(), promotes=["*"])

        weight_sum = om.AddSubtractComp()
        weight_sum.add_equation(
            "data:weight:furniture:mass",
            [
                "data:weight:furniture:passenger_seats:mass",
                "data:weight:furniture:food_water:mass",
                "data:weight:furniture:security_kit:mass",
                "data:weight:furniture:toilets:mass",
            ],
            units="kg",
            desc="Mass of aircraft furniture",
        )

        self.add_subsystem(
            "furniture_weight_sum", weight_sum, promotes=["*"],
        )


class OperatingWeightEmpty(om.Group):
    """Operating Empty Weight (OEW) estimation.

    This group aggregates weight from all components of the aircraft.
    """

    def setup(self):
        # Propulsion should be done before airframe, because it drives pylon mass.
        self.add_subsystem("propulsion_weight", PropulsionWeight(), promotes=["*"])
        self.add_subsystem("airframe_weight", AirframeWeight(), promotes=["*"])
        self.add_subsystem("systems_weight", SystemsWeight(), promotes=["*"])
        self.add_subsystem("furniture_weight", FurnitureWeight(), promotes=["*"])
        self.add_subsystem("crew_weight", CrewWeight(), promotes=["*"])

        weight_sum = om.AddSubtractComp()
        weight_sum.add_equation(
            "data:weight:aircraft:OWE",
            [
                "data:weight:airframe:mass",
                "data:weight:propulsion:mass",
                "data:weight:systems:mass",
                "data:weight:furniture:mass",
                "data:weight:crew:mass",
            ],
            units="kg",
            desc="Mass of crew",
        )

        self.add_subsystem("OWE_sum", weight_sum, promotes=["*"])
