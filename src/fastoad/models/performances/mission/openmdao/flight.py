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
from scipy.constants import foot, nautical_mile

from fastoad import BundleLoader
from fastoad.base.flight_point import FlightPoint
from fastoad.constants import FlightPhase
from fastoad.models.aerodynamics.constants import POLAR_POINT_COUNT
from fastoad.models.performances.breguet import Breguet
from fastoad.models.performances.mission.segments.hold import HoldSegment
from fastoad.models.performances.mission.segments.taxi import TaxiSegment
from fastoad.models.propulsion.fuel_propulsion.base import FuelEngineSet
from ..flight.base import RangedFlight
from ..flight.standard_flight import StandardFlight
from ..polar import Polar


class SizingFlight(om.ExplicitComponent):
    """
    Simulates a complete flight mission with diversion.
    """

    def __init__(self, **kwargs):
        """
        Computes thrust, SFC and thrust rate by direct call to engine model.

        Options:
          - propulsion_id: (mandatory) the identifier of the propulsion wrapper.
          - out_file: if provided, a csv file will be written at provided path with all computed
                      flight points. If path is relative, it will be resolved from working
                      directory
        """
        super().__init__(**kwargs)
        self.flight_points = None
        self._engine_wrapper = None

    def initialize(self):
        self.options.declare("propulsion_id", default="", types=str)
        self.options.declare("out_file", default="", types=str)

    def setup(self):
        self._engine_wrapper = BundleLoader().instantiate_component(self.options["propulsion_id"])
        self._engine_wrapper.setup(self)

        # Inputs -----------------------------------------------------------------------------------
        self.add_input("data:TLAR:cruise_mach", np.nan)
        self.add_input("data:TLAR:range", np.nan, units="m")

        self.add_input("data:geometry:propulsion:engine:count", 2)
        self.add_input("data:geometry:wing:area", np.nan, units="m**2")

        self.add_input("data:aerodynamics:aircraft:cruise:CL", np.nan, shape=POLAR_POINT_COUNT)
        self.add_input("data:aerodynamics:aircraft:cruise:CD", np.nan, shape=POLAR_POINT_COUNT)

        self.add_input("data:aerodynamics:aircraft:takeoff:CL", np.nan, shape=POLAR_POINT_COUNT)
        self.add_input("data:aerodynamics:aircraft:takeoff:CD", np.nan, shape=POLAR_POINT_COUNT)

        self.add_input("data:weight:aircraft:MTOW", np.nan, units="kg")

        self.add_input("data:mission:sizing:taxi_out:fuel", np.nan, units="kg")

        self.add_input("data:mission:sizing:takeoff:V2", np.nan, units="m/s")

        self.add_input("data:mission:sizing:takeoff:altitude", np.nan, units="m")
        self.add_input("data:mission:sizing:takeoff:fuel", np.nan, units="kg")

        self.add_input("data:mission:sizing:climb:thrust_rate", np.nan)
        self.add_input("data:mission:sizing:descent:thrust_rate", np.nan)

        self.add_input("data:mission:sizing:diversion:distance", np.nan, units="m")
        self.add_input("data:mission:sizing:holding:duration", np.nan, units="s")

        self.add_input("data:mission:sizing:taxi_in:duration", np.nan, units="s")
        self.add_input("data:mission:sizing:taxi_in:speed", np.nan, units="m/s")
        self.add_input("data:mission:sizing:taxi_in:thrust_rate", np.nan)

        # Outputs ----------------------------------------------------------------------------------
        self.add_output("data:mission:sizing:initial_climb:fuel", units="kg")
        self.add_output("data:mission:sizing:main_route:climb:fuel", units="kg")
        self.add_output("data:mission:sizing:main_route:cruise:fuel", units="kg")
        self.add_output("data:mission:sizing:main_route:descent:fuel", units="kg")

        self.add_output("data:mission:sizing:initial_climb:distance", units="m")
        self.add_output("data:mission:sizing:main_route:climb:distance", units="m")
        self.add_output("data:mission:sizing:main_route:cruise:distance", units="m")
        self.add_output("data:mission:sizing:main_route:descent:distance", units="m")

        self.add_output("data:mission:sizing:initial_climb:duration", units="s")
        self.add_output("data:mission:sizing:main_route:climb:duration", units="s")
        self.add_output("data:mission:sizing:main_route:cruise:duration", units="s")
        self.add_output("data:mission:sizing:main_route:descent:duration", units="s")

        self.add_output("data:mission:sizing:diversion:climb:fuel", units="kg")
        self.add_output("data:mission:sizing:diversion:cruise:fuel", units="kg")
        self.add_output("data:mission:sizing:diversion:descent:fuel", units="kg")

        self.add_output("data:mission:sizing:diversion:climb:distance", units="m")
        self.add_output("data:mission:sizing:diversion:cruise:distance", units="m")
        self.add_output("data:mission:sizing:diversion:descent:distance", units="m")

        self.add_output("data:mission:sizing:diversion:climb:duration", units="s")
        self.add_output("data:mission:sizing:diversion:cruise:duration", units="s")
        self.add_output("data:mission:sizing:diversion:descent:duration", units="s")

        self.add_output("data:mission:sizing:holding:fuel", units="kg")
        self.add_output("data:mission:sizing:taxi_in:fuel", units="kg")

        self.add_output("data:mission:sizing:ZFW", units="kg")
        self.add_output("data:mission:sizing:fuel", units="kg")

        self.declare_partials(["*"], ["*"])

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        try:
            self.compute_mission(inputs, outputs)
        except IndexError:
            self.compute_breguet(inputs, outputs)

    def compute_breguet(self, inputs, outputs):
        propulsion_model = FuelEngineSet(
            self._engine_wrapper.get_model(inputs), inputs["data:geometry:propulsion:engine:count"]
        )
        high_speed_polar = Polar(
            inputs["data:aerodynamics:aircraft:cruise:CL"],
            inputs["data:aerodynamics:aircraft:cruise:CD"],
        )

        breguet = Breguet(
            propulsion_model,
            max(
                10.0, high_speed_polar.optimal_cl / high_speed_polar.cd(high_speed_polar.optimal_cl)
            ),
            inputs["data:TLAR:cruise_mach"],
            10000.0,
        )
        breguet.compute(
            inputs["data:weight:aircraft:MTOW"], inputs["data:TLAR:range"],
        )

        outputs["data:mission:sizing:ZFW"] = breguet.zfw
        outputs["data:mission:sizing:fuel"] = breguet.mission_fuel

    def compute_mission(self, inputs, outputs):
        propulsion_model = FuelEngineSet(
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
            inputs["data:aerodynamics:aircraft:takeoff:CL"],
            inputs["data:aerodynamics:aircraft:takeoff:CD"],
        )

        base_flight_calculator = RangedFlight(
            StandardFlight(
                propulsion=propulsion_model,
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

        flight_points = base_flight_calculator.compute_from(end_of_takeoff)

        # Update start flight point with computed (non initialized) parameters
        end_of_takeoff = FlightPoint(flight_points.iloc[0])

        # Get flight points for each end of phase
        end_of_initial_climb = FlightPoint(
            flight_points.loc[flight_points.name == FlightPhase.INITIAL_CLIMB.value].iloc[-1]
        )
        end_of_climb = FlightPoint(
            flight_points.loc[flight_points.name == FlightPhase.CLIMB.value].iloc[-1]
        )
        end_of_cruise = FlightPoint(
            flight_points.loc[flight_points.name == FlightPhase.CRUISE.value].iloc[-1]
        )
        end_of_descent = FlightPoint(
            flight_points.loc[flight_points.name == FlightPhase.DESCENT.value].iloc[-1]
        )

        # Set OpenMDAO outputs
        outputs["data:mission:sizing:initial_climb:fuel"] = (
            end_of_takeoff.mass - end_of_initial_climb.mass
        )
        outputs["data:mission:sizing:main_route:climb:fuel"] = (
            end_of_initial_climb.mass - end_of_climb.mass
        )
        outputs["data:mission:sizing:main_route:cruise:fuel"] = (
            end_of_climb.mass - end_of_cruise.mass
        )
        outputs["data:mission:sizing:main_route:descent:fuel"] = (
            end_of_cruise.mass - end_of_descent.mass
        )
        outputs["data:mission:sizing:initial_climb:distance"] = (
            end_of_initial_climb.ground_distance - end_of_takeoff.ground_distance
        )
        outputs["data:mission:sizing:main_route:climb:distance"] = (
            end_of_climb.ground_distance - end_of_initial_climb.ground_distance
        )
        outputs["data:mission:sizing:main_route:cruise:distance"] = (
            end_of_cruise.ground_distance - end_of_climb.ground_distance
        )
        outputs["data:mission:sizing:main_route:descent:distance"] = (
            end_of_descent.ground_distance - end_of_cruise.ground_distance
        )
        outputs["data:mission:sizing:initial_climb:duration"] = (
            end_of_initial_climb.time - end_of_takeoff.time
        )
        outputs["data:mission:sizing:main_route:climb:duration"] = (
            end_of_climb.time - end_of_initial_climb.time
        )
        outputs["data:mission:sizing:main_route:cruise:duration"] = (
            end_of_cruise.time - end_of_climb.time
        )
        outputs["data:mission:sizing:main_route:descent:duration"] = (
            end_of_descent.time - end_of_cruise.time
        )

        # Diversion flight =====================================================
        diversion_distance = inputs["data:mission:sizing:diversion:distance"]
        if diversion_distance <= 200 * nautical_mile:
            diversion_cruise_altitude = 22000 * foot

        else:
            diversion_cruise_altitude = 31000 * foot

        diversion_flight_calculator = RangedFlight(
            StandardFlight(
                propulsion=propulsion_model,
                reference_area=reference_area,
                low_speed_climb_polar=low_speed_climb_polar,
                high_speed_polar=high_speed_polar,
                cruise_mach=cruise_mach,
                thrust_rates=thrust_rates,
                climb_target_altitude=diversion_cruise_altitude,
            ),
            diversion_distance,
        )
        diversion_flight_points = diversion_flight_calculator.compute_from(end_of_descent)

        # Get flight points for each end of phase
        end_of_diversion_climb = FlightPoint(
            diversion_flight_points.loc[
                diversion_flight_points.name == FlightPhase.CLIMB.value
            ].iloc[-1]
        )
        end_of_diversion_cruise = FlightPoint(
            diversion_flight_points.loc[
                diversion_flight_points.name == FlightPhase.CRUISE.value
            ].iloc[-1]
        )
        end_of_diversion_descent = FlightPoint(
            diversion_flight_points.loc[
                diversion_flight_points.name == FlightPhase.DESCENT.value
            ].iloc[-1]
        )

        # rename phases because all flight points will be concatenated later.
        diversion_flight_points.name = "diversion_" + diversion_flight_points.name

        # Set OpenMDAO outputs
        outputs["data:mission:sizing:diversion:climb:fuel"] = (
            end_of_descent.mass - end_of_diversion_climb.mass
        )
        outputs["data:mission:sizing:diversion:cruise:fuel"] = (
            end_of_diversion_climb.mass - end_of_diversion_cruise.mass
        )
        outputs["data:mission:sizing:diversion:descent:fuel"] = (
            end_of_diversion_cruise.mass - end_of_diversion_descent.mass
        )
        outputs["data:mission:sizing:diversion:climb:distance"] = (
            end_of_diversion_climb.ground_distance - end_of_descent.ground_distance
        )
        outputs["data:mission:sizing:diversion:cruise:distance"] = (
            end_of_diversion_cruise.ground_distance - end_of_diversion_climb.ground_distance
        )
        outputs["data:mission:sizing:diversion:descent:distance"] = (
            end_of_diversion_descent.ground_distance - end_of_diversion_cruise.ground_distance
        )
        outputs["data:mission:sizing:diversion:climb:duration"] = (
            end_of_diversion_climb.time - end_of_descent.time
        )
        outputs["data:mission:sizing:diversion:cruise:duration"] = (
            end_of_diversion_cruise.time - end_of_diversion_climb.time
        )
        outputs["data:mission:sizing:diversion:descent:duration"] = (
            end_of_diversion_descent.time - end_of_diversion_cruise.time
        )

        # Holding ==============================================================

        holding_duration = inputs["data:mission:sizing:holding:duration"]

        holding_calculator = HoldSegment(
            target=FlightPoint(time=holding_duration),
            propulsion=propulsion_model,
            reference_area=reference_area,
            polar=high_speed_polar,
            name="holding",
        )

        holding_flight_points = holding_calculator.compute_from(end_of_diversion_descent)

        end_of_holding = FlightPoint(holding_flight_points.iloc[-1])
        outputs["data:mission:sizing:holding:fuel"] = (
            end_of_diversion_descent.mass - end_of_holding.mass
        )

        # Taxi-in ==============================================================
        taxi_in_duration = inputs["data:mission:sizing:taxi_in:duration"]
        taxi_in_thrust_rate = inputs["data:mission:sizing:taxi_in:thrust_rate"]

        taxi_in_calculator = TaxiSegment(
            target=FlightPoint(time=taxi_in_duration),
            propulsion=propulsion_model,
            thrust_rate=taxi_in_thrust_rate,
            name=FlightPhase.TAXI_IN.value,
        )
        start_of_taxi_in = FlightPoint(end_of_holding)
        start_of_taxi_in.true_airspeed = inputs["data:mission:sizing:taxi_in:speed"]
        taxi_in_flight_points = taxi_in_calculator.compute_from(end_of_holding)

        end_of_taxi_in = FlightPoint(taxi_in_flight_points.iloc[-1])
        outputs["data:mission:sizing:taxi_in:fuel"] = end_of_holding.mass - end_of_taxi_in.mass

        # Final ================================================================
        fuel_route = inputs["data:weight:aircraft:MTOW"] - end_of_descent.mass
        outputs["data:mission:sizing:ZFW"] = end_of_taxi_in.mass - 0.03 * fuel_route
        outputs["data:mission:sizing:fuel"] = (
            inputs["data:weight:aircraft:MTOW"] - outputs["data:mission:sizing:ZFW"]
        )

        self.flight_points = (
            pd.concat(
                [
                    flight_points,
                    diversion_flight_points,
                    holding_flight_points,
                    taxi_in_flight_points,
                ]
            )
            .reset_index(drop=True)
            .applymap(lambda x: np.asscalar(np.asarray(x)))
        )

        if self.options["out_file"]:
            self.flight_points.to_csv(self.options["out_file"])
