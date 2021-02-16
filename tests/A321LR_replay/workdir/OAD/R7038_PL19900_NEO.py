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
    aircraft_geometry_plot,
)

# %%
def plot_results(fast_oad_csv, compare_with=None):
    fast_df = pd.read_csv(fast_oad_csv)
    fast_df.altitude /= foot
    fast_df.ground_distance /= nautical_mile
    name = "FAST-OAD A321NEO"
    if compare_with:
        fast_df2 = pd.read_csv(compare_with)
        fast_df2.altitude /= foot
        fast_df2.ground_distance /= nautical_mile
        name2 = "FAST-OAD A321NEO CFM tuned"

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
    if compare_with:
        fig.add_trace(
            go.Scatter(
                x=fast_df2["ground_distance"],
                y=fast_df2["altitude"],
                name="[%s] altitude vs distance" % name2,
            ),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(
                x=fast_df2["ground_distance"],
                y=fast_df2["CL"],
                name="[%s] CL vs distance" % name2,
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
    if compare_with:
        fig.add_trace(
            go.Scatter(
                x=fast_df2["ground_distance"],
                y=fast_df2["thrust"],
                name="[%s] thrust vs distance" % name2,
            ),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(
                x=fast_df2["ground_distance"],
                y=fast_df2["mass"].iloc[0] - fast_df2["mass"],
                name="[%s] fuel vs distance" % name2,
                line=dict(dash="dot"),
            ),
            secondary_y=True,
        )
    fig.update_xaxes(title_text="Range [nm]", range=[-30, 2800.0])
    fig.update_yaxes(title_text="Thrust [N]", range=[0, 300000.0], secondary_y=False)
    fig.update_yaxes(title_text="Block fuel [kg]", range=[0.0, 21000.0], secondary_y=True)
    fig.update_layout(margin=dict(l=300, r=280, t=0, b=20), width=1000, height=250)
    fig.show()

    fig = make_subplots()
    fig.add_trace(
        go.Scatter(
            x=fast_df["ground_distance"], y=fast_df["sfc"], name="[%s] sfc vs distance" % name
        )
    )
    if compare_with:
        fig.add_trace(
            go.Scatter(
                x=fast_df2["ground_distance"],
                y=fast_df2["sfc"],
                name="[%s] sfc vs distance" % name2,
            )
        )
    fig.update_xaxes(title_text="Range [nm]", range=[-30, 2800.0])
    fig.update_yaxes(title_text="TSFC [kg/s/N]", range=[0, 300000.0])
    fig.update_layout(margin=dict(l=300, r=280, t=0, b=20), width=1000, height=250)
    fig.show()


# %%
"""
# Inputs
"""

# %%
mission_name = "R7408_PL18000"
ref_mission = "R4167_PL21500_CEO"

A321NEO_INPUT_FILE = pth.join(pth.pardir, pth.pardir, "reference_data.xml")
FUEL_SIZING_INPUT_FILE = pth.join(ref_mission, "outputs", "oad_sizing_out.xml")

WORK_FOLDER_PATH = mission_name
FUEL_SIZING_CONFIGURATION_FILE = pth.join(WORK_FOLDER_PATH, "fuel_sizing.toml")
FUEL_SIZING_CFM_CONFIGURATION_FILE = pth.join(WORK_FOLDER_PATH, "fuel_sizing_cfm.toml")
WING_IMPOSED_CONFIGURATION_FILE = pth.join(WORK_FOLDER_PATH, "oad_sizing_wing_imposed.toml")

OUTPUT_FOLDER_PATH = pth.join(WORK_FOLDER_PATH, "outputs")
rmtree(OUTPUT_FOLDER_PATH, ignore_errors=True)
mkdir(OUTPUT_FOLDER_PATH)
FUEL_SIZING_CSV_FILE = pth.join(OUTPUT_FOLDER_PATH, "fuel_sizing.csv")
FUEL_SIZING_CFM_CSV_FILE = pth.join(OUTPUT_FOLDER_PATH, "fuel_sizing_cfm.csv")
WING_IMPOSED_CSV_FILE = pth.join(OUTPUT_FOLDER_PATH, "oad_sizing_wing_imposed.csv")

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s: %(message)s")

# %%
"""
# NEO Engine LEAP-1A Specific consumption
"""

# %%

engine_leap = RubberEngine(
    bypass_ratio=11,
    overall_pressure_ratio=40,
    turbine_inlet_temperature=1833,
    mto_thrust=143050,
    maximum_mach=0.85,
    design_altitude=34500 * foot,
    delta_t4_climb=-50.0,
    delta_t4_cruise=-100.0,
    k1_sfc=1.215,
    k2_sfc=1.01,
)

engine_cfm56 = RubberEngine(
    bypass_ratio=5.5,
    overall_pressure_ratio=34.4,
    turbine_inlet_temperature=1633,
    mto_thrust=133440.0,
    maximum_mach=0.85,
    design_altitude=10058.4,
    delta_t4_climb=-50.0,
    delta_t4_cruise=-100.0,
    k1_sfc=0.85,
    k2_sfc=0.92,
)

thrust = np.linspace(5.0e3, 15.0e4, 200)

bucket_points = pd.DataFrame(
    [
        FlightPoint(
            altitude=0 * foot,
            mach=0.2,
            thrust=thrust,
            thrust_rate=0.0,
            thrust_is_regulated=True,
            engine_setting=EngineSetting.convert("TAKEOFF"),
        )
        for thrust in np.linspace(10.0e3, 15.0e4, 200)
    ]
)
bucket_points_cfm56 = pd.DataFrame(
    [
        FlightPoint(
            altitude=0 * foot,
            mach=0.2,
            thrust=thrust,
            thrust_rate=0.0,
            thrust_is_regulated=True,
            engine_setting=EngineSetting.convert("TAKEOFF"),
        )
        for thrust in np.linspace(10.0e3, 15.0e4, 200)
    ]
)


engine_leap.compute_flight_points(bucket_points)
bucket_points["sfc"] = bucket_points["sfc"]
engine_cfm56.compute_flight_points(bucket_points_cfm56)
bucket_points_cfm56["sfc"] = bucket_points_cfm56["sfc"]

fig = make_subplots()
fig.add_trace(go.Scatter(x=bucket_points["thrust"], y=bucket_points["sfc"], name="LEAP"))
fig.update_xaxes(title_text="Thrust per engine [N]", range=[5000, 150000])
fig.update_yaxes(title_text="SFC [kg/s/N]", range=[0.9e-5, 1.0e-5])
fig.update_layout(margin=dict(l=265, r=145, t=20, b=20),)
# fig.show()

fig.add_trace(
    go.Scatter(x=bucket_points_cfm56["thrust"], y=bucket_points_cfm56["sfc"], name="CFM56 mod")
)
fig.update_xaxes(title_text="Thrust per engine [N]", range=[5000, 150000])
fig.update_yaxes(title_text="SFC [kg/s/N]", range=[0.9e-5, 1.0e-5])
fig.update_layout(margin=dict(l=265, r=145, t=20, b=20),)
fig.show()

thrust = np.linspace(5.0e3, 40.0e3, 20)

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
        for thrust in np.linspace(5.0e3, 40.0e3, 20)
    ]
)
bucket_points_cfm56 = pd.DataFrame(
    [
        FlightPoint(
            altitude=35000 * foot,
            mach=0.78,
            thrust=thrust,
            thrust_rate=0.0,
            thrust_is_regulated=True,
            engine_setting=EngineSetting.convert("CRUISE"),
        )
        for thrust in np.linspace(5.0e3, 40.0e3, 20)
    ]
)


