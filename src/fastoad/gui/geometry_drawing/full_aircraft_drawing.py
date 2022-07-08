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
import pandas as pd
import plotly
import plotly.graph_objects as go
from ipywidgets import widgets
from IPython.display import display

pi = np.pi

from fastoad.io import VariableIO

COLS = plotly.colors.DEFAULT_PLOTLY_COLORS
NACELLE_POSITION = (
    0.7  # Nacelle position compared to the leading edge. 0 means that the back of the nacelle is
)

# aligned with the beginning of the root, 1 means that the beginning of the nacelle is aligned with the kink_x.
HORIZONTAL_TAIL_ROOT = 0.3  # Percentage of the tail root concerned by the elevator
HORIZONTAL_TAIL_TIP = (
    0.3  # Percentage of the tail tip, at 90 percent of the horizontal tail width, covered by the
)

# Elevator
HORIZONTAL_WIDTH_ELEVATOR = (
    0.85  # Percentage of the width of the horizontal tail concerned by the elevator
)

# Horizontal tail
HT_HEIGHT = 0.3  # Height of the horizontal tail root compared to the center line of the fuselage. 0.0 means on the
# center line, 1.0 means at a height same as the radius of the fuselage
HT_DIHEDRAL = 0.42  # Height of the horizontal tail tip compared to the center line of the fuselage. 0.0 means on the
# center line, 1.0 means at a height same as the radius of the fuselage

# Engine
ENGINE_HEIGHT = 0.5  # Heigth of the middle of the ingine 0.0 means on the center line   1.0 means the middle of the
# engine is just on the lower line of the aircraft
WING_ROOT_HEIGHT = (
    0.2  # Height of the wing root compared to the center line of the fuselage. 0.0 means on the
)


# center line, 1.0 means at a height same as the radius of the fuselage below


