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
import plotly.graph_objects as go
from fastoad.io import VariableIO


def v_n_diagram_drawing_plot(
    aircraft_file_path: str, name=None, fig=None, file_formatter=None
) -> go.FigureWidget:
    """
    Returns a figure plot of the V-n diagram of the aircraft.
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
    v_vector = variables["data:performance:V-n_diagram:speed_vector"].value
    v_stall_equivalent = float(variables["data:performance:V-n_diagram:v_stall"].value[0])
    v_manoeuvre_equivalent = float(variables["data:performance:V-n_diagram:v_manoeuvre"].value[0])
    v_cruising_equivalent = float(variables["data:performance:V-n_diagram:v_cruising"].value[0])
    v_dive_equivalent = float(variables["data:performance:V-n_diagram:v_dive"].value[0])
    cruise_altitude = float(variables["data:mission:sizing:main_route:cruise:altitude"].value[0])

    # Plot the results
    fig = go.Figure()

    scatter_v_n = go.Scatter(
        x=v_vector,
        y=v_vector,
        legendgroup="group",
        legendgrouptitle_text="Sea level",
        line=dict(
            color="#636efa",
        ),
        mode="lines",
        name="V_n diagram",
    )

    fig.add_trace(scatter_v_n)
    fig.add_vline(
        x=v_stall_equivalent,
        line_width=2,
        line_dash="dash",
        line_color="#636efa",
        annotation_text="v_stall",
        annotation_position="top left",
    )
    fig.add_vline(
        x=v_manoeuvre_equivalent,
        line_width=2,
        line_dash="dash",
        line_color="#ef553b",
        annotation_text="v_manoeuvre",
        annotation_position="top left",
    )
    fig.add_vline(
        x=v_cruising_equivalent,
        line_width=2,
        line_dash="dash",
        line_color="#00cc96",
        annotation_text="v_cruising",
        annotation_position="top left",
    )
    fig.add_vline(
        x=v_dive_equivalent,
        line_width=2,
        line_dash="dash",
        line_color="#ab63fa",
        annotation_text="v_dive",
        annotation_position="top right",
    )

    fig = go.FigureWidget(fig)
    fig.update_layout(
        height=700,
        width=700,
        title_x=0.5,
        xaxis_title="Equivalent Air Speed [m/s]",
        yaxis_title="Load factor [-]",
    )
    return fig
