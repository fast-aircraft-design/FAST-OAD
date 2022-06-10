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
import plotly
import plotly.graph_objects as go
import pandas as pd
from ipywidgets import widgets, HBox
from IPython.display import display


from fastoad.io import VariableIO
from scipy.interpolate import interp1d


def available_power_diagram_drawing_plot(
    aircraft_file_path: str, name=None, fig=None, file_formatter=None
) -> go.FigureWidget:
    """
    Returns a figure plot of the ceiling_mass diagram of the aircraft.
    Different designs can be superposed by providing an existing fig.
    Each design can be provided a name.

    :param aircraft_file_path: path of data file
    :param name: name to give to the trace added to the figure
    :param fig: existing figure to which add the plot
    :param file_formatter: the formatter that defines the format of data file. If not provided,
                           default format will be assumed.
    :return: wing plot figure
    """
    variables = VariableIO(aircraft_file_path, file_formatter).read()

    # Diagram parameters
    v_vector_sea = variables["data:performance:available_power_diagram:sea_level:speed_vector"].value
    v_vector_cruise_altitude = variables["data:performance:available_power_diagram:cruise_altitude:speed_vector"].value
    power_available_sea = variables["data:performance:available_power_diagram:sea_level:power_available"].value
    power_max_sea = variables["data:performance:available_power_diagram:sea_level:power_max"].value
    power_available_cruise = variables["data:performance:available_power_diagram:cruise_altitude:power_available"].value
    power_max_cruise= variables["data:performance:available_power_diagram:cruise_altitude:power_max"].value
    cruise_altitude = float(variables["data:mission:sizing:main_route:cruise:altitude"].value[0])

    # Plot the results
    fig = go.Figure()

    scatter_thrust_max_sea = go.Scatter(
        x=v_vector_sea,
        y=power_max_sea,
        legendgroup="group",
        legendgrouptitle_text="Sea level",
        line=dict(
            color="#636efa",
        ),
        mode="lines",
        name="Max Power",
    )
    scatter_thrust_available_sea = go.Scatter(
        x=v_vector_sea,
        y=power_available_sea,
        legendgroup="group",
        line=dict(
            color="#ef553b",
        ),
        mode="lines",
        name="Available Power",
    )
    scatter_thrust_max_cruise_altitude = go.Scatter(
        x=v_vector_cruise_altitude,
        y=power_max_cruise,
        legendgroup="group2",
        legendgrouptitle_text="Cruise altitude at %i m"%int(cruise_altitude),
        line=dict(
            color="#0d2a63",
        ),
        mode="lines",
        name="Max Power",
        visible="legendonly",
    )
    scatter_thrust_available_cruise_altitude = go.Scatter(
        x=v_vector_cruise_altitude,
        y=power_available_cruise,
        legendgroup="group2",
        line=dict(
            color="#af0038",
        ),
        mode="lines",
        name="Available Power",
        visible="legendonly",
    )

    fig.add_trace(scatter_thrust_max_sea)
    fig.add_trace(scatter_thrust_available_sea)
    fig.add_trace(scatter_thrust_max_cruise_altitude)
    fig.add_trace(scatter_thrust_available_cruise_altitude)

    # Creating the table with all the lengths of the variables
    d = {
        "Variable": [
            "X0 (m)",
            "X1 (m)",
            "X2 (m)",
            "Y0 (m)",
            "Y1 (m)",
            "Y2 (m)",
            "Y3 (m)",
            "L0 (m)",
            "L1 (m)",
            "L2 (m)",
            "L3 (m)",
            "MAC (m)",
            "Span (m)",
            "Wing surface (m²)",
        ],
        "Value": [
            3,  # X0
            3,  # X1
            3,  # X2
            3,  # Y0
            3,  # Y1
            3,  # Y2
            3,  # Y3
            3,  # L0
            3,  # L1
            3,  # L2
            3,  # L3
            3,  # MAC
            3,  # Span
            3,  # Wing surface
        ],
    }

    df = pd.DataFrame(data=d)
    out = widgets.Output()
    with out:
        display(df)

    fig = go.FigureWidget(fig)
    fig.update_layout(
        height=700,
        width=700,
        title_text="Available power diagram",
        title_x=0.5,
        xaxis_title="Speed [m/s]",
        yaxis_title="Power [MW]",
    )
    return widgets.HBox([fig, out])