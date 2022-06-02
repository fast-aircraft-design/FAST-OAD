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


from fastoad.io import VariableIO


def ceiling_mass_diagram_drawing_plot(
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
    v_min_mtow = variables["data:performance:speed_altitude_diagram:MTOW:v_min"].value
    v_max_mtow = variables["data:performance:speed_altitude_diagram:MTOW:v_max"].value
    v_computed_vector_mtow = variables[
        "data:performance:speed_altitude_diagram:MTOW:v_computed"
    ].value
    v_dive_mtow = variables["data:performance:speed_altitude_diagram:MTOW:v_dive"].value
    v_engine_mtow = variables["data:performance:speed_altitude_diagram:MTOW:v_engine"].value

    v_min_mzfw = variables["data:performance:speed_altitude_diagram:MZFW:v_min"].value
    v_max_mzfw = variables["data:performance:speed_altitude_diagram:MZFW:v_max"].value
    v_computed_vector_mzfw = variables[
        "data:performance:speed_altitude_diagram:MZFW:v_computed"
    ].value
    v_dive_mzfw = variables["data:performance:speed_altitude_diagram:MZFW:v_dive"].value
    v_engine_mzfw = variables["data:performance:speed_altitude_diagram:MZFW:v_engine"].value

    ceiling_mtow = float(variables["data:performance:ceiling:MTOW"].value[0])
    ceiling_mzfw = float(variables["data:performance:ceiling:MZFW"].value[0])


    # Plot the results
    fig = go.Figure()

    scatter_final_mtow = go.Scatter(
        x=v_final_mtow,
        y=altitude_final_mtow,
        legendgroup="group",
        legendgrouptitle_text="MTOW",
        line=dict(color="royalblue", width=4),
        mode="lines",
        name="MTOW : Ceiling at %i ft" % ceiling_mtow,
        visible="legendonly",
    )  # Altitude-Speed line for MTOW


    fig.add_trace(scatter_final_mzfw)

    fig = go.FigureWidget(fig)
    fig.update_layout(
        height=700,
        title_text="Altitude-Speed diagram",
        title_x=0.5,
        xaxis_title="Speed [m/s]",
        yaxis_title="Altitude [ft]",
    )
    return fig
