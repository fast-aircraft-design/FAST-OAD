"""Implementation of the Breguet Formula."""
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
from fastoad.base.flight_point import FlightPoint
from fastoad.constants import EngineSetting
from fastoad.models.propulsion import IPropulsion
from fastoad.utils.physics import AtmosphereSI
from scipy.constants import g


class Breguet:
    def __init__(
        self,
        propulsion: IPropulsion,
        lift_drag_ratio: float,
        cruise_mach: float,
        cruise_altitude: float,
        climb_mass_ratio: float = 0.97,
        descent_mass_ratio: float = 0.98,
        reserve_mass_ratio: float = 0.06,
        climb_descent_distance: float = 500.0e3,
    ):
        """
        Class for computing consumed fuel for a simple flight.

        Fuel consumption during cruise is computing with Breguet formula. Climb and descent
        phases are roughly estimated using provided mass ratios.

        :param propulsion: the propulsion model for computation of consumption
        :param lift_drag_ratio: the lift/drag ratio that will be used during cruise
        :param cruise_mach: Mach number in cruise
        :param cruise_altitude: in meters. Altitude in cruise
        :param climb_mass_ratio: (mass at end of climb ) / (mass at start of climb)
        :param descent_mass_ratio:  (mass at end of descent ) / (mass at start of descent)
        :param reserve_mass_ratio:  (mass of reserve fuel) / ZFW
        :param climb_descent_distance:  in meters. Sum of ground distances during climb and descent
        """
        self.cruise_altitude = cruise_altitude
        self.cruise_mach = cruise_mach
        self.lift_drag_ratio = lift_drag_ratio
        self.propulsion = propulsion
        self.climb_mass_ratio = climb_mass_ratio
        self.descent_mass_ratio = descent_mass_ratio
        self.reserve_mass_ratio = reserve_mass_ratio
        self.climb_descent_distance = climb_descent_distance
        self.climb_distance = self.descent_distance = climb_descent_distance / 2.0

        self.thrust = None
        self.thrust_rate = None
        self.sfc = None
        self.mission_fuel = None
        self.zfw = None
        self.flight_fuel = None
        self.climb_fuel = None
        self.cruise_fuel = None
        self.descent_fuel = None
        self.reserve_fuel = None
        self.cruise_distance = None

    def compute(self, takeoff_weight, flight_range):
        """
        Computes the flight consumption.

        Results are provided as class attributes.

        :param takeoff_weight:
        :param flight_range:
        """
        initial_cruise_mass = takeoff_weight * self.climb_mass_ratio
        self.cruise_distance = flight_range - self.climb_descent_distance
        cruise_mass_ratio = self.compute_cruise_mass_ratio(
            initial_cruise_mass, self.cruise_distance
        )
        flight_mass_ratio = cruise_mass_ratio * self.climb_mass_ratio * self.descent_mass_ratio

        self.zfw = takeoff_weight * flight_mass_ratio / (1.0 + self.reserve_mass_ratio)
        self.mission_fuel = takeoff_weight - self.zfw
        self.flight_fuel = takeoff_weight * (1.0 - flight_mass_ratio)
        self.climb_fuel = takeoff_weight * (1.0 - self.climb_mass_ratio)
        self.cruise_fuel = takeoff_weight * self.climb_mass_ratio * (1.0 - cruise_mass_ratio)
        self.descent_fuel = (
            takeoff_weight
            * self.climb_mass_ratio
            * cruise_mass_ratio
            * (1.0 - self.descent_mass_ratio)
        )
        self.reserve_fuel = self.zfw * self.reserve_mass_ratio

    def compute_cruise_mass_ratio(self, initial_cruise_mass, cruise_distance):
        """

        :param initial_cruise_mass:
        :param cruise_distance:
        :return: (mass at end of cruise) / (mass at start of cruise)
        """
        self.thrust = initial_cruise_mass / self.lift_drag_ratio * g
        flight_point = FlightPoint(
            mach=self.cruise_mach,
            altitude=self.cruise_altitude,
            engine_setting=EngineSetting.CRUISE,
            thrust=self.thrust,
        )
        self.propulsion.compute_flight_points(flight_point)
        self.sfc = flight_point.sfc
        self.thrust_rate = flight_point.thrust_rate

        atmosphere = AtmosphereSI(self.cruise_altitude)
        cruise_speed = atmosphere.speed_of_sound * self.cruise_mach
        range_factor = cruise_speed * self.lift_drag_ratio / g / self.sfc
        return 1.0 / np.exp(cruise_distance / range_factor)
