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
from scipy.interpolate import interp1d


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
    mtow = float(variables["data:weight:aircraft:MTOW"].value[0])
    mzfw = float(variables["data:weight:aircraft:MZFW"].value[0])
    v_stall_equivalent = float(variables["data:performance:V-n_diagram:v_stall"].value[0])
    v_manoeuvre_equivalent = float(variables["data:performance:V-n_diagram:v_manoeuvre"].value[0])
    v_manoeuvre_equivalent_vector = np.linspace(0, v_manoeuvre_equivalent, 100)
    v_cruising_equivalent = float(variables["data:performance:V-n_diagram:v_cruising"].value[0])
    v_dive_equivalent = float(variables["data:performance:V-n_diagram:v_dive"].value[0])
    n_v_c_pos_vector_mtow = float(
        variables["data:performance:V-n_diagram:mtow:n_v_c_pos_vector"].value[0]
    )
    n_v_c_neg_vector_mtow = float(
        variables["data:performance:V-n_diagram:mtow:n_v_c_neg_vector"].value[0]
    )
    n_v_d_pos_vector_mtow = float(
        variables["data:performance:V-n_diagram:mtow:n_v_d_pos_vector"].value[0]
    )
    n_v_d_neg_vector_mtow = float(
        variables["data:performance:V-n_diagram:mtow:n_v_d_neg_vector"].value[0]
    )
    n_v_c_pos_vector_mzfw = float(
        variables["data:performance:V-n_diagram:mzfw:n_v_c_pos_vector"].value[0]
    )
    n_v_c_neg_vector_mzfw = float(
        variables["data:performance:V-n_diagram:mzfw:n_v_c_neg_vector"].value[0]
    )
    n_v_d_pos_vector_mzfw = float(
        variables["data:performance:V-n_diagram:mzfw:n_v_d_pos_vector"].value[0]
    )
    n_v_d_neg_vector_mzfw = float(
        variables["data:performance:V-n_diagram:mzfw:n_v_d_neg_vector"].value[0]
    )
    v_manoeuvre_equivalent_neg = float(
        variables["data:performance:V-n_diagram:v_manoeuvre_equivalent_neg"].value[0]
    )
    v_minus_1g = float(variables["data:performance:V-n_diagram:v_minus_1g"].value[0])

    # MTOW Computation
    n_positive_vector_mtow = np.zeros_like(v_manoeuvre_equivalent_vector)
    for i in range(len(v_manoeuvre_equivalent_vector)):
        n_positive_vector_mtow[i] = (v_manoeuvre_equivalent_vector[i] / v_stall_equivalent) * (
            v_manoeuvre_equivalent_vector[i] / v_stall_equivalent
        )

    v_manoeuvre_equivalent_neg_vector = np.linspace(0, v_manoeuvre_equivalent_neg, 50)
    n_negative_vector_mtow = np.zeros_like(v_manoeuvre_equivalent_neg_vector)
    for i in range(len(v_manoeuvre_equivalent_neg_vector)):
        n_negative_vector_mtow[i] = -(v_manoeuvre_equivalent_neg_vector[i] / v_minus_1g) * (
            v_manoeuvre_equivalent_neg_vector[i] / v_minus_1g
        )

    v_remaining = np.array(
        [
            v_manoeuvre_equivalent,
            v_dive_equivalent,
            v_dive_equivalent,
            v_cruising_equivalent,
            v_manoeuvre_equivalent_neg,
        ]
    )
    n_remaining = np.array(
        [
            n_positive_vector_mtow[-1],
            n_positive_vector_mtow[-1],
            0,
            n_negative_vector_mtow[-1],
            n_negative_vector_mtow[-1],
        ]
    )

    v_stall_vertical = np.array([v_stall_equivalent, v_stall_equivalent])
    n_stall_vertical = np.array([0, 1])

    v_manoeuvre_vertical = np.array([v_manoeuvre_equivalent, v_manoeuvre_equivalent])
    n_manoeuvre_vertical = np.array([n_negative_vector_mtow[-1], n_positive_vector_mtow[-1]])

    v_cruising_vertical = np.array([v_cruising_equivalent, v_cruising_equivalent])
    n_cruising_vertical = np.array([n_negative_vector_mtow[-1], n_positive_vector_mtow[-1]])

    # MZFW Computation
    ratio = np.sqrt(mzfw / mtow)
    v_manoeuvre_equivalent_vector_mzfw = v_manoeuvre_equivalent_vector * ratio
    v_manoeuvre_equivalent_neg_vector_mzfw = v_manoeuvre_equivalent_neg_vector * ratio
    v_cruising_equivalent_mzfw = v_cruising_equivalent * ratio
    v_dive_equivalent_mzfw = v_dive_equivalent * ratio

    v_remaining_mzfw = np.array(
        [
            v_manoeuvre_equivalent * ratio,
            v_dive_equivalent * ratio,
            v_dive_equivalent * ratio,
            v_cruising_equivalent * ratio,
            v_manoeuvre_equivalent_neg * ratio,
        ]
    )
    n_remaining_mzfw = np.array(
        [
            n_positive_vector_mtow[-1],
            n_positive_vector_mtow[-1],
            0,
            n_negative_vector_mtow[-1],
            n_negative_vector_mtow[-1],
        ]
    )

    v_stall_vertical_mzfw = np.array([v_stall_equivalent * ratio, v_stall_equivalent * ratio])
    n_stall_vertical_mzfw = np.array([0, 1])

    v_manoeuvre_vertical_mzfw = np.array(
        [v_manoeuvre_equivalent * ratio, v_manoeuvre_equivalent * ratio]
    )
    n_manoeuvre_vertical_mzfw = np.array([n_negative_vector_mtow[-1], n_positive_vector_mtow[-1]])

    v_cruising_vertical_mzfw = np.array(
        [v_cruising_equivalent * ratio, v_cruising_equivalent * ratio]
    )
    n_cruising_vertical_mzfw = np.array([n_negative_vector_mtow[-1], n_positive_vector_mtow[-1]])

    # Flight envelope computation

    # Plot the results
    fig = go.Figure()
    fig2 = go.Figure()

    scatter_v_c_pos = go.Scatter(
        x=np.array([1, v_cruising_equivalent]),
        y=np.array([1, n_v_c_pos_vector_mtow]),
        legendgroup="group",
        line=dict(
            color="#ff7f0e",
            dash="dash",
        ),
        name="50 ft/s",
    )
    scatter_v_c_neg = go.Scatter(
        x=np.array([1, v_cruising_equivalent]),
        y=np.array([1, n_v_c_neg_vector_mtow]),
        legendgroup="group",
        line=dict(
            color="#ff7f0e",
            dash="dash",
        ),
        showlegend=False,
    )
    scatter_v_d_pos = go.Scatter(
        x=np.array([1, v_dive_equivalent]),
        y=np.array([1, n_v_d_pos_vector_mtow]),
        legendgroup="group",
        line=dict(
            color="#00cc96",
            dash="dash",
        ),
        showlegend=False,
    )
    scatter_v_d_neg = go.Scatter(
        x=np.array([1, v_dive_equivalent]),
        y=np.array([1, n_v_d_neg_vector_mtow]),
        legendgroup="group",
        line=dict(
            color="#00cc96",
            dash="dash",
        ),
        name="25 ft/s",
    )

    scatter_v_c_pos_mzfw = go.Scatter(
        x=np.array([1, v_cruising_equivalent_mzfw]),
        y=np.array([1, n_v_c_pos_vector_mzfw]),
        legendgroup="group2",
        legendgrouptitle_text="MZFW",
        line=dict(
            color="#ff7f0e",
            dash="dash",
        ),
        name="50 ft/s",
        visible="legendonly",
    )
    scatter_v_c_neg_mzfw = go.Scatter(
        x=np.array([1, v_cruising_equivalent_mzfw]),
        y=np.array([1, n_v_c_neg_vector_mzfw]),
        legendgroup="group2",
        line=dict(
            color="#ff7f0e",
            dash="dash",
        ),
        showlegend=False,
        visible="legendonly",
    )
    scatter_v_d_pos_mzfw = go.Scatter(
        x=np.array([1, v_dive_equivalent_mzfw]),
        y=np.array([1, n_v_d_pos_vector_mzfw]),
        legendgroup="group2",
        line=dict(
            color="#00cc96",
            dash="dash",
        ),
        showlegend=False,
        visible="legendonly",
    )
    scatter_v_d_neg_mzfw = go.Scatter(
        x=np.array([1, v_dive_equivalent_mzfw]),
        y=np.array([1, n_v_d_neg_vector_mzfw]),
        legendgroup="group2",
        line=dict(
            color="#00cc96",
            dash="dash",
        ),
        name="25 ft/s",
        visible="legendonly",
    )

    scatter_n_max_positive = go.Scatter(
        x=v_manoeuvre_equivalent_vector,
        y=n_positive_vector_mtow,
        legendgroup="group",
        legendgrouptitle_text="MZFW",
        line=dict(color="#636efa", dash="dash"),
        name="V_n diagram",
    )
    scatter_n_max_negative = go.Scatter(
        x=v_manoeuvre_equivalent_neg_vector,
        y=n_negative_vector_mtow,
        legendgroup="group",
        line=dict(color="#636efa", dash="dash"),
        showlegend=False,
    )
    scatter_v_n_remaining = go.Scatter(
        x=v_remaining,
        y=n_remaining,
        legendgroup="group",
        line=dict(color="#636efa", dash="dash"),
        showlegend=False,
    )
    scatter_stall_vertical = go.Scatter(
        x=v_stall_vertical,
        y=n_stall_vertical,
        legendgroup="group",
        line=dict(
            color="#636efa",
            dash="dot",
        ),
        showlegend=False,
    )
    scatter_manoeuvre_vertical = go.Scatter(
        x=v_manoeuvre_vertical,
        y=n_manoeuvre_vertical,
        legendgroup="group",
        line=dict(
            color="#636efa",
            dash="dot",
        ),
        showlegend=False,
    )
    scatter_cruising_vertical = go.Scatter(
        x=v_cruising_vertical,
        y=n_cruising_vertical,
        legendgroup="group",
        line=dict(
            color="#636efa",
            dash="dot",
        ),
        showlegend=False,
    )

    scatter_n_max_positive_mzfw = go.Scatter(
        x=v_manoeuvre_equivalent_vector_mzfw,
        y=n_positive_vector_mtow,
        legendgroup="group2",
        legendgrouptitle_text="MZFW",
        line=dict(color="#ef553b", dash="dash"),
        name="V_n diagram",
        visible="legendonly",
    )
    scatter_n_max_negative_mzfw = go.Scatter(
        x=v_manoeuvre_equivalent_neg_vector_mzfw,
        y=n_negative_vector_mtow,
        legendgroup="group2",
        line=dict(color="#ef553b", dash="dash"),
        showlegend=False,
        visible="legendonly",
    )
    scatter_v_n_remaining_mzfw = go.Scatter(
        x=v_remaining_mzfw,
        y=n_remaining_mzfw,
        legendgroup="group2",
        line=dict(color="#ef553b", dash="dash"),
        showlegend=False,
        visible="legendonly",
    )
    scatter_stall_vertical_mzfw = go.Scatter(
        x=v_stall_vertical_mzfw,
        y=n_stall_vertical_mzfw,
        legendgroup="group2",
        line=dict(
            color="#ef553b",
            dash="dot",
        ),
        showlegend=False,
        visible="legendonly",
    )
    scatter_manoeuvre_vertical_mzfw = go.Scatter(
        x=v_manoeuvre_vertical_mzfw,
        y=n_manoeuvre_vertical_mzfw,
        legendgroup="group2",
        line=dict(
            color="#ef553b",
            dash="dot",
        ),
        showlegend=False,
        visible="legendonly",
    )
    scatter_cruising_vertical_mzfw = go.Scatter(
        x=v_cruising_vertical_mzfw,
        y=n_cruising_vertical_mzfw,
        legendgroup="group2",
        line=dict(
            color="#ef553b",
            dash="dot",
        ),
        showlegend=False,
        visible="legendonly",
    )

    fig.add_trace(scatter_n_max_positive)
    fig.add_trace(scatter_n_max_negative)
    fig.add_trace(scatter_v_n_remaining)
    fig.add_trace(scatter_cruising_vertical)
    fig.add_trace(scatter_manoeuvre_vertical)
    fig.add_trace(scatter_stall_vertical)

    fig.add_trace(scatter_n_max_positive_mzfw)
    fig.add_trace(scatter_n_max_negative_mzfw)
    fig.add_trace(scatter_v_n_remaining_mzfw)
    fig.add_trace(scatter_cruising_vertical_mzfw)
    fig.add_trace(scatter_manoeuvre_vertical_mzfw)
    fig.add_trace(scatter_stall_vertical_mzfw)

    fig.add_trace(scatter_v_c_pos)
    fig.add_trace(scatter_v_c_neg)
    fig.add_trace(scatter_v_d_pos)
    fig.add_trace(scatter_v_d_neg)

    fig.add_trace(scatter_v_c_pos_mzfw)
    fig.add_trace(scatter_v_c_neg_mzfw)
    fig.add_trace(scatter_v_d_pos_mzfw)
    fig.add_trace(scatter_v_d_neg_mzfw)

    fig = go.FigureWidget(fig)
    fig2 = go.FigureWidget(fig2)

    fig.update_layout(
        height=700,
        width=700,
        title_text="V-n maoeuvre diagram",
        title_x=0.5,
        xaxis_title="Equivalent Air Speed [m/s]",
        yaxis_title="Load factor [-]",
    )
    fig2.update_layout(
        height=700,
        width=700,
        title_text="V-n gust diagram",
        title_x=0.5,
        xaxis_title="Equivalent Air Speed [m/s]",
        yaxis_title="Load factor [-]",
    )
    return fig
