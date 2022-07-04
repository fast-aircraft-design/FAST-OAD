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

# TO DO : put comments
import plotly.graph_objects as go
from fastoad.io import VariableIO
import numpy as np
from stdatm import Atmosphere

from scipy.optimize import fsolve

pi = np.pi

# Undefined constants by FAST-OAD so plausible values have been chosen
cl0_wing = 0.15
cm0_wing = -0.2
ths_deportation = -5 * pi / 180  # rad


def stability_diagram_plot(
    aircraft_file_path: str, name=None, fig=None, file_formatter=None
) -> go.FigureWidget:
    """
    Returns a figure plot of the available power diagram of the aircraft.
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

    cl_alpha_wing = variables["data:aerodynamics:aircraft:cruise:CL_alpha"].value[0]
    cl_max_clean_wing = variables["data:aerodynamics:aircraft:landing:CL_max_clean"].value[0]
    cl_delta_flaps = variables["data:aerodynamics:high_lift_devices:landing:CL"].value[0]
    cl_alpha_ht = variables["data:aerodynamics:horizontal_tail:cruise:CL_alpha"].value[0]

    mac = variables["data:geometry:wing:MAC:length"].value[0]
    mac_ht = variables["data:geometry:horizontal_tail:MAC:length"].value[0]

    x_aerodynamic_center = variables["data:geometry:wing:MAC:at25percent:x"].value[0]
    x_ht_form_wing = variables[
        "data:geometry:horizontal_tail:MAC:at25percent:x:from_wingMAC25"
    ].value[0]
    x_ht = x_aerodynamic_center + x_ht_form_wing

    area_ht = variables["data:geometry:horizontal_tail:area"].value[0]
    area_wing = variables["data:geometry:wing:area"].value[0]
    aspect_ratio_wing = variables["data:geometry:wing:aspect_ratio"].value[0]
    span_wing = variables["data:geometry:wing:span"].value[0]

    mtow = variables["data:weight:aircraft:MTOW"].value[0]
    # mzfw = variables["data:weight:aircraft:MZFW"].value[0]
    # owe = variables["data:weight:aircraft:OWE"].value[0]

    # volume of fuselage
    fuselage_front_length = variables["data:geometry:fuselage:front_length"].value[0]
    fuselage_length = variables["data:geometry:fuselage:length"].value[0]
    fuselage_radius = 0.25 * (
        variables["data:geometry:fuselage:maximum_height"].value[0]
        + variables["data:geometry:fuselage:maximum_width"].value[0]
    )
    fuselage_rear_length = variables["data:geometry:fuselage:rear_length"].value[0]

    v1 = 2.0 * pi / 3.0 * fuselage_radius ** 3.0
    v2 = (
        pi * fuselage_radius ** 2 * (fuselage_length - fuselage_rear_length - fuselage_front_length)
    )
    v3 = 1 / 3.0 * pi * fuselage_radius ** 2 * fuselage_rear_length
    v = v1 + v2 + v3

    # Sh/S
    surface_ratio = np.linspace(0.05, 0.35, 10)
    actual_surface_ratio = area_ht / area_wing

    # beta calculation (geometry):
    beta = np.arctan2(span_wing / 2.0 * pi / 4.0, x_ht_form_wing)

    # 1) Neutral point calculation (rear limit):

    ht_effectiveness = 1 - cl_alpha_wing * 8 / (pi ** 3 * aspect_ratio_wing) * (
        1 + 1 / np.cos(beta)
    )
    numerator = (
        x_aerodynamic_center * cl_alpha_wing
        + surface_ratio * x_ht * cl_alpha_ht * ht_effectiveness
        - 2.0 * v / area_wing
    )
    denominator = cl_alpha_wing + surface_ratio * cl_alpha_ht * ht_effectiveness
    x_cg_rear = numerator / denominator

    mac_leading_edge = x_aerodynamic_center - mac / 4.0
    x_cg_rear_percentage = (x_cg_rear - mac_leading_edge) / mac
    x_cg_rear_percentage_minus_5perc = x_cg_rear_percentage - 0.05
    x_cg_rear_percentage_minus_10perc = x_cg_rear_percentage - 0.1
    x_cg_rear_percentage_minus_15perc = x_cg_rear_percentage - 0.15

    # 2) trim to glide : forward limit
    atm = Atmosphere(altitude=0)
    rho = atm.density

    def epsilon(cl_wing_function):
        return -8 * cl_wing_function / (pi ** 3 * aspect_ratio_wing) * (1 + 1 / np.cos(beta))

    def lift_equilibrium(alpha_function, surface_ratio_function, mass):
        v_stall = 2 * mass * 9.81 / (rho * area_wing * cl_max_clean_wing * area_wing)

        left_member = mass * 9.81 / (0.5 * rho * (1.3 * v_stall) ** 2 * area_wing)

        cl_w = cl0_wing + alpha_function * cl_alpha_wing + cl_delta_flaps
        epsilon_ht = epsilon(cl_w)
        cl_ht = cl_alpha_ht * (alpha_function + epsilon_ht + ths_deportation)

        right_member = cl_w + surface_ratio_function * cl_ht

        return left_member - right_member

    alpha_initial_guess = 5 * pi / 180 * np.ones(len(surface_ratio))

    alpha = fsolve(lift_equilibrium, alpha_initial_guess, args=(surface_ratio, mtow))

    cl_wing = cl0_wing + alpha * cl_alpha_wing + cl_delta_flaps
    alpha_ht = alpha + epsilon(cl_wing) + ths_deportation
    cl_horizontal_tail = cl_alpha_ht * alpha_ht

    # Moment equilibrium
    numerator = (
        -cm0_wing * mac
        + x_aerodynamic_center * cl_wing
        + surface_ratio * x_ht * cl_horizontal_tail
        - 2 * alpha * v / area_wing
    )  # ac near pc
    denominator = cl_wing + surface_ratio * cl_horizontal_tail

    x_cg_front = numerator / denominator
    x_cg_front_percentage = (x_cg_front - mac_leading_edge) / mac

    delta_x_cg = [0, 0]
    delta_x_cg[0] = np.interp(actual_surface_ratio, surface_ratio, x_cg_front_percentage) * 100
    delta_x_cg[1] = (
        np.interp(actual_surface_ratio, surface_ratio, x_cg_rear_percentage_minus_5perc) * 100
    )

    # 2) Negative_ressource :
    v_mo = 463.0 / 3.6  # Speed see EASA CS25
    q = 9.81 / (2.0 * v_mo)  # rad/s : rotation speed

    def lift_equilibrium2(alpha_function, surface_ratio_function, mass):
        left_member = mass * 9.81 / (0.5 * rho * v_mo ** 2 * area_wing)

        cl_w = cl0_wing + alpha_function * cl_alpha_wing + cl_delta_flaps + q * mac / v_mo
        epsilon_ht = epsilon(cl_w)
        cl_ht = cl_alpha_ht * (alpha_function + epsilon_ht + ths_deportation + q * mac_ht / v_mo)

        right_member = cl_w + surface_ratio_function * cl_ht

        return left_member - right_member

    alpha = fsolve(lift_equilibrium2, alpha_initial_guess, args=(surface_ratio, mtow))

    cl_wing = cl0_wing + alpha * cl_alpha_wing + cl_delta_flaps + q * mac / v_mo
    alpha_ht = alpha + epsilon(cl_wing) + ths_deportation + q * mac_ht / v_mo
    cl_horizontal_tail = cl_alpha_ht * alpha_ht

    # Moment equilibrium
    numerator = (
        -cm0_wing * mac
        + x_aerodynamic_center * cl_wing
        + surface_ratio * x_ht * cl_horizontal_tail
        - 2 * alpha * v / area_wing
    )  # ac near pc
    denominator = cl_wing + surface_ratio * cl_horizontal_tail

    x_cg_front_nressource = numerator / denominator
    x_cg_front_percentage_nressource = (x_cg_front_nressource - mac_leading_edge) / mac

    # Figure
    if fig is None:
        fig = go.Figure()

    fig = go.FigureWidget(fig)

    scatter_ac = go.Scatter(
        x=x_cg_rear_percentage * 100,
        y=surface_ratio * 100,
        line=dict(color="darkslateblue"),
        mode="lines",
        name="Neutral point",
    )
    scatter_ac2 = go.Scatter(
        x=x_cg_rear_percentage_minus_5perc * 100,
        y=surface_ratio * 100,
        line=dict(color="blue"),
        mode="lines",
        name="Neutral point - 5%",
    )

    scatter_ac3 = go.Scatter(
        x=x_cg_rear_percentage_minus_10perc * 100,
        y=surface_ratio * 100,
        line=dict(color="lightblue"),
        mode="lines",
        name="Neutral point - 10%",
    )
    scatter_ac4 = go.Scatter(
        x=x_cg_rear_percentage_minus_15perc * 100,
        y=surface_ratio * 100,
        line=dict(color="white"),
        mode="lines",
        name="Neutral point - 15%",
    )

    scatter_trim_mtow = go.Scatter(
        x=x_cg_front_percentage * 100,
        y=surface_ratio * 100,
        line=dict(color="orange"),
        mode="lines",
        name="Trim on glide (landing)",
    )

    delta_x_cg_dif = (delta_x_cg[1] - delta_x_cg[0]) * 100

    scatter_actual = go.Scatter(
        x=delta_x_cg,
        y=[actual_surface_ratio * 100, actual_surface_ratio * 100],
        line=dict(color="green"),
        mode="lines",
        name="$\Delta X_{cg}$ %d: " % delta_x_cg_dif,
    )

    scatter_trim_nressource = go.Scatter(
        x=x_cg_front_percentage_nressource,
        y=surface_ratio,
        line=dict(color="yellow"),
        mode="lines",
        name="Trim on glide (landing)",
    )

    fig.add_trace(scatter_ac)
    fig.add_trace(scatter_ac2)
    fig.add_trace(scatter_ac3)
    fig.add_trace(scatter_ac4)
    fig.add_trace(scatter_trim_mtow)
    # fig.add_trace(scatter_trim_nressource)
    fig.add_trace(scatter_actual)

    fig.update_layout(
        title_text="Stability Diagram",
        title_x=0.5,
        xaxis_title="Centering (% of MAC)",
        yaxis_title="Sh/S (%)",
        showlegend=True,
    )
    return fig
