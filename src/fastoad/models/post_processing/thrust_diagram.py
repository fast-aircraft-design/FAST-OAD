"""Computation of the Thrust diagram."""
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
from fastoad.model_base import FlightPoint
from fastoad.constants import EngineSetting
from .ceiling_computation import thrust_minus_drag
from scipy.optimize import fsolve
from fastoad.module_management._plugins import FastoadLoader
from matplotlib import pyplot as plt

FastoadLoader()

class ThrustDiagram(om.ExplicitComponent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._engine_wrapper = None

    def initialize(self):

        self.options.declare("propulsion_id", default="", types=str)

    def setup(self):

        self.add_input("data:geometry:wing:area", units="m**2", val=np.nan)
        self.add_input("data:weight:aircraft:MTOW", units="kg", val=np.nan)
        self.add_input("data:weight:aircraft:MZFW", units="kg", val=np.nan)
        self.add_input("data:aerodynamics:aircraft:cruise:CL", val=np.nan, shape=150)
        self.add_input("data:aerodynamics:aircraft:cruise:CD", val=np.nan, shape=150)
        self.add_input("data:aerodynamics:aircraft:landing:CL_max_clean", val=np.nan)
        self.add_input("data:performance:ceiling:MTOW", val=np.nan)
        self.add_input("data:performance:ceiling:MZFW", val=np.nan)
        self.add_input("data:TLAR:cruise_mach", val=np.nan)

        self._engine_wrapper = BundleLoader().instantiate_component(self.options["propulsion_id"])
        self._engine_wrapper.setup(self)

        self.add_output(
            "data:performance:thrust_diagram:iso_rating_thrust:ratio_F_F0",
            shape=(5,50)
        )
        self.add_output(
            "data:performance:thrust_diagram:iso_rating_consumption:SFC",
            shape=(5, 50)
        )

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):

        propulsion_model = self._engine_wrapper.get_model(inputs)

        wing_area = inputs["data:geometry:wing:area"]
        mtow = inputs["data:weight:aircraft:MTOW"]
        mzfw = inputs["data:weight:aircraft:MZFW"]
        cl_vector_input = inputs["data:aerodynamics:aircraft:cruise:CL"]
        cd_vector_input = inputs["data:aerodynamics:aircraft:cruise:CD"]
        cl_max_clean = inputs["data:aerodynamics:aircraft:landing:CL_max_clean"]
        cruise_mach = inputs["data:TLAR:cruise_mach"]
        maximum_engine_mach = inputs["data:propulsion:rubber_engine:maximum_mach"]
        ceiling_mtow = float(inputs["data:performance:ceiling:MTOW"])
        ceiling_mzfw = float(inputs["data:performance:ceiling:MZFW"])
        initial_thrust = 2*inputs["data:propulsion:MTO_thrust"]
        diving_mach = 0.07 + cruise_mach

        g = 9.80665  # m/s^2

        # iso rating thrust
        altitude_vector = np.array([0, 10000, 20000, 30000, 40000])
        maximum_mach = np.maximum(cruise_mach, np.maximum(diving_mach, maximum_engine_mach))
        mach_vector = np.linspace(0, maximum_mach, 50)
        thrust_available = np.zeros((5, 50))
        specific_consumption_in_altitude = np.zeros((5, 50))

        for i in range(len(altitude_vector)):
            atm = Atmosphere(altitude=altitude_vector[i], altitude_in_feet=True)

            flight_point = FlightPoint(
                mach=mach_vector,
                altitude=atm.get_altitude(altitude_in_feet=False),
                engine_setting=EngineSetting.CLIMB,
                thrust_is_regulated=False,
                thrust_rate=1.0,
            )
            propulsion_model.compute_flight_points(flight_point)
            thrust_available[i] = np.transpose(flight_point.thrust)
            specific_consumption_in_altitude[i] = np.transpose(flight_point.sfc)

        ratio_thrust = thrust_available / initial_thrust

        outputs["data:performance:thrust_diagram:iso_rating_thrust:ratio_F_F0"] = ratio_thrust
        outputs["data:performance:thrust_diagram:iso_rating_consumption:SFC"] = specific_consumption_in_altitude

# v_max_computed_mtow = fsolve(
#    thrust_minus_drag,
#    500,
#    args=(
#        altitude_vector_mtow[i],
#        mtow,
#        wing_area,
#        cl_vector_input,
#        cd_vector_input,
#        propulsion_model,
#    ),
# )[
#    0
# ]  # Maximum speed of the aircraft computed with the Cl and Cd coefficient
#
## Compute the maximum speed of the aircraft (diving speed)
# v_dive_mtow = (0.07 + cruise_mach) * atm_mtow.speed_of_sound
#
## Compute the maximum engine supportable-speed
# v_engine_mtow = maximum_engine_mach * atm_mtow.speed_of_sound