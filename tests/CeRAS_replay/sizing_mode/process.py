#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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

# %%
"""
<div class="row">
  <div class="column">
    <img src="../img/logo-onera.png" width="200">
  </div>
  <div class="column">
    <img src="../img/logo-ISAE_SUPAERO.png" width="200">
  </div>
</div>
"""

# %%
import logging
import os.path as pth

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.constants import foot
from scipy.constants import nautical_mile

from fastoad import api
from fastoad.base.flight_point import FlightPoint
from fastoad.constants import EngineSetting
from fastoad.models.propulsion.fuel_propulsion.rubber_engine import RubberEngine
from fastoad.utils.postprocessing.analysis_and_plots import (
    wing_geometry_plot,
    mass_breakdown_sun_plot,
    aircraft_geometry_plot,
    mass_breakdown_bar_plot,
)

# %%
engine = RubberEngine(
    bypass_ratio=4.9,
    overall_pressure_ratio=32.6,
    turbine_inlet_temperature=1600,
    mto_thrust=117880,
    maximum_mach=0.85,
    design_altitude=10058.4,
    delta_t4_climb=-50.0,
    delta_t4_cruise=-100.0,
)

thrust = np.linspace(10.0e3, 32.0e3, 20)

bucket_points = pd.DataFrame(
    [
        FlightPoint(
            altitude=35000 * foot,
            mach=0.78,
            thrust=thrust,
            thrust_rate=0.0,
            thrust_is_regulated=True,
            engine_setting=EngineSetting.convert("CRUISE"),
        )
        for thrust in np.linspace(10.0e3, 32.0e3, 20)
    ]
)


engine.compute_flight_points(bucket_points)

fig = px.line(bucket_points, x="thrust", y="sfc", width=800, height=350)
fig.update_xaxes(title_text="Thrust per engine [N]", range=[5000, 35000])
fig.update_yaxes(title_text="SFC [kg/s/N]", range=[1.4e-5, 2.0e-5])
fig.update_layout(margin=dict(l=265, r=145, t=20, b=20),)
fig.show()

# %%
"""
#### From CeRAS_CSR-01_report.pdf
<img src="../img/CeRAS_report/CeRAS_bucket_curve.jpg" width="600">
"""

# %%
BREGUET_WORK_FOLDER_PATH = "breguet"
TIMESTEP_WORK_FOLDER_PATH = "time_step"

BREGUET_CONFIGURATION_FILE = pth.join(BREGUET_WORK_FOLDER_PATH, "oad_process.toml")
TIMESTEP_CONFIGURATION_FILE = pth.join(TIMESTEP_WORK_FOLDER_PATH, "oad_process.toml")
CeRAS_INPUT_FILE = pth.join(pth.pardir, "reference_data.xml")
MISSION_CSV_FILE = pth.join(TIMESTEP_WORK_FOLDER_PATH, "outputs", "mission_CeRAS.csv")


# For having log messages on screen
logging.basicConfig(level=logging.INFO, format="%(levelname)-8s: %(message)s")

# # For using all screen width
# from IPython.core.display import display, HTML
# display(HTML("<style>.container { width:95% !important; }</style>"))

# %%
ceras_breguet_input_file = api.generate_inputs(
    BREGUET_CONFIGURATION_FILE, CeRAS_INPUT_FILE, overwrite=True
)
api.variable_viewer(ceras_breguet_input_file, editable=False)

# %%
breguet_problem = api.evaluate_problem(BREGUET_CONFIGURATION_FILE, overwrite=True)

# %%
ceras_timestep_input_file = api.generate_inputs(
    TIMESTEP_CONFIGURATION_FILE, CeRAS_INPUT_FILE, overwrite=True
)
api.variable_viewer(ceras_timestep_input_file, editable=False)

# %%
timestep_problem = api.evaluate_problem(TIMESTEP_CONFIGURATION_FILE, overwrite=True)

# %%
api.variable_viewer(timestep_problem.output_file_path, editable=False)

# %%
fig = wing_geometry_plot(breguet_problem.output_file_path, name="Breguet")
fig = wing_geometry_plot(timestep_problem.output_file_path, name="Mission", fig=fig)
fig.show()

# %%
"""
#### From CeRAS_CSR-01_report.pdf
<img src="../img/CeRAS_report/wing_parameters.png" width="600">
"""

# %%
fig = aircraft_geometry_plot(breguet_problem.output_file_path, name="Breguet")
fig = aircraft_geometry_plot(timestep_problem.output_file_path, name="Mission", fig=fig)
fig.show()

# %%
fig = mass_breakdown_sun_plot(breguet_problem.output_file_path)
fig.show()

# %%
fig = mass_breakdown_sun_plot(timestep_problem.output_file_path)
fig.show()

# %%
"""
#### From CeRAS_CSR-01_report.pdf
| ![mass 1](../img/CeRAS_report/mass_breakdown_1.png) | ![mass 2](../img/CeRAS_report/mass_breakdown_2.png) |
|:---:|:---:|
"""

# %%
fig = mass_breakdown_bar_plot(breguet_problem.output_file_path, name="Breguet")
fig = mass_breakdown_bar_plot(timestep_problem.output_file_path, name="Mission", fig=fig)
fig.show()

# %%
df = pd.read_csv(MISSION_CSV_FILE)
df.altitude /= foot
df.ground_distance /= nautical_mile

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(
    go.Scatter(x=df["ground_distance"], y=df["altitude"], name="altitude vs distance"),
    secondary_y=False,
)

fig.add_trace(
    go.Scatter(x=df["ground_distance"], y=df["CL"], name="CL vs distance", line=dict(dash="dot"),),
    secondary_y=True,
)

fig.update_xaxes(range=[-30, 2800.0])
fig.update_yaxes(title_text="Altitude [ft]", range=[0, 40000.0], secondary_y=False)
fig.update_yaxes(title_text="CL", range=[0.3, 0.8], secondary_y=True)
fig.update_layout(margin=dict(l=300, r=280, t=20, b=0), width=1000, height=250)

fig.show()

fig = make_subplots(specs=[[{"secondary_y": True}]])

fig.add_trace(
    go.Scatter(x=df["ground_distance"], y=df["thrust"], name="thrust vs distance"),
    secondary_y=False,
)

fig.add_trace(
    go.Scatter(
        x=df["ground_distance"],
        y=df["mass"].iloc[0] - df["mass"],
        name="fuel vs distance",
        line=dict(dash="dot"),
    ),
    secondary_y=True,
)

fig.update_xaxes(title_text="Range [nm]", range=[-30, 2800.0])
fig.update_yaxes(title_text="Thrust [N]", range=[0, 300000.0], secondary_y=False)
fig.update_yaxes(title_text="Block fuel [kg]", range=[0.0, 21000.0], secondary_y=True)
fig.update_layout(margin=dict(l=300, r=280, t=0, b=20), width=1000, height=250)


fig.show()

# %%
"""
#### From CeRAS_CSR-01_report.pdf
<img src="../img/CeRAS_report/design_mission.png" width="600">
"""
