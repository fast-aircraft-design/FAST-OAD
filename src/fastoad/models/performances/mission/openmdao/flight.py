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
import pandas as pd
from fastoad import BundleLoader
from fastoad.constants import FlightPhase
from fastoad.models.aerodynamics.constants import POLAR_POINT_COUNT
from fastoad.models.performances.mission.segments.hold import HoldSegment
from fastoad.models.performances.mission.segments.taxi import TaxiSegment
from fastoad.models.propulsion import EngineSet
from scipy.constants import foot, nautical_mile

from ..flight.base import RangedFlight
from ..flight.standard_flight import StandardFlight
from ..flight_point import FlightPoint
from ..polar import Polar


class SizingFlight(om.ExplicitComponent):
    def __init__(self, **kwargs):
        """
        Computes thrust, SFC and thrust rate by direct call to engine model.
        """
        super().__init__(**kwargs)
        self._engine_wrapper = BundleLoader().instantiate_component(self.options["propulsion_id"])
        self.flight_points = None

    def initialize(self):
        self.options.declare("propulsion_id", default="", types=str)

    def setup(self):

        self._engine_wrapper.setup(self)

        self.add_input("data:geometry:propulsion:engine:count", 2)
        self.add_input("data:geometry:wing:area", np.nan, units="m**2")
        self.add_input("data:TLAR:cruise_mach", np.nan)
        self.add_input("data:TLAR:range", np.nan, units="m")
        self.add_input("data:mission:sizing:alternate_cruise:distance", np.nan, units="m")
        self.add_input("data:mission:sizing:climb:thrust_rate", np.nan)
        self.add_input("data:mission:sizing:descent:thrust_rate", np.nan)
        self.add_input("data:aerodynamics:aircraft:cruise:CL", np.nan, shape=POLAR_POINT_COUNT)
        self.add_input("data:aerodynamics:aircraft:cruise:CD", np.nan, shape=POLAR_POINT_COUNT)
        self.add_input("data:aerodynamics:aircraft:low_speed:CL", np.nan, shape=POLAR_POINT_COUNT)
        self.add_input("data:aerodynamics:aircraft:low_speed:CD", np.nan, shape=POLAR_POINT_COUNT)

        self.add_input("data:aerodynamics:high_lift_devices:takeoff:CL", np.nan)
        self.add_input("data:aerodynamics:high_lift_devices:takeoff:CD", np.nan)

        self.add_input("data:mission:sizing:holding:duration", np.nan, units="s")
        self.add_input("data:mission:sizing:taxi_in:duration", np.nan, units="s")
        self.add_input("data:mission:sizing:taxi_in:thrust_rate", np.nan, units="s")
        self.add_input("data:weight:aircraft:MTOW", np.nan, units="kg")
        self.add_input("data:mission:sizing:takeoff:V2", np.nan, units="m/s")
        self.add_input("data:mission:sizing:takeoff:altitude", np.nan, units="m")
        self.add_input("data:mission:sizing:takeoff:fuel", np.nan, units="kg")

        self.add_output("data:mission:sizing:ZFW", units="kg")
        self.add_output("data:mission:sizing:initial_climb:fuel", units="kg")
        self.add_output("data:mission:sizing:climb:fuel", units="kg")
        self.add_output("data:mission:sizing:cruise:fuel", units="kg")
        self.add_output("data:mission:sizing:descent:fuel", units="kg")
        self.add_output("data:mission:sizing:alternate_climb:fuel", units="kg")
        self.add_output("data:mission:sizing:alternate_cruise:fuel", units="kg")
        self.add_output("data:mission:sizing:alternate_descent:fuel", units="kg")
        self.add_output("data:mission:sizing:holding:fuel", units="kg")
        self.add_output("data:mission:sizing:taxi_in:fuel", units="kg")

        self.declare_partials(["*"], ["*"])

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        engine_model = EngineSet(
            self._engine_wrapper.get_model(inputs), inputs["data:geometry:propulsion:engine:count"]
        )
        reference_area = inputs["data:geometry:wing:area"]
        cruise_mach = inputs["data:TLAR:cruise_mach"]
        flight_distance = inputs["data:TLAR:range"]
        thrust_rates = {
            FlightPhase.CLIMB: inputs["data:mission:sizing:climb:thrust_rate"],
            FlightPhase.DESCENT: inputs["data:mission:sizing:descent:thrust_rate"],
        }
        high_speed_polar = Polar(
            inputs["data:aerodynamics:aircraft:cruise:CL"],
            inputs["data:aerodynamics:aircraft:cruise:CD"],
        )
        low_speed_climb_polar = Polar(
            inputs["data:aerodynamics:aircraft:low_speed:CL"]
            + inputs["data:aerodynamics:high_lift_devices:takeoff:CL"],
            inputs["data:aerodynamics:aircraft:low_speed:CD"]
            + inputs["data:aerodynamics:high_lift_devices:takeoff:CD"],
        )

        base_flight_calculator = RangedFlight(
            StandardFlight(
                propulsion=engine_model,
                reference_area=reference_area,
                low_speed_climb_polar=low_speed_climb_polar,
                high_speed_polar=high_speed_polar,
                cruise_mach=cruise_mach,
                thrust_rates=thrust_rates,
            ),
            flight_distance,
        )

        end_of_takeoff = FlightPoint(
            mass=inputs["data:weight:aircraft:MTOW"] - inputs["data:mission:sizing:takeoff:fuel"],
            true_airspeed=inputs["data:mission:sizing:takeoff:V2"],
            altitude=inputs["data:mission:sizing:takeoff:altitude"] + 35 * foot,
            ground_distance=0.0,
        )

        flight_points = base_flight_calculator.compute(end_of_takeoff)

        end_of_takeoff = FlightPoint(flight_points.iloc[0])  # now updated for every parameter
        end_of_initial_climb = FlightPoint(
            flight_points.loc[flight_points.tag == "End of initial climb"].iloc[0]
        )
        end_of_climb = FlightPoint(flight_points.loc[flight_points.tag == "End of climb"].iloc[0])
        end_of_cruise = FlightPoint(flight_points.loc[flight_points.tag == "End of cruise"].iloc[0])
        end_of_descent = FlightPoint(
            flight_points.loc[flight_points.tag == "End of descent"].iloc[0]
        )
        outputs["data:mission:sizing:initial_climb:fuel"] = (
            end_of_takeoff.mass - end_of_initial_climb.mass
        )
        outputs["data:mission:sizing:climb:fuel"] = end_of_initial_climb.mass - end_of_climb.mass
        outputs["data:mission:sizing:cruise:fuel"] = end_of_climb.mass - end_of_cruise.mass
        outputs["data:mission:sizing:descent:fuel"] = end_of_cruise.mass - end_of_descent.mass

        # Alternate flight =====================================================
        alternate_distance = inputs["data:mission:sizing:alternate_cruise:distance"]
        if alternate_distance <= 200 * nautical_mile:
            alternate_cruise_altitude = 22000 * foot

        else:
            alternate_cruise_altitude = 31000 * foot

        alternate_flight_calculator = RangedFlight(
            StandardFlight(
                propulsion=engine_model,
                reference_area=reference_area,
                low_speed_climb_polar=low_speed_climb_polar,
                high_speed_polar=high_speed_polar,
                cruise_mach=cruise_mach,
                thrust_rates=thrust_rates,
                climb_target_altitude=alternate_cruise_altitude,
            ),
            alternate_distance,
        )
        alternate_flight_points = alternate_flight_calculator.compute(end_of_descent)

        end_of_alternate_climb = FlightPoint(
            alternate_flight_points.loc[alternate_flight_points.tag == "End of climb"].iloc[0]
        )
        end_of_alternate_cruise = FlightPoint(
            alternate_flight_points.loc[alternate_flight_points.tag == "End of cruise"].iloc[0]
        )
        end_of_alternate_descent = FlightPoint(
            alternate_flight_points.loc[alternate_flight_points.tag == "End of descent"].iloc[0]
        )

        outputs["data:mission:sizing:alternate_climb:fuel"] = (
            end_of_descent.mass - end_of_alternate_climb.mass
        )
        outputs["data:mission:sizing:alternate_cruise:fuel"] = (
            end_of_alternate_climb.mass - end_of_alternate_cruise.mass
        )
        outputs["data:mission:sizing:alternate_descent:fuel"] = (
            end_of_alternate_cruise.mass - end_of_alternate_descent.mass
        )

        # Holding ==============================================================

        holding_duration = inputs["data:mission:sizing:holding:duration"]

        holding_calculator = HoldSegment(
            target=FlightPoint(time=holding_duration),
            propulsion=engine_model,
            reference_area=reference_area,
            polar=high_speed_polar,
        )

        holding_flight_points = holding_calculator.compute(end_of_alternate_descent)
        holding_flight_points.tag.iloc[-1] = "End of holding"

        end_of_holding = FlightPoint(holding_flight_points.iloc[-1])
        outputs["data:mission:sizing:holding:fuel"] = (
            end_of_alternate_descent.mass - end_of_holding.mass
        )

        # Taxi-in ==============================================================
        taxi_in_duration = inputs["data:mission:sizing:taxi_in:duration"]
        taxi_in_thrust_rate = inputs["data:mission:sizing:taxi_in:thrust_rate"]

        taxi_in_calculator = TaxiSegment(
            target=FlightPoint(time=taxi_in_duration),
            propulsion=engine_model,
            thrust_rate=taxi_in_thrust_rate,
        )
        taxi_in_flight_points = taxi_in_calculator.compute(end_of_holding)
        taxi_in_flight_points.tag.iloc[-1] = "End of taxi-in"

        end_of_taxi_in = FlightPoint(taxi_in_flight_points.iloc[-1])
        outputs["data:mission:sizing:taxi_in:fuel"] = end_of_holding.mass - end_of_taxi_in.mass

        # Final ================================================================
        fuel_route = inputs["data:weight:aircraft:MTOW"] - end_of_descent.mass
        outputs["data:mission:sizing:ZFW"] = end_of_taxi_in.mass - 0.03 * fuel_route
        self.flight_points = pd.concat(
            [flight_points, alternate_flight_points, holding_flight_points, taxi_in_flight_points]
        ).reset_index(drop=True)
