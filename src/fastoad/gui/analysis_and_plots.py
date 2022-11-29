"""
Defines the analysis and plotting functions for postprocessing
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2022 ONERA & ISAE-SUPAERO
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
import plotly.express as px
import plotly.graph_objects as go
from openmdao.utils.units import convert_units
from plotly.subplots import make_subplots

from fastoad.io import VariableIO
from fastoad.openmdao.variables import VariableList

COLS = px.colors.qualitative.Plotly


# pylint: disable-msg=too-many-locals
def wing_geometry_plot(
    aircraft_file_path: str, name=None, fig=None, *, file_formatter=None
) -> go.FigureWidget:
    """
    Returns a figure plot of the top view of the wing.
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

    wing_kink_leading_edge_x = variables["data:geometry:wing:kink:leading_edge:x:local"].value[0]
    wing_tip_leading_edge_x = variables["data:geometry:wing:tip:leading_edge:x:local"].value[0]
    wing_root_y = variables["data:geometry:wing:root:y"].value[0]
    wing_kink_y = variables["data:geometry:wing:kink:y"].value[0]
    wing_tip_y = variables["data:geometry:wing:tip:y"].value[0]
    wing_root_chord = variables["data:geometry:wing:root:chord"].value[0]
    wing_kink_chord = variables["data:geometry:wing:kink:chord"].value[0]
    wing_tip_chord = variables["data:geometry:wing:tip:chord"].value[0]

    mean_aerodynamic_chord = variables["data:geometry:wing:MAC:length"].value[0]
    mac25_x_position = variables["data:geometry:wing:MAC:at25percent:x"].value[0]
    distance_root_mac_chords = variables["data:geometry:wing:MAC:leading_edge:x:local"].value[0]
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

    x = x + mac25_x_position - 0.25 * mean_aerodynamic_chord - distance_root_mac_chords
    # pylint: disable=invalid-name # that's a common naming
    x = np.concatenate((x, x))

    if fig is None:
        fig = go.Figure()

    scatter = go.Scatter(x=y, y=x, mode="lines+markers", name=name)

    fig.add_trace(scatter)

    fig.layout = go.Layout(yaxis=dict(scaleanchor="x", scaleratio=1))

    fig = go.FigureWidget(fig)

    fig.update_layout(title_text="Wing Geometry", title_x=0.5, xaxis_title="y", yaxis_title="x")

    return fig


# pylint: disable-msg=too-many-locals
def aircraft_geometry_plot(
    aircraft_file_path: str, name=None, fig=None, *, file_formatter=None
) -> go.FigureWidget:
    """
    Returns a figure plot of the top view of the wing.
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

    fig.update_layout(title_text="Aircraft Geometry", title_x=0.5, xaxis_title="y", yaxis_title="x")

    return fig


def drag_polar_plot(
    aircraft_file_path: str, name=None, fig=None, *, file_formatter=None
) -> go.FigureWidget:
    """
    Returns a figure plot of the aircraft drag polar.
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

    fig.update_layout(title_text="Drag Polar", title_x=0.5, xaxis_title="Cd", yaxis_title="Cl")

    return fig


def mass_breakdown_bar_plot(
    aircraft_file_path: str,
    name=None,
    fig=None,
    *,
    file_formatter=None,
    input_mass_name="data:weight:aircraft:MTOW",
) -> go.FigureWidget:
    """
    Returns a figure plot of the aircraft mass breakdown using bar plots.
    Different designs can be superposed by providing an existing fig.
    Each design can be provided a name.

    :param aircraft_file_path: path of data file
    :param name: name to give to the trace added to the figure
    :param fig: existing figure to which add the plot
    :param file_formatter: the formatter that defines the format of data file. If not provided,
                           default format will be assumed.
    :param input_mass_name: the variable name for the mass input as defined in the mission
                            definition file.
    :return: bar plot figure
    """
    variables = VariableIO(aircraft_file_path, file_formatter).read()

    var_names_and_new_units = {
        input_mass_name: "kg",
        "data:weight:aircraft:OWE": "kg",
        "data:weight:aircraft:payload": "kg",
        "data:weight:aircraft:sizing_onboard_fuel_at_input_weight": "kg",
    }

    # pylint: disable=unbalanced-tuple-unpacking # It is balanced for the parameters provided
    mtow, owe, payload, fuel_mission = _get_variable_values_with_new_units(
        variables, var_names_and_new_units
    )

    if fig is None:
        fig = make_subplots(
            rows=1,
            cols=2,
            subplot_titles=("Maximum Take-Off Weight Breakdown", "Overall Weight Empty Breakdown"),
        )

    # Same color for each aircraft configuration
    i = int(len(fig.data) / 2) % 10

    weight_labels = ["MTOW", "OWE", "Fuel - Mission", "Payload"]
    weight_values = [mtow, owe, fuel_mission, payload]
    fig.add_trace(
        go.Bar(name="", x=weight_labels, y=weight_values, marker_color=COLS[i], showlegend=False),
        row=1,
        col=1,
    )

    # Get data:weight decomposition
    main_weight_values, main_weight_names, _ = _data_weight_decomposition(variables, owe=None)
    fig.add_trace(
        go.Bar(name=name, x=main_weight_names, y=main_weight_values, marker_color=COLS[i]),
        row=1,
        col=2,
    )

    fig.update_layout(yaxis_title="[kg]")

    return fig