engine_leap.compute_flight_points(bucket_points)
bucket_points["sfc"] = bucket_points["sfc"]
engine_cfm56.compute_flight_points(bucket_points_cfm56)
bucket_points_cfm56["sfc"] = bucket_points_cfm56["sfc"]

fig = make_subplots()
fig.add_trace(go.Scatter(x=bucket_points["thrust"], y=bucket_points["sfc"], name="LEAP"))
fig.update_xaxes(title_text="Thrust per engine [N]", range=[5000, 45000])
fig.update_yaxes(title_text="SFC [kg/s/N]", range=[1.4e-5, 2.0e-5])
fig.update_layout(margin=dict(l=265, r=145, t=20, b=20),)
# fig.show()

fig.add_trace(
    go.Scatter(x=bucket_points_cfm56["thrust"], y=bucket_points_cfm56["sfc"], name="CFM56 mod")
)
fig.update_xaxes(title_text="Thrust per engine [N]", range=[5000, 45000])
fig.update_yaxes(title_text="SFC [kg/s/N]", range=[1.4e-5, 2.0e-5])
fig.update_layout(margin=dict(l=265, r=145, t=20, b=20),)
fig.show()

# %%
"""
## Fuel Sizing with LEAP characteristics
Here the geometry is frozen to WV00 without sharklet one. The engine rating is updated to take into 
account the New Engine Option. The performance of the engine, particularly the consumption is tuned 
through a linear correction that penalise Rubber Engine model to better fit LEAP performances. 
"""

