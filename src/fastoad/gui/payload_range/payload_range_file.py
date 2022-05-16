"""
Defines the analysis and plotting functions for postprocessing
"""
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
from scipy.optimize import fsolve

from fastoad.constants import EngineSetting
from fastoad.io import VariableIO
from fastoad.model_base import FlightPoint
from fastoad.model_base import Atmosphere
from fastoad.openmdao.variables import VariableList

import openmdao.api as om
from fastoad.module_management._bundle_loader import BundleLoader
from fastoad.openmdao.problem import FASTOADProblem

COLS = plotly.colors.DEFAULT_PLOTLY_COLORS



def breguet_leduc(mass_in, mass_out, constant_coeff, x0):
    """
    Returns the range in "NM" using the breguet leduc modified formula
    x0 : in NM
    """

    ratio = mass_in / mass_out

    def non_linear_function(ra):
        k_ra = 1 - 0.895 * np.exp(-ra / 814)
        return ra - k_ra * constant_coeff * np.log(ratio)

    sol = fsolve(non_linear_function, x0)
    return sol


def payload_range_simple(
    aircraft_file_path: str,
    propulsion_id: str,
    name=None,
    fig=None,
    file_formatter=None,
) -> go.FigureWidget:
    """
    Returns a figure of the payload range using the corrected leduc-breguet formula
    Different designs can be superposed by providing an existing fig.
    Each design can be provided a name.

    :param aircraft_file_path: path of data file
    :param name: name to give to the trace added to the figure
    :param fig: existing figure to which add the plot
    :param file_formatter: the formatter that defines the format of data file. If not provided,
                           default format will be assumed.
    :return: wing plot figure
    """

    from fastoad.module_management._plugins import FastoadLoader

    FastoadLoader()

    variables = VariableIO(aircraft_file_path, file_formatter).read()

    glide_ratio = variables["data:aerodynamics:aircraft:cruise:L_D_max"].value[
        0
    ]  # max glide ratio during cruise
    altitude = variables["data:mission:sizing:main_route:cruise:altitude"].value[
        0
    ]  # cruise altitude
    cruise_mach = variables["data:TLAR:cruise_mach"].value[0]
    mission_range = variables["data:TLAR:range"].value[0]  # first approximation for the range

    max_payload = variables["data:weight:aircraft:max_payload"].value[0]
    payload = variables["data:weight:aircraft:payload"].value[0]
    mtow = variables["data:weight:aircraft:MTOW"].value[0]
    owe = variables["data:weight:aircraft:OWE"].value[0]
    mfw = variables["data:weight:aircraft:MFW"].value[0]
    fuel_burned = variables["data:mission:sizing:main_route:fuel"].value[0]

    bypass_ratio = variables["data:propulsion:rubber_engine:bypass_ratio"].value[0]
    delta_t4_climb = variables["data:propulsion:rubber_engine:delta_t4_climb"].value[0]
    delta_t4_cruise = variables["data:propulsion:rubber_engine:delta_t4_cruise"].value[0]
    design_altitude = variables["data:propulsion:rubber_engine:design_altitude"].value[0]
    maximum_mach = variables["data:propulsion:rubber_engine:maximum_mach"].value[0]
    overall_pressure_ratio = variables[
        "data:propulsion:rubber_engine:overall_pressure_ratio"
    ].value[0]
    turbine_inlet_temperature = variables[
        "data:propulsion:rubber_engine:turbine_inlet_temperature"
    ].value[0]
    # k_sfc_sl = variables["tuning:propulsion:rubber_engine:SFC:k_sl"].value[0]
    # k_sfc_cr = variables["tuning:propulsion:rubber_engine:SFC:k_cr"].value[0]

    g = 9.81
    atm = Atmosphere(altitude, altitude_in_feet=False)
    atm.mach = cruise_mach
    speed = atm.true_airspeed

    thrust = 0.98 * mtow * g / glide_ratio
    fp = FlightPoint(
        altitude=altitude,
        mach=cruise_mach,
        thrust=thrust,
        thrust_rate=0.7,
        thrust_is_regulated=True,
        engine_setting=EngineSetting.convert("CRUISE"),
    )
    weight_end = mtow - fuel_burned
    thrust2 = weight_end * g / glide_ratio

    fp2 = FlightPoint(
        altitude=altitude,
        mach=cruise_mach,
        thrust=thrust2,
        thrust_rate=0.7,
        thrust_is_regulated=True,
        engine_setting=EngineSetting.convert("CRUISE"),
    )
    flight_points_list = pd.DataFrame([fp, fp2])

    # Create a rubber engine
    blank_comp = om.ExplicitComponent()
    loader = BundleLoader().instantiate_component(propulsion_id)
    loader.setup(blank_comp)
    problem = FASTOADProblem()
    model = problem.model
    model.add_subsystem("list_propulsion_inputs", blank_comp, promotes=["*"])
    problem.setup()
    variables_to_add = VariableList.from_problem(problem)
    inputs = [var.name for var in variables_to_add if var.is_input]

    inputs_dictionary = dict()
    for input_to_add in inputs:
        inputs_dictionary[str(input_to_add)] = variables[input_to_add].value[0]

    propulsion_model = loader.get_model(inputs_dictionary)
    propulsion_model.compute_flight_points(flight_points_list)

    sfc = np.mean(flight_points_list.sfc)

    # Breguet-Leduc
    coeff = glide_ratio * speed * 3.6 / 1.852 / (g * sfc) * 10 / (3600 * 10)

    # point A :
    a = np.array([0, max_payload])

    # point B:
    mass_in = mtow
    mass_out = owe + max_payload
    ra_b = breguet_leduc(mass_in, mass_out, coeff, mission_range)

    # point C
    mass_out = mtow - mfw
    payload_c = mtow - mfw - owe
    ra_c = breguet_leduc(mass_in, mass_out, coeff, mission_range)

    # point D
    mass_in = owe + mfw
    mass_out = owe
    ra_d = breguet_leduc(mass_in, mass_out, coeff, ra_c)
    print(ra_d)

    x = np.array([0, ra_b[0], ra_c[0], ra_d[0]])
    y = np.array([max_payload, max_payload, payload_c, 0]) / 10 ** 3

    if fig is None:
        fig = go.Figure()
    scatter = go.Scatter(x=x, y=y, mode="markers", name=name, showlegend=False)
    scatter2 = go.Scatter(x=x, y=y, mode="lines", name=name, showlegend=False)
    scatter3 = go.Scatter(
        x=[mission_range], y=[payload / 10 ** 3], mode="markers", name="Design point"
    )
    scatter3 = go.Scatter(x=[2500], y=[17000 / 10 ** 3], mode="markers", name="Design point")
    fig.add_trace(scatter)
    fig.add_trace(scatter2)
    fig.add_trace(scatter3)

    fig = go.FigureWidget(fig)
    fig.update_layout(
        title_text="Payload range diagram", xaxis_title="range [NM]", yaxis_title="Payload [tonnes]"
    )

    return fig
