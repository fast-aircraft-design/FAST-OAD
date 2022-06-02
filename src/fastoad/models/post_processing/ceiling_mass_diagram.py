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
from fastoad.constants import RangeCategory
from .ceiling_computation import CeilingComputation
from .ceiling_computation import thrust_minus_drag
from fastoad.constants import EngineSetting
from fastoad.model_base import FlightPoint
from scipy.optimize import fsolve
import plotly.graph_objects as go
from fastoad.module_management._plugins import FastoadLoader

FastoadLoader()

CEILING_MASS_SHAPE = 100 # Number of points used for the computation of the graph


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

        self._engine_wrapper = BundleLoader().instantiate_component(self.options["propulsion_id"])
        self._engine_wrapper.setup(self)

        self.add_output(
            "data:performance:ceiling_mass_diagram:cruise:altitude",
            shape=CEILING_MASS_SHAPE,
            units="ft",
        )
        self.add_output(
            "data:performance:ceiling_mass_diagram:climb:altitude",
            shape=CEILING_MASS_SHAPE,
            units="ft",
        )
        self.add_output(
            "data:performance:ceiling_mass_diagram:buffeting:altitude",
            shape=CEILING_MASS_SHAPE,
            units="ft",
        )

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):

        propulsion_model = self._engine_wrapper.get_model(inputs)

        tlar_range = inputs["data:TLAR:range"]
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

        # Mass vectors
        mass_vector = np.linspace(mzfw, mtow, CEILING_MASS_SHAPE)

        # Altitude vectors
        alti_cruise = np.zeros(mass_vector.size)
        alti_climb = np.zeros(mass_vector.size)
        alti_buffeting = np.zeros(mass_vector.size)

        alti_interpol = np.linspace(0, 60000, 121) # ft
        pressure_interpol = np.zeros(alti_interpol.size)
        for i in (len(alti_interpol)):
            pressure_interpol[i] = Atmosphere(altitude=alti_interpol[i], altitude_in_feet=True).pressure

        mach_interpol = np.linspace(0.59,0.86, 28) # mach used for the curve Cz_buffeting - Mach
        cz_buffeting_vector = np.array([0.741, 0.73,0.722,0.712,0.704,0.698,0.692,0.689,0.687,0.682,0.681,0.68,0.679,0.679,0.679,0.679,0.68,0.6790,0.677,0.67,0.662,0.65,0.634,0.619,0.591,0.56,0.51,0.45])

        if tlar_range in RangeCategory.SHORT:
            v_z = 500 #ft/min
        elif tlar_range in RangeCategory.SHORT_MEDIUM:
            v_z = 500 #ft/min
        elif tlar_range in RangeCategory.MEDIUM:
            v_z = 500 #ft/min
        else:
            v_z = 300 #ft/min

        # Compute the diagram for cruise, climb and buffeting case
        for j in range(len(mass_vector)):

            cz_buffeting = np.interp([cruise_mach, mach_interpol, cz_buffeting_vector])
            min_pressure = mass_vector[j]*g*1.3/(0.7*cruise_mach*cruise_mach*wing_area*cz_buffeting)
            alti_buffeting[j] = np.interp(min_pressure, pressure_interpol, alti_interpol)

            alti_climb[j] = 1
            alti_cruise[j] = 1






        # Put the resultst in the output file
        outputs["data:performance:ceiling_mass_diagram:cruise:altitude"] = alti_cruise
        outputs["data:performance:ceiling_mass_diagram:climb:altitude"] = alti_climb
        outputs["data:performance:ceiling_mass_diagram:buffeting:altitude"] = alti_buffeting