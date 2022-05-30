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


SPEED_ALTITUDE_SHAPE = 45 # Numbre of points used for the computation of the graph between the sea-level and the ceiling level


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
            "data:performance:speed_altitude_diagram:v_min_mtow",
            shape=40,
            units="m/s",
        )
        self.add_output(
            "data:performance:speed_altitude_diagram:v_max_mtow",
            shape=40,
            units="m/s",
        )
        self.add_output(
            "data:performance:speed_altitude_diagram:v_min_mzfw",
            shape=46,
            units="m/s",
        )
        self.add_output(
            "data:performance:speed_altitude_diagram:v_max_mzfw",
            shape=46,
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
        ceiling = inputs["data:performance:ceiling"]
        ceiling_mtow = 39000
        ceiling_mzfw = 45000

        g = 9.80665  # m/s^2
        altitude_vector_mtow = np.linspace(0, ceiling_mtow, 40)  # feet
        altitude_vector_mzfw = np.linspace(0, ceiling_mzfw, 46)  # feet

        v_max_mtow = np.zeros(altitude_vector_mtow.size)
        v_min_mtow = np.zeros(altitude_vector_mtow.size)

        v_max_mzfw = np.zeros(altitude_vector_mzfw.size)
        v_min_mzfw = np.zeros(altitude_vector_mzfw.size)

        v_dive_vector = np.zeros(altitude_vector_mzfw.size)
        v_engine_vector = np.zeros(altitude_vector_mzfw.size)
        v_computed_vector_mzfw = np.zeros(altitude_vector_mzfw.size)

        v_computed_vector_mtow = np.zeros(altitude_vector_mtow.size)

        # Compute the diagram for MTOW
        for i in range(len(altitude_vector_mtow)):
            atm_mtow = Atmosphere(altitude=altitude_vector_mtow[i], altitude_in_feet=True)
            rho_mtow = atm_mtow.density

            # Compute the minimum and the maximum speed
            v_min_mtow[i] = np.sqrt(2 * mtow * g / (rho_mtow * wing_area * cl_max_clean))
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
            )[0]

            # Compute the maximum speed of the aircraft (diving speed)
            v_dive_mtow = (0.07 + cruise_mach) * atm_mtow.speed_of_sound

            # Compute the maximum speed of the engine
            v_max_engine_mtow = maximum_engine_mach * atm_mtow.speed_of_sound

            # The maximum speed will be the most restrictive one between the computed and the maximum speed of the aircraft (diving speed)
            v_max_mtow[i] = np.minimum(np.minimum(v_dive_mtow, v_max_engine_mtow), v_max_computed_mtow)

            v_computed_vector_mtow[i] = v_max_computed_mtow


        # Compute the diagram for MZFW
        for j in range(len(altitude_vector_mzfw)):
            atm_mzfw = Atmosphere(altitude=altitude_vector_mzfw[j], altitude_in_feet=True)
            rho_mzfw = atm_mzfw.density

            # Compute the minimum and the maximum speed
            v_min_mzfw[j] = np.sqrt(2 * mzfw * g / (rho_mzfw * wing_area * cl_max_clean))
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
            )[0]

            # Compute the maximum speed of the aircraft (diving speed)
            v_dive_mzfw = (0.07 + cruise_mach) * atm_mzfw.speed_of_sound

            # Compute the maximum speed of the engine
            v_max_engine_mzfw = maximum_engine_mach * atm_mzfw.speed_of_sound

            # The maximum speed will be the most restrictive one between the computed and the maximum speed of the aircraft (diving speed)
            v_max_mzfw[j] = np.minimum(np.minimum(v_dive_mzfw, v_max_engine_mzfw), v_max_computed_mzfw)

            v_dive_vector[j] = v_dive_mzfw[0]
            v_engine_vector[j] = v_max_engine_mzfw[0]
            v_computed_vector_mzfw[j] = v_max_computed_mzfw

        # Compute the ceiling line used in the graphical representation
        x_ceiling_mtow = np.array([v_min_mtow[-1], v_max_mtow[-1]])
        y_ceiling_mtow = np.array([ceiling_mtow, ceiling_mtow])

        x_ceiling_mzfw = np.array([v_min_mzfw[-1], v_max_mzfw[-1]])
        y_ceiling_mzfw = np.array([ceiling_mzfw, ceiling_mzfw])

        v_final_mtow = np.append(np.append(v_min_mtow, x_ceiling_mtow), v_max_mtow[::-1])
        altitude_final_mtow = np.append(np.append(altitude_vector_mtow, y_ceiling_mtow), altitude_vector_mtow[::-1])

        v_final_mzfw = np.append(np.append(v_min_mzfw, x_ceiling_mzfw), v_max_mzfw[::-1])
        altitude_final_mzfw = np.append(np.append(altitude_vector_mzfw, y_ceiling_mzfw), altitude_vector_mzfw[::-1])

        # Put the resultst in the output file
        outputs["data:performance:speed_altitude_diagram:v_min_mtow"] = v_min_mtow
        outputs["data:performance:speed_altitude_diagram:v_max_mtow"] = v_max_mtow

        outputs["data:performance:speed_altitude_diagram:v_min_mzfw"] = v_min_mzfw
        outputs["data:performance:speed_altitude_diagram:v_max_mzfw"] = v_max_mzfw

        # Plot the results
        fig = go.Figure()

        scatter_final_mtow = go.Scatter(
            x=v_final_mtow,
            y=altitude_final_mtow,
            line=dict(color="royalblue", width=4),
            mode="lines",
            name="MTOW : Ceiling at %i" % ceiling_mtow,
        )
        scatter_final_mzfw = go.Scatter(
            x=v_final_mzfw,
            y=altitude_final_mzfw,
            line=dict(color="dodgerblue", width=4),
            mode="lines",
            name="MZFW : Ceiling at %i" % ceiling_mzfw,
        )

        scatter_v_dive_vector = go.Scatter(x=v_dive_vector, y=altitude_vector_mzfw, mode="markers",
                                                marker_symbol="circle", marker_color="indianred", marker_size=7,
                                                name="v_dive")
        scatter_v_engine_vector = go.Scatter(x=v_engine_vector, y=altitude_vector_mzfw, mode="markers",
                                                marker_symbol="circle", marker_color="black", marker_size=5,
                                                name="v_engine")

        scatter_v_computed_vector_mzfw = go.Scatter(x=v_computed_vector_mzfw, y=altitude_vector_mzfw, mode="markers",
                                                marker_symbol="circle", marker_color="dodgerblue", marker_size=4.6,
                                                name="v_computed_mzfw")
        scatter_v_computed_vector_mtow = go.Scatter(x=v_computed_vector_mtow, y=altitude_vector_mtow,
                                                line=dict(color="royalblue", dash="dot", width=4),
                                                name="v_computed_mtow")

        fig.add_trace(scatter_final_mzfw)
        fig.add_trace(scatter_final_mtow)
        fig.add_trace(scatter_v_dive_vector)
        fig.add_trace(scatter_v_engine_vector)

        fig.add_trace(scatter_v_computed_vector_mzfw)
        fig.add_trace(scatter_v_computed_vector_mtow)


        fig = go.FigureWidget(fig)
        fig.update_layout(
            title_text="Altitude-Speed diagram",
            title_x=0.5,
            xaxis_title="Speed [m/s]",
            yaxis_title="Altitude [ft]",
        )
        fig.show()
