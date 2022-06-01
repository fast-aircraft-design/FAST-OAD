"""Computation of the Altitude-Speed diagram."""
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
from .ceiling_computation import CeilingComputation
from .ceiling_computation import thrust_minus_drag
from fastoad.constants import EngineSetting
from fastoad.model_base import FlightPoint
from scipy.optimize import fsolve
import plotly.graph_objects as go
from fastoad.module_management._plugins import FastoadLoader

FastoadLoader()

SPEED_ALTITUDE_SHAPE = 45  # Numbre of points used for the computation of the graph between the sea-level and the ceiling level
EXTRA_ALTITUDE_SHAPE = 6  # Number of points used for the computation of the curves curves between the "MTOW ceiling" and the "MZFW ceiling"


class SpeedAltitudeDiagram(om.ExplicitComponent):
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
            "data:performance:speed_altitude_diagram:MTOW:v_min",
            shape=SPEED_ALTITUDE_SHAPE,
            units="m/s",
        )
        self.add_output(
            "data:performance:speed_altitude_diagram:MTOW:v_max",
            shape=SPEED_ALTITUDE_SHAPE,
            units="m/s",
        )
        self.add_output(
            "data:performance:speed_altitude_diagram:MTOW:v_computed",
            shape=SPEED_ALTITUDE_SHAPE,
            units="m/s",
        )
        self.add_output(
            "data:performance:speed_altitude_diagram:MTOW:v_dive",
            shape=SPEED_ALTITUDE_SHAPE,
            units="m/s",
        )
        self.add_output(
            "data:performance:speed_altitude_diagram:MTOW:v_engine",
            shape=SPEED_ALTITUDE_SHAPE,
            units="m/s",
        )
        self.add_output(
            "data:performance:speed_altitude_diagram:MZFW:v_min",
            shape=SPEED_ALTITUDE_SHAPE + EXTRA_ALTITUDE_SHAPE,
            units="m/s",
        )
        self.add_output(
            "data:performance:speed_altitude_diagram:MZFW:v_max",
            shape=SPEED_ALTITUDE_SHAPE + EXTRA_ALTITUDE_SHAPE,
            units="m/s",
        )
        self.add_output(
            "data:performance:speed_altitude_diagram:MZFW:v_computed",
            shape=SPEED_ALTITUDE_SHAPE + EXTRA_ALTITUDE_SHAPE,
            units="m/s",
        )
        self.add_output(
            "data:performance:speed_altitude_diagram:MZFW:v_dive",
            shape=SPEED_ALTITUDE_SHAPE + EXTRA_ALTITUDE_SHAPE,
            units="m/s",
        )
        self.add_output(
            "data:performance:speed_altitude_diagram:MZFW:v_engine",
            shape=SPEED_ALTITUDE_SHAPE + EXTRA_ALTITUDE_SHAPE,
            units="m/s",
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

        g = 9.80665  # m/s^2

        # Altitude vectors
        altitude_vector_mtow = np.linspace(0, ceiling_mtow, SPEED_ALTITUDE_SHAPE)  # feet
        altitude_extra = np.linspace(ceiling_mtow, ceiling_mzfw, EXTRA_ALTITUDE_SHAPE)
        altitude_vector_mzfw = np.append(altitude_vector_mtow, altitude_extra)  # feet

        # Speed vectors for MTOW
        v_max_mtow = np.zeros(altitude_vector_mtow.size)
        v_min_mtow = np.zeros(altitude_vector_mtow.size)
        v_computed_vector_mtow = np.zeros(altitude_vector_mtow.size)
        v_dive_vector_mtow = np.zeros(altitude_vector_mtow.size)
        v_engine_vector_mtow = np.zeros(altitude_vector_mtow.size)

        # Speed vectors for MZFW
        v_max_mzfw = np.zeros(altitude_vector_mzfw.size)
        v_min_mzfw = np.zeros(altitude_vector_mzfw.size)
        v_computed_vector_mzfw = np.zeros(altitude_vector_mzfw.size)

        # Diving speed vector and engine speed vector for the curves between the "MTOW ceiling" and the "MZFW ceiling"
        v_dive_extra = np.zeros(altitude_extra.size)
        v_engine_extra = np.zeros(altitude_extra.size)

        # Compute the diagram for MTOW
        for i in range(len(altitude_vector_mtow)):
            atm_mtow = Atmosphere(altitude=altitude_vector_mtow[i], altitude_in_feet=True)
            rho_mtow = atm_mtow.density

            # Compute the minimum and the maximum speed
            # Utilisation of the function fsolve and a function defined in the class "ceiling_computation"
            v_min_mtow[i] = np.sqrt(
                2 * mtow * g / (rho_mtow * wing_area * cl_max_clean)
            )  # Minimal speed of the aircraft
            v_max_computed_mtow = fsolve(
                thrust_minus_drag,
                500,
                args=(
                    altitude_vector_mtow[i],
                    mtow,
                    wing_area,
                    cl_vector_input,
                    cd_vector_input,
                    propulsion_model,
                ),
            )[
                0
            ]  # Maximum speed of the aircraft computed with the Cl and Cd coefficient
            v_computed_vector_mtow[i] = v_max_computed_mtow

            # Compute the maximum speed of the aircraft (diving speed)
            v_dive_mtow = (0.07 + cruise_mach) * atm_mtow.speed_of_sound
            v_dive_vector_mtow[i] = v_dive_mtow[0]

            # Compute the maximum engine supportable-speed
            v_engine_mtow = maximum_engine_mach * atm_mtow.speed_of_sound
            v_engine_vector_mtow[i] = v_engine_mtow[0]

            # The maximum speed will be the most restrictive one between the three speeds computed before
            v_max_mtow[i] = np.minimum(np.minimum(v_dive_mtow, v_engine_mtow), v_max_computed_mtow)

        # Compute the diagram for MZFW
        for j in range(len(altitude_vector_mzfw)):
            atm_mzfw = Atmosphere(altitude=altitude_vector_mzfw[j], altitude_in_feet=True)
            rho_mzfw = atm_mzfw.density

            # Compute the minimum and the maximum speed
            # Utilisation of the function fsolve and a function defined in the class "ceiling_computation"
            v_min_mzfw[j] = np.sqrt(
                2 * mzfw * g / (rho_mzfw * wing_area * cl_max_clean)
            )  # Minimal speed of the aircraft
            v_max_computed_mzfw = fsolve(
                thrust_minus_drag,
                500,
                args=(
                    altitude_vector_mzfw[j],
                    mzfw,
                    wing_area,
                    cl_vector_input,
                    cd_vector_input,
                    propulsion_model,
                ),
            )[
                0
            ]  # Maximum speed of the aircraft computed with the Cl and Cd coefficient
            v_computed_vector_mzfw[j] = v_max_computed_mzfw

            # Compute the maximum speed of the aircraft (diving speed)
            v_dive_mzfw = (0.07 + cruise_mach) * atm_mzfw.speed_of_sound

            # Compute the maximum engine supportable-speed
            v_engine_mzfw = maximum_engine_mach * atm_mzfw.speed_of_sound

            # The maximum speed will be the most restrictive one between the three speeds computed before
            v_max_mzfw[j] = np.minimum(np.minimum(v_dive_mzfw, v_engine_mzfw), v_max_computed_mzfw)

        # Compute the diagram for the extra vector v_dive and v_engine between "MTOW ceiling" and "MZFW ceiling"
        for k in range(len(altitude_extra)):
            atm_extra = Atmosphere(altitude=altitude_extra[k], altitude_in_feet=True)

            # Compute the maximum speed of the aircraft (diving speed)
            v_dive_extra[k] = (0.07 + cruise_mach) * atm_extra.speed_of_sound

            # Compute the maximum engine supportable-speed
            v_engine_extra[k] = maximum_engine_mach * atm_extra.speed_of_sound

        # Compute the vector v_dive and v_engine for the MZFW
        v_dive_vector_mzfw = np.append(v_dive_vector_mtow, v_dive_extra)
        v_engine_vector_mzfw = np.append(v_engine_vector_mtow, v_engine_extra)

        # Put the resultst in the output file
        outputs["data:performance:speed_altitude_diagram:MTOW:v_min"] = v_min_mtow
        outputs["data:performance:speed_altitude_diagram:MTOW:v_max"] = v_max_mtow
        outputs["data:performance:speed_altitude_diagram:MTOW:v_computed"] = v_computed_vector_mtow
        outputs["data:performance:speed_altitude_diagram:MTOW:v_dive"] = v_dive_vector_mtow
        outputs["data:performance:speed_altitude_diagram:MTOW:v_engine"] = v_engine_vector_mtow
        outputs["data:performance:speed_altitude_diagram:MZFW:v_min"] = v_min_mzfw
        outputs["data:performance:speed_altitude_diagram:MZFW:v_max"] = v_max_mzfw
        outputs["data:performance:speed_altitude_diagram:MZFW:v_computed"] = v_computed_vector_mzfw
        outputs["data:performance:speed_altitude_diagram:MZFW:v_dive"] = v_dive_vector_mzfw
        outputs["data:performance:speed_altitude_diagram:MZFW:v_engine"] = v_engine_vector_mzfw