# %%
input_file = pth.join(WORK_FOLDER_PATH, "inputs", "fuel_sizing_in.xml")

# %%

api.variable_viewer(input_file, editable=True)

# %%
problem = api.evaluate_problem(FUEL_SIZING_CONFIGURATION_FILE, overwrite=True)

# %%
api.variable_viewer(problem.output_file_path, editable=True)

# %%

plot_results(FUEL_SIZING_CSV_FILE)

# %%

print("TOW = ", problem["data:mission:MTOW_mission:TOW"])
print("Fuel = ", problem["data:mission:MTOW_mission:block_fuel"])

# %%
"""
## Fuel Sizing with CFM56 characteristics
Here the geometry is frozen to WV00 without sharklet one. The engine rating is updated to take into 
account the New Engine Option. The performance of the engine, particularly the consumption is tuned 
through a linear correction to fit CFM56 engine with LEAP performance. Only the MTO thrust is 
updated BR and PR remain at CFM56 values as well as inlet temperature. In that way we remain in the 
domain of validity of rubber engine model. 
"""

# %%
input_file = pth.join(WORK_FOLDER_PATH, "inputs", "fuel_sizing_cfm_in.xml")

# %%

api.variable_viewer(input_file, editable=True)

# %%
problem = api.evaluate_problem(FUEL_SIZING_CFM_CONFIGURATION_FILE, overwrite=True)

# %%
api.variable_viewer(problem.output_file_path, editable=True)

# %%

plot_results(FUEL_SIZING_CSV_FILE, compare_with=FUEL_SIZING_CFM_CSV_FILE)

# %%

print("TOW = ", problem["data:mission:MTOW_mission:TOW"])
print("Fuel = ", problem["data:mission:MTOW_mission:block_fuel"])

# %%
"""
## OAD Sizing no wing loop

Here the wing shape is imposed from WV00 OAD sizing results.
However, the geometry is slightly updated to account for the addition of the sharklet: AR is set to 
10.18 and span to 35.8m. The tuning coefficient on induced drag is also updated to account for the 
sharklet, and a weight penalty on secondary wing structure is considered. 
Other part of the aircraft are sized according to the payload. 
"""

# %%

input_file = pth.join(WORK_FOLDER_PATH, "inputs", "oad_sizing_wing_imposed_in.xml")

# %%

api.variable_viewer(input_file, editable=True)

# %%
problem = api.evaluate_problem(WING_IMPOSED_CONFIGURATION_FILE, overwrite=True)

# %%
api.variable_viewer(problem.output_file_path, editable=True)

# %%

plot_results(WING_IMPOSED_CSV_FILE)

# %%

mass_breakdown_sun_plot(problem.output_file_path)

# %%

fig = wing_geometry_plot(problem.output_file_path, name="A321 CEO WV00 SKL")
fig = wing_geometry_plot(
    pth.join(ref_mission, "outputs", "oad_sizing_out.xml"), name="A321 CEO WV00", fig=fig
)
fig.show()

# %%

fig = aircraft_geometry_plot(problem.output_file_path, name="A321 CEO WV00 SKL")
fig = aircraft_geometry_plot(
    pth.join(ref_mission, "outputs", "oad_sizing_out.xml"), name="A321 CEO WV00", fig=fig
)
fig.show()
