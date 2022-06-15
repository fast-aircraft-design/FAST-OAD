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
from ipywidgets import widgets, HBox
from IPython.display import display


from fastoad.io import VariableIO

COLS = plotly.colors.DEFAULT_PLOTLY_COLORS
NACELLE_POSITION = 0.6  # Nacelle position compared to the leading edge. 0 means that the back of the nacelle is aligned with the beginning of the root, 1 means that the beginning of the nacelle is aligned with the kink_x.
HORIZONTAL_TAIL_ROOT = 0.3  # Percentage of the tail root concerned by the elevator
HORIZONTAL_TAIL_TIP = 0.3 # Percentage of the tail tip, at 90 percent of the horizontal tail width, covered by the elevator
HORIZONTAL_WIDTH_ELEVATOR = (
    0.85  # Percentage of the width of the horizontal tail concerned by the elevator
)


def aircraft_drawing_side_view_plot(
    aircraft_file_path: str, name=None, fig=None, file_formatter=None
) -> go.FigureWidget:
    """
    Returns a figure plot of the top view of the aircraft with the engines, the flaps, the slats and the elevator.
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

    # Wing parameters
    wing_kink_leading_edge_x = variables["data:geometry:wing:kink:leading_edge:x:local"].value[0]
    wing_tip_leading_edge_x = variables["data:geometry:wing:tip:leading_edge:x:local"].value[0]
    wing_root_y = variables["data:geometry:wing:root:y"].value[0]
    wing_kink_y = variables["data:geometry:wing:kink:y"].value[0]
    wing_tip_y = variables["data:geometry:wing:tip:y"].value[0]
    wing_root_chord = variables["data:geometry:wing:root:chord"].value[0]
    wing_kink_chord = variables["data:geometry:wing:kink:chord"].value[0]
    wing_tip_chord = variables["data:geometry:wing:tip:chord"].value[0]
    nacelle_diameter = variables["data:geometry:propulsion:nacelle:diameter"].value[0]
    nacelle_length = variables["data:geometry:propulsion:nacelle:length"].value[0]
    nacelle_y = variables["data:geometry:propulsion:nacelle:y"].value[0]

    trailing_edge_kink_sweep_100_outer = variables["data:geometry:wing:sweep_100_outer"].value[0]
    slat_chord_ratio = variables["data:geometry:slat:chord_ratio"].value[0]
    slat_span_ratio = variables["data:geometry:slat:span_ratio"].value[0]
    total_wing_span = variables["data:geometry:wing:span"].value[0]
    flaps_span_ratio = variables["data:geometry:flap:span_ratio"].value[0]
    flaps_chord_ratio = variables["data:geometry:flap:chord_ratio"].value[0]
    mean_aerodynamic_chord = variables["data:geometry:wing:MAC:length"].value[0]
    mac25_x_position = variables["data:geometry:wing:MAC:at25percent:x"].value[0]
    distance_root_mac_chords = variables["data:geometry:wing:MAC:leading_edge:x:local"].value[0]

    # Wing
    y_wing = np.array(
        [0, wing_root_y, wing_kink_y, wing_tip_y, wing_tip_y, wing_kink_y, wing_root_y, 0, 0]
    )

    x_wing = np.array(
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

    # Engine
    y_engine = np.array(
        [
            nacelle_y - nacelle_diameter / 2,
            nacelle_y + nacelle_diameter / 2,
            nacelle_y + nacelle_diameter / 2,
            nacelle_y - nacelle_diameter / 2,
            nacelle_y - nacelle_diameter / 2,
        ]
    )
    x_engine = np.array([-nacelle_length, -nacelle_length, 0, 0, -nacelle_length])

    # Horizontal Tail parameters
    ht_root_chord = variables["data:geometry:horizontal_tail:root:chord"].value[0]
    ht_tip_chord = variables["data:geometry:horizontal_tail:tip:chord"].value[0]
    ht_span = variables["data:geometry:horizontal_tail:span"].value[0]
    ht_sweep_0 = variables["data:geometry:horizontal_tail:sweep_0"].value[0]
    ht_sweep_100 = variables["data:geometry:horizontal_tail:sweep_100"].value[0]

    ht_tip_leading_edge_x = ht_span / 2.0 * np.tan(ht_sweep_0 * np.pi / 180.0)

    y_ht = np.array([0, ht_span / 2.0, ht_span / 2.0, 0.0, 0.0])

    x_ht = np.array(
        [0, ht_tip_leading_edge_x, ht_tip_leading_edge_x + ht_tip_chord, ht_root_chord, 0]
    )

    # Fuselage parameters
    fuselage_max_width = variables["data:geometry:fuselage:maximum_width"].value[0]
    fuselage_length = variables["data:geometry:fuselage:length"].value[0]
    fuselage_front_length = variables["data:geometry:fuselage:front_length"].value[0]
    fuselage_rear_length = variables["data:geometry:fuselage:rear_length"].value[0]

    x_fuselage = np.array(
        [
            0.0,
            0.0,
            fuselage_front_length,
            fuselage_length - fuselage_rear_length,
            fuselage_length,
            fuselage_length,
        ]
    )

    y_fuselage = np.array(
        [
            0.0,
            fuselage_max_width / 4.0,
            fuselage_max_width / 2.0,
            fuselage_max_width / 2.0,
            fuselage_max_width / 4.0,
            0.0,
        ]
    )

    # Flaps
    # Part of the code dedicated to the flaps

    flap_chord_kink = wing_kink_chord * flaps_chord_ratio
    flap_chord_tip = wing_tip_chord * flaps_chord_ratio

    # Inboard flap
    # Part of the code dedicated to the inboard flap

    y_flaps_inboard = np.array([wing_kink_y, wing_kink_y, wing_root_y, wing_root_y, wing_kink_y])
    y_flaps_inboard = np.concatenate((-y_flaps_inboard, y_flaps_inboard))

    x_flaps_inboard = np.array(
        [
            wing_root_chord,
            wing_root_chord - flap_chord_kink,
            wing_root_chord - flap_chord_kink,
            wing_root_chord,
            wing_root_chord,
        ]
    )

    x_flaps_inboard = (
        x_flaps_inboard
        + mac25_x_position
        - 0.25 * mean_aerodynamic_chord
        - distance_root_mac_chords
    )
    # pylint: disable=invalid-name # that's a common naming
    x_flaps_inboard = np.concatenate((x_flaps_inboard, x_flaps_inboard))

    # Outboard flap
    # Part of the code dedicated to the outboard flap

    # The points "_te" are the ones placed on the trailing edge.
    # The points "_ow" are the projection of "_te" on the wing (on wing)
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

    y_te_1 = wing_kink_y
    x_te_1 = wing_root_chord

    y_te_2 = wing_root_y + (total_wing_span / 2) * flaps_span_ratio
    x_te_2 = (
        wing_tip_leading_edge_x
        + wing_tip_chord
        - (wing_tip_y - (wing_root_y + (total_wing_span / 2) * flaps_span_ratio))
        * np.tan(trailing_edge_kink_sweep_100_outer * np.pi / 180)
    )

    ow_local_1 = np.array([-flap_chord_tip, 0])
    x_ow_1, y_ow_1 = rotation_matrix @ ow_local_1 + np.array([x_te_2, y_te_2])

    ow_local_2 = np.array([-flap_chord_kink, 0])
    x_ow_2, y_ow_2 = rotation_matrix @ ow_local_2 + np.array([x_te_1, y_te_1])

    y_flaps_outboard = np.array([y_te_1, y_te_2, y_ow_1, y_ow_2, y_te_1])
    y_flaps_outboard = np.concatenate((-y_flaps_outboard, y_flaps_outboard))

    x_flaps_outboard = np.array([x_te_1, x_te_2, x_ow_1, x_ow_2, x_te_1])

    x_flaps_outboard = (
        x_flaps_outboard
        + mac25_x_position
        - 0.25 * mean_aerodynamic_chord
        - distance_root_mac_chords
    )
    # pylint: disable=invalid-name # that's a common naming
    x_flaps_outboard = np.concatenate((x_flaps_outboard, x_flaps_outboard))

    # Design line
    # Part of the code dedicated to a lign only used for an aesthetic reason.
    # This line joins the two inboard flaps

    y_design_line = np.array([wing_root_y])
    y_design_line = np.concatenate((-y_design_line, y_design_line))

    x_design_line = np.array([wing_root_chord])

    x_design_line = (
        x_design_line + mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords
    )
    # pylint: disable=invalid-name # that's a common naming
    x_design_line = np.concatenate((x_design_line, x_design_line))

    # Slats
    # Part of the code dedicated to the slats
    # The dimensions are given by two parameters : span_ratio and chord_ratio
    # Here the span_ratio is given by the span of the airplane minus the fuselage radius
    # the chord_ratio is given by the kink chord

    wing_span_no_fuselage = wing_tip_y - wing_root_y

    slat_y = (
        (1 - slat_span_ratio) / 2.0 * wing_span_no_fuselage
    )  # position in y of the beginning of the slats near the root
    slat_x_root = wing_tip_leading_edge_x * (1 - slat_span_ratio) / 2.0

    y_slats_left = np.array(
        [
            slat_y + wing_root_y,
            slat_y + wing_root_y,
            wing_tip_y - slat_y,
            wing_tip_y - slat_y,
            slat_y + wing_root_y,
        ]
    )

    y_slats_right = -y_slats_left  # slats on the other wing

    x_slats_left = np.array(
        [
            slat_x_root,
            slat_x_root + slat_chord_ratio * wing_kink_chord,
            wing_tip_leading_edge_x * (1 - (1 - slat_span_ratio) / 2.0)
            + slat_chord_ratio * wing_kink_chord,
            wing_tip_leading_edge_x * (1 - (1 - slat_span_ratio) / 2.0),
            slat_x_root,
        ]
    )
    x_slats_left += mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords
    x_slats_right = x_slats_left

    # CGs
    wing_25mac_x = variables["data:geometry:wing:MAC:at25percent:x"].value[0]
    wing_mac_length = variables["data:geometry:wing:MAC:length"].value[0]
    local_wing_mac_le_x = variables["data:geometry:wing:MAC:leading_edge:x:local"].value[0]
    local_ht_25mac_x = variables["data:geometry:horizontal_tail:MAC:at25percent:x:local"].value[0]
    ht_distance_from_wing = variables[
        "data:geometry:horizontal_tail:MAC:at25percent:x:from_wingMAC25"
    ].value[0]

    x_wing = x_wing + wing_25mac_x - 0.25 * wing_mac_length - local_wing_mac_le_x
    x_engine += (
        wing_25mac_x
        - 0.25 * wing_mac_length
        - local_wing_mac_le_x
        + NACELLE_POSITION * nacelle_length
    )
    x_ht = x_ht + wing_25mac_x + ht_distance_from_wing - local_ht_25mac_x

    # pylint: disable=invalid-name # that's a common naming
    x = np.concatenate((x_fuselage, x_wing, x_ht))
    # pylint: disable=invalid-name # that's a common naming
    y = np.concatenate((y_fuselage, y_wing, y_ht))

    # pylint: disable=invalid-name # that's a common naming
    y = np.concatenate((-y, y))
    # pylint: disable=invalid-name # that's a common naming
    x = np.concatenate((x, x))

    # Design of the elevator
    A = x_fuselage[5] - x_ht[3]  # constants used for the computation

    B = y_fuselage[4] - y_fuselage[5]  # constants used for the computation

    D = x_ht[2] - x_ht[3]  # constants used for the computation

    E = y_ht[1] - y_ht[3]  # constants used for the computation

    tg_alpha = (y_fuselage[3] - y_fuselage[4]) / (
        x_fuselage[4] - x_fuselage[3]
    )  # constants used for the computation

    ht_root_tip_x_percent = (
        x_ht[2] - (1 - HORIZONTAL_WIDTH_ELEVATOR) * y_ht[1] * np.tan(ht_sweep_100 * np.pi / 180)
    ) - (
        x_ht[1] - (1 - HORIZONTAL_WIDTH_ELEVATOR) * y_ht[1] * np.tan(ht_sweep_0 * np.pi / 180)
    )  # constants used for the computation. Root chord at X percent of the horizontal tail width (depending on the value of the parameter "HORIZONTAL_WIDTH_ELEVATOR"

    delta_l = (ht_root_chord - np.tan(ht_sweep_0 * np.pi / 180) * (B + A * tg_alpha)) / (
        1 + np.tan(ht_sweep_0 * np.pi / 180) * tg_alpha
    )  # constants used for the computation

    delta_y_tot = tg_alpha * (A + delta_l)  # constants used for the computation

    delta_x = (A * E - D * B) / (E + D * tg_alpha)  # constants used for the computation

    delta_y = tg_alpha * delta_x  # constants used for the computation

    x_elevator = np.array(
        [
            x_fuselage[4] - delta_x,
            x_ht[3] - delta_l * HORIZONTAL_TAIL_ROOT,
            x_ht[2]
            - (1 - HORIZONTAL_WIDTH_ELEVATOR) * y_ht[1] * np.tan(ht_sweep_100 * np.pi / 180)
            - HORIZONTAL_TAIL_TIP * ht_root_tip_x_percent,
            x_ht[2]
            - (1 - HORIZONTAL_WIDTH_ELEVATOR) * y_ht[1] * np.tan(ht_sweep_100 * np.pi / 180),
            x_fuselage[4] - delta_x,
        ]
    )
    y_elevator = np.array(
        [
            y_fuselage[4] + delta_y,
            y_fuselage[4] + HORIZONTAL_TAIL_ROOT * delta_y_tot,
            y_ht[1] * HORIZONTAL_WIDTH_ELEVATOR,
            y_ht[1] * HORIZONTAL_WIDTH_ELEVATOR,
            y_fuselage[4] + delta_y,
        ]
    )

    if fig is None:
        fig = go.Figure()

    scatter_aircraft = go.Scatter(
        x=y, y=x, line=dict(color="blue"), mode="lines", name=name, showlegend=False
    )  # Aircraft
    scatter_left = go.Scatter(
        x=y_engine, y=x_engine, line=dict(color="blue"), mode="lines", name=name, showlegend=False
    )  # Left engine
    scatter_right = go.Scatter(
        x=-y_engine, y=x_engine, line=dict(color="blue"), mode="lines", name=name, showlegend=False
    )  # Right engine
    scatter_flaps_inboard = go.Scatter(
        x=y_flaps_inboard,
        y=x_flaps_inboard,
        mode="lines",
        line=dict(color="blue", width=1),
        name=name,
        showlegend=False,
    )  # inboard flap
    scatter_flaps_outboard = go.Scatter(
        x=y_flaps_outboard,
        y=x_flaps_outboard,
        mode="lines",
        line=dict(color="blue", width=1),
        name=name,
        showlegend=False,
    )  # outboard flap
    scatter_design_line = go.Scatter(
        x=y_design_line,
        y=x_design_line,
        mode="lines",
        line=dict(color="blue", width=1),
        name=name,
        showlegend=False,
    )  # design line
    scatter_slats_left = go.Scatter(
        x=y_slats_left,
        y=x_slats_left,
        line=dict(color="blue", width=1),
        mode="lines",
        name=name,
        showlegend=False,
    )  # left slats
    scatter_slats_right = go.Scatter(
        x=y_slats_right,
        y=x_slats_right,
        line=dict(color="blue", width=1),
        mode="lines",
        name=name,
        showlegend=False,
    )  # right slats
    scatter_elevator_right = go.Scatter(
        x=y_elevator,
        y=x_elevator,
        line=dict(color="blue", width=1),
        mode="lines",
        name=name,
        showlegend=False,
    )  # elevator
    scatter_elevator_left = go.Scatter(
        x=-y_elevator,
        y=x_elevator,
        line=dict(color="blue", width=1),
        mode="lines",
        name=name,
        showlegend=False,
    )  # elevator

    fig.add_trace(scatter_aircraft)
    fig.add_trace(scatter_right)  # engine
    fig.add_trace(scatter_left)  # engine
    fig.add_trace(scatter_flaps_outboard)  # flaps
    fig.add_trace(scatter_flaps_inboard)  # flaps
    fig.add_trace(scatter_design_line)
    fig.add_trace(scatter_slats_left)
    fig.add_trace(scatter_slats_right)
    fig.add_trace(scatter_elevator_right)
    fig.add_trace(scatter_elevator_left)

    fig.layout = go.Layout(yaxis=dict(scaleanchor="x", scaleratio=1))

    fig = go.FigureWidget(fig)

    fig.update_layout(title_text="Aircraft Geometry", title_x=0.5, xaxis_title="y", yaxis_title="x")

    return fig


