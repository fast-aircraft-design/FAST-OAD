"""
Defines the analysis and plotting functions for postprocessing
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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
from plotly.subplots import make_subplots

COLS = plotly.colors.DEFAULT_PLOTLY_COLORS


def wing_geometry_plot(
    aircraft_file_path: str, name=None, fig=None, file_formatter=None
) -> go.FigureWidget:
    """
    Returns a figure plot of the top view of the wing.
    Different designs can be superposed by providing an existing fig.
    Each design can be provided a name.

    :param aircraft_file_path: path of data file
    :param name: name to give to the trace added to the figure
    :param fig: existing figure to which add the plot
    :param file_formatter: the formatter that defines the format of data file. If not provided, default format will
                           be assumed.
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
    # pylint: disable=invalid-name # that's a common naming
    x = np.concatenate((x, x))

    if fig is None:
        fig = go.Figure()

    scatter = go.Scatter(x=y, y=x, mode="lines+markers", name=name)

    fig.add_trace(scatter)

    fig.layout = go.Layout(yaxis=dict(scaleanchor="x", scaleratio=1))

    fig = go.FigureWidget(fig)

    fig.update_layout(
        title_text="Wing Geometry", title_x=0.5, xaxis_title="y", yaxis_title="x",
    )

    return fig


# pylint: disable-msg=too-many-locals
def aircraft_geometry_plot(
    aircraft_file_path: str, name=None, fig=None, file_formatter=None
) -> go.FigureWidget:
    """
    Returns a figure plot of the top view of the wing.
    Different designs can be superposed by providing an existing fig.
    Each design can be provided a name.

    :param aircraft_file_path: path of data file
    :param name: name to give to the trace added to the figure
    :param fig: existing figure to which add the plot
    :param file_formatter: the formatter that defines the format of data file. If not provided, default format will
                           be assumed.
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

    # Horizontal Tail parameters
    ht_root_chord = variables["data:geometry:horizontal_tail:root:chord"].value[0]
    ht_tip_chord = variables["data:geometry:horizontal_tail:tip:chord"].value[0]
    ht_span = variables["data:geometry:horizontal_tail:span"].value[0]
    ht_sweep_0 = variables["data:geometry:horizontal_tail:sweep_0"].value[0]

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

    # CGs
    wing_25mac_x = variables["data:geometry:wing:MAC:at25percent:x"].value[0]
    wing_mac_length = variables["data:geometry:wing:MAC:length"].value[0]
    local_wing_mac_le_x = variables["data:geometry:wing:MAC:leading_edge:x:local"].value[0]
    local_ht_25mac_x = variables["data:geometry:horizontal_tail:MAC:at25percent:x:local"].value[0]
    ht_distance_from_wing = variables[
        "data:geometry:horizontal_tail:MAC:at25percent:x:from_wingMAC25"
    ].value[0]

    x_wing = x_wing + wing_25mac_x - 0.25 * wing_mac_length - local_wing_mac_le_x
    x_ht = x_ht + wing_25mac_x + ht_distance_from_wing - local_ht_25mac_x

    # pylint: disable=invalid-name # that's a common naming
    x = np.concatenate((x_fuselage, x_wing, x_ht))
    # pylint: disable=invalid-name # that's a common naming
    y = np.concatenate((y_fuselage, y_wing, y_ht))

    # pylint: disable=invalid-name # that's a common naming
    y = np.concatenate((-y, y))
    # pylint: disable=invalid-name # that's a common naming
    x = np.concatenate((x, x))

    if fig is None:
        fig = go.Figure()

    scatter = go.Scatter(x=y, y=x, mode="lines+markers", name=name)

    fig.add_trace(scatter)

    fig.layout = go.Layout(yaxis=dict(scaleanchor="x", scaleratio=1))

    fig = go.FigureWidget(fig)

    fig.update_layout(
        title_text="Aircraft Geometry", title_x=0.5, xaxis_title="y", yaxis_title="x",
    )

    return fig


def drag_polar_plot(
    aircraft_file_path: str, name=None, fig=None, file_formatter=None
) -> go.FigureWidget:
    """
    Returns a figure plot of the aircraft drag polar.
    Different designs can be superposed by providing an existing fig.
    Each design can be provided a name.

    :param aircraft_file_path: path of data file
    :param name: name to give to the trace added to the figure
    :param fig: existing figure to which add the plot
    :param file_formatter: the formatter that defines the format of data file. If not provided, default format will
                           be assumed.
    :return: wing plot figure
    """
    variables = VariableIO(aircraft_file_path, file_formatter).read()

    # pylint: disable=invalid-name # that's a common naming
    cd = np.asarray(variables["data:aerodynamics:aircraft:cruise:CD"].value)
    # pylint: disable=invalid-name # that's a common naming
    cl = np.asarray(variables["data:aerodynamics:aircraft:cruise:CL"].value)

    # TODO: remove filtering one models provide proper bounds
    cd_short = cd[cd <= 2.0]
    cl_short = cl[cd <= 2.0]

    if fig is None:
        fig = go.Figure()

    scatter = go.Scatter(x=cd_short, y=cl_short, mode="lines+markers", name=name)

    fig.add_trace(scatter)

    fig = go.FigureWidget(fig)

    fig.update_layout(
        title_text="Drag Polar", title_x=0.5, xaxis_title="Cd", yaxis_title="Cl",
    )

    return fig


def mass_breakdown_bar_plot(
    aircraft_file_path: str, name=None, fig=None, file_formatter=None
) -> go.FigureWidget:
    """
    Returns a figure plot of the aircraft mass breakdown using bar plots.
    Different designs can be superposed by providing an existing fig.
    Each design can be provided a name.

    :param aircraft_file_path: path of data file
    :param name: name to give to the trace added to the figure
    :param fig: existing figure to which add the plot
    :param file_formatter: the formatter that defines the format of data file. If not provided, default format will
                           be assumed.
    :return: bar plot figure
    """
    variables = VariableIO(aircraft_file_path, file_formatter).read()

    systems = variables["data:weight:systems:mass"].value[0]

    furniture = variables["data:weight:furniture:mass"].value[0]

    crew = variables["data:weight:crew:mass"].value[0]

    airframe = variables["data:weight:airframe:mass"].value[0]

    propulsion = variables["data:weight:propulsion:mass"].value[0]

    # pylint: disable=invalid-name # that's a common naming
    MTOW = variables["data:weight:aircraft:MTOW"].value[0]
    # pylint: disable=invalid-name # that's a common naming
    OWE = variables["data:weight:aircraft:OWE"].value[0]
    payload = variables["data:weight:aircraft:payload"].value[0]
    fuel_mission = variables["data:mission:sizing:fuel"].value[0]

    if fig is None:
        fig = make_subplots(
            rows=1,
            cols=2,
            subplot_titles=("Maximum Take-Off Weight Breakdown", "Overall Weight Empty Breakdown"),
        )

    # Same color for each aircraft configuration
    i = len(fig.data)

    weight_labels = ["MTOW", "OWE", "Fuel - Mission", "Payload"]
    weight_values = [MTOW, OWE, fuel_mission, payload]
    fig.add_trace(
        go.Bar(name="", x=weight_labels, y=weight_values, marker_color=COLS[i], showlegend=False),
        row=1,
        col=1,
    )

    weight_labels = ["Airframe", "Propulsion", "Systems", "Furniture", "Crew"]
    weight_values = [airframe, propulsion, systems, furniture, crew]
    fig.add_trace(
        go.Bar(name=name, x=weight_labels, y=weight_values, marker_color=COLS[i]), row=1, col=2,
    )

    fig.update_layout(yaxis_title="[kg]")

    return fig


def mass_breakdown_sun_plot(aircraft_file_path: str, file_formatter=None):
    """
    Returns a figure sunburst plot of the mass breakdown.
    On the left a MTOW sunburst and on the right a OWE sunburst.
    Different designs can be superposed by providing an existing fig.
    Each design can be provided a name.

    :param aircraft_file_path: path of data file
    :param file_formatter: the formatter that defines the format of data file. If not provided, default format will
                           be assumed.
    :return: sunburst plot figure
    """
    variables = VariableIO(aircraft_file_path, file_formatter).read()

    systems = variables["data:weight:systems:mass"].value[0]
    C11 = variables["data:weight:systems:power:auxiliary_power_unit:mass"].value[0]
    C12 = variables["data:weight:systems:power:electric_systems:mass"].value[0]
    C13 = variables["data:weight:systems:power:hydraulic_systems:mass"].value[0]
    C21 = variables["data:weight:systems:life_support:insulation:mass"].value[0]
    C22 = variables["data:weight:systems:life_support:air_conditioning:mass"].value[0]
    C23 = variables["data:weight:systems:life_support:de-icing:mass"].value[0]
    C24 = variables["data:weight:systems:life_support:cabin_lighting:mass"].value[0]
    C25 = variables["data:weight:systems:life_support:seats_crew_accommodation:mass"].value[0]
    C26 = variables["data:weight:systems:life_support:oxygen:mass"].value[0]
    C27 = variables["data:weight:systems:life_support:safety_equipment:mass"].value[0]
    C3 = variables["data:weight:systems:navigation:mass"].value[0]
    C4 = variables["data:weight:systems:transmission:mass"].value[0]
    C51 = variables["data:weight:systems:operational:radar:mass"].value[0]
    C52 = variables["data:weight:systems:operational:cargo_hold:mass"].value[0]
    C6 = variables["data:weight:systems:flight_kit:mass"].value[0]

    furniture = variables["data:weight:furniture:mass"].value[0]
    D2 = variables["data:weight:furniture:passenger_seats:mass"].value[0]
    D3 = variables["data:weight:furniture:food_water:mass"].value[0]
    D4 = variables["data:weight:furniture:security_kit:mass"].value[0]
    D5 = variables["data:weight:furniture:toilets:mass"].value[0]

    crew = variables["data:weight:crew:mass"].value[0]

    airframe = variables["data:weight:airframe:mass"].value[0]
    wing = variables["data:weight:airframe:wing:mass"].value[0]
    fuselage = variables["data:weight:airframe:fuselage:mass"].value[0]
    h_tail = variables["data:weight:airframe:horizontal_tail:mass"].value[0]
    v_tail = variables["data:weight:airframe:vertical_tail:mass"].value[0]
    control_surface = variables["data:weight:airframe:flight_controls:mass"].value[0]
    landing_gear_1 = variables["data:weight:airframe:landing_gear:main:mass"].value[0]
    landing_gear_2 = variables["data:weight:airframe:landing_gear:front:mass"].value[0]
    engine_pylon = variables["data:weight:airframe:pylon:mass"].value[0]
    paint = variables["data:weight:airframe:paint:mass"].value[0]

    propulsion = variables["data:weight:propulsion:mass"].value[0]
    B1 = variables["data:weight:propulsion:engine:mass"].value[0]
    B2 = variables["data:weight:propulsion:fuel_lines:mass"].value[0]
    B3 = variables["data:weight:propulsion:unconsumables:mass"].value[0]

    MTOW = variables["data:weight:aircraft:MTOW"].value[0]
    OWE = variables["data:weight:aircraft:OWE"].value[0]
    payload = variables["data:weight:aircraft:payload"].value[0]
    fuel_mission = variables["data:mission:sizing:fuel"].value[0]

    # TODO: Deal with this in a more generic manner ?
    if round(MTOW, 6) == round(OWE + payload + fuel_mission, 6):
        MTOW = OWE + payload + fuel_mission

    fig = make_subplots(1, 2, specs=[[{"type": "domain"}, {"type": "domain"}]],)

    fig.add_trace(
        go.Sunburst(
            labels=[
                "MTOW" + "<br>" + str(int(MTOW)) + " [kg]",
                "payload"
                + "<br>"
                + str(int(payload))
                + " [kg] ("
                + str(round(payload / MTOW * 100, 1))
                + "%)",
                "fuel_mission"
                + "<br>"
                + str(int(fuel_mission))
                + " [kg] ("
                + str(round(fuel_mission / MTOW * 100, 1))
                + "%)",
                "OWE" + "<br>" + str(int(OWE)) + " [kg] (" + str(round(OWE / MTOW * 100, 1)) + "%)",
            ],
            parents=[
                "",
                "MTOW" + "<br>" + str(int(MTOW)) + " [kg]",
                "MTOW" + "<br>" + str(int(MTOW)) + " [kg]",
                "MTOW" + "<br>" + str(int(MTOW)) + " [kg]",
            ],
            values=[MTOW, payload, fuel_mission, OWE],
            branchvalues="total",
        ),
        1,
        1,
    )

    airframe_str = (
        "airframe"
        + "<br>"
        + str(int(airframe))
        + " [kg] ("
        + str(round(airframe / OWE * 100, 1))
        + "%)"
    )
    propulsion_str = (
        "propulsion"
        + "<br>"
        + str(int(propulsion))
        + " [kg] ("
        + str(round(propulsion / MTOW * 100, 1))
        + "%)"
    )
    systems_str = (
        "systems"
        + "<br>"
        + str(int(systems))
        + " [kg] ("
        + str(round(systems / MTOW * 100, 1))
        + "%)"
    )
    furniture_str = (
        "furniture"
        + "<br>"
        + str(int(furniture))
        + " [kg] ("
        + str(round(furniture / MTOW * 100, 1))
        + "%)"
    )
    crew_str = (
        "crew" + "<br>" + str(int(crew)) + " [kg] (" + str(round(crew / MTOW * 100, 1)) + "%)"
    )

    fig.add_trace(
        go.Sunburst(
            labels=[
                "OWE" + "<br>" + str(int(OWE)) + " [kg]",
                airframe_str,
                propulsion_str,
                systems_str,
                furniture_str,
                crew_str,
                "wing",
                "fuselage",
                "horizontal_tail",
                "vertical_tail",
                "flight_controls",
                "landing_gear_main",
                "landing_gear_front",
                "pylon",
                "paint",
                "engine",
                "fuel_lines",
                "unconsumables",
                "auxiliary_power_unit",
                "electric_systems",
                "hydraulic_systems",
                "insulation",
                "air_conditioning",
                "de-icing",
                "cabin_lighting",
                "seats_crew_accommodation",
                "oxygen",
                "safety_equipment",
                "navigation",
                "transmission",
                "radar",
                "cargo_hold",
                "flight_kit",
                # "cargo", "passenger_seats", "food_water", "security_kit", "toilets",
                "passenger_seats",
                "food_water",
                "security_kit",
                "toilets",
            ],
            parents=[
                "",
                "OWE" + "<br>" + str(int(OWE)) + " [kg]",
                "OWE" + "<br>" + str(int(OWE)) + " [kg]",
                "OWE" + "<br>" + str(int(OWE)) + " [kg]",
                "OWE" + "<br>" + str(int(OWE)) + " [kg]",
                "OWE" + "<br>" + str(int(OWE)) + " [kg]",
                airframe_str,
                airframe_str,
                airframe_str,
                airframe_str,
                airframe_str,
                airframe_str,
                airframe_str,
                airframe_str,
                airframe_str,
                propulsion_str,
                propulsion_str,
                propulsion_str,
                systems_str,
                systems_str,
                systems_str,
                systems_str,
                systems_str,
                systems_str,
                systems_str,
                systems_str,
                systems_str,
                systems_str,
                systems_str,
                systems_str,
                systems_str,
                systems_str,
                systems_str,
                # "furniture", "furniture", "furniture", "furniture", "furniture",
                furniture_str,
                furniture_str,
                furniture_str,
                furniture_str,
            ],
            values=[
                OWE,
                airframe,
                propulsion,
                systems,
                furniture,
                crew,
                wing,
                fuselage,
                h_tail,
                v_tail,
                control_surface,
                landing_gear_1,
                landing_gear_2,
                engine_pylon,
                paint,
                B1,
                B2,
                B3,
                C11,
                C12,
                C13,
                C21,
                C22,
                C23,
                C24,
                C25,
                C26,
                C27,
                C3,
                C4,
                C51,
                C52,
                C6,
                D2,
                D3,
                D4,
                D5,
            ],
            branchvalues="total",
        ),
        1,
        2,
    )

    fig.update_layout(title_text="Mass Breakdown", title_x=0.5)

    return fig
