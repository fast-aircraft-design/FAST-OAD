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
from fastoad.module_management._plugins import FastoadLoader

FastoadLoader()


class ThrustDiagram(om.ExplicitComponent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._engine_wrapper = None

    def initialize(self):

        self.options.declare("propulsion_id", default="", types=str)

    def setup(self):

        self.add_input("data:TLAR:cruise_mach", val=np.nan)

        self._engine_wrapper = BundleLoader().instantiate_component(self.options["propulsion_id"])
        self._engine_wrapper.setup(self)

        self.add_output(
            "data:performance:thrust_diagram:iso_rating_thrust:ratio_F_F0", shape=(5, 50)
        )
        self.add_output(
            "data:performance:thrust_diagram:iso_altitude_thrust:ratio_F_F0", shape=(4, 50)
        )
        self.add_output("data:performance:thrust_diagram:iso_rating_consumption:SFC", shape=(5, 50))
        self.add_output(
            "data:performance:thrust_diagram:iso_altitude_consumption:SFC", shape=(4, 50)
        )

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):

        propulsion_model = self._engine_wrapper.get_model(inputs)

        cruise_mach = inputs["data:TLAR:cruise_mach"]
        maximum_engine_mach = inputs["data:propulsion:rubber_engine:maximum_mach"]
        initial_thrust = 2 * inputs["data:propulsion:MTO_thrust"]  # because 2 engines
        diving_mach = 0.07 + cruise_mach

        maximum_mach = np.maximum(cruise_mach, np.maximum(diving_mach, maximum_engine_mach))
        mach_vector = np.linspace(0, maximum_mach, 50)
        thrust_rate_vector = np.array(
            [1, 0.98, 0.93, 0.35]
        )  # vector to use for the different regimes of the engine

        altitude_vector = np.array([0, 10000, 20000, 30000, 40000])
        thrust_iso_rating_thrust = np.zeros((5, 50))
        thrust_iso_altitude_thrust = np.zeros((4, 50))
        sfc_iso_rating_consumption = np.zeros((5, 50))
        sfc_iso_altitude_consumption = np.zeros((4, 50))

        for i in range(len(altitude_vector)):

            if (
                altitude_vector[i] == 0
            ):  # the case for iso altitude thrust and iso altitude consumption at 0 ft

                atm = Atmosphere(altitude=0, altitude_in_feet=True)
                for j in range(len(thrust_rate_vector)):

                    flight_point = FlightPoint(
                        mach=mach_vector,
                        altitude=atm.get_altitude(altitude_in_feet=False),
                        engine_setting=EngineSetting.CLIMB,
                        thrust_is_regulated=False,
                        thrust_rate=thrust_rate_vector[j],
                    )
                    propulsion_model.compute_flight_points(flight_point)
                    thrust_iso_altitude_thrust[j] = np.transpose(flight_point.thrust)
                    sfc_iso_altitude_consumption[j] = np.transpose(flight_point.sfc)

            atm = Atmosphere(altitude=altitude_vector[i], altitude_in_feet=True)
            flight_point = FlightPoint(
                mach=mach_vector,
                altitude=atm.get_altitude(altitude_in_feet=False),
                engine_setting=EngineSetting.CLIMB,
                thrust_is_regulated=False,
                thrust_rate=1.0,
            )
            propulsion_model.compute_flight_points(flight_point)
            thrust_iso_rating_thrust[i] = np.transpose(flight_point.thrust)
            sfc_iso_rating_consumption[i] = np.transpose(flight_point.sfc)

        ratio_iso_rating_thrust = thrust_iso_rating_thrust / initial_thrust
        ratio_iso_altitude_thrust = thrust_iso_altitude_thrust / initial_thrust

        outputs[
            "data:performance:thrust_diagram:iso_rating_thrust:ratio_F_F0"
        ] = ratio_iso_rating_thrust
        outputs[
            "data:performance:thrust_diagram:iso_altitude_thrust:ratio_F_F0"
        ] = ratio_iso_altitude_thrust
        outputs[
            "data:performance:thrust_diagram:iso_rating_consumption:SFC"
        ] = sfc_iso_rating_consumption
        outputs[
            "data:performance:thrust_diagram:iso_altitude_consumption:SFC"
        ] = sfc_iso_altitude_consumption
