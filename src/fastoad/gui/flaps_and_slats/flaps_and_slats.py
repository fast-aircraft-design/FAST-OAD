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
import pandas as pd
import plotly
import plotly.graph_objects as go
from openmdao.utils.units import convert_units
from plotly.subplots import make_subplots
from ipywidgets import widgets, HBox
from IPython.display import display


from fastoad.io import VariableIO
from fastoad.openmdao.variables import VariableList

COLS = plotly.colors.DEFAULT_PLOTLY_COLORS
NACELLE_POSITION = 0.6  # Nacelle position compared to the leading edge. 0 means that the back of the nacelle is aligned with the beginning of the root, 1 means that the beginning of the nacelle is aligned with the kink_x.
HORIZONTAL_TAIL_ROOT = 0.3  # Percentage of the tail root concerned by the elevator
HORIZONTAL_TAIL_TIP = 0.3  # Percentage of the tail tip, at 90 percent of the horizontal tail width, covered by the elevator


def flaps_and_slats_plot(
    aircraft_file_path: str, name=None, fig=None, file_formatter=None
) -> go.FigureWidget:
    """
    Returns a figure plot of the top view of the wing with the flaps and slats added.
    Different designs can be superposed by providing an existing fig.
    Each design can be provided a name.

    :param aircraft_file_path: path of data file
    :param name: name to give to the trace added to the figure
    :param fig: existing figure to which add the plot
    :param file_formatter: the formatter that defines the format of data file. If not provided,
                           default format will be assumed.
    :return: plot figure of wing the wing with flaps and slats
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
    trailing_edge_kink_sweep_100_outer = variables["data:geometry:wing:sweep_100_outer"].value[0]

    slat_chord_ratio = variables["data:geometry:slat:chord_ratio"].value[0]
    slat_span_ratio = variables["data:geometry:slat:span_ratio"].value[0]

    total_wing_span = variables["data:geometry:wing:span"].value[0]
    flaps_span_ratio = variables["data:geometry:flap:span_ratio"].value[0]
    flaps_chord_ratio = variables["data:geometry:flap:chord_ratio"].value[0]

    mean_aerodynamic_chord = variables["data:geometry:wing:MAC:length"].value[0]
    mac25_x_position = variables["data:geometry:wing:MAC:at25percent:x"].value[0]
    distance_root_mac_chords = variables["data:geometry:wing:MAC:leading_edge:x:local"].value[0]

    # 1) overall wing
    # Part of the code dedicated to the geometry of the general wing

    y = np.array(
        [0, wing_root_y, wing_kink_y, wing_tip_y, wing_tip_y, wing_kink_y, wing_root_y, 0, 0]
    )
    y = np.concatenate((-y, y))

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

    x = x + mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords
    # pylint: disable=invalid-name # that's a common naming
    x = np.concatenate((x, x))

    # 2) flaps
    # Part of the code dedicated to the flaps

    flap_chord_kink = wing_kink_chord * flaps_chord_ratio
    flap_chord_tip = wing_tip_chord * flaps_chord_ratio

    # 2.1) Inboard flap
    # Part of the code dedicated to the inboard flap

    y2 = np.array([wing_kink_y, wing_kink_y, wing_root_y, wing_root_y, wing_kink_y])
    y2 = np.concatenate((-y2, y2))

    x2 = np.array(
        [
            wing_root_chord,
            wing_root_chord - flap_chord_kink,
            wing_root_chord - flap_chord_kink,
            wing_root_chord,
            wing_root_chord,
        ]
    )

    x2 = x2 + mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords
    # pylint: disable=invalid-name # that's a common naming
    x2 = np.concatenate((x2, x2))

    # 2.2) Outboard flap
    # Part of the code dedicated to the outboard flap

    # The points "_a" and "_b" are the ones placed on the trailing edge.
    # The points "_c" and "_d" are the projection of "_a" and "_b" normal to the trailing edge, on the wing.
    # This projection is made with a rotation matrix.
    # The points are place respecting the flaps span ratio compared to the total span of the aircraft.

    rotation_matrix = np.array(
        [
            [
                np.cos(trailing_edge_kink_sweep_100_outer * np.pi / 180),
                np.sin(trailing_edge_kink_sweep_100_outer * np.pi / 180),
            ],
            [
                -np.sin(trailing_edge_kink_sweep_100_outer * np.pi / 180),
                np.cos(trailing_edge_kink_sweep_100_outer * np.pi / 180),
            ],
        ]
    )

    y_a = wing_kink_y
    x_a = wing_root_chord

    y_b = wing_root_y + (total_wing_span / 2) * flaps_span_ratio
    x_b = (
        wing_tip_leading_edge_x
        + wing_tip_chord
        - (wing_tip_y - (wing_root_y + (total_wing_span / 2) * flaps_span_ratio))
        * np.tan(trailing_edge_kink_sweep_100_outer * np.pi / 180)
    )

    c_local = np.array([-flap_chord_tip, 0])
    x_c, y_c = rotation_matrix @ c_local + np.array([x_b, y_b])

    d_local = np.array([-flap_chord_kink, 0])
    x_d, y_d = rotation_matrix @ d_local + np.array([x_a, y_a])

    y3 = np.array([y_a, y_b, y_c, y_d, y_a])
    y3 = np.concatenate((-y3, y3))

    x3 = np.array([x_a, x_b, x_c, x_d, x_a])

    x3 = x3 + mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords
    # pylint: disable=invalid-name # that's a common naming
    x3 = np.concatenate((x3, x3))

    # 2.3) Design line
    # Part of the code dedicated to a lign only used for an aesthetic reason.
    # This line joins the two inboard flaps

    y4 = np.array([wing_root_y])
    y4 = np.concatenate((-y4, y4))

    x4 = np.array([wing_root_chord])

    x4 = x4 + mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords
    # pylint: disable=invalid-name # that's a common naming
    x4 = np.concatenate((x4, x4))

    # 3) slats
    # Part of the code dedicated to the slats
    # The dimensions are given by two parameters : span_ratio and chord_ratio
    # Here the span_ratio is given by the span of the airplane minus the fuselage radius
    # the chord_ratio is given by the kink chord

    wing_span_no_fuselage = wing_tip_y - wing_root_y

    slat_y = (
        (1 - slat_span_ratio) / 2.0 * wing_span_no_fuselage
    )  # position in y of the beginning of the slats near the root
    slat_x_root = wing_tip_leading_edge_x * (1 - slat_span_ratio) / 2.0

    y5 = np.array(
        [
            slat_y + wing_root_y,
            slat_y + wing_root_y,
            wing_tip_y - slat_y,
            wing_tip_y - slat_y,
            slat_y + wing_root_y,
        ]
    )

    y6 = -y5  # slats on the other wing

    x5 = np.array(
        [
            slat_x_root,
            slat_x_root + slat_chord_ratio * wing_kink_chord,
            wing_tip_leading_edge_x * (1 - (1 - slat_span_ratio) / 2.0)
            + slat_chord_ratio * wing_kink_chord,
            wing_tip_leading_edge_x * (1 - (1 - slat_span_ratio) / 2.0),
            slat_x_root,
        ]
    )
    x5 += mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords
    x6 = x5

    # 4) Figure
    # Here  the different points are added on the same figure. The wing is in blue and the high lift devices in red

    if fig is None:
        fig = go.Figure()

    scatter = go.Scatter(
        x=y, y=x, line=dict(color="blue"), mode="lines", name=name, showlegend=False
    )  # wing
    scatter2 = go.Scatter(
        x=y2, y=x2, mode="lines", line=dict(color="blue", width=1), name=name, showlegend=False
    )  # first flap
    scatter3 = go.Scatter(
        x=y3, y=x3, mode="lines", line=dict(color="blue", width=1), name=name, showlegend=False
    )  # second flap
    scatter4 = go.Scatter(
        x=y4, y=x4, mode="lines", line=dict(color="blue"), name=name, showlegend=False
    )  # design line
    scatter5 = go.Scatter(
        x=y5, y=x5, line=dict(color="blue", width=1), mode="lines", name=name, showlegend=False
    )  # slats
    scatter6 = go.Scatter(
        x=y6, y=x6, line=dict(color="blue", width=1), mode="lines", name=name, showlegend=False
    )  # slats

    fig.layout = go.Layout(yaxis=dict(scaleanchor="x", scaleratio=1))

    fig.add_trace(scatter)
    fig.add_trace(scatter3)
    fig.add_trace(scatter2)
    fig.add_trace(scatter4)
    fig.add_trace(scatter5)
    fig.add_trace(scatter6)

    fig = go.FigureWidget(fig)
    fig.update_xaxes(constrain="domain")
    fig.update_yaxes(constrain="domain")
    fig.update_layout(title_text="Wing Drawing", title_x=0.5, xaxis_title="y", yaxis_title="x")

    return fig
