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
from fastoad.io import VariableIO
from fastoad.model_base import FlightPoint
import os.path as pth


def drag_distribution_plot(
    aircraft_file_path: str, name=None, fig=None, file_formatter=None
) -> go.FigureWidget:
    """
    Returns a figure plot of the drag distribution at a certain flight point
    Different designs can be superposed by providing an existing fig.
    Each design can be provided a name.

    :param aircraft_file_path: path of data file
    :param name: name to give to the trace added to the figure
    :param fig: existing figure to which add the plot
    :param file_formatter: the formatter that defines the format of data file. If not provided,
                           default format will be assumed.
    :return: sun distribution of the drag
    """
    variables = VariableIO(aircraft_file_path, file_formatter).read()



    if fig is None:
        fig = go.Figure()

    x = [1,2,3,4,5]
    y = [1,2,3,4,5]

    scatter = go.Scatter(
        x=y, y=x, line=dict(color="blue"), mode="lines", name=name, showlegend=False
    )

    fig.layout = go.Layout(yaxis=dict(scaleanchor="x", scaleratio=1))

    fig.add_trace(scatter)

    fig = go.FigureWidget(fig)
    fig.update_xaxes(constrain="domain")
    fig.update_yaxes(constrain="domain")
    fig.update_layout(title_text="Drag coefficient distribution", title_x=0.5, xaxis_title="y", yaxis_title="x")

    return fig