def mass_breakdown_sun_plot(
    aircraft_file_path: str,
    *,
    file_formatter=None,
    input_mass_name="data:weight:aircraft:MTOW",
):
    """
    Returns a figure sunburst plot of the mass breakdown.
    On the left a MTOW sunburst and on the right a OWE sunburst.
    Different designs can be superposed by providing an existing fig.
    Each design can be provided a name.

    :param aircraft_file_path: path of data file
    :param file_formatter: the formatter that defines the format of data file. If not provided,
                           default format will be assumed.
    :param input_mass_name: the variable name for the mass input as defined in the mission
                            definition file.
    :return: sunburst plot figure
    """
    variables = VariableIO(aircraft_file_path, file_formatter).read()

    var_names_and_new_units = {
        input_mass_name: "kg",
        "data:weight:aircraft:OWE": "kg",
        "data:weight:aircraft:payload": "kg",
        "data:weight:aircraft:sizing_onboard_fuel_at_input_weight": "kg",
    }

    # pylint: disable=unbalanced-tuple-unpacking # It is balanced for the parameters provided
    mtow, owe, payload, onboard_fuel_at_takeoff = _get_variable_values_with_new_units(
        variables, var_names_and_new_units
    )

    # TODO: Deal with this in a more generic manner ?
    if round(mtow, 6) == round(owe + payload + onboard_fuel_at_takeoff, 6):
        mtow = owe + payload + onboard_fuel_at_takeoff

    fig = make_subplots(1, 2, specs=[[{"type": "domain"}, {"type": "domain"}]])

    fig.add_trace(
        go.Sunburst(
            labels=[
                "MTOW" + "<br>" + str(int(mtow)) + " [kg]",
                "payload"
                + "<br>"
                + str(int(payload))
                + " [kg] ("
                + str(round(payload / mtow * 100, 1))
                + "%)",
                "onboard_fuel_at_takeoff"
                + "<br>"
                + str(int(onboard_fuel_at_takeoff))
                + " [kg] ("
                + str(round(onboard_fuel_at_takeoff / mtow * 100, 1))
                + "%)",
                "OWE" + "<br>" + str(int(owe)) + " [kg] (" + str(round(owe / mtow * 100, 1)) + "%)",
            ],
            parents=[
                "",
                "MTOW" + "<br>" + str(int(mtow)) + " [kg]",
                "MTOW" + "<br>" + str(int(mtow)) + " [kg]",
                "MTOW" + "<br>" + str(int(mtow)) + " [kg]",
            ],
            values=[mtow, payload, onboard_fuel_at_takeoff, owe],
            branchvalues="total",
        ),
        1,
        1,
    )

    # Get data:weight 2-levels decomposition
    categories_values, categories_names, categories_labels = _data_weight_decomposition(
        variables, owe=owe
    )

    sub_categories_values = []
    sub_categories_names = []
    sub_categories_parent = []
    for variable in variables.names():
        name_split = variable.split(":")
        if isinstance(name_split, list) and len(name_split) >= 5:
            parent_name = name_split[2]
            if parent_name in categories_names and name_split[-1] == "mass":
                variable_name = "_".join(name_split[3:-1])
                sub_categories_values.append(
                    convert_units(variables[variable].value[0], variables[variable].units, "kg")
                )
                sub_categories_parent.append(categories_labels[categories_names.index(parent_name)])
                sub_categories_names.append(variable_name)

    # Define figure data
    figure_labels = ["OWE" + "<br>" + str(int(owe)) + " [kg]"]
    figure_labels.extend(categories_labels)
    figure_labels.extend(sub_categories_names)
    figure_parents = [""]
    for _ in categories_names:
        figure_parents.append("OWE" + "<br>" + str(int(owe)) + " [kg]")
    figure_parents.extend(sub_categories_parent)
    figure_values = [owe]
    figure_values.extend(categories_values)
    figure_values.extend(sub_categories_values)

    # Plot figure
    fig.add_trace(
        go.Sunburst(
            labels=figure_labels, parents=figure_parents, values=figure_values, branchvalues="total"
        ),
        1,
        2,
    )

    fig.update_layout(title_text="Mass Breakdown", title_x=0.5)

    return fig


def _get_variable_values_with_new_units(
    variables: VariableList, var_names_and_new_units: Dict[str, str]
):
    """
    Returns the value of the requested variable names with respect to their new units in the order
    in which their were given. This function works only for variable of value with shape=1 or float.

    :param variables: instance containing variables information
    :param var_names_and_new_units: dictionary of the variable names as keys and units as value
    :return: values of the requested variables with respect to their new units
    """
    new_values = []
    for variable_name, unit in var_names_and_new_units.items():
        new_values.append(
            convert_units(variables[variable_name].value[0], variables[variable_name].units, unit)
        )

    return new_values


def _data_weight_decomposition(variables: VariableList, owe=None):
    """
    Returns the two level weight decomposition of MTOW and optionally the decomposition of owe
    subcategories.

    :param variables: instance containing variables information
    :param owe: value of OWE, if provided names of owe subcategories will be provided
    :return: variable values, names and optionally owe subcategories names
    """
    category_values = []
    category_names = []
    owe_subcategory_names = []
    for variable in variables.names():
        name_split = variable.split(":")
        if isinstance(name_split, list) and len(name_split) == 4:
            if name_split[0] + name_split[1] + name_split[3] == "dataweightmass" and not (
                "aircraft" in name_split[2]
            ):
                category_values.append(
                    convert_units(variables[variable].value[0], variables[variable].units, "kg")
                )
                category_names.append(name_split[2])
                if owe:
                    owe_subcategory_names.append(
                        name_split[2]
                        + "<br>"
                        + str(int(variables[variable].value[0]))
                        + " [kg] ("
                        + str(round(variables[variable].value[0] / owe * 100, 1))
                        + "%)"
                    )
    if owe:
        result = category_values, category_names, owe_subcategory_names
    else:
        result = category_values, category_names, None

    return result
