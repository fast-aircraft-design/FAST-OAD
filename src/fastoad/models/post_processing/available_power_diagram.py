"""Computation of the Available-power diagram."""
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
from stdatm import Atmosphere
from fastoad.module_management._bundle_loader import BundleLoader
from fastoad.constants import RangeCategory
from fastoad.constants import EngineSetting
from fastoad.model_base import FlightPoint
from scipy.optimize import fsolve
from fastoad.module_management._plugins import FastoadLoader
from scipy.interpolate import interp1d

FastoadLoader()

AVAILABLE_POWER_SHAPE = 150  # Number of points used for the computation of the graph


class AvailablepowerDiagram(om.ExplicitComponent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._engine_wrapper = None

    def initialize(self):

        self.options.declare("propulsion_id", default="", types=str)

    def setup(self):

        self.add_input("data:geometry:wing:area", units="m**2", val=np.nan)
        self.add_input("data:geometry:wing:aspect_ratio", val=np.nan)
        self.add_input("data:weight:aircraft:MTOW", units="kg", val=np.nan)
        self.add_input("data:weight:aircraft:MZFW", units="kg", val=np.nan)
        self.add_input("data:aerodynamics:aircraft:cruise:CL", val=np.nan, shape=150)
        self.add_input("data:aerodynamics:aircraft:cruise:CD", val=np.nan, shape=150)
        self.add_input("data:aerodynamics:aircraft:cruise:oswald_coefficient", val=np.nan)
        self.add_input("data:aerodynamics:aircraft:landing:CL_max_clean", val=np.nan)
        self.add_input("data:performance:ceiling:MTOW", val=np.nan)
        self.add_input("data:performance:ceiling:MZFW", val=np.nan)
        self.add_input("data:TLAR:cruise_mach", val=np.nan)
        self.add_input("data:TLAR:range", val=np.nan)
        self.add_input("data:mission:sizing:main_route:cruise:altitude", val=np.nan)


        self._engine_wrapper = BundleLoader().instantiate_component(self.options["propulsion_id"])
        self._engine_wrapper.setup(self)

        self.add_output(
            "data:performance:available_power_diagram:sea_level:power_available",
            shape=AVAILABLE_POWER_SHAPE,
            units="N",
        )
        self.add_output(
            "data:performance:available_power_diagram:sea_level:power_max",
            shape=AVAILABLE_POWER_SHAPE,
            units="N",
        )
        self.add_output(
            "data:performance:available_power_diagram:sea_level:speed_vector",
            shape=AVAILABLE_POWER_SHAPE,
            units="m/s",
        )
        self.add_output(
            "data:performance:available_power_diagram:cruise_altitude:speed_vector",
            shape=AVAILABLE_POWER_SHAPE,
            units="m/s",
        )
        self.add_output(
            "data:performance:available_power_diagram:cruise_altitude:power_available",
            shape=AVAILABLE_POWER_SHAPE,
            units="N",
        )
        self.add_output(
            "data:performance:available_power_diagram:cruise_altitude:power_max",
            shape=AVAILABLE_POWER_SHAPE,
            units="N",
        )

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):

        propulsion_model = self._engine_wrapper.get_model(inputs)

        tlar_range = inputs["data:TLAR:range"]
        wing_area = float(inputs["data:geometry:wing:area"])
        aspect_ratio = float(inputs["data:geometry:wing:aspect_ratio"])
        mtow = inputs["data:weight:aircraft:MTOW"]
        mzfw = inputs["data:weight:aircraft:MZFW"]
        cl_vector_input = inputs["data:aerodynamics:aircraft:cruise:CL"]
        cd_vector_input = inputs["data:aerodynamics:aircraft:cruise:CD"]
        oswald_coefficient = inputs["data:aerodynamics:aircraft:cruise:oswald_coefficient"]
        cl_max_clean = inputs["data:aerodynamics:aircraft:landing:CL_max_clean"]
        cruise_mach = float(inputs["data:TLAR:cruise_mach"])
        maximum_engine_mach = inputs["data:propulsion:rubber_engine:maximum_mach"]
        thrust_max = 2*inputs["data:propulsion:MTO_thrust"]
        cruise_altitude = inputs["data:mission:sizing:main_route:cruise:altitude"]

        k = 1/(np.pi*aspect_ratio*oswald_coefficient)
        g = 9.80665  # m/s^2


        # Compute the thrusts at sea level
        atm = Atmosphere(altitude=0, altitude_in_feet=False)
        rho = atm.density
        v_min = np.sqrt(
            2 * mtow * g / (rho * wing_area * cl_max_clean)
        )  # Minimal speed of the aircraft m/s
        v_vector_sea = np.linspace(v_min, maximum_engine_mach*atm.speed_of_sound, AVAILABLE_POWER_SHAPE) # m/s
        atm.true_airspeed = v_vector_sea

        cl_vector = mtow*g/(0.5*rho*v_vector_sea*v_vector_sea*wing_area)
        cd_vector = cd_vector =np.interp(cl_vector, cl_vector_input, cd_vector_input)
        power_available_sea = 0.5*rho*v_vector_sea*v_vector_sea*v_vector_sea*wing_area*cd_vector

        flight_point = FlightPoint(
            mach=atm.mach,
            altitude=atm.get_altitude(altitude_in_feet=False),
            engine_setting=EngineSetting.CLIMB,
            thrust_is_regulated=False,
            thrust_rate=1.0,
        )
        propulsion_model.compute_flight_points(flight_point)
        power_max_sea = flight_point.thrust*v_vector_sea


        # Compute the thrusts at cruise altitude
        atm = Atmosphere(altitude=cruise_altitude, altitude_in_feet=False)
        rho = atm.density
        v_min = np.sqrt(
            2 * mtow * g / (rho * wing_area * cl_max_clean)
        )  # Minimal speed of the aircraft m/s
        v_vector_cruise = np.linspace(v_min, maximum_engine_mach * atm.speed_of_sound, AVAILABLE_POWER_SHAPE)  # m/s
        atm.true_airspeed = v_vector_cruise

        cl_vector = mtow * g / (0.5 * rho * v_vector_cruise * v_vector_cruise * wing_area)
        cd_vector =np.interp(cl_vector, cl_vector_input, cd_vector_input)
        power_available_cruise = 0.5 * rho * v_vector_cruise * v_vector_cruise * v_vector_cruise * wing_area * cd_vector

        flight_point = FlightPoint(
            mach=atm.mach,
            altitude=atm.get_altitude(altitude_in_feet=False),
            engine_setting=EngineSetting.CLIMB,
            thrust_is_regulated=False,
            thrust_rate=1.0,
        )
        propulsion_model.compute_flight_points(flight_point)
        power_max_cruise = flight_point.thrust*v_vector_cruise

        # Put the resultst in the output file
        outputs["data:performance:available_power_diagram:sea_level:power_available"] = power_available_sea/1000000
        outputs["data:performance:available_power_diagram:sea_level:power_max"] = power_max_sea/1000000
        outputs["data:performance:available_power_diagram:cruise_altitude:power_available"] = power_available_cruise/1000000
        outputs["data:performance:available_power_diagram:cruise_altitude:power_max"] = power_max_cruise/1000000
        outputs["data:performance:available_power_diagram:sea_level:speed_vector"] = v_vector_sea
        outputs["data:performance:available_power_diagram:cruise_altitude:speed_vector"] = v_vector_cruise
