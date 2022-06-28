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
    ratio = variables["data:performance:thrust_diagram:iso_rating_thrust:ratio_F_F0"].value
    #ratio = np.transpose(ratio)
    ratio_0 = ratio[0]
    ratio_10000 = ratio[1]
    ratio_20000 = ratio[2]
    ratio_30000 = ratio[3]
    ratio_40000 = ratio[4]

    ceiling_mtow = float(variables["data:performance:ceiling:MTOW"].value[0])
    ceiling_mzfw = float(variables["data:performance:ceiling:MZFW"].value[0])
    initial_thrust = float(variables["data:propulsion:MTO_thrust"].value[0])
    cruise_mach = float(variables["data:TLAR:cruise_mach"].value[0])
    maximum_engine_mach = float(variables["data:propulsion:rubber_engine:maximum_mach"].value[0])

    initial_thrust = 2*initial_thrust
    diving_mach = 0.07 + cruise_mach
    maximum_mach = np.maximum(cruise_mach, np.maximum(diving_mach, maximum_engine_mach))

    # Altitude vectors
    mach_vector = np.linspace(0, maximum_mach, 50)
    altitude_vector_mtow = np.linspace(0, ceiling_mtow, 45)  # feet
    altitude_extra = np.linspace(ceiling_mtow, ceiling_mzfw, 6)
    altitude_vector_mzfw = np.append(altitude_vector_mtow, altitude_extra)  # feet

    # Plot the results
    fig = go.Figure() # Iso rating thrust
    fig2 = go.Figure() # Iso altitude thrust

    scatter_0_ft = go.Scatter(
        x=mach_vector,
        y=ratio_0,
        legendgroup="group",
        legendgrouptitle_text="Altitude (ft)",
        line=dict(color="blue", width=1.5),
        mode="lines",
        name="0",
    )  # Altitude-Speed line for MTOW
    scatter_10000_ft = go.Scatter(
        x=mach_vector,
        y=ratio_10000,
        legendgroup="group",
        line=dict(color="red", width=1.5),
        mode="lines",
        name="10000",
    )  # Altitude-Speed line for MTOW
    scatter_20000_ft = go.Scatter(
        x=mach_vector,
        y=ratio_20000,
        legendgroup="group",
        line=dict(color="green", width=1.5),
        mode="lines",
        name="20000",
    )  # Altitude-Speed line for MTOW
    scatter_30000_ft = go.Scatter(
        x=mach_vector,
        y=ratio_30000,
        legendgroup="group",
        line=dict(color="black", width=1.5),
        mode="lines",
        name="30000",
    )  # Altitude-Speed line for MTOW
    scatter_40000_ft = go.Scatter(
        x=mach_vector,
        y=ratio_40000,
        legendgroup="group",
        line=dict(color="goldenrod", width=1.5),
        mode="lines",
        name="40000",
    )  # Altitude-Speed line for MTOW

    fig.add_trace(scatter_0_ft)
    fig.add_trace(scatter_10000_ft)
    fig.add_trace(scatter_20000_ft)
    fig.add_trace(scatter_30000_ft)
    fig.add_trace(scatter_40000_ft)

    fig = go.FigureWidget(fig)
    fig.update_layout(
        height=700,
        width=900,
        title_text="Thrust at rating 100%    F0 = " + str(initial_thrust/1000) + " kN",
        title_x=0.5,
        yaxis_title="F/F0 [-]",
        xaxis_title="Mach [-]",
    )

    fig2.add_trace(scatter_0_ft)
    fig2.add_trace(scatter_10000_ft)

    fig2 = go.FigureWidget(fig2)
    fig2.update_layout(
        height=700,
        width=900,
        title_text="Thrust at 0 ft    F0 = " + str(initial_thrust / 1000) + " kN",
        title_x=0.5,
        yaxis_title="F/F0 [-]",
        xaxis_title="Mach [-]",
    )
    return fig, fig2


    #scatter_v_computed_vector_mzfw = go.Scatter(
    #    x=v_computed_vector_mzfw,
    #    y=altitude_vector_mzfw,
    #    legendgroup="group2",
    #    mode="markers",
    #    marker_symbol="circle",
    #    marker_color="dodgerblue",
    #    marker_size=4.6,
    #    name="v_MZFW",
    #   visible = "legendonly",
    #)  # Altitude-Speed line for v_computed_mzfw