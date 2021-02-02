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
    <img src="../../img/logo-onera.png" width="200">
  </div>
  <div class="column">
    <img src="../../img/logo-ISAE_SUPAERO.png" width="200">
  </div>
</div>
"""

# %%
import logging
import os.path as pth
from os import mkdir
from shutil import rmtree

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
from fastoad.io import VariableIO
from fastoad.models.propulsion.fuel_propulsion.rubber_engine import RubberEngine
from fastoad.utils.postprocessing.analysis_and_plots import (
    mass_breakdown_sun_plot,
    wing_geometry_plot,
)

# %%
mission_name = "R4167_PL21500_CEO"

A321CEO_INPUT_FILE = pth.join(pth.pardir, pth.pardir, "reference_data.xml")

WORK_FOLDER_PATH = mission_name
OAD_SIZING_CONFIGURATION_FILE = pth.join(WORK_FOLDER_PATH, "oad_sizing.toml")
OAD_WING_CONFIGURATION_FILE = pth.join(WORK_FOLDER_PATH, "oad_sizing_wing_imposed.toml")
FUEL_SIZING_CONFIGURATION_FILE = pth.join(WORK_FOLDER_PATH, "fuel_sizing.toml")

INPUT_FOLDER_PATH = pth.join(WORK_FOLDER_PATH, "inputs")


OUTPUT_FOLDER_PATH = pth.join(WORK_FOLDER_PATH, "outputs")
rmtree(OUTPUT_FOLDER_PATH, ignore_errors=True)
mkdir(OUTPUT_FOLDER_PATH)
OAD_SIZING_CSV_FILE = pth.join(OUTPUT_FOLDER_PATH, "oad_sizing.csv")
OAD_WING_CSV_FILE = pth.join(OUTPUT_FOLDER_PATH, "oad_sizing_wing.csv")
FUEL_SIZING_CSV_FILE = pth.join(OUTPUT_FOLDER_PATH, "fuel_sizing.csv")

# For having log messages on screen
logging.basicConfig(level=logging.INFO, format="%(levelname)-8s: %(message)s")
# %%


def plot_results(fast_oad_csv):
    fast_df = pd.read_csv(fast_oad_csv)
    fast_df.altitude /= foot
    fast_df.ground_distance /= nautical_mile
    name = "FAST-OAD A321LR"
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=fast_df["ground_distance"],
            y=fast_df["altitude"],
            name="[%s] altitude vs distance" % name,
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=fast_df["ground_distance"],
            y=fast_df["CL"],
            name="[%s] CL vs distance" % name,
            line=dict(dash="dot"),
        ),
        secondary_y=True,
    )

    fig.update_xaxes(range=[-30, 3100.0])
    fig.update_yaxes(title_text="Altitude [ft]", range=[0, 40000.0], secondary_y=False)
    fig.update_yaxes(title_text="CL", range=[0.3, 0.8], secondary_y=True)
    fig.update_layout(margin=dict(l=300, r=280, t=20, b=0), width=1000, height=250)
    fig.show()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=fast_df["ground_distance"], y=fast_df["thrust"], name="[%s] thrust vs distance" % name
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=fast_df["ground_distance"],
            y=fast_df["mass"].iloc[0] - fast_df["mass"],
            name="[%s] fuel vs distance" % name,
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
# A321 CEO No Sharklet No ACT WV 00 89T
## IAE V2533-A5 Engine
"""


# %%

engine = RubberEngine(
    bypass_ratio=4.9,
    overall_pressure_ratio=32.5,
    turbine_inlet_temperature=1633,
    mto_thrust=140550,
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
## OAD Sizing
"""

# %%
# input_file = api.generate_inputs(OAD_SIZING_CONFIGURATION_FILE, A321CEO_INPUT_FILE, overwrite=True)
input_file = pth.join(INPUT_FOLDER_PATH, "oad_sizing_in.xml")
# %%

api.variable_viewer(input_file, editable=False)

# %%
problem = api.evaluate_problem(OAD_SIZING_CONFIGURATION_FILE, overwrite=True)

# %%
api.variable_viewer(problem.output_file_path, editable=True)

# %%

plot_results(OAD_SIZING_CSV_FILE)

# %%

mass_breakdown_sun_plot(problem.output_file_path)

# %%

wing_geometry_plot(problem.output_file_path, name="FAST-OAD A321")

# %%
"""
## OAD Sizing wing imposed to A320 Shape
"""

# %%
# input_file = api.generate_inputs(OAD_WING_CONFIGURATION_FILE, A321CEO_INPUT_FILE_WING, overwrite=False)
input_file = pth.join(INPUT_FOLDER_PATH, "oad_sizing_wing_imposed_in.xml")
# %%

api.variable_viewer(input_file, editable=True)

# %%
problem = api.evaluate_problem(OAD_WING_CONFIGURATION_FILE, overwrite=True)

# %%
api.variable_viewer(problem.output_file_path, editable=True)

# %%

plot_results(OAD_WING_CSV_FILE)

# %%

mass_breakdown_sun_plot(problem.output_file_path)

# %%

wing_geometry_plot(problem.output_file_path, name="FAST-OAD A321")

# %%
"""
## Fuel sizing wing imposed to A320 Shape
"""

# %%
# input_file = api.generate_inputs(FUEL_SIZING_CONFIGURATION_FILE, A321CEO_INPUT_FILE, overwrite=True)
input_file = pth.join(INPUT_FOLDER_PATH, "fuel_sizing_in.xml")
api.variable_viewer(input_file, editable=True)

# %%
problem = api.evaluate_problem(FUEL_SIZING_CONFIGURATION_FILE, overwrite=True)

# %%
plot_results(FUEL_SIZING_CSV_FILE)

# %%
