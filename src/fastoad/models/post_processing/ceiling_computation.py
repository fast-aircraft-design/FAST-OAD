"""Computation of the ceiling of the aircraft."""
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
from scipy.optimize import fsolve


class CeilingComputation(om.ExplicitComponent):
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
        self.add_input("data:TLAR:cruise_mach", val=np.nan)
        self._engine_wrapper = BundleLoader().instantiate_component(self.options["propulsion_id"])
        self._engine_wrapper.setup(self)

        self.add_output(
            "data:performance:ceiling",
            units="m",
        )

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):

        propulsion_model = self._engine_wrapper.get_model(inputs)

        wing_area = inputs["data:geometry:wing:area"]
        mtow = inputs["data:weight:aircraft:MTOW"]
        mzfw = inputs["data:weight:aircraft:MZFW"]
        cl_vector_input = inputs["data:aerodynamics:aircraft:cruise:CL"]
        cd_vector_input = inputs["data:aerodynamics:aircraft:cruise:CD"]
        cl_max_clean = inputs["data:aerodynamics:aircraft:landing:CL_max_clean"]
        maximum_engine_mac = inputs["data:propulsion:rubber_engine:maximum_mach"]
        cruise_mac = inputs["data:TLAR:cruise_mach"]

        # Computation of the ceiling of the aircraft for a given mass
        ceiling = get_ceiling(
            mzfw,
            propulsion_model,
            wing_area,
            cl_vector_input,
            cd_vector_input,
            cl_max_clean,
            maximum_engine_mac,
            cruise_mac,
        )

        outputs["data:performance:ceiling"] = ceiling
        print(ceiling)


def get_ceiling(
    mass,
    propulsion_model,
    wing_area,
    cl_vector_input,
    cd_vector_input,
    cl_max_clean,
    maximum_engine_mac,
    cruise_mac,
):

    g = 9.80665  # m/s^2
    ceiling = 20000  # starting value of the ceiling
    iter_again = True  # variable used to decide if the iteration needs to continue or not. "True" means that the iteration needs to continue because the ceiling value is not found yet. "False" means that the ceiling value is found and the iteration can stop.

    while iter_again:
        atm = Atmosphere(altitude=ceiling, altitude_in_feet=True)
        rho = atm.density
        v_min = np.sqrt(
            2 * mass * g / (rho * wing_area * cl_max_clean)
        )  # the minimum speed is the stall speed
        v_max_engine = (
            maximum_engine_mac * atm.speed_of_sound
        )  # the maximum speed is given by the maximum mac number
        v_dive = (cruise_mac + 0.07) * atm.speed_of_sound
        v_max = np.minimum(v_dive, v_max_engine)
        speed_vector = np.linspace(
            v_min, v_max, 25
        )  # the 25 speeds tested start at stall speed until the maximum speed given by the
        count = 0  # variable used to know, at each altitude, how many speed give a thrust bigger than the drag

        for speed in speed_vector:  # iteration on each speed

            difference = thrust_minus_drag(
                speed,
                ceiling,
                mass,
                wing_area,
                cl_vector_input,
                cd_vector_input,
                propulsion_model,
            )  # variable which gives the difference between the thrust and the drag
            if difference > 0:
                count += 1

        # Decides if an extra iteration is needed or not
        if (
            count > 0
        ):  # if at least one speed in the speed vector gives a thrust bigger than the drag, it means that the ceiling is not reached and an extra iteration is needed
            iter_again = True
            ceiling += 1000  # the next ceiling value tested is 1000 ft bigger than the previous one
        else:
            iter_again = False
            ceiling -= 1000

    return ceiling


# Function which computes the difference between the thrust and the drag
def thrust_minus_drag(v, alti, mtow, wing_area, cl_vector_input, cd_vector_input, propulsion_model):
    atm = Atmosphere(altitude=alti, altitude_in_feet=True)
    atm.true_airspeed = v
    rho = atm.density
    g = 9.80665  # m/s^2

    # Compute thrust
    flight_point = FlightPoint(
        mach=atm.mach,
        altitude=atm.get_altitude(altitude_in_feet=False),
        engine_setting=EngineSetting.CLIMB,
        thrust_is_regulated=False,
        # Si je mets false, cela veut dire que je fixe la manette des gaz sans connaitre la poussée en N. Si je mets True, je pose la poussée en N et je demande qu'il calcule la position de la manette des gaz.
        thrust_rate=1.0,
    )
    propulsion_model.compute_flight_points(flight_point)
    thrust = flight_point.thrust

    # Compute the aerodynamic coefficients
    cl = 2 * mtow * g / (rho * wing_area * atm.true_airspeed * atm.true_airspeed)
    cd_interpolated = np.interp(cl, cl_vector_input, cd_vector_input)

    # Compute the drag
    drag_interpolated = (
        cd_interpolated * 0.5 * rho * atm.true_airspeed * atm.true_airspeed * wing_area
    )

    return thrust - drag_interpolated
