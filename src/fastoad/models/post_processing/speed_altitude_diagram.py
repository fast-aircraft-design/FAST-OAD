"""Computation of the V-a diagram."""
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

# noinspection PyProtectedMember
from fastoad.module_management._bundle_loader import BundleLoader
from fastoad.constants import EngineSetting
from fastoad.model_base import FlightPoint
from scipy.optimize import fsolve


SPEED_ALTITUDE_SHAPE = 100


class SpeedAltitudeDiagram(om.ExplicitComponent):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._engine_wrapper = None

    def initialize(self):

        self.options.declare("propulsion_id", default="", types=str)

    def setup(self):

        self.add_input("data:geometry:wing:area", units="m**2", val=np.nan)
        self.add_input("data:weight:aircraft:MTOW", units="kg", val=np.nan)
        self.add_input("data:aerodynamics:aircraft:cruise:CL", val=np.nan, shape=150)
        self.add_input("data:aerodynamics:aircraft:cruise:CD", val=np.nan, shape=150)
        self.add_input("data:aerodynamics:aircraft:landing:CD", val=np.nan, shape=150)
        self._engine_wrapper = BundleLoader().instantiate_component(self.options["propulsion_id"])
        self._engine_wrapper.setup(self)

        self.add_output(
            "data:performance:speed_altitude_diagram:v_stall",
            shape=SPEED_ALTITUDE_SHAPE,
            units="m/s",
        )
        self.add_output(
            "data:performance:speed_altitude_diagram:v_max",
            shape=SPEED_ALTITUDE_SHAPE,
            units="m/s",
        )

    @staticmethod
    def func(v, alti, mtow, g, rho, wing_area, cl_vector_input, cd_vector_input, propulsion_model):
        atm = Atmosphere(altitude=alti, altitude_in_feet=True)
        atm.true_airspeed = v
        rho = atm.density

        # Compute thrust
        flight_point = FlightPoint(
            mach=atm.mach,
            altitude=atm.get_altitude(altitude_in_feet=True),
            engine_setting=EngineSetting.CLIMB,
            thrust_is_regulated=False,
            # Si je mets false, cela veut dire que je fixe la manette des gaz sans connaitre la poussée en N. Si je mets True, je pose la poussée en N et je demande qu'il calcule la position de la manette des gaz.
            thrust_rate=1.0,
        )
        propulsion_model.compute_flight_points(flight_point)
        thrust = flight_point.thrust
        cl = 2*mtow*g/(rho*wing_area*v*v)
        cd_interpolated = np.interp(cl, cl_vector_input, cd_vector_input)
        drag_interpolated = cd_interpolated * 0.5 * rho * v * v * wing_area
        return drag_interpolated - thrust

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):

        propulsion_model = self._engine_wrapper.get_model(inputs)

        wing_area = inputs["data:geometry:wing:area"]
        mtow = inputs["data:weight:aircraft:MTOW"]
        cl_vector_input = inputs["data:aerodynamics:aircraft:cruise:CL"]
        cd_vector_input = inputs["data:aerodynamics:aircraft:cruise:CD"]
        g = 9.80665 #m/s^2
        altitude_vector = np.arange(0, 20000, 100)
        speed_final = np.zeros(altitude_vector.size)

        #atm = Atmosphere(altitude=10000.0, altitude_in_feet=True)
        #atm.true_airspeed = 250
        #rho = atm.density

        for i in range(len(altitude_vector)):
            atm = Atmosphere(altitude=altitude_vector[i], altitude_in_feet=True)
            atm.true_airspeed = 250
            rho = atm.density

            speed_final[i] = fsolve(self.func, 220, args=(altitude_vector[i], mtow, g, rho, wing_area, cl_vector_input, cd_vector_input, propulsion_model))


        print(speed_final)
        print(altitude_vector)
        v_stall = np.ones(SPEED_ALTITUDE_SHAPE) / wing_area
        outputs["data:performance:speed_altitude_diagram:v_stall"] = v_stall
