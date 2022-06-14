"""Computation of the Ceiling-altitude diagram."""
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

CEILING_MASS_SHAPE = 100  # Number of points used for the computation of the graph


class CeilingMassDiagram(om.ExplicitComponent):
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
        self.add_input("data:TLAR:range", val=np.nan)

        self._engine_wrapper = BundleLoader().instantiate_component(self.options["propulsion_id"])
        self._engine_wrapper.setup(self)

        self.add_output(
            "data:performance:ceiling_mass_diagram:altitude:cruise",
            shape=CEILING_MASS_SHAPE,
            units="ft",
        )
        self.add_output(
            "data:performance:ceiling_mass_diagram:altitude:climb",
            shape=CEILING_MASS_SHAPE,
            units="ft",
        )
        self.add_output(
            "data:performance:ceiling_mass_diagram:altitude:buffeting",
            shape=CEILING_MASS_SHAPE,
            units="ft",
        )
        self.add_output(
            "data:performance:ceiling_mass_diagram:mass",
            shape=CEILING_MASS_SHAPE,
            units="kg",
        )

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):

        propulsion_model = self._engine_wrapper.get_model(inputs)

        tlar_range = inputs["data:TLAR:range"]
        wing_area = float(inputs["data:geometry:wing:area"])
        mtow = inputs["data:weight:aircraft:MTOW"]
        mzfw = inputs["data:weight:aircraft:MZFW"]
        cl_vector_input = inputs["data:aerodynamics:aircraft:cruise:CL"]
        cd_vector_input = inputs["data:aerodynamics:aircraft:cruise:CD"]
        cruise_mach = float(inputs["data:TLAR:cruise_mach"])

        g = 9.80665  # m/s^2

        # Mass vectors
        mass_vector = np.linspace(float(mzfw), float(mtow + 500), CEILING_MASS_SHAPE)

        # Altitude vectors
        alti_cruise = np.zeros_like(mass_vector)
        alti_climb = np.zeros_like(mass_vector)
        alti_buffeting = np.zeros_like(mass_vector)

        # Compute the pressure vector corresponding to the altitude vector
        alti_interpol = np.linspace(0, 60000, 121)  # ft
        pressure_interpol = Atmosphere(altitude=alti_interpol, altitude_in_feet=True).pressure

        # Mach used for the curve Cz_buffeting - Mach
        mach_interpol = np.linspace(0.59, 0.86, 28)
        cz_buffeting_vector = np.array(
            [
                0.741,
                0.73,
                0.722,
                0.712,
                0.704,
                0.698,
                0.692,
                0.689,
                0.687,
                0.682,
                0.681,
                0.68,
                0.679,
                0.679,
                0.679,
                0.679,
                0.68,
                0.6790,
                0.677,
                0.67,
                0.662,
                0.65,
                0.634,
                0.619,
                0.591,
                0.56,
                0.51,
                0.45,
            ]
        )

        if tlar_range in RangeCategory.SHORT:
            v_z = 500  # ft/min
        elif tlar_range in RangeCategory.SHORT_MEDIUM:
            v_z = 500  # ft/min
        elif tlar_range in RangeCategory.MEDIUM:
            v_z = 500  # ft/min
        else:
            v_z = 300  # ft/min

        cz_buffeting = float(np.interp(cruise_mach, mach_interpol, cz_buffeting_vector))

        for i in range(len(mass_vector)):

            mass = mass_vector[i]

            # Compute the buffeting limit
            min_pressure = (
                mass * g * 1.3 / (0.7 * cruise_mach * cruise_mach * wing_area * cz_buffeting)
            )
            alti_buffeting[i] = interp1d(pressure_interpol, alti_interpol)(min_pressure)

            # Compute the climb limit
            alti_climb[i] = fsolve(
                roc_minus_v_z,
                30000,
                args=(
                    mass,
                    v_z,
                    cruise_mach,
                    wing_area,
                    cl_vector_input,
                    cd_vector_input,
                    propulsion_model,
                ),
            )[0]

            # Compute the cruise limit
            alti_cruise[i] = fsolve(
                roc_minus_v_z,
                30000,
                args=(
                    mass,
                    0,
                    cruise_mach,
                    wing_area,
                    cl_vector_input,
                    cd_vector_input,
                    propulsion_model,
                ),
            )[0]

        # Put the resultst in the output file
        outputs["data:performance:ceiling_mass_diagram:altitude:cruise"] = alti_cruise
        outputs["data:performance:ceiling_mass_diagram:altitude:climb"] = alti_climb
        outputs["data:performance:ceiling_mass_diagram:altitude:buffeting"] = alti_buffeting
        outputs["data:performance:ceiling_mass_diagram:mass"] = mass_vector


# This function computes the difference between the Rate of Climbing (roc) and the ascending speed
def roc_minus_v_z(
    alti, mass, vz, mach, wing_area, cl_vector_input, cd_vector_input, propulsion_model
):
    atm = Atmosphere(altitude=alti, altitude_in_feet=True)
    rho = atm.density

    # Convert the ft/min into m/s
    v_z = vz * 0.3054 / 60

    flight_point = FlightPoint(
        mach=mach,
        altitude=atm.get_altitude(altitude_in_feet=False),
        engine_setting=EngineSetting.CLIMB,
        thrust_is_regulated=False,
        thrust_rate=1.0,
    )
    propulsion_model.compute_flight_points(flight_point)
    thrust = flight_point.thrust

    v = mach * atm.speed_of_sound
    g = 9.80665  # m/s^2
    cl = mass * g / (0.5 * rho * v * v * wing_area)
    cd = np.interp(cl, cl_vector_input, cd_vector_input)
    drag = 0.5 * rho * v * v * wing_area * cd

    difference = (v * (thrust - drag) / (mass * g)) - v_z

    return difference
