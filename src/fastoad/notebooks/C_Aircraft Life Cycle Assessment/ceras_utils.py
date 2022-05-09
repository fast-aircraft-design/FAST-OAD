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


import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.constants import foot, nautical_mile


def read_ceras_df(csv_file_path):
    df = pd.read_csv(csv_file_path, sep=";", index_col=False)

    df.rename(
        columns={
            "(1) Time [s]": "time [s]",
            " (2) Range [m]": "ground_distance [m]",
            " (3) alt [m]": "altitude [m]",
            " (4) TAS [m/s]": "true_airspeed [m/s]",
            " (5) CAS [m/s]": "calibrated_airspeed [m/s]",
            " (6) m [kg]": "mass [kg]",
            " (7) Fuel consumed [kg]": "fuel [kg]",
            " (8) Thrust [kN]": "thrust [kN]",
            " (9) Fuelflow [kg/s]": "fuel_flow [kg/s]",
            " (10) TAS [kts]": "tas_knots [kts]",
            " (11) Mach [-]": "mach [-]",
            " (12) FL [100 ft]": "flight_level",
            " (13) ROC [fpm]": "climb_rate [ft/m]",
            " (14) CA [-]": "CL [-]",
            " (15) SAR [m/kg]": "SAR [m/kg]",
            " (16) bleed [kg/s]": "bleed [kg/s]",
            " (17) shaftPowerOfftake [kW]": "offtake [kW]",
            " (18) CO2 [kg/s]": "CO2 [kg/s]",
            " (19) NOX [kg/s]": "NOX [kg/s]",
        },
        inplace=True,
    )
    df["thrust [N]"] = df["thrust [kN]"] * 1000.0
    return df


def plot_mission_against_ceras(fastoad_csv_path, ceras_csv_path):
    fastoad_df = pd.read_csv(fastoad_csv_path)
    ref_df = read_ceras_df(ceras_csv_path)

    for df in [fastoad_df, ref_df]:
        df["altitude [ft]"] = df["altitude [m]"] / foot
        df["ground_distance [NM]"] = df["ground_distance [m]"] / nautical_mile

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    for df, name in zip([fastoad_df, ref_df], ["FAST-OAD", "CeRAS ref"]):
        fig.add_trace(
            go.Scatter(
                x=df["ground_distance [NM]"],
                y=df["altitude [ft]"],
                name="[%s] altitude vs distance" % name,
            ),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(
                x=df["ground_distance [NM]"],
                y=df["CL [-]"],
                name="[%s] CL vs distance" % name,
                line=dict(dash="dot"),
            ),
            secondary_y=True,
        )
    fig.update_yaxes(title_text="Altitude [ft]", range=[0, 40000.0], secondary_y=False)
    fig.update_yaxes(title_text="CL", range=[0.3, 0.8], secondary_y=True)
    fig.update_layout(margin=dict(l=300, r=280, t=20, b=0), width=1000, height=250)
    fig.show()

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    for df, name in zip([fastoad_df, ref_df], ["FAST-OAD", "CeRAS ref"]):
        fig.add_trace(
            go.Scatter(
                x=df["ground_distance [NM]"],
                y=df["thrust [N]"],
                name="[%s] thrust vs distance" % name,
            ),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(
                x=df["ground_distance [NM]"],
                y=df["mass [kg]"].iloc[0] - df["mass [kg]"],
                name="[%s] fuel vs distance" % name,
                line=dict(dash="dot"),
            ),
            secondary_y=True,
        )
    fig.update_xaxes(title_text="Range [NM]")
    fig.update_yaxes(title_text="Thrust [N]", range=[0, 300000.0], secondary_y=False)
    fig.update_yaxes(title_text="Block fuel [kg]", range=[0.0, 21000.0], secondary_y=True)
    fig.update_layout(margin=dict(l=300, r=280, t=0, b=20), width=1000, height=250)
    fig.show()