def aircraft_drawing_top_view(
    aircraft_file_path: str,
    name=None,
    fig=None,
    file_formatter=None,
    height=500,
    width=900,
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
    :param height : height of the image
    :param width : width of the image
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

    y_fuselage = np.linspace(0, fuselage_max_width / 2, 10)
    x_fuselage = (
        fuselage_front_length / (0.5 * fuselage_max_width) ** 2 * y_fuselage ** 2
    )  # parabola
    x_fuselage = np.append(
        x_fuselage,
        np.array(
            [
                fuselage_length - fuselage_rear_length,
                fuselage_length,
                fuselage_length,
            ]
        ),
    )

    y_fuselage = np.append(
        y_fuselage,
        np.array(
            [
                fuselage_max_width / 2.0,
                fuselage_max_width / 4.0,
                0.0,
            ]
        ),
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

    # Design of the elevator
    x_ht_position = fuselage_length - x_ht[3]  # constants used for the computation
    x_virtual_ht_leading_edge = ht_tip_leading_edge_x + ht_tip_chord - ht_root_chord

    tg_alpha = (y_fuselage[-3] - y_fuselage[-2]) / (
        x_fuselage[-2] - x_fuselage[-3]
    )  # constants used for the computation

    ht_root_tip_x_percent = (
        x_ht[2] - (1 - HORIZONTAL_WIDTH_ELEVATOR) * y_ht[1] * np.tan(ht_sweep_100 * np.pi / 180)
    ) - (x_ht[1] - (1 - HORIZONTAL_WIDTH_ELEVATOR) * y_ht[1] * np.tan(ht_sweep_0 * np.pi / 180))
    # constants used for the computation. Root chord at X percent of the horizontal tail width
    # (depending on the value of the parameter "HORIZONTAL_WIDTH_ELEVATOR")

    delta_l = (
        ht_root_chord
        - np.tan(ht_sweep_0 * np.pi / 180) * (fuselage_max_width / 4.0 + x_ht_position * tg_alpha)
    ) / (
        1 + np.tan(ht_sweep_0 * np.pi / 180) * tg_alpha
    )  # constants used for the computation

    delta_y_tot = tg_alpha * (x_ht_position + delta_l)  # constants used for the computation

    delta_x = (
        x_ht_position * ht_span / 2.0 - x_virtual_ht_leading_edge * fuselage_max_width / 4.0
    ) / (ht_span / 2.0 + x_virtual_ht_leading_edge * tg_alpha)
    # constants used for the computation

    delta_y = tg_alpha * delta_x  # constants used for the computation

    x_elevator = np.array(
        [
            x_fuselage[-2] - delta_x,
            x_ht[3] - delta_l * HORIZONTAL_TAIL_ROOT,
            x_ht[2]
            - (1 - HORIZONTAL_WIDTH_ELEVATOR) * y_ht[1] * np.tan(ht_sweep_100 * np.pi / 180)
            - HORIZONTAL_TAIL_TIP * ht_root_tip_x_percent,
            x_ht[2]
            - (1 - HORIZONTAL_WIDTH_ELEVATOR) * y_ht[1] * np.tan(ht_sweep_100 * np.pi / 180),
            x_fuselage[-2] - delta_x,
        ]
    )
    y_elevator = np.array(
        [
            y_fuselage[-2] + delta_y,
            y_fuselage[-2] + HORIZONTAL_TAIL_ROOT * delta_y_tot,
            y_ht[1] * HORIZONTAL_WIDTH_ELEVATOR,
            y_ht[1] * HORIZONTAL_WIDTH_ELEVATOR,
            y_fuselage[-2] + delta_y,
        ]
    )

    x_fuselage[-2] = x_elevator[-1]
    x_fuselage = x_fuselage[:-1]
    y_fuselage = y_fuselage[:-1]

    x_elev = x_elevator[-1]
    y_elev = y_elevator[-1]

    y_rear = np.flip(np.linspace(0, fuselage_max_width / 4, 10))

    x_rear = fuselage_length + (x_elev - fuselage_length) / y_elev ** 2 * y_rear ** 2

    x_fuselage = np.concatenate((x_fuselage, x_rear))
    y_fuselage = np.concatenate((y_fuselage, y_rear))
    # pylint: disable=invalid-name # that's a common naming
    x_aircraft = np.concatenate((x_fuselage, x_wing, x_ht))
    # pylint: disable=invalid-name # that's a common naming
    y_aircraft = np.concatenate((y_fuselage, y_wing, y_ht))

    # pylint: disable=invalid-name # that's a common naming
    y_aircraft = np.concatenate((-y_aircraft, y_aircraft))

    # pylint: disable=invalid-name # that's a common naming
    x_aircraft = np.concatenate((x_aircraft, x_aircraft))

    if fig is None:
        fig = go.Figure()

    scatter_aircraft = go.Scatter(
        x=y_aircraft,
        y=x_aircraft,
        line=dict(color="blue"),
        mode="lines",
        name=name,
        showlegend=False,
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
        line=dict(color="#636efa", width=1),
        name=name,
        showlegend=False,
    )  # inboard flap
    scatter_flaps_outboard = go.Scatter(
        x=y_flaps_outboard,
        y=x_flaps_outboard,
        mode="lines",
        line=dict(color="#636efa", width=1),
        name=name,
        showlegend=False,
    )  # outboard flap
    scatter_design_line = go.Scatter(
        x=y_design_line,
        y=x_design_line,
        mode="lines",
        line=dict(color="#636efa", width=1),
        name=name,
        showlegend=False,
    )  # design line
    scatter_slats_left = go.Scatter(
        x=y_slats_left,
        y=x_slats_left,
        line=dict(color="#636efa", width=1),
        mode="lines",
        name=name,
        showlegend=False,
    )  # left slats
    scatter_slats_right = go.Scatter(
        x=y_slats_right,
        y=x_slats_right,
        line=dict(color="#636efa", width=1),
        mode="lines",
        name=name,
        showlegend=False,
    )  # right slats
    scatter_elevator_right = go.Scatter(
        x=y_elevator,
        y=x_elevator,
        line=dict(color="#636efa", width=1),
        mode="lines",
        name=name,
        showlegend=False,
    )  # elevator
    scatter_elevator_left = go.Scatter(
        x=-y_elevator,
        y=x_elevator,
        line=dict(color="#636efa", width=1),
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

    if name is None:
        fig.update_layout(
            title_text="Aircraft Geometry",
            title_x=0.5,
            xaxis_title="y",
            yaxis_title="x",
            height=height,
            width=width,
        )
    else:
        fig.update_layout(
            title_text=name,
            title_x=0.5,
            xaxis_title="y",
            yaxis_title="x",
            height=height,
            width=width,
        )
    # fig.update_xaxes(range=[-50, 50])
    # fig.update_yaxes(range=[y_axis[0], y_axis[1]])

    return fig


def wing_drawing(
    aircraft_file_path: str,
    name=None,
    fig=None,
    file_formatter=None,
    height=500,
    width=900,
) -> go.FigureWidget:
    """
    Returns a figure plot of the top view of the wing with the relevant distances on it.
    Different designs can be superposed by providing an existing fig.
    Each design can be provided a name.

    :param aircraft_file_path: path of data file
    :param name: name to give to the trace added to the figure
    :param fig: existing figure to which add the plot
    :param file_formatter: the formatter that defines the format of data file. If not provided,
                           default format will be assumed.
    :param height : height of the image
    :param width : width of the image
    :return: wing plot figure
    """
    variables = VariableIO(aircraft_file_path, file_formatter).read()

    wing_kink_leading_edge_x = variables["data:geometry:wing:kink:leading_edge:x:local"].value[0]
    wing_tip_leading_edge_x = variables["data:geometry:wing:tip:leading_edge:x:local"].value[0]
    wing_root_y = variables["data:geometry:wing:root:y"].value[0]
    wing_kink_y = variables["data:geometry:wing:kink:y"].value[0]
    wing_tip_y = variables["data:geometry:wing:tip:y"].value[0]
    wing_area = variables["data:geometry:wing:area"].value[0]
    wing_root_chord = variables["data:geometry:wing:root:chord"].value[0]
    wing_kink_chord = variables["data:geometry:wing:kink:chord"].value[0]
    wing_tip_chord = variables["data:geometry:wing:tip:chord"].value[0]
    trailing_edge_kink_sweep_100_outer = variables["data:geometry:wing:sweep_100_outer"].value[0]
    sweep_0 = variables["data:geometry:wing:sweep_0"].value[0]
    total_wing_span = variables["data:geometry:wing:span"].value[0]
    mean_aerodynamic_chord = variables["data:geometry:wing:MAC:length"].value[0]
    mean_aerodynamic_chord_y_global = variables["data:geometry:wing:MAC:y"].value[0]
    mac25_x_position = variables["data:geometry:wing:MAC:at25percent:x"].value[0]
    distance_root_mac_chords = variables["data:geometry:wing:MAC:leading_edge:x:local"].value[0]

    # 1) overall wing
    # Part of the code dedicated to the geometry of the general wing

    y = np.array(
        [wing_root_y, wing_kink_y, wing_tip_y, wing_tip_y, wing_kink_y, wing_root_y, wing_root_y]
    )

    x = np.array(
        [
            0,
            wing_kink_leading_edge_x,
            wing_tip_leading_edge_x,
            wing_tip_leading_edge_x + wing_tip_chord,
            wing_kink_leading_edge_x + wing_kink_chord,
            wing_root_chord,
            0,
        ]
    )

    x = x + mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords
    # pylint: disable=invalid-name # that's a common naming
    x = np.concatenate((x, x))

    # 2) flaps
    # Not represented here

    # 3) slats
    # Not represented here

    # 4) Fuselage axis
    # The line representing the fuselage axis in y=0
    y_fuselage = np.array([0, 0])
    x_fuselage = np.array([-wing_root_chord * 0.2, wing_root_chord * 1.6])
    x_fuselage += mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords

    # 5) Tip (L3)
    # The line along the tip of the wing
    y_l3 = np.array([wing_tip_y * 1.03, wing_tip_y * 1.03])
    x_l3 = np.array([wing_tip_leading_edge_x, wing_tip_leading_edge_x + wing_tip_chord])
    x_l3 += mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords

    # 6) Leading edge to tip (X1)
    # The line parallel to the fuselage axis joining the leading edge and the tip
    y_x1 = np.array([wing_tip_y * 1.03, wing_tip_y * 1.03])
    x_x1 = np.array([0, wing_tip_leading_edge_x])
    x_x1 += mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords

    # 7) Fuselage axis to tip
    # The line joining the fuselage axis and the line X1
    y_fuselage_to_tip = np.array([total_wing_span / 2, wing_tip_y * 1.03])
    x_fuselage_to_tip = np.array([0.0, 0.0])
    x_fuselage_to_tip += mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords

    # 7bis) Half span (Y3)
    # The line joining representing the span of the half wing
    y_y3 = np.array([0, total_wing_span / 2])
    x_y3 = np.array([0.0, 0.0])
    x_y3 += mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords

    # 8) Break
    # The line representing the kink (the break) of the wing
    y_break = np.array([wing_kink_y, wing_kink_y])
    x_break = np.array([wing_kink_leading_edge_x, wing_kink_leading_edge_x + wing_kink_chord * 1.7])
    x_break += mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords

    # 9) MAC
    # The line representing the mean aerodynamic chord of the wing
    y_mac = np.array([mean_aerodynamic_chord_y_global, mean_aerodynamic_chord_y_global])
    x_mac = np.array([distance_root_mac_chords, distance_root_mac_chords + mean_aerodynamic_chord])
    x_mac += mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords

    # 10) Perpendiculaire Down Break
    # The upper line perpendicular to the break line
    y_perp_down = np.array([wing_kink_y, wing_kink_y + (wing_tip_y - wing_kink_y) * 0.25])
    x_perp_down = np.array([wing_kink_leading_edge_x, wing_kink_leading_edge_x])
    x_perp_down += mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords

    # 11) Perpendiculaire Up Break
    # The lower line perpendicular to the break line
    y_perp_up = np.array([wing_kink_y, wing_kink_y + (wing_tip_y - wing_kink_y) * 0.25])
    x_perp_up = np.array(
        [wing_kink_leading_edge_x + wing_kink_chord, wing_kink_leading_edge_x + wing_kink_chord]
    )
    x_perp_up += mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords

    # 12) Kink chord (L2)
    # The line representing the kink chord of the wing
    y_l2 = np.array(
        [
            wing_kink_y + (wing_tip_y - wing_kink_y) * 0.25,
            wing_kink_y + (wing_tip_y - wing_kink_y) * 0.25,
        ]
    )
    x_l2 = np.array([wing_kink_leading_edge_x, wing_kink_leading_edge_x + wing_kink_chord])
    x_l2 += mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords

    # 13) Kink to leading edge (X2)
    # The line parallel to L2 and joining the line Y3 and L2
    y_x2 = np.array(
        [
            wing_kink_y + (wing_tip_y - wing_kink_y) * 0.25,
            wing_kink_y + (wing_tip_y - wing_kink_y) * 0.25,
        ]
    )
    x_x2 = np.array([wing_kink_leading_edge_x, 0])
    x_x2 += mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords

    # 14) Fuselage axis to break (Y2)
    # The line parallel to the x axis and joining the fuselage axis and the break line
    y_y2 = np.array([0, wing_kink_y])
    x_y2 = np.array(
        [
            wing_kink_leading_edge_x + wing_kink_chord * 1.4,
            wing_kink_leading_edge_x + wing_kink_chord * 1.4,
        ]
    )
    x_y2 += mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords

    # 15) Fuselage axis to MAC (Y0)
    # The line parallel to the x axis and joining the fuselage axis and the MAC line
    y_y0 = np.array([0, mean_aerodynamic_chord_y_global])
    x_y0 = np.array(
        [
            distance_root_mac_chords + mean_aerodynamic_chord,
            distance_root_mac_chords + mean_aerodynamic_chord,
        ]
    )
    x_y0 += mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords

    # 16) Perpendicular Down MAC
    # The lower line perpendicular to the MAC line
    y_down_mac = np.array(
        [
            mean_aerodynamic_chord_y_global,
            mean_aerodynamic_chord_y_global - mean_aerodynamic_chord / 2,
        ]
    )
    x_down_mac = np.array([distance_root_mac_chords, distance_root_mac_chords])
    x_down_mac += mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords

    # 17) X0
    # The line parallel to the fuselage axis and joining the line Y3 with the "Perpendicular Down MAC" line
    y_x0 = np.array(
        [
            mean_aerodynamic_chord_y_global - mean_aerodynamic_chord / 2,
            mean_aerodynamic_chord_y_global - mean_aerodynamic_chord / 2,
        ]
    )
    x_x0 = np.array([distance_root_mac_chords, 0])
    x_x0 += mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords

    # 18) L0
    # The line parallel to the fuselage axis and representing the root chord
    y_l0 = np.array([wing_root_y / 2, wing_root_y / 2])
    x_l0 = np.array([0, wing_root_chord])
    x_l0 += mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords

    # 19) Continuity trailing edge
    # The line representing the continuity of the trailing edge until the fuselage axis
    y_continuity1 = np.array([wing_kink_y, 0])
    x_continuity1 = np.array(
        [
            wing_kink_leading_edge_x + wing_kink_chord,
            wing_kink_leading_edge_x
            + wing_kink_chord
            - wing_kink_y * np.tan(np.pi * trailing_edge_kink_sweep_100_outer / 180),
        ]
    )
    x_continuity1 += mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords

    # 20) Continuity leading edge
    # The line representing the continuity of the leading edge until the fuselage axis
    y_continuity2 = np.array([wing_root_y, 0])
    x_continuity2 = np.array(
        [
            0,
            0 - wing_root_y * np.tan(np.pi * sweep_0 / 180),
        ]
    )
    x_continuity2 += mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords

    # 21) L1
    # The line joining the two previous continuity lines at the root level
    y_l1 = np.array([wing_root_y * 1.025, wing_root_y * 1.025])
    x_l1 = np.array(
        [
            wing_kink_leading_edge_x
            + wing_kink_chord
            - (wing_kink_y - wing_root_y)
            * np.sin(np.pi * trailing_edge_kink_sweep_100_outer / 180),
            0,
        ]
    )
    x_l1 += mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords

    # 22) Y1
    # The line parallel to the Y3 line joining the fuselage axis line and the L1 line
    y_y1 = np.array([0, wing_root_y])
    x_y1 = np.array([-wing_root_chord * 0.2, -wing_root_chord * 0.2])
    x_y1 += mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords

    # X) Figure
    # Here  the different points are added on the same figure. The wing is in blue and the measuring lines are in black

    if fig is None:
        fig = go.Figure()

    scatter = go.Scatter(
        x=y, y=x, line=dict(color="#636efa", width=3), mode="lines", name=name, showlegend=False
    )  # wing

    scatter_fuselage = go.Scatter(
        x=y_fuselage,
        y=x_fuselage,
        line=dict(color="black", dash="dot"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # fuselage axis

    scatter_l3 = go.Scatter(
        x=y_l3,
        y=x_l3,
        line=dict(color="black"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # L3

    scatter_x1 = go.Scatter(
        x=y_x1,
        y=x_x1,
        line=dict(color="black", dash="dot"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # X1

    scatter_fuselage_to_tip = go.Scatter(
        x=y_fuselage_to_tip,
        y=x_fuselage_to_tip,
        line=dict(color="gray", dash="dot"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # Fuselage axis to tip

    scatter_y3 = go.Scatter(
        x=y_y3,
        y=x_y3,
        line=dict(color="black"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # Y3

    scatter_break = go.Scatter(
        x=y_break,
        y=x_break,
        line=dict(color="gray", dash="dot"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # break

    scatter_mac = go.Scatter(
        x=y_mac,
        y=x_mac,
        line=dict(color="black"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # MAC

    scatter_perp_up = go.Scatter(
        x=y_perp_up,
        y=x_perp_up,
        line=dict(color="grey"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # Perpendicular up Break

    scatter_perp_down = go.Scatter(
        x=y_perp_down,
        y=x_perp_down,
        line=dict(color="grey"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # Perpendicular down Break

    scatter_l2 = go.Scatter(
        x=y_l2,
        y=x_l2,
        line=dict(color="black"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # L2

    scatter_x2 = go.Scatter(
        x=y_x2,
        y=x_x2,
        line=dict(color="black", dash="dot"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # X2

    scatter_y2 = go.Scatter(
        x=y_y2,
        y=x_y2,
        line=dict(color="black", dash="dot"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # Y2

    scatter_y0 = go.Scatter(
        x=y_y0,
        y=x_y0,
        line=dict(color="black", dash="dot"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # Y0

    scatter_down_mac = go.Scatter(
        x=y_down_mac,
        y=x_down_mac,
        line=dict(color="gray"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # Perpendicular down MAC

    scatter_x0 = go.Scatter(
        x=y_x0,
        y=x_x0,
        line=dict(color="black", dash="dot"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # X0

    scatter_l0 = go.Scatter(
        x=y_l0,
        y=x_l0,
        line=dict(color="black"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # L0

    scatter_continuity1 = go.Scatter(
        x=y_continuity1,
        y=x_continuity1,
        line=dict(color="gray", dash="dot"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # Continuity1

    scatter_continuity2 = go.Scatter(
        x=y_continuity2,
        y=x_continuity2,
        line=dict(color="gray", dash="dot"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # Continuity2

    scatter_l1 = go.Scatter(
        x=y_l1,
        y=x_l1,
        line=dict(color="black"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # L1

    scatter_y1 = go.Scatter(
        x=y_y1,
        y=x_y1,
        line=dict(color="black"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # Y1

    # Adding the lines to the figure
    fig.add_trace(scatter)
    fig.add_trace(scatter_fuselage)
    fig.add_trace(scatter_l3)
    fig.add_trace(scatter_x1)
    fig.add_trace(scatter_fuselage_to_tip)
    fig.add_trace(scatter_break)
    fig.add_trace(scatter_mac)
    fig.add_trace(scatter_perp_up)
    fig.add_trace(scatter_perp_down)
    fig.add_trace(scatter_l2)
    fig.add_trace(scatter_x2)
    fig.add_trace(scatter_y2)
    fig.add_trace(scatter_y0)
    fig.add_trace(scatter_x0)
    fig.add_trace(scatter_l0)
    fig.add_trace(scatter_down_mac)
    fig.add_trace(scatter_continuity1)
    fig.add_trace(scatter_continuity2)
    fig.add_trace(scatter_l1)
    fig.add_trace(scatter_y1)
    fig.add_trace(scatter_y3)

    # Creating the table with all the lengths of the variables
    d = {
        "Variable": [
            "X0 (m)",
            "X1 (m)",
            "X2 (m)",
            "Y0 (m)",
            "Y1 (m)",
            "Y2 (m)",
            "Y3 (m)",
            "L0 (m)",
            "L1 (m)",
            "L2 (m)",
            "L3 (m)",
            "MAC (m)",
            "Span (m)",
            "Wing surface (m²)",
        ],
        "Value": [
            np.round(x_x0[0] - x_x0[1], 1),  # X0
            np.round(x_x1[1] - x_x1[0], 1),  # X1
            np.round(x_x2[0] - x_x2[1], 1),  # X2
            np.round(y_y0[1] - y_y0[0], 1),  # Y0
            np.round(y_y1[1] - y_y1[0], 1),  # Y1
            np.round(y_y2[1] - y_y2[0], 1),  # Y2
            np.round(y_y3[1] - y_y3[0], 1),  # Y3
            np.round(x_l0[1] - x_l0[0], 1),  # L0
            np.round(x_l1[0] - x_l1[1], 1),  # L1
            np.round(x_l2[1] - x_l2[0], 1),  # L2
            np.round(x_l3[1] - x_l3[0], 1),  # L3
            np.round(mean_aerodynamic_chord, 1),  # MAC
            np.round(total_wing_span, 1),  # Span
            np.round(wing_area, 1),  # Wing surface
        ],
    }
    df = pd.DataFrame(data=d)
    out = widgets.Output()
    with out:
        display(df)

    # Adding all the notes to the lines
    fig.add_annotation(
        x=wing_tip_y * 1.03,
        y=(wing_tip_leading_edge_x / 2)
        + mac25_x_position
        - 0.25 * mean_aerodynamic_chord
        - distance_root_mac_chords,
        text="X1",
        showarrow=True,
        arrowhead=1,
    )
    fig.add_annotation(
        x=wing_tip_y * 1.03,
        y=wing_tip_leading_edge_x
        + wing_tip_chord
        + mac25_x_position
        - 0.25 * mean_aerodynamic_chord
        - distance_root_mac_chords,
        text="L3",
        showarrow=True,
        arrowhead=1,
    )
    fig.add_annotation(
        x=0,
        y=wing_root_chord * 1.6
        + mac25_x_position
        - 0.25 * mean_aerodynamic_chord
        - distance_root_mac_chords,
        text="Fuselage axis",
        showarrow=True,
        arrowhead=1,
    )
    fig.add_annotation(
        x=3 * total_wing_span / 8,
        y=mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords,
        text="Y3",
        showarrow=True,
        arrowhead=1,
    )
    fig.add_annotation(
        x=wing_kink_y,
        y=wing_kink_leading_edge_x
        + wing_kink_chord * 1.7
        + mac25_x_position
        - 0.25 * mean_aerodynamic_chord
        - distance_root_mac_chords,
        text="Break",
        showarrow=True,
        arrowhead=1,
    )
    fig.add_annotation(
        x=mean_aerodynamic_chord_y_global * 1.08,
        y=distance_root_mac_chords
        + mean_aerodynamic_chord / 2
        + mac25_x_position
        - 0.25 * mean_aerodynamic_chord
        - distance_root_mac_chords,
        text="MAC",
        showarrow=False,
        yshift=0,
    )
    fig.add_annotation(
        x=wing_kink_y + (wing_tip_y - wing_kink_y) * 0.25,
        y=wing_kink_leading_edge_x
        + wing_kink_chord / 2
        + mac25_x_position
        - 0.25 * mean_aerodynamic_chord
        - distance_root_mac_chords,
        text="L2",
        showarrow=True,
        arrowhead=1,
    )
    fig.add_annotation(
        x=(wing_kink_y + (wing_tip_y - wing_kink_y) * 0.25),
        y=distance_root_mac_chords / 4
        + mac25_x_position
        - 0.25 * mean_aerodynamic_chord
        - distance_root_mac_chords,
        text="X2",
        showarrow=True,
        arrowhead=1,
    )
    fig.add_annotation(
        x=3 * wing_kink_y / 4,
        y=wing_kink_leading_edge_x
        + wing_kink_chord * 1.4
        + mac25_x_position
        - 0.25 * mean_aerodynamic_chord
        - distance_root_mac_chords,
        text="Y2",
        showarrow=True,
        arrowhead=1,
    )
    fig.add_annotation(
        x=wing_kink_y / 4,
        y=distance_root_mac_chords
        + mean_aerodynamic_chord
        + mac25_x_position
        - 0.25 * mean_aerodynamic_chord
        - distance_root_mac_chords,
        text="Y0",
        showarrow=True,
        arrowhead=1,
    )
    fig.add_annotation(
        x=mean_aerodynamic_chord_y_global - mean_aerodynamic_chord / 2,
        y=3 * distance_root_mac_chords / 4
        + mac25_x_position
        - 0.25 * mean_aerodynamic_chord
        - distance_root_mac_chords,
        text="X0",
        showarrow=True,
        arrowhead=1,
    )
    fig.add_annotation(
        x=(wing_root_y / 2),
        y=wing_root_chord / 3
        + mac25_x_position
        - 0.25 * mean_aerodynamic_chord
        - distance_root_mac_chords,
        text="L0",
        showarrow=True,
        arrowhead=1,
    )
    fig.add_annotation(
        x=wing_root_y * 1.25,
        y=wing_root_chord / 2
        + mac25_x_position
        - 0.25 * mean_aerodynamic_chord
        - distance_root_mac_chords,
        text="L1",
        showarrow=False,
        yshift=0,
    )
    fig.add_annotation(
        x=wing_root_y * 0.05,
        y=-wing_root_chord * 0.2
        + mac25_x_position
        - 0.25 * mean_aerodynamic_chord
        - distance_root_mac_chords,
        text="Y1",
        showarrow=True,
        arrowhead=1,
    )

    fig = go.FigureWidget(fig)
    fig.update_yaxes(constrain="domain")
    fig.update_xaxes(constrain="domain")
    fig.update_layout(
        title_text=name,
        title_x=0.8,
        title_y=0.98,
        xaxis_title="y",
        yaxis_title="x",
        height=height,
        width=width,
    )

    return widgets.HBox([fig, out])


def flaps_and_slats_drawing(
    aircraft_file_path: str,
    name=None,
    fig=None,
    file_formatter=None,
    height=500,
    width=900,
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
    :param height : height of the image
    :param width : width of the image
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

    # Inboard flap
    # Part of the code dedicated to the inboard flap

    y_inboard = np.array([wing_kink_y, wing_kink_y, wing_root_y, wing_root_y, wing_kink_y])
    y_inboard = np.concatenate((-y_inboard, y_inboard))

    x_inboard = np.array(
        [
            wing_root_chord,
            wing_root_chord - flap_chord_kink,
            wing_root_chord - flap_chord_kink,
            wing_root_chord,
            wing_root_chord,
        ]
    )

    x_inboard = (
        x_inboard + mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords
    )
    # pylint: disable=invalid-name # that's a common naming
    x_inboard = np.concatenate((x_inboard, x_inboard))

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

    y_outboard = np.array([y_te_1, y_te_2, y_ow_1, y_ow_2, y_te_1])
    y_outboard = np.concatenate((-y_outboard, y_outboard))

    x_outboard = np.array([x_te_1, x_te_2, x_ow_1, x_ow_2, x_te_1])

    x_outboard = (
        x_outboard + mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords
    )
    # pylint: disable=invalid-name # that's a common naming
    x_outboard = np.concatenate((x_outboard, x_outboard))

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

    # 3) Figure
    # Here  the different points are added on the same figure. The wing is in blue and the high lift devices in red

    if fig is None:
        fig = go.Figure()

    scatter = go.Scatter(
        x=y, y=x, line=dict(color="blue"), mode="lines", name=name, showlegend=False
    )  # wing
    scatter_inboard = go.Scatter(
        x=y_inboard,
        y=x_inboard,
        mode="lines",
        line=dict(color="#636efa", width=1),
        name=name,
        showlegend=False,
    )  # first flap
    scatter_outboard = go.Scatter(
        x=y_outboard,
        y=x_outboard,
        mode="lines",
        line=dict(color="#636efa", width=1),
        name=name,
        showlegend=False,
    )  # second flap
    scatter_design_line = go.Scatter(
        x=y_design_line,
        y=x_design_line,
        mode="lines",
        line=dict(color="#636efa"),
        name=name,
        showlegend=False,
    )  # design line
    scatter_slats_left = go.Scatter(
        x=y_slats_left,
        y=x_slats_left,
        line=dict(color="#636efa", width=1),
        mode="lines",
        name=name,
        showlegend=False,
    )  # slats
    scatter_slats_right = go.Scatter(
        x=y_slats_right,
        y=x_slats_right,
        line=dict(color="#636efa", width=1),
        mode="lines",
        name=name,
        showlegend=False,
    )  # slats

    fig.layout = go.Layout(yaxis=dict(scaleanchor="x", scaleratio=1))

    fig.add_trace(scatter)
    fig.add_trace(scatter_outboard)
    fig.add_trace(scatter_inboard)
    fig.add_trace(scatter_design_line)
    fig.add_trace(scatter_slats_left)
    fig.add_trace(scatter_slats_right)

    fig = go.FigureWidget(fig)
    fig.update_xaxes(constrain="domain")
    fig.update_yaxes(constrain="domain")
    fig.update_layout(
        title_text=name,
        title_x=0.5,
        xaxis_title="y",
        yaxis_title="x",
        height=height,
        width=width,
    )

    return fig


def aircraft_drawing_side_view(
    aircraft_file_path: str,
    name=None,
    fig=None,
    file_formatter=None,
    height=500,
    width=900,
) -> go.FigureWidget:
    """
    Returns a figure plot of the side view of the aircraft with the engines, the flaps, the slats and the elevator.
    Different designs can be superposed by providing an existing fig.
    Each design can be provided a name.

    :param aircraft_file_path: path of data file
    :param name: name to give to the trace added to the figure
    :param fig: existing figure to which add the plot
    :param file_formatter: the formatter that defines the format of data file. If not provided,
                           default format will be assumed.
    :param height : height of the image
    :param width : width of the image
    :return: wing plot figure
    """
    variables = VariableIO(aircraft_file_path, file_formatter).read()

    # Wing parameters
    wing_tip_leading_edge_x = variables["data:geometry:wing:tip:leading_edge:x:local"].value[0]
    wing_root_chord = variables["data:geometry:wing:root:chord"].value[0]
    wing_tip_chord = variables["data:geometry:wing:tip:chord"].value[0]
    wing_kink_chord = variables["data:geometry:wing:kink:chord"].value[0]
    wing_kink_leading_edge_x = variables["data:geometry:wing:kink:leading_edge:x:local"].value[0]
    mac25_x_position = variables["data:geometry:wing:MAC:at25percent:x"].value[0]
    distance_root_mac_chords = variables["data:geometry:wing:MAC:leading_edge:x:local"].value[0]
    mean_aerodynamic_chord = variables["data:geometry:wing:MAC:length"].value[0]

    # Horizontal tail parameters
    ht_root_chord = variables["data:geometry:horizontal_tail:root:chord"].value[0]
    ht_tip_chord = variables["data:geometry:horizontal_tail:tip:chord"].value[0]
    ht_sweep_0 = variables["data:geometry:horizontal_tail:sweep_0"].value[0]
    local_ht_25mac_x = variables["data:geometry:horizontal_tail:MAC:at25percent:x:local"].value[0]
    ht_distance_from_wing = variables[
        "data:geometry:horizontal_tail:MAC:at25percent:x:from_wingMAC25"
    ].value[0]
    ht_span = variables["data:geometry:horizontal_tail:span"].value[0]

    # Vertical tail parameters
    vt_root_chord = variables["data:geometry:vertical_tail:root:chord"].value[0]
    vt_tip_chord = variables["data:geometry:vertical_tail:tip:chord"].value[0]
    vt_sweep_0 = variables["data:geometry:vertical_tail:sweep_0"].value[0]
    local_vt_25mac_x = variables["data:geometry:vertical_tail:MAC:at25percent:x:local"].value[0]
    vt_distance_from_wing = variables[
        "data:geometry:vertical_tail:MAC:at25percent:x:from_wingMAC25"
    ].value[0]
    vt_span = variables["data:geometry:vertical_tail:span"].value[0]

    # CGs
    wing_25mac_x = variables["data:geometry:wing:MAC:at25percent:x"].value[0]
    wing_mac_length = variables["data:geometry:wing:MAC:length"].value[0]
    local_wing_mac_le_x = variables["data:geometry:wing:MAC:leading_edge:x:local"].value[0]

    # Fuselage parameters
    fuselage_max_height = variables["data:geometry:fuselage:maximum_height"].value[0]
    fuselage_length = variables["data:geometry:fuselage:length"].value[0]
    fuselage_front_length = variables["data:geometry:fuselage:front_length"].value[0]
    fuselage_rear_length = variables["data:geometry:fuselage:rear_length"].value[0]

    # Nacelle and pylon values parameters :
    nacelle_diameter = variables["data:geometry:propulsion:nacelle:diameter"].value[0]
    nacelle_length = variables["data:geometry:propulsion:nacelle:length"].value[0]
    pylon_length = variables["data:geometry:propulsion:pylon:length"]

    """
    Side view : x-z
    """
    # 1 fuselage

    z_fuselage_front = np.flip(np.linspace(0, fuselage_max_height / 2, 10))
    x_fuselage_front = (
        fuselage_front_length / (0.5 * fuselage_max_height) ** 2 * z_fuselage_front ** 2
    )

    z_nose_cone = np.linspace(-fuselage_max_height / 8.0, fuselage_max_height / 8.0, 100)
    x_nose_cone = fuselage_front_length / (0.5 * fuselage_max_height) ** 2 * z_nose_cone ** 2

    z_nose_cone = np.append(z_nose_cone, z_nose_cone[0])
    x_nose_cone = np.append(x_nose_cone, x_nose_cone[0])

    z_cockpit = np.linspace(
        fuselage_max_height / 2.0 * 1 / 5, fuselage_max_height / 2.0 * 3.5 / 5, 50
    )
    x_cockpit = fuselage_front_length / (0.5 * fuselage_max_height) ** 2 * z_cockpit ** 2

    z_cockpit = np.append(z_cockpit, z_cockpit[-1])
    z_cockpit = np.append(z_cockpit, z_cockpit[0])
    z_cockpit = np.append(z_cockpit, z_cockpit[0])
    x_cockpit = np.append(x_cockpit, fuselage_front_length * 4 / 5)
    x_cockpit = np.append(x_cockpit, fuselage_front_length * 4 / 5)
    x_cockpit = np.append(x_cockpit, x_cockpit[0])

    x_fuselage_middle = np.array(
        [
            fuselage_front_length,
            fuselage_length - fuselage_rear_length,
        ]
    )

    z_fuselage_middle = np.array(
        [
            fuselage_max_height / 2.0,
            fuselage_max_height / 2.0,
        ]
    )

    r = fuselage_max_height / 8
    x_fuselage_rear = np.array([fuselage_length - fuselage_rear_length, fuselage_length - r])

    z_fuselage_rear = np.array([fuselage_max_height / 2.0, fuselage_max_height / 2.0])

    z_centre = fuselage_max_height / 2.0 - r
    x_centre = fuselage_length - r

    z_rear = np.linspace(fuselage_max_height / 2.0, fuselage_max_height / 2.0 - 2 * r, 10)
    x_rear = np.sqrt(abs(r ** 2 - (z_rear - z_centre) ** 2)) + x_centre

    x_fuselage_front = np.concatenate((x_fuselage_front, np.flip(x_fuselage_front)))
    z_fuselage_front = np.concatenate((z_fuselage_front, np.flip(-z_fuselage_front)))

    x_belly = np.array(
        [fuselage_front_length, fuselage_length - fuselage_rear_length, fuselage_length - r]
    )
    z_belly = np.array(
        [-fuselage_max_height / 2.0, -fuselage_max_height / 2.0, fuselage_max_height / 2.0 - 2 * r]
    )

    # 2 wing

    x_wing = np.array(
        [
            0.0,
            wing_root_chord,
            wing_kink_leading_edge_x + wing_kink_chord,
            wing_tip_leading_edge_x + wing_tip_chord,
            wing_tip_leading_edge_x,
            0.0,
        ]
    )
    x_wing = x_wing + (mac25_x_position - distance_root_mac_chords - 0.25 * mean_aerodynamic_chord)

    z_wing = np.array(
        [
            -fuselage_max_height * WING_ROOT_HEIGHT,
            -fuselage_max_height * WING_ROOT_HEIGHT,
            -fuselage_max_height / 8.0,
            0.0,
            0.0,
            -fuselage_max_height * WING_ROOT_HEIGHT,
        ]
    )

    # 3 engine

    x_engine = np.array([-nacelle_length, -nacelle_length, 0, 0, -nacelle_length])

    x_engine += (
        wing_25mac_x
        - 0.25 * wing_mac_length
        - local_wing_mac_le_x
        + NACELLE_POSITION * nacelle_length
    )
    z_engine = np.array(
        [
            -fuselage_max_height * ENGINE_HEIGHT + nacelle_diameter / 2.0,
            -fuselage_max_height * ENGINE_HEIGHT - nacelle_diameter / 2.0,
            -fuselage_max_height * ENGINE_HEIGHT - nacelle_diameter / 2.0,
            -fuselage_max_height * ENGINE_HEIGHT + nacelle_diameter / 2.0,
            -fuselage_max_height * ENGINE_HEIGHT + nacelle_diameter / 2.0,
        ]
    )

    # 4 vertical tail

    x_vt = np.array(
        [
            0.0,
            vt_span * np.tan(vt_sweep_0 * pi / 180),
            vt_span * np.tan(vt_sweep_0 * pi / 180) + vt_tip_chord,
            vt_root_chord,
            0.0,
        ]
    )
    x_vt += wing_25mac_x + vt_distance_from_wing - local_vt_25mac_x
    z_vt = np.array(
        [
            fuselage_max_height / 2.0,
            fuselage_max_height / 2.0 + vt_span,
            fuselage_max_height / 2.0 + vt_span,
            fuselage_max_height / 2.0,
            fuselage_max_height / 2.0,
        ]
    )

    # 5 horizontal tail

    x_ht = np.array(
        [
            0.0,
            ht_span / 2.0 * np.tan(ht_sweep_0 * pi / 180),
            ht_tip_chord + ht_span / 2.0 * np.tan(ht_sweep_0 * pi / 180),
            ht_root_chord,
            0.0,
        ]
    )
    x_ht += wing_25mac_x + ht_distance_from_wing - local_ht_25mac_x

    z_ht = np.array(
        [
            fuselage_max_height * HT_HEIGHT,
            fuselage_max_height * HT_DIHEDRAL,
            fuselage_max_height * HT_DIHEDRAL,
            fuselage_max_height * HT_HEIGHT,
            fuselage_max_height * HT_HEIGHT,
        ]
    )

    """
    fig plotting
    """
    scatter_front = go.Scatter(
        x=x_fuselage_front,
        y=z_fuselage_front,
        line=dict(color="blue"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # Aircraft front

    scatter_middle = go.Scatter(
        x=x_fuselage_middle,
        y=z_fuselage_middle,
        line=dict(color="blue"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # Aircraft middle

    scatter_fuselage_rear = go.Scatter(
        x=x_fuselage_rear,
        y=z_fuselage_rear,
        line=dict(color="blue"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # Aircraft rear

    scatter_rear = go.Scatter(
        x=x_rear,
        y=z_rear,
        line=dict(color="blue"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # Aircraft rear

    scatter_belly = go.Scatter(
        x=x_belly,
        y=z_belly,
        line=dict(color="blue"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # Aircraft belly

    scatter_wing = go.Scatter(
        x=x_wing,
        y=z_wing,
        line=dict(color="blue"),
        mode="lines",
        name=name,
        showlegend=False,
    )

    scatter_engine = go.Scatter(
        x=x_engine,
        y=z_engine,
        fill="tonexty",
        line=dict(color="blue"),
        mode="lines",
        name=name,
        showlegend=False,
    )

    scatter_ht = go.Scatter(
        x=x_ht,
        y=z_ht,
        line=dict(color="blue"),
        fill="tonexty",
        mode="lines",
        name=name,
        showlegend=False,
    )

    scatter_vt = go.Scatter(
        x=x_vt,
        y=z_vt,
        line=dict(color="blue"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # Aircraft nose cone

    scatter_nose_cone = go.Scatter(
        x=x_nose_cone,
        y=z_nose_cone,
        line=dict(color="blue"),
        fill="tonexty",
        mode="lines",
        name=name,
        showlegend=False,
    )  # Aircraft nose cone

    scatter_cockpit = go.Scatter(
        x=x_cockpit,
        y=z_cockpit,
        line=dict(color="blue"),
        mode="lines",
        name=name,
        showlegend=False,
    )  # Aircraft cockpit

    if fig is None:
        fig = go.Figure()

    fig.add_trace(scatter_front)
    fig.add_trace(scatter_middle)
    fig.add_trace(scatter_rear)
    fig.add_trace(scatter_fuselage_rear)
    fig.add_trace(scatter_belly)
    fig.add_trace(scatter_vt)
    fig.add_trace(scatter_cockpit)
    fig.add_trace(scatter_wing)
    fig.add_trace(scatter_engine)
    fig.add_trace(scatter_ht)
    fig.add_trace(scatter_nose_cone)

    fig.layout = go.Layout(yaxis=dict(scaleanchor="x", scaleratio=1))

    if name is None:
        fig.update_layout(
            title_text="Aircraft Geometry (side view)",
            title_x=0.5,
            xaxis_title="y",
            yaxis_title="z",
            height=height,
            width=width,
        )
    if name is not None:
        fig.update_layout(
            title_text=name,
            title_x=0.5,
            xaxis_title="y",
            yaxis_title="z",
            height=height,
            width=width,
        )
    fig = go.FigureWidget(fig)
    return fig


def aircraft_drawing_front_view(
    aircraft_file_path: str,
    name=None,
    fig=None,
    file_formatter=None,
    height=500,
    width=900,
) -> go.FigureWidget:
    """
    Returns a figure plot of the front view of the aircraft with the engines, the flaps, the slats and the elevator.
    Different designs can be superposed by providing an existing fig.
    Each design can be provided a name.

    :param aircraft_file_path: path of data file
    :param name: name to give to the trace added to the figure
    :param fig: existing figure to which add the plot
    :param file_formatter: the formatter that defines the format of data file. If not provided,
                           default format will be assumed.
    :param height : height of the image
    :param width : width of the image
    :return: wing plot figure
    """
    variables = VariableIO(aircraft_file_path, file_formatter).read()

    # Wing parameters
    wing_tip_y = variables["data:geometry:wing:tip:y"].value[0]

    # Horizontal tail parameters
    ht_span = variables["data:geometry:horizontal_tail:span"].value[0]

    # Vertical tail parameters
    vt_span = variables["data:geometry:vertical_tail:span"].value[0]

    # Fuselage parameters
    fuselage_max_height = variables["data:geometry:fuselage:maximum_height"].value[0]
    fuselage_max_width = variables["data:geometry:fuselage:maximum_width"].value[0]

    # Nacelle and pylon values parameters :
    nacelle_diameter = variables["data:geometry:propulsion:nacelle:diameter"].value[0]
    nacelle_y = variables["data:geometry:propulsion:nacelle:y"].value[0]

    """
    Front view (y-z)
    """
    # fuselage
    y_fuselage = np.linspace(-fuselage_max_width / 2.0, fuselage_max_width / 2.0, 100)
    z_fuselage = (
        np.sqrt(1 - (y_fuselage / (fuselage_max_width / 2.0)) ** 2) * fuselage_max_height / 2.0
    )
    y_fuselage2 = y_fuselage
    z_fuselage2 = -z_fuselage
    y_fuselage3, z_fuselage3 = make_circle(
        0, -fuselage_max_height * 1 / 10, fuselage_max_height / 8.0
    )

    # wing
    z_wing = np.array(
        [
            -fuselage_max_height * WING_ROOT_HEIGHT,
            0.0,
        ]
    )

    y_wing = np.array(
        [
            np.sqrt(1 - (z_wing[0] / (fuselage_max_height / 2.0)) ** 2) * fuselage_max_width / 2.0,
            wing_tip_y,
        ]
    )

    z_wing2 = 1 * z_wing
    y_wing2 = -1 * y_wing

    # engine
    z_engine_center = -fuselage_max_height * ENGINE_HEIGHT
    y_engine_center = nacelle_y

    y_engine, z_engine = make_circle(y_engine_center, z_engine_center, nacelle_diameter / 2.0)
    y_engine2, z_engine2 = make_circle(-y_engine_center, z_engine_center, nacelle_diameter / 2.0)
    y_engine3, z_engine3 = make_circle(y_engine_center, z_engine_center, nacelle_diameter / 8.0)
    y_engine4, z_engine4 = make_circle(
        -1 * y_engine_center, z_engine_center, nacelle_diameter / 8.0
    )

    # ht
    z_ht = np.array(
        [
            fuselage_max_height * HT_HEIGHT,
            fuselage_max_height * HT_DIHEDRAL,
        ]
    )

    y_ht = np.array(
        [
            np.sqrt(1 - (z_ht[0] / (fuselage_max_height / 2.0)) ** 2) * fuselage_max_width / 2.0,
            ht_span / 2.0,
        ]
    )

    y_ht2 = -1 * y_ht
    z_ht2 = 1 * z_ht

    # vt

    y_vt = np.array([0, 0])
    z_vt = np.array([fuselage_max_height / 2.0, fuselage_max_height / 2.0 + vt_span])

    # cockpit

    y_cockpit = np.array(
        [
            fuselage_max_width / 2.0 * 2.5 / 5,
            fuselage_max_width / 2.0 * 3.5 / 5,
            -fuselage_max_width / 2.0 * 3.5 / 5,
            -fuselage_max_width / 2.0 * 2.5 / 5,
            fuselage_max_width / 2.0 * 2.5 / 5,
        ]
    )

    z_cockpit = np.array(
        [
            fuselage_max_height / 2.0 * 3.5 / 5,
            fuselage_max_height / 2.0 * 1 / 5,
            fuselage_max_height / 2.0 * 1 / 5,
            fuselage_max_height / 2.0 * 3.5 / 5,
            fuselage_max_height / 2.0 * 3.5 / 5,
        ]
    )

    y_cockpit2 = np.array([0, 0])
    z_cockpit2 = np.array(
        [
            fuselage_max_height / 2.0 * 3.5 / 5,
            fuselage_max_height / 2.0 * 1 / 5,
        ]
    )

    scatter_fuselage = go.Scatter(
        x=y_fuselage,
        y=z_fuselage,
        line=dict(color="blue"),
        mode="lines",
        name=name,
        showlegend=False,
    )

    scatter_fuselage2 = go.Scatter(
        x=y_fuselage2,
        y=z_fuselage2,
        line=dict(color="blue"),
        mode="lines",
        name=name,
        showlegend=False,
    )

    scatter_wing = go.Scatter(
        x=y_wing,
        y=z_wing,
        line=dict(color="blue"),
        mode="lines",
        name=name,
        showlegend=False,
    )

    scatter_wing2 = go.Scatter(
        x=y_wing2,
        y=z_wing2,
        line=dict(color="blue"),
        mode="lines",
        name=name,
        showlegend=False,
    )

    scatter_engine = go.Scatter(
        x=y_engine,
        y=z_engine,
        line=dict(color="blue"),
        mode="lines",
        name=name,
        showlegend=False,
    )

    scatter_engine2 = go.Scatter(
        x=y_engine2,
        y=z_engine2,
        line=dict(color="blue"),
        mode="lines",
        name=name,
        showlegend=False,
    )

    scatter_engine3 = go.Scatter(
        x=y_engine3,
        y=z_engine3,
        line=dict(color="blue"),
        mode="lines",
        name=name,
        showlegend=False,
    )

    scatter_engine4 = go.Scatter(
        x=y_engine4,
        y=z_engine4,
        line=dict(color="blue"),
        fill="tonexty",
        mode="lines",
        name=name,
        showlegend=False,
    )

    scatter_fuselage3 = go.Scatter(
        x=y_fuselage3,
        y=z_fuselage3,
        line=dict(color="blue"),
        fill="tonexty",
        mode="lines",
        name=name,
        showlegend=False,
    )

    scatter_ht = go.Scatter(
        x=y_ht,
        y=z_ht,
        line=dict(color="blue"),
        mode="lines",
        name=name,
        showlegend=False,
    )

    scatter_ht2 = go.Scatter(
        x=y_ht2,
        y=z_ht2,
        line=dict(color="blue"),
        mode="lines",
        name=name,
        showlegend=False,
    )
    scatter_vt = go.Scatter(
        x=y_vt,
        y=z_vt,
        line=dict(color="blue"),
        mode="lines",
        name=name,
        showlegend=False,
    )

    scatter_cockpit = go.Scatter(
        x=y_cockpit,
        y=z_cockpit,
        line=dict(color="blue"),
        mode="lines",
        name=name,
        showlegend=False,
    )

    scatter_cockpit2 = go.Scatter(
        x=y_cockpit2,
        y=z_cockpit2,
        line=dict(color="blue"),
        mode="lines",
        name=name,
        showlegend=False,
    )

    if fig is None:
        fig = go.Figure()

    fig.add_trace(scatter_fuselage)
    fig.add_trace(scatter_fuselage2)
    fig.add_trace(scatter_wing)
    fig.add_trace(scatter_wing2)
    fig.add_trace(scatter_ht)
    fig.add_trace(scatter_ht2)
    fig.add_trace(scatter_vt)
    fig.add_trace(scatter_cockpit)
    fig.add_trace(scatter_cockpit2)
    fig.add_trace(scatter_engine)
    fig.add_trace(scatter_engine2)
    fig.add_trace(scatter_engine3)
    fig.add_trace(scatter_fuselage3)
    fig.add_trace(scatter_engine4)

    fig.layout = go.Layout(yaxis=dict(scaleanchor="x", scaleratio=1))

    fig = go.FigureWidget(fig)
    if name is None:
        fig.update_layout(
            title_text="Aircraft Geometry (front view)",
            title_x=0.5,
            xaxis_title="y",
            yaxis_title="z",
            height=height,
            width=width,
        )
    if name is not None:
        fig.update_layout(
            title_text=name,
            title_x=0.5,
            xaxis_title="y",
            yaxis_title="z",
            height=height,
            width=width,
        )
    return fig


def make_circle(center_x: float, center_y: float, radius: float):
    """
    Inner function used in the functions above
    returns 2 ndarrays containing a the x and y coordinates of a circle of radius centered in (center_x,center_y)
    :param center_x : x coordinate of the circle's center
    :param center_y : y coordinate of the circle's center
    :param radius : radius of the circle

    :return : 2 ndarrays with the circle coordinates
    """

    x = np.linspace(-radius, radius, 50)
    y = np.sqrt(radius ** 2 - x ** 2)
    x = np.concatenate((x, np.flip(x)))
    y = np.concatenate((y, -y))

    x = np.append(x, x[0])
    y = np.append(y, y[0])

    x += center_x
    y += center_y

    return x, y
