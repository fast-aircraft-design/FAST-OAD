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
from scipy.interpolate import interp1d


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
    mass_vector = variables["data:performance:ceiling_mass_diagram:mass"].value
    alti_buffeting = variables["data:performance:ceiling_mass_diagram:altitude:buffeting"].value
    alti_climb = variables["data:performance:ceiling_mass_diagram:altitude:climb"].value
    alti_cruise = variables["data:performance:ceiling_mass_diagram:altitude:cruise"].value
    mtow = float(variables["data:weight:aircraft:MTOW"].value[0])

    # Compute the ceiling values
    alti_ceiling = []
    mass_ceiling = []
    alti_minimum = np.minimum(np.minimum(alti_cruise, alti_climb), alti_buffeting)
    alti_mtow = float(interp1d(mass_vector, alti_minimum)(mtow))
    alti_ceiling.append(alti_mtow)
    mass_ceiling.append(mtow)
    alti_link_ceiling = []
    mass_link_ceiling = []
    alti_link_ceiling.append(alti_mtow)
    mass_link_ceiling.append(mtow)

    alti_iter = alti_mtow + 2000
    i = 0
    while alti_iter <= alti_minimum[0]:
        alti_ceiling.append(alti_iter)
        mass_ceiling.append(float(interp1d(alti_minimum, mass_vector)(alti_iter)))

        alti_link_ceiling.append(alti_ceiling[i])
        alti_link_ceiling.append(alti_ceiling[i + 1])

        mass_link_ceiling.append(mass_ceiling[i + 1])
        mass_link_ceiling.append(mass_ceiling[i + 1])

        i += 1
        alti_iter = alti_iter + 2000

    # Plot the results
    fig = go.Figure()

    scatter_buffeting = go.Scatter(
        x=mass_vector,
        y=alti_buffeting,
        line=dict(
            color="#636efa",
        ),
        mode="lines",
        name="Buffeting",
    )  # Ceiling mass Line for buffeting
    scatter_climb = go.Scatter(
        x=mass_vector,
        y=alti_climb,
        line=dict(
            color="#ef553b",
        ),
        mode="lines",
        name="Climb",
    )  # Ceiling mass Line for climb
    scatter_cruise = go.Scatter(
        x=mass_vector,
        y=alti_cruise,
        line=dict(
            color="#00cc96",
        ),
        mode="lines",
        name="Cruise",
    )  # Ceiling mass Line for cruise
    scatter_ceiling = go.Scatter(
        x=mass_ceiling,
        y=alti_ceiling,
        line=dict(
            color="black",
        ),
        mode="markers",
        name="Flight level",
    )  # Ceiling mass Line for ceiling level
    # scatter_link_ceiling = go.Scatter(
    #    x=[mass_ceiling[0], mass_ceiling[1], mass_ceiling[1], mass_ceiling[2], mass_ceiling[2]],
    #    y=[alti_ceiling[0], alti_ceiling[0], alti_ceiling[1], alti_ceiling[1], alti_ceiling[2]],
    #    line=dict(
    #        color="black", dash="dash", width=1,
    #    ),
    #    mode="lines",
    #    name="Flight path",
    # )  # Ceiling mass Line for ceiling level
    scatter_link_ceiling = go.Scatter(
        x=mass_link_ceiling,
        y=alti_link_ceiling,
        line=dict(
            color="black",
            dash="dash",
            width=1,
        ),
        mode="lines",
        name="Flight path",
    )  # Ceiling mass Line for ceiling level

    fig.add_trace(scatter_buffeting)
    fig.add_trace(scatter_climb)
    fig.add_trace(scatter_cruise)
    fig.add_trace(scatter_ceiling)
    fig.add_trace(scatter_link_ceiling)

    fig = go.FigureWidget(fig)
    fig.update_layout(
        height=700,
        title_text="Ceiling-Mass diagram",
        title_x=0.5,
        xaxis_title="Mass [kg]",
        yaxis_title="Altitude [ft]",
    )
    return fig
