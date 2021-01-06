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
<img src="../../img/CeRAS_report/CeRAS_bucket_curve.jpg" width="600">
"""


# %%
CeRAS_REF_DIR = pth.join(pth.pardir, pth.pardir, "CeRAS_ref")
CeRAS_INPUT_FILE = pth.join(pth.pardir, pth.pardir, "reference_data.xml")
SIZING_MISSION_WORK_FOLDER_PATH = "missionStudy_R5093_PL13608"
SIZING_MISSION_REPLAY_CONFIGURATION_FILE = pth.join(
    SIZING_MISSION_WORK_FOLDER_PATH, "mission_replay.toml"
)
SIZING_MISSION_FUEL_SIZING_CONFIGURATION_FILE = pth.join(
    SIZING_MISSION_WORK_FOLDER_PATH, "fuel_sizing.toml"
)
SIZING_MISSION_REPLAY_CSV_FILE = pth.join(
    SIZING_MISSION_WORK_FOLDER_PATH, "outputs", "mission_replay.csv"
)
SIZING_MISSION_FUEL_SIZING_CSV_FILE = pth.join(
    SIZING_MISSION_WORK_FOLDER_PATH, "outputs", "fuel_sizing.csv"
)


# For having log messages on screen
logging.basicConfig(level=logging.INFO, format="%(levelname)-8s: %(message)s")

# # For using all screen width
# from IPython.core.display import display, HTML
# display(HTML("<style>.container { width:95% !important; }</style>"))

# %%
sizing_mission_input_file = api.generate_inputs(
    SIZING_MISSION_REPLAY_CONFIGURATION_FILE, CeRAS_INPUT_FILE, overwrite=True
)
api.variable_viewer(sizing_mission_input_file, editable=False)

# %%
sizing_mission_problem = api.evaluate_problem(
    SIZING_MISSION_REPLAY_CONFIGURATION_FILE, overwrite=True
)

# %%
api.variable_viewer(sizing_mission_problem.output_file_path, editable=False)


# %%
CL_cruise = sizing_mission_problem["data:aerodynamics:aircraft:cruise:CL"]
CD_cruise = sizing_mission_problem["data:aerodynamics:aircraft:cruise:CD"]
CD0_cruise = sizing_mission_problem["data:aerodynamics:aircraft:cruise:CD0"]
CDi_cruise = (
    sizing_mission_problem["data:aerodynamics:aircraft:cruise:induced_drag_coefficient"]
    * CL_cruise ** 2
    * sizing_mission_problem["tuning:aerodynamics:aircraft:cruise:CD:winglet_effect:k"]
)
CDc_cruise = sizing_mission_problem["data:aerodynamics:aircraft:cruise:CD:compressibility"]
CDtrim_cruise = sizing_mission_problem["data:aerodynamics:aircraft:cruise:CD:trim"]
CDwing_cruise = sizing_mission_problem["data:aerodynamics:wing:cruise:CD0"]
CDfuselage_cruise = sizing_mission_problem["data:aerodynamics:fuselage:cruise:CD0"]

fig = make_subplots(rows=1, cols=2)
fig.add_trace(go.Scatter(x=CD_cruise, y=CL_cruise, name="Drag polar at Mach 0.78"), col=1, row=1)
fig.add_trace(go.Scatter(x=CD0_cruise, y=CL_cruise, name="CD0 polar at Mach 0.78"), col=1, row=1)
fig.add_trace(go.Scatter(x=CDi_cruise, y=CL_cruise, name="CDi polar at Mach 0.78"), col=1, row=1)
fig.add_trace(go.Scatter(x=CDc_cruise, y=CL_cruise, name="CDc polar at Mach 0.78"), col=1, row=1)
fig.add_trace(
    go.Scatter(x=CDtrim_cruise, y=CL_cruise, name="CDtrim polar at Mach 0.78"), col=1, row=1
)
fig.add_trace(
    go.Scatter(x=CDwing_cruise, y=CL_cruise, name="CD wing polar at Mach 0.78"), col=1, row=1
)
fig.add_trace(
    go.Scatter(x=CDfuselage_cruise, y=CL_cruise, name="CD fuselage polar at Mach 0.78"),
    col=1,
    row=1,
)


fig.add_trace(
    go.Scatter(x=CL_cruise, y=CL_cruise / CD_cruise, name="L/D polar at Mach 0.78"), col=2, row=1
)
fig.update_xaxes(title_text="CD", range=[0, 0.1], col=1, row=1)
fig.update_yaxes(title_text="CL", range=[-0.3, 1.2], col=1, row=1)
fig.update_xaxes(title_text="CL", range=[0, 1.2], col=2, row=1)
fig.update_yaxes(title_text="L/D", range=[4, 20], col=2, row=1)
fig.show()


# %%
"""
#### From CeRAS_CSR-01_report.pdf
<img src="../../img/CeRAS_report/polars.png" width="600">
"""


# %%
def read_ceras_df(csv_file_path):
    df = pd.read_csv(csv_file_path, sep=";", index_col=False,)

    df.rename(
        columns={
            "(1) Time [s]": "time",
            " (2) Range [m]": "ground_distance",
            " (3) alt [m]": "altitude",
            " (4) TAS [m/s]": "true_airspeed",
            " (5) CAS [m/s]": "calibrated_airspeed",
            " (6) m [kg]": "mass",
            " (7) Fuel consumed [kg]": "fuel",
            " (8) Thrust [kN]": "thrust",
            " (9) Fuelflow [kg/s]": "fuel_flow",
            " (10) TAS [kts]": "tas_knots",
            " (11) Mach [-]": "mach",
            " (12) FL [100 ft]": "flight_level",
            " (13) ROC [fpm]": "climb_rate",
            " (14) CA [-]": "CL",
            " (15) SAR [m/kg]": "SAR",
            " (16) bleed [kg/s]": "bleed",
            " (17) shaftPowerOfftake [kW]": "offtake",
            " (18) CO2 [kg/s]": "CO2",
            " (19) NOX [kg/s]": "NOX",
        },
        inplace=True,
    )
    df.thrust *= 1000.0
    return df


# %%
sizing_mission_df = pd.read_csv(SIZING_MISSION_REPLAY_CSV_FILE)
ref_sizing_mission_df = read_ceras_df(
    pth.join(CeRAS_REF_DIR, "CSR-01_missionStudy_R5093_PL13608_out.csv")
)

for df in [sizing_mission_df, ref_sizing_mission_df]:
    df.altitude /= foot
    df.ground_distance /= nautical_mile

fig = make_subplots(specs=[[{"secondary_y": True}]])
for df, name in zip([sizing_mission_df, ref_sizing_mission_df], ["FAST-OAD", "CeRAS ref"]):
    fig.add_trace(
        go.Scatter(
            x=df["ground_distance"], y=df["altitude"], name="[%s] altitude vs distance" % name
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df["ground_distance"],
            y=df["CL"],
            name="[%s] CL vs distance" % name,
            line=dict(dash="dot"),
        ),
        secondary_y=True,
    )
fig.update_xaxes(range=[-30, 2800.0])
fig.update_yaxes(title_text="Altitude [ft]", range=[0, 40000.0], secondary_y=False)
fig.update_yaxes(title_text="CL", range=[0.3, 0.8], secondary_y=True)
fig.update_layout(margin=dict(l=300, r=280, t=20, b=0), width=1000, height=250)
fig.show()

fig = make_subplots(specs=[[{"secondary_y": True}]])
for df, name in zip([sizing_mission_df, ref_sizing_mission_df], ["FAST-OAD", "CeRAS ref"]):
    fig.add_trace(
        go.Scatter(x=df["ground_distance"], y=df["thrust"], name="[%s] thrust vs distance" % name),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df["ground_distance"],
            y=df["mass"].iloc[0] - df["mass"],
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
sizing_mission_input_file = api.generate_inputs(
    SIZING_MISSION_FUEL_SIZING_CONFIGURATION_FILE, CeRAS_INPUT_FILE, overwrite=True
)
api.variable_viewer(sizing_mission_input_file, editable=False)

# %%
sizing_mission_problem = api.evaluate_problem(
    SIZING_MISSION_FUEL_SIZING_CONFIGURATION_FILE, overwrite=True
)

# %%
vars = VariableIO(sizing_mission_problem.output_file_path).read()
print(vars["data:mission:sizing:TOW"])

# %%
api.variable_viewer(sizing_mission_problem.output_file_path, editable=False)

# %%
sizing_mission_df = pd.read_csv(SIZING_MISSION_FUEL_SIZING_CSV_FILE)
ref_sizing_mission_df = read_ceras_df(
    pth.join(CeRAS_REF_DIR, "CSR-01_missionStudy_R5093_PL13608_out.csv")
)

for df in [sizing_mission_df, ref_sizing_mission_df]:
    df.altitude /= foot
    df.ground_distance /= nautical_mile

fig = make_subplots(specs=[[{"secondary_y": True}]])
for df, name in zip([sizing_mission_df, ref_sizing_mission_df], ["FAST-OAD", "CeRAS ref"]):
    fig.add_trace(
        go.Scatter(
            x=df["ground_distance"], y=df["altitude"], name="[%s] altitude vs distance" % name
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df["ground_distance"],
            y=df["CL"],
            name="[%s] CL vs distance" % name,
            line=dict(dash="dot"),
        ),
        secondary_y=True,
    )
fig.update_xaxes(range=[-30, 2800.0])
fig.update_yaxes(title_text="Altitude [ft]", range=[0, 40000.0], secondary_y=False)
fig.update_yaxes(title_text="CL", range=[0.3, 0.8], secondary_y=True)
fig.update_layout(margin=dict(l=300, r=280, t=20, b=0), width=1000, height=250)
fig.show()


fig = make_subplots(specs=[[{"secondary_y": True}]])
for df, name in zip([sizing_mission_df, ref_sizing_mission_df], ["FAST-OAD", "CeRAS ref"]):
    fig.add_trace(
        go.Scatter(x=df["ground_distance"], y=df["thrust"], name="[%s] thrust vs distance" % name),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df["ground_distance"],
            y=df["mass"].iloc[0] - df["mass"],
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
