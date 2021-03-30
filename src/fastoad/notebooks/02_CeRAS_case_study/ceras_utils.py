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
from scipy.constants import foot
from scipy.constants import nautical_mile


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


def plot_mission_against_ceras(fastoad_csv_path, ceras_csv_path):
    fastoad_df = pd.read_csv(fastoad_csv_path)
    ref_df = read_ceras_df(ceras_csv_path)

    for df in [fastoad_df, ref_df]:
        df.altitude /= foot
        df.ground_distance /= nautical_mile

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    for df, name in zip([fastoad_df, ref_df], ["FAST-OAD", "CeRAS ref"]):
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
    fig.update_yaxes(title_text="Altitude [ft]", range=[0, 40000.0], secondary_y=False)
    fig.update_yaxes(title_text="CL", range=[0.3, 0.8], secondary_y=True)
    fig.update_layout(margin=dict(l=300, r=280, t=20, b=0), width=1000, height=250)
    fig.show()

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    for df, name in zip([fastoad_df, ref_df], ["FAST-OAD", "CeRAS ref"]):
        fig.add_trace(
            go.Scatter(
                x=df["ground_distance"], y=df["thrust"], name="[%s] thrust vs distance" % name
            ),
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
    fig.update_xaxes(title_text="Range [nm]")
    fig.update_yaxes(title_text="Thrust [N]", range=[0, 300000.0], secondary_y=False)
    fig.update_yaxes(title_text="Block fuel [kg]", range=[0.0, 21000.0], secondary_y=True)
    fig.update_layout(margin=dict(l=300, r=280, t=0, b=20), width=1000, height=250)
    fig.show()
