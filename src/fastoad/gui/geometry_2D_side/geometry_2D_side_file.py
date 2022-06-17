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
from plotly.subplots import make_subplots

pi = np.pi

from fastoad.io import VariableIO

COLS = plotly.colors.DEFAULT_PLOTLY_COLORS
NACELLE_POSITION = 0.6  # Nacelle position compared to the leading edge. 0 means that the back of the nacelle is aligned with the beginning of the root, 1 means that the beginning of the nacelle is aligned with the kink_x.
HT_HEIGHT = 0.3
HT_DIHEDRAL = 0.42
ENGINE_HEIGHT = 0.9  # Heigth of the middle of the ingine 0.0 means on the center line   1.0 means the middle of the engine is just on the lower line of the aircraft


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

    x_engine = np.array([-nacelle_length, -nacelle_length, 0, 0, -nacelle_length])

    x_engine += (
        wing_25mac_x
        - 0.25 * wing_mac_length
        - local_wing_mac_le_x
        + NACELLE_POSITION * nacelle_length
    )
    z_engine = np.array(
        [
            -fuselage_max_height / 2.0 * ENGINE_HEIGHT + nacelle_diameter / 4.0,
            -fuselage_max_height / 2.0 * ENGINE_HEIGHT - nacelle_diameter / 4.0,
            -fuselage_max_height / 2.0 * ENGINE_HEIGHT - nacelle_diameter / 4.0,
            -fuselage_max_height / 2.0 * ENGINE_HEIGHT + nacelle_diameter / 4.0,
            -fuselage_max_height / 2.0 * ENGINE_HEIGHT + nacelle_diameter / 4.0,
        ]
    )

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
            -fuselage_max_height / 4.0,
            -fuselage_max_height / 4.0,
            -fuselage_max_height / 8.0,
            0.0,
            0.0,
            -fuselage_max_height / 4.0,
        ]
    )

    z_fuselage_front = np.flip(np.linspace(0, fuselage_max_height / 2, 10))
    x_fuselage_front = (
        fuselage_front_length / (0.5 * fuselage_max_height) ** 2 * z_fuselage_front ** 2
    )

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

    if fig is None:
        fig = go.Figure()

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
        x=x_vt, y=z_vt, line=dict(color="blue"), mode="lines", name=name, showlegend=False
    )

    fig.add_trace(
        scatter_front,
    )
    fig.add_trace(
        scatter_middle,
    )
    fig.add_trace(
        scatter_rear,
    )
    fig.add_trace(
        scatter_fuselage_rear,
    )
    fig.add_trace(
        scatter_belly,
    )
    fig.add_trace(
        scatter_wing,
    )
    fig.add_trace(
        scatter_engine,
    )
    fig.add_trace(
        scatter_ht,
    )
    fig.add_trace(
        scatter_vt,
    )

    fig.layout = go.Layout(yaxis=dict(scaleanchor="x", scaleratio=1))

    fig = go.FigureWidget(fig)

    fig.update_layout(
        title_text="Aircraft Geometry (side view)", title_x=0.5, xaxis_title="x", yaxis_title="y"
    )

    return fig


def aircraft_drawing_front_view_plot(
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
    Front view 
    """
    x_fuselage = np.linspace(-fuselage_max_height / 2.0, fuselage_max_height / 2.0, 10)
    y_fuselage = np.sqrt(abs((fuselage_max_height / 2.0) ** 2 - x_fuselage ** 2))
    if fig is None:
        fig = go.Figure()

    scatter_fuselage = go.Scatter(
        x=x_fuselage,
        y=y_fuselage,
        line=dict(color="blue"),
        mode="lines",
        name=name,
        showlegend=False,
    )
    fig.add_trace(scatter_fuselage)

    fig.layout = go.Layout(yaxis=dict(scaleanchor="x", scaleratio=1))

    fig = go.FigureWidget(fig)

    fig.update_layout(
        title_text="Aircraft Geometry (front view)", title_x=0.5, xaxis_title="x", yaxis_title="y"
    )
    return fig
