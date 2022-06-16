"""Computation of the V-n diagram."""
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
from fastoad.constants import EngineSetting
from fastoad.model_base import FlightPoint
from fastoad.module_management._plugins import FastoadLoader
from scipy.interpolate import interp1d

FastoadLoader()

V_n_SHAPE = 150  # Number of points used for the computation of the graph


class VnDiagram(om.ExplicitComponent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._engine_wrapper = None

    def initialize(self):

        self.options.declare("propulsion_id", default="", types=str)

    def setup(self):

        self.add_input("data:geometry:wing:area", units="m**2", val=np.nan)
        self.add_input("data:geometry:wing:aspect_ratio", val=np.nan)
        self.add_input("data:geometry:wing:MAC:length", val=np.nan)
        self.add_input("data:weight:aircraft:MTOW", units="kg", val=np.nan)
        self.add_input("data:weight:aircraft:MZFW", units="kg", val=np.nan)
        self.add_input("data:aerodynamics:aircraft:cruise:CL", val=np.nan, shape=150)
        self.add_input("data:aerodynamics:aircraft:cruise:CD", val=np.nan, shape=150)
        self.add_input("data:aerodynamics:aircraft:cruise:oswald_coefficient", val=np.nan)
        self.add_input("data:aerodynamics:aircraft:cruise:CL_alpha", val=np.nan)
        self.add_input("data:aerodynamics:aircraft:landing:CL_max_clean", val=np.nan)
        self.add_input("data:performance:ceiling:MTOW", val=np.nan)
        self.add_input("data:performance:ceiling:MZFW", val=np.nan)
        self.add_input("data:TLAR:cruise_mach", val=np.nan)
        self.add_input("data:TLAR:range", val=np.nan)
        self.add_input("data:mission:sizing:main_route:cruise:altitude", val=np.nan)

        self._engine_wrapper = BundleLoader().instantiate_component(self.options["propulsion_id"])
        self._engine_wrapper.setup(self)

        self.add_output(
            "data:performance:V-n_diagram:speed_vector",
            shape=V_n_SHAPE,
            units="m/s",
        )
        self.add_output(
            "data:performance:V-n_diagram:v_stall",
            shape=1,
            units="m/s",
        )
        self.add_output(
            "data:performance:V-n_diagram:v_manoeuvre",
            shape=1,
            units="m/s",
        )
        self.add_output(
            "data:performance:V-n_diagram:v_cruising",
            shape=1,
            units="m/s",
        )
        self.add_output(
            "data:performance:V-n_diagram:v_dive",
            shape=1,
            units="m/s",
        )

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):

        propulsion_model = self._engine_wrapper.get_model(inputs)

        wing_area = float(inputs["data:geometry:wing:area"])
        mtow = inputs["data:weight:aircraft:MTOW"]
        mzfw = inputs["data:weight:aircraft:MZFW"]
        cl_vector_input = inputs["data:aerodynamics:aircraft:cruise:CL"]
        cd_vector_input = inputs["data:aerodynamics:aircraft:cruise:CD"]
        mac = inputs["data:geometry:wing:MAC:length"]  # length of the mean aerodynamic chord
        cl_alpha = inputs["data:aerodynamics:aircraft:cruise:CL_alpha"]

        maximum_engine_mach = inputs["data:propulsion:rubber_engine:maximum_mach"]
        cruise_altitude = inputs["data:mission:sizing:main_route:cruise:altitude"]
        cruise_mach = inputs["data:TLAR:cruise_mach"]

        g = 9.80665  # m/s^2

        atm = Atmosphere(altitude=20000, altitude_in_feet=True)
        rho = atm.density

        mass_min = 1.05 * mzfw
        mass_max = mtow

        maximum_positive_load_factor = 3.8
        maximum_negative_load_factor = -0.4 * maximum_positive_load_factor

        cl_max = max(cl_vector_input)
        cl_min = (-2 / 3) * cl_max

        v_stall_true = np.sqrt(
            2 * mtow * g / (rho * wing_area * cl_max)
        )  # Minimal speed of the aircraft m/s
        v_stall_equivalent = v_stall_true * np.sqrt(rho / 1.225)  # V_s

        v_manoeuvre = np.sqrt(
            (2 * mtow * g * maximum_positive_load_factor) / (rho * wing_area * cl_max)
        )
        v_manoeuvre_equivalent = v_manoeuvre * np.sqrt(rho / 1.225)  # V_a

        v_cruising_true = cruise_mach * atm.speed_of_sound
        v_cruising_equivalent = v_cruising_true * np.sqrt(rho / 1.225)  # V_c
        v_cruising_equivalent_vector = np.linspace(0, v_cruising_equivalent, 100)

        v_dive_true = (0.07 + cruise_mach) * atm.speed_of_sound  # V_d
        v_dive_equivalent = v_dive_true * np.sqrt(rho / 1.225)
        v_dive_equivalent_vector = np.linspace(0, v_dive_equivalent, 100)

        v_vector_true = np.linspace(0, v_dive_equivalent, V_n_SHAPE)  # speed vector m/s
        v_vector_equivalent = v_vector_true * np.sqrt(rho / 1.225)

        u_gust_v_c = 50 * 0, 3048  # 50ft/s into m/s
        u_gust_v_d = 25 * 0, 3048  # 50ft/s into m/s

        # Computation for MTOW
        mu = 2 * mtow / (rho * wing_area * mac * cl_alpha)
        K_g = (0.88 * mu) / (5.3 + mu)
        n_v_c_pos_vector = 1 + (
            1.225 * K_g * u_gust_v_c * v_cruising_equivalent_vector * wing_area * cl_alpha
        ) / (2 * g * mtow)
        n_v_d_pos_vector = 1 + (
            1.225 * K_g * u_gust_v_d * v_dive_equivalent_vector * wing_area * cl_alpha
        ) / (2 * g * mtow)

        n_v_c_neg_vector = 1 - (
            1.225 * K_g * u_gust_v_c * v_cruising_equivalent_vector * wing_area * cl_alpha
        ) / (2 * g * mtow)
        n_v_d_neg_vector = 1 - (
            1.225 * K_g * u_gust_v_d * v_dive_equivalent_vector * wing_area * cl_alpha
        ) / (2 * g * mtow)

        # Computation for 1.05*MZFW

        print("v_stall_equivalent = ", v_stall_equivalent)
        print("v_manoeuvre_equivalent = ", v_manoeuvre_equivalent)
        print("v_operational_equivalent = ", v_cruising_equivalent)
        print("v_dive_equivalent = ", v_dive_equivalent)

        # cl_vector = mtow * g / (0.5 * rho * v_vector * v_vector * wing_area)
        # cd_vector = interp1d(cl_vector_input, cd_vector_input, fill_value="extrapolate")(cl_vector)

        flight_point = FlightPoint(
            mach=atm.mach,
            altitude=atm.get_altitude(altitude_in_feet=False),
            engine_setting=EngineSetting.CLIMB,
            thrust_is_regulated=False,
            thrust_rate=1.0,
        )
        # propulsion_model.compute_flight_points(flight_point)
        # power_available_sea = flight_point.thrust * v_vector

        # Put the resultst in the output file
        outputs["data:performance:V-n_diagram:speed_vector"] = v_vector_true
        outputs["data:performance:V-n_diagram:v_stall"] = v_stall_equivalent
        outputs["data:performance:V-n_diagram:v_manoeuvre"] = v_manoeuvre_equivalent
        outputs["data:performance:V-n_diagram:v_cruising"] = v_cruising_equivalent
        outputs["data:performance:V-n_diagram:v_dive"] = v_dive_equivalent
        # outputs[
        #    "data:performance:V-n_diagram:speed_vector"
        # ] = v_vector
        #
        # "data:performance:V-n_diagram:load_vector"
