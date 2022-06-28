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
    sfc = variables["data:performance:thrust_diagram:iso_rating_consumption:SFC"].value

    #ratio = np.transpose(ratio)
    ratio_0 = ratio[0]
    ratio_10000 = ratio[1]
    ratio_20000 = ratio[2]
    ratio_30000 = ratio[3]
    ratio_40000 = ratio[4]

    ratio_0_max_to = ratio[0]
    ratio_0_max_cl = [float(x)*0.95 for x in ratio[0]]
    ratio_0_max_cr = [float(x)*0.93 for x in ratio[0]]
    ratio_0_idle = [float(x)*0.35 for x in ratio[0]]

    sfc_0 = [float(x)*36000 for x in sfc[0]]
    sfc_10000 = [float(x)*36000 for x in sfc[1]]
    sfc_20000 = [float(x)*36000 for x in sfc[2]]
    sfc_30000 = [float(x)*36000 for x in sfc[3]]
    sfc_40000 = [float(x)*36000 for x in sfc[4]]

    sfc_0_max_to = [float(x) * 36000 for x in sfc[0]]
    sfc_0_max_cl = [float(x) * 36000 * 1.01 for x in sfc[0]]
    sfc_0_max_cr = [float(x) * 36000 * 1.03 for x in sfc[0]]
    sfc_0_idle = [float(x) * 36000 * 1.75 for x in sfc[0]]

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
    fig3 = go.Figure() # Iso rating consumption
    fig4 = go.Figure() # Iso rating consumption

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
        line=dict(color="red", width=1.5),
        mode="lines",
        name="10000",
    )  # Altitude-Speed line for MTOW
    scatter_20000_ft = go.Scatter(
        x=mach_vector,
        y=ratio_20000,
        line=dict(color="green", width=1.5),
        mode="lines",
        name="20000",
    )  # Altitude-Speed line for MTOW
    scatter_30000_ft = go.Scatter(
        x=mach_vector,
        y=ratio_30000,
        line=dict(color="black", width=1.5),
        mode="lines",
        name="30000",
    )  # Altitude-Speed line for MTOW
    scatter_40000_ft = go.Scatter(
        x=mach_vector,
        y=ratio_40000,
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


    scatter_0_ft_max_to = go.Scatter(
        x=mach_vector,
        y=ratio_0_max_to,
        legendgroup="group",
        legendgrouptitle_text="Régime",
        line=dict(color="blue", width=1.5),
        mode="lines",
        name="Max TO",
    )  # Altitude-Speed line for MTOW
    scatter_0_ft_max_cl = go.Scatter(
        x=mach_vector,
        y=ratio_0_max_cl,
        line=dict(color="red", width=1.5),
        mode="lines",
        name="Max CL",
    )  # Altitude-Speed line for MTOW
    scatter_0_ft_max_cr = go.Scatter(
        x=mach_vector,
        y=ratio_0_max_cr,
        line=dict(color="green", width=1.5),
        mode="lines",
        name="Max CR",
    )  # Altitude-Speed line for MTOW
    scatter_0_ft_idle = go.Scatter(
        x=mach_vector,
        y=ratio_0_idle,
        line=dict(color="black", width=1.5),
        mode="lines",
        name="Idle",
    )  # Altitude-Speed line for MTOW

    fig2.add_trace(scatter_0_ft_max_to)
    fig2.add_trace(scatter_0_ft_max_cl)
    fig2.add_trace(scatter_0_ft_max_cr)
    fig2.add_trace(scatter_0_ft_idle)

    fig2 = go.FigureWidget(fig2)
    fig2.update_layout(
        height=700,
        width=900,
        title_text="Thrust at 0 ft    F0 = " + str(initial_thrust / 1000) + " kN",
        title_x=0.5,
        yaxis_title="F/F0 [-]",
        xaxis_title="Mach [-]",
    )


    scatter_sfc_0 = go.Scatter(
        x=mach_vector,
        y=sfc_0,
        legendgroup="group",
        legendgrouptitle_text="Altitude (ft)",
        line=dict(color="blue", width=1.5),
        mode="lines",
        name="0",
    )  # Altitude-Speed line for MTOW
    scatter_sfc_10000 = go.Scatter(
        x=mach_vector,
        y=sfc_10000,
        line=dict(color="red", width=1.5),
        mode="lines",
        name="10000",
    )  # Altitude-Speed line for MTOW
    scatter_sfc_20000 = go.Scatter(
        x=mach_vector,
        y=sfc_20000,
        line=dict(color="green", width=1.5),
        mode="lines",
        name="20000",
    )  # Altitude-Speed line for MTOW
    scatter_sfc_30000 = go.Scatter(
        x=mach_vector,
        y=sfc_30000,
        legendgrouptitle_text="Altitude (ft)",
        line=dict(color="black", width=1.5),
        mode="lines",
        name="30000",
    )  # Altitude-Speed line for MTOW
    scatter_sfc_40000 = go.Scatter(
        x=mach_vector,
        y=sfc_40000,
        line=dict(color="goldenrod", width=1.5),
        mode="lines",
        name="40000",
    )  # Altitude-Speed line for MTOW

    fig3.add_trace(scatter_sfc_0)
    fig3.add_trace(scatter_sfc_10000)
    fig3.add_trace(scatter_sfc_20000)
    fig3.add_trace(scatter_sfc_30000)
    fig3.add_trace(scatter_sfc_40000)

    fig3 = go.FigureWidget(fig3)
    fig3.update_layout(
        height=700,
        width=900,
        title_text="Specific consumption at rating 100%    F0 = " + str(initial_thrust / 1000) + " kN",
        title_x=0.5,
        yaxis_title="SFC [kg/daN/h]",
        xaxis_title="Mach [-]",
    )


    scatter_sfc_0_max_to = go.Scatter(
        x=mach_vector,
        y=sfc_0_max_to,
        legendgroup="group",
        legendgrouptitle_text="Régigme",
        line=dict(color="blue", width=1.5),
        mode="lines",
        name="Max TO",
    )  # Altitude-Speed line for MTOW
    scatter_sfc_0_max_cl = go.Scatter(
        x=mach_vector,
        y=sfc_0_max_cl,
        line=dict(color="red", width=1.5),
        mode="lines",
        name="Max CL",
    )  # Altitude-Speed line for MTOW
    scatter_sfc_0_max_cr = go.Scatter(
        x=mach_vector,
        y=sfc_0_max_cr,
        line=dict(color="green", width=1.5),
        mode="lines",
        name="Max CR",
    )  # Altitude-Speed line for MTOW
    scatter_sfc_0_idle = go.Scatter(
        x=mach_vector,
        y=sfc_0_idle,
        line=dict(color="black", width=1.5),
        mode="lines",
        name="Idle",
    )

    fig4.add_trace(scatter_sfc_0_max_to)
    fig4.add_trace(scatter_sfc_0_max_cl)
    fig4.add_trace(scatter_sfc_0_max_cr)
    fig4.add_trace(scatter_sfc_0_idle)

    fig4 = go.FigureWidget(fig4)
    fig4.update_layout(
        height=700,
        width=900,
        title_text="Specific consumption at 0 ft   F0 = " + str(initial_thrust / 1000) + " kN",
        title_x=0.5,
        yaxis_title="SFC [kg/daN/h]",
        xaxis_title="Mach [-]",
    )


    return fig, fig2, fig3, fig4


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