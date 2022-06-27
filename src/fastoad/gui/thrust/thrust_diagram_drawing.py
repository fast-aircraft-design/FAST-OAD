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

COLS = plotly.colors.DEFAULT_PLOTLY_COLORS


def thrust_diagram_drawing_plot(
    aircraft_file_path: str, name=None, fig=None, file_formatter=None
) -> go.FigureWidget:
    """
    Returns a figure plot of the thrust for the aircraft.
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

    ceiling_mtow = float(variables["data:performance:ceiling:MTOW"].value[0])
    ceiling_mzfw = float(variables["data:performance:ceiling:MZFW"].value[0])

    # Altitude vectors
    altitude_vector_mtow = np.linspace(0, ceiling_mtow, 45)  # feet
    altitude_extra = np.linspace(ceiling_mtow, ceiling_mzfw, 6)
    altitude_vector_mzfw = np.append(altitude_vector_mtow, altitude_extra)  # feet

    # Plot the results
    fig = go.Figure()

    #scatter_final_mtow = go.Scatter(
    #    x=v_final_mtow,
    #    y=altitude_final_mtow,
    #    legendgroup="group",
    #    legendgrouptitle_text="MTOW",
    #    line=dict(color="royalblue", width=4),
    #    mode="lines",
    #    name="MTOW : Ceiling at %i ft" % ceiling_mtow,
    #    visible="legendonly",
    #)  # Altitude-Speed line for MTOW
    #
    #scatter_v_computed_vector_mzfw = go.Scatter(
    #    x=v_computed_vector_mzfw,
    #    y=altitude_vector_mzfw,
    #    legendgroup="group2",
    #    mode="markers",
    #    marker_symbol="circle",
    #    marker_color="dodgerblue",
    #    marker_size=4.6,
    #    name="v_MZFW",
    #)  # Altitude-Speed line for v_computed_mzfw

    #fig.add_trace(scatter_v_computed_vector_mzfw)
    #fig.add_trace(scatter_final_mtow)

    fig = go.FigureWidget(fig)
    fig.update_layout(
        height=700,
        title_text="Altitude-Speed diagram",
        title_x=0.5,
        xaxis_title="Speed [m/s]",
        yaxis_title="Altitude [ft]",
    )
    return fig