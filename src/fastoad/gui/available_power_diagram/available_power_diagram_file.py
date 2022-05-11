"""
Defines the analysis and plotting functions for postprocessing
"""
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

from typing import Dict

import numpy as np
import plotly
import plotly.graph_objects as go
from openmdao.utils.units import convert_units
from plotly.subplots import make_subplots

from fastoad.io import VariableIO
from fastoad.openmdao.variables import VariableList

COLS = plotly.colors.DEFAULT_PLOTLY_COLORS

def TrialPlot(
    aircraft_file_path: str, name=None, fig=None, file_formatter=None
) -> go.FigureWidget:
    """
        Returns a figure plot of the available power and needed power as a function
        of the altitude et height
        Different designs can be superposed by providing an existing fig.
        Each design can be provided a name.

        :param aircraft_file_path: path of data file
        :param name: name to give to the trace added to the figure
        :param fig: existing figure to which add the plot
        :param file_formatter: the formatter that defines the format of data file. If not provided,
                               default format will be assumed.
        :return: available power plot figure
        """
    """
    x = np.linspace(-10, 20, 15)
    if fig is None:
        fig = go.Figure()
    
    scatter = go.Scatter(x=x, y=x**3, mode="lines+markers", name=name)
    fig.add_trace(scatter)
    fig = go.FigureWidget(fig)
    fig.update_layout(title_text="Test available_power_diagram_plot", title_x=0.5, xaxis_title="x", yaxis_title="y=x**3")
    """

    """
    # pylint: disable=invalid-name # that's a common naming
    cd = np.asarray(variables["data:aerodynamics:aircraft:cruise:CD"].value)
    # pylint: disable=invalid-name # that's a common naming
    cl = np.asarray(variables["data:aerodynamics:aircraft:cruise:CL"].value)

    # TODO: remove filtering one models provide proper bounds
    cd_short = cd[cd <= 2.0]
    cl_short = cl[cd <= 2.0]
    x = np.linspace(-10, 20, 15)

    if fig is None:
        fig = make_subplots(
            rows=1,
            cols=2,
            subplot_titles=("Drag Polar", "Test : y=x**3"),
        )
    fig.add_trace(go.Scatter(x=cd_short, y=cl_short, mode="lines+markers", name=name), row=1, col=1)
    fig.add_trace(go.Scatter(x=x, y=x**3, mode="lines+markers", name=name), row=1, col=2)
    #fig = go.FigureWidget(fig)
    #fig.update_layout(title_text="Drag Polar", title_x=0.5, xaxis_title="Cd", yaxis_title="Cl")
    """




    return fig

def available_power_diagram_plot(
    aircraft_file_path: str, name=None, fig=None, file_formatter=None
) -> go.FigureWidget:
    """
        Returns a figure plot of the top view of the wing with the control surfaces.
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

    wing_kink_leading_edge_x = variables["data:geometry:wing:kink:leading_edge:x:local"].value[0]
    wing_tip_leading_edge_x = variables["data:geometry:wing:tip:leading_edge:x:local"].value[0]
    wing_root_y = variables["data:geometry:wing:root:y"].value[0]
    wing_kink_y = variables["data:geometry:wing:kink:y"].value[0]
    wing_tip_y = variables["data:geometry:wing:tip:y"].value[0]
    wing_root_chord = variables["data:geometry:wing:root:chord"].value[0]
    wing_kink_chord = variables["data:geometry:wing:kink:chord"].value[0]
    wing_tip_chord = variables["data:geometry:wing:tip:chord"].value[0]

    mean_aerodynamic_chord = variables["data:geometry:wing:MAC:length"].value[0]
    mac25_x_position = variables["data:geometry:wing:MAC:at25percent:x"].value[0]
    distance_root_mac_chords = variables["data:geometry:wing:MAC:leading_edge:x:local"].value[0]
    # pylint: disable=invalid-name # that's a common naming
    y = np.array(
        [0, wing_root_y, wing_kink_y, wing_tip_y, wing_tip_y, wing_kink_y, wing_root_y, 0, 0]
    )
    # pylint: disable=invalid-name # that's a common naming
    y = np.concatenate((-y, y))

    # pylint: disable=invalid-name # that's a common naming
    x = np.array(
        [
            0,
            0,
            wing_kink_leading_edge_x,
            wing_tip_leading_edge_x,
            wing_tip_leading_edge_x + wing_tip_chord,
            wing_kink_leading_edge_x + wing_kink_chord,
            wing_root_chord,
            wing_root_chord,
            0,
        ]
    )

    #x = x + mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords
    # pylint: disable=invalid-name # that's a common naming
    #x = np.concatenate((x, x))

    if fig is None:
        fig = go.Figure()

    scatter = go.Scatter(x=y, y=x, mode="lines+markers", name=name)

    fig.add_trace(scatter)

    fig.layout = go.Layout(yaxis=dict(scaleanchor="x", scaleratio=1))

    fig = go.FigureWidget(fig)

    fig.update_layout(title_text="Wing Geometry", title_x=0.5, xaxis_title="y", yaxis_title="x")

    return fig