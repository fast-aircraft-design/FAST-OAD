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
from .ceiling_computation import thrust_minus_drag
from scipy.optimize import fsolve
from fastoad.module_management._plugins import FastoadLoader

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
            "data:performance:speed_altitude_diagram:MZFW:v_engine",
            shape=1,
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
        #altitude_vector_mtow = np.linspace(0, ceiling_mtow, SPEED_ALTITUDE_SHAPE)  # feet

        atm_mtow = Atmosphere(altitude=20000, altitude_in_feet=True)
        rho_mtow = atm_mtow.density

        #v_max_computed_mtow = fsolve(
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
        #)[
        #    0
        #]  # Maximum speed of the aircraft computed with the Cl and Cd coefficient
        #
        ## Compute the maximum speed of the aircraft (diving speed)
        #v_dive_mtow = (0.07 + cruise_mach) * atm_mtow.speed_of_sound
        #
        ## Compute the maximum engine supportable-speed
        #v_engine_mtow = maximum_engine_mach * atm_mtow.speed_of_sound

        outputs["data:performance:speed_altitude_diagram:MZFW:v_engine"] = 3