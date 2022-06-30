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

import plotly.graph_objects as go
from fastoad.io import VariableIO


def available_power_diagram_drawing_plot(
    aircraft_file_path: str, name=None, fig=None, file_formatter=None
) -> go.FigureWidget:
    """
    Returns a figure plot of the available power diagram of the aircraft.
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
    v_vector_sea = variables[
        "data:performance:available_power_diagram:sea_level:speed_vector"
    ].value
    v_vector_cruise = variables[
        "data:performance:available_power_diagram:cruise_altitude:speed_vector"
    ].value
    power_required_sea = variables[
        "data:performance:available_power_diagram:sea_level:power_required"
    ].value
    power_available_sea = variables[
        "data:performance:available_power_diagram:sea_level:power_available"
    ].value
    power_required_cruise = variables[
        "data:performance:available_power_diagram:cruise_altitude:power_required"
    ].value
    power_available_cruise = variables[
        "data:performance:available_power_diagram:cruise_altitude:power_available"
    ].value
    cruise_altitude = float(variables["data:mission:sizing:main_route:cruise:altitude"].value[0])

    start_cruise = 0
    start_sea = 0

    i = 0
    while power_required_sea[i] > power_available_sea[i]:
        start_sea = i
        i = i + 1

    j = 0
    while power_required_cruise[j] > power_available_cruise[j]:
        start_cruise = j
        j = j + 1

    v_vector_sea = v_vector_sea[start_sea:]
    power_required_sea = power_required_sea[start_sea:]
    power_available_sea = power_available_sea[start_sea:]
    v_vector_cruise = v_vector_cruise[start_cruise:]
    power_required_cruise = power_required_cruise[start_cruise:]
    power_available_cruise = power_available_cruise[start_cruise:]

    # Plot the results
    fig = go.Figure()

    scatter_power_available_sea = go.Scatter(
        x=v_vector_sea,
        y=power_available_sea,
        legendgroup="group",
        legendgrouptitle_text="Sea level",
        line=dict(
            color="#636efa",
        ),
        mode="lines",
        name="Available Power",
    )
    scatter_power_required_sea = go.Scatter(
        x=v_vector_sea,
        y=power_required_sea,
        legendgroup="group",
        line=dict(
            color="#ef553b",
        ),
        mode="lines",
        name="Required Power",
    )
    scatter_power_available_cruise_altitude = go.Scatter(
        x=v_vector_cruise,
        y=power_available_cruise,
        legendgroup="group2",
        legendgrouptitle_text="Cruise altitude at %i m" % int(cruise_altitude),
        line=dict(
            color="#0d2a63",
        ),
        mode="lines",
        name="Available Power",
        visible="legendonly",
    )
    scatter_power_required_cruise_altitude = go.Scatter(
        x=v_vector_cruise,
        y=power_required_cruise,
        legendgroup="group2",
        line=dict(
            color="#af0038",
        ),
        mode="lines",
        name="Required Power",
        visible="legendonly",
    )

    fig.add_trace(scatter_power_available_sea)
    fig.add_trace(scatter_power_required_sea)
    fig.add_trace(scatter_power_available_cruise_altitude)
    fig.add_trace(scatter_power_required_cruise_altitude)

    fig = go.FigureWidget(fig)
    fig.update_layout(
        height=700,
        width=700,
        title_text="Available Power Diagram",
        title_x=0.5,
        xaxis_title="Speed [m/s]",
        yaxis_title="Power [W]",
    )
    return fig
