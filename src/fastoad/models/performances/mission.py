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
from scipy.constants import g
from scipy.integrate import cumtrapz
from scipy.interpolate import interp1d
import openmdao.api as om

from fastoad.constants import FlightPhase
from fastoad.utils.physics import Atmosphere

CLIMB_MASS_RATIO = 0.97  # = mass at end of climb / mass at start of climb
DESCENT_MASS_RATIO = 0.98  # = mass at end of descent / mass at start of descent
RESERVE_MASS_RATIO = 0.06  # = (weight of fuel reserve)/ZFW
CLIMB_DESCENT_DISTANCE = 500  # in km, distance of climb + descent


class _CruiseTimeSpeedDistance(om.ExplicitComponent):
    """
    Estimation of time, speed and distance vectors for a given cruise distance
    """

    def initialize(self):
        self.options.declare("flight_point_count", 50, types=(int, tuple))

    def setup(self):
        shape = self.options["flight_point_count"]
        self.add_input("data:mission:sizing:cruise:time:initial", np.nan, units="s")
        self.add_input("data:TLAR:cruise_mach", np.nan, shape=shape)
        self.add_input("data:mission:sizing:cruise:altitude", np.nan, shape=shape, units="m")
        self.add_input("data:mission:sizing:cruise:distance:initial", np.nan, units="m")
        self.add_input("data:mission:sizing:cruise:distance:final", np.nan, units="m")

        self.add_output("data:mission:sizing:cruise:time", shape=shape, units="s")
        self.add_output("data:mission:sizing:cruise:time:final", units="s")
        self.add_output("data:mission:sizing:cruise:speed", shape=shape, units="m/s")
        self.add_output("data:mission:sizing:cruise:distance", shape=shape, units="m")

        self.declare_partials("data:mission:sizing:cruise:time", "*", method="fd")
        self.declare_partials("data:mission:sizing:cruise:speed", "*", method="fd")
        self.declare_partials("data:mission:sizing:cruise:time:final", "*", method="fd")
        self.declare_partials("data:mission:sizing:cruise:distance", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        flight_point_count = self.options["flight_point_count"]
        t_0 = inputs["data:mission:sizing:cruise:time:initial"]
        mach = inputs["data:TLAR:cruise_mach"]
        initial_distance = inputs["data:mission:sizing:cruise:distance:initial"]
        final_distance = inputs["data:mission:sizing:cruise:distance:final"]

        total_distance = final_distance - initial_distance

        dx_distance = total_distance / (flight_point_count - 1)

        atmosphere = Atmosphere(
            inputs["data:mission:sizing:cruise:altitude"], altitude_in_feet=False
        )

        speed = atmosphere.speed_of_sound * mach

        distance = np.full((flight_point_count - 1), dx_distance)
        distance = np.concatenate((initial_distance, distance))
        distance = np.cumsum(distance)

        time = distance / speed + t_0

        outputs["data:mission:sizing:cruise:time"] = time
        outputs["data:mission:sizing:cruise:time:final"] = time[-1]
        outputs["data:mission:sizing:cruise:speed"] = speed
        outputs["data:mission:sizing:cruise:distance"] = distance


class _CruiseAltitude(om.ExplicitComponent):
    """
    Estimation of altitude vector
    """

    def initialize(self):

        altitude_ref = 0.3048 * np.linspace(0.0, 60e3, num=1000)

        rho_ref = Atmosphere(altitude_ref, altitude_in_feet=False).density

        self.options.declare("flight_point_count", 50, types=(int, tuple))
        self.options.declare(
            "altitude_interpolation", interp1d(rho_ref, altitude_ref), types=interp1d
        )

    def setup(self):

        shape = self.options["flight_point_count"]
        # TODO: is it necessary to keep initial altitude ?
        self.add_input("data:mission:sizing:cruise:altitude:initial", np.nan, units="m")
        self.add_input("data:mission:sizing:cruise:speed", np.nan, shape=shape, units="m/s")
        self.add_input("data:mission:sizing:cruise:weight", np.nan, shape=shape, units="kg")
        self.add_input("data:aerodynamics:aircraft:cruise:optimal_CL", np.nan)
        self.add_input("data:geometry:aircraft:wing:area", np.nan, units="m**2")

        # TODO: solver needs an initial guess, how to not hard code it ?
        self.add_output(
            "data:mission:sizing:cruise:altitude",
            0.3048 * np.full(shape, 35000),
            shape=shape,
            units="m",
        )

        self.declare_partials("data:mission:sizing:cruise:altitude", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        altitude_interpolation = self.options["altitude_interpolation"]
        initial_altitude = inputs["data:mission:sizing:cruise:altitude:initial"]
        speed = inputs["data:mission:sizing:cruise:speed"]
        weight = inputs["data:mission:sizing:cruise:weight"]
        optimum_cl = inputs["data:aerodynamics:aircraft:cruise:optimal_CL"]
        wing_area = inputs["data:geometry:aircraft:wing:area"]

        rho = 2 * weight * g / optimum_cl / wing_area / speed ** 2

        altitude = altitude_interpolation(rho)
        altitude[0] = initial_altitude

        outputs["data:mission:sizing:cruise:altitude"] = altitude


class _CruiseThrust(om.ExplicitComponent):
    """
    Estimation of thrust vector
    """

    def initialize(self):
        self.options.declare("flight_point_count", 50, types=(int, tuple))

    def setup(self):

        shape = self.options["flight_point_count"]
        self.add_input("data:mission:sizing:cruise:altitude", np.nan, shape=shape, units="m")
        self.add_input("data:TLAR:cruise_mach", np.nan, shape=shape)
        self.add_input("data:mission:sizing:cruise:weight", np.nan, shape=shape, units="kg")
        self.add_input("data:aerodynamics:aircraft:cruise:optimal_CL", np.nan)
        self.add_input("data:aerodynamics:aircraft:cruise:optimal_CD", np.nan)

        self.add_output("data:propulsion:phase", FlightPhase.CRUISE, shape=shape)
        self.add_output("data:propulsion:use_thrust_rate", False, shape=shape)
        self.add_output(
            "data:propulsion:required_thrust_rate", 0.0, shape=shape, lower=0.0, upper=1.0
        )
        self.add_output("data:propulsion:required_thrust", shape=shape, units="N")
        self.add_output("data:propulsion:altitude", shape=shape, units="m")
        self.add_output("data:propulsion:mach", shape=shape)

        self.declare_partials("data:propulsion:phase", "*", method="fd")
        self.declare_partials("data:propulsion:use_thrust_rate", "*", method="fd")
        self.declare_partials("data:propulsion:required_thrust_rate", "*", method="fd")
        self.declare_partials("data:propulsion:required_thrust", "*", method="fd")
        self.declare_partials("data:propulsion:altitude", "*", method="fd")
        self.declare_partials("data:propulsion:mach", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        weight = inputs["data:mission:sizing:cruise:weight"]
        optimum_cl = inputs["data:aerodynamics:aircraft:cruise:optimal_CL"]
        optimum_cd = inputs["data:aerodynamics:aircraft:cruise:optimal_CD"]

        outputs["data:propulsion:altitude"] = inputs["data:mission:sizing:cruise:altitude"]
        outputs["data:propulsion:mach"] = inputs["data:TLAR:cruise_mach"]

        thrust = weight * g / (optimum_cl / optimum_cd)

        outputs["data:propulsion:required_thrust"] = thrust


class _CruiseWeight(om.ExplicitComponent):
    """
    Estimation of weight vector
    """

    def initialize(self):
        self.options.declare("flight_point_count", 50, types=(int, tuple))

    def setup(self):

        shape = self.options["flight_point_count"]
        self.add_input("data:mission:sizing:cruise:consumption:initial", np.nan, units="kg")
        self.add_input("data:mission:sizing:cruise:time", np.nan, shape=shape, units="s")
        self.add_input("data:mission:sizing:cruise:weight:initial", np.nan, units="kg")
        self.add_input("data:propulsion:SFC", np.nan, shape=shape, units="kg/N/s")
        self.add_input("data:propulsion:required_thrust", np.nan, shape=shape)

        self.add_output(
            "data:mission:sizing:cruise:weight",
            np.full(shape, 77037 * CLIMB_MASS_RATIO),
            shape=shape,
            units="kg",
        )
        self.add_output("data:mission:sizing:cruise:consumption", shape=shape, units="kg")

        self.declare_partials("data:mission:sizing:cruise:weight", "*", method="fd")
        self.declare_partials("data:mission:sizing:cruise:consumption", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        initial_consumption = inputs["data:mission:sizing:cruise:consumption:initial"]
        time = inputs["data:mission:sizing:cruise:time"]
        initial_weight = inputs["data:mission:sizing:cruise:weight:initial"]
        sfc = inputs["data:propulsion:SFC"]
        thrust = inputs["data:propulsion:required_thrust"]

        consumption = cumtrapz(sfc * thrust, time)
        consumption = np.concatenate((initial_consumption, consumption))
        weight = initial_weight - consumption

        outputs["data:mission:sizing:cruise:weight"] = weight
        outputs["data:mission:sizing:cruise:consumption"] = consumption


class Cruise(om.Group):
    """
    Complete Cruise
    """

    def initialize(self):
        self.options.declare("flight_point_count", 50, types=(int, tuple))

    def setup(self):

        shape = self.options["flight_point_count"]

        self.add_subsystem(
            "time_speed_distance",
            _CruiseTimeSpeedDistance(flight_point_count=shape),
            promotes=["*"],
        )
        self.add_subsystem("altitude", _CruiseAltitude(flight_point_count=shape), promotes=["*"])
        self.add_subsystem("thrust", _CruiseThrust(flight_point_count=shape), promotes=["*"])
        self.add_subsystem("weight", _CruiseWeight(flight_point_count=shape), promotes=["*"])

        self.nonlinear_solver = om.NonlinearBlockGS()
        self.nonlinear_solver.options["iprint"] = 2
        self.nonlinear_solver.options["maxiter"] = 100
        self.linear_solver = om.LinearBlockGS()
