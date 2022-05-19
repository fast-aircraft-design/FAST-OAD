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

import fastoad.api as oad
import os.path as pth
import time

COLS = plotly.colors.DEFAULT_PLOTLY_COLORS


def breguet_leduc_formula(mass_in, mass_out, constant_coeff, x0):
    """
    Function used internally
    Returns the range in "NM" using the breguet leduc modified formula
    x0 : in NM
    """
    ratio = mass_in / mass_out

    def non_linear_function(ra):
        k_ra = 1 - 0.895 * np.exp(-ra / 814)
        return ra - k_ra * constant_coeff * np.log(ratio)

    sol = fsolve(non_linear_function, x0)
    return sol


def breguet_leduc_points(
        aircraft_file_path: str,
        propulsion_id: str = "fastoad.wrapper.propulsion.rubber_engine",
        sizing_name: str = "sizing",
        file_formatter=None,
):
    from fastoad.module_management._plugins import FastoadLoader

    FastoadLoader()

    variables = VariableIO(aircraft_file_path, file_formatter).read()

    glide_ratio = variables["data:aerodynamics:aircraft:cruise:L_D_max"].value[
        0
    ]  # max glide ratio during cruise
    altitude = variables["data:mission:" + sizing_name + ":main_route:cruise:altitude"].value[
        0
    ]  # cruise altitude
    cruise_mach = variables["data:TLAR:cruise_mach"].value[0]
    sizing_range = variables["data:TLAR:range"].value[0]  # first approximation for the range

    max_payload = variables["data:weight:aircraft:max_payload"].value[0]
    payload = variables["data:weight:aircraft:payload"].value[0]
    mtow = variables["data:weight:aircraft:MTOW"].value[0]
    owe = variables["data:weight:aircraft:OWE"].value[0]
    mfw = variables["data:weight:aircraft:MFW"].value[0]
    fuel_burned = variables["data:mission:" + sizing_name + ":main_route:fuel"].value[0]

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
    thrust_end = weight_end * g / glide_ratio

    fp_end = FlightPoint(
        altitude=altitude,
        mach=cruise_mach,
        thrust=thrust_end,
        thrust_rate=0.7,
        thrust_is_regulated=True,
        engine_setting=EngineSetting.convert("CRUISE"),
    )
    flight_points_list = pd.DataFrame([fp, fp_end])

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

    inputs_dictionary = dict()  # bypass_ratio, delta_t4, maximum_mach, overall_pressure_ratio
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
    ra_b = breguet_leduc_formula(mass_in, mass_out, coeff, sizing_range)

    # point C
    mass_out = mtow - mfw
    payload_c = mtow - mfw - owe
    ra_c = breguet_leduc_formula(mass_in, mass_out, coeff, sizing_range)

    # point D
    mass_in = owe + mfw
    mass_out = owe
    ra_d = breguet_leduc_formula(mass_in, mass_out, coeff, ra_c)

    BL_ranges = np.array([0, ra_b[0], ra_c[0], ra_d[0]])
    BL_payloads = np.array([max_payload, max_payload, payload_c, 0]) / 10 ** 3
    return BL_ranges, BL_payloads


def payload_range_simple(
        aircraft_file_path: str,
        propulsion_id: str = "fastoad.wrapper.propulsion.rubber_engine",
        sizing_name: str = "sizing",
        name=None,
        fig=None,
        file_formatter=None,
        x_axis=None,
        y_axis=None,
) -> go.FigureWidget:
    """
    Returns a figure of the payload range using the corrected leduc-breguet formula
    Different designs can be superposed by providing an existing fig.
    Each design can be provided a name.

    :param aircraft_file_path: path of data file
    :param propulsion_id: name the model for the engine
    :param sizing_name: name of the siizing mission : default sizing
    :param name: name to give to the trace added to the figure
    :param fig: existing figure to which add the plot
    :param file_formatter: the formatter that defines the format of data file. If not provided,
                           default format will be assumed.
    :param x_axis: defines the x axis if the user wants to
    :param y_axis: defines the y axis if the user wants to
    :return: wing plot figure
    """
    BL_ranges, BL_payloads = breguet_leduc_points(
        aircraft_file_path, propulsion_id, sizing_name, file_formatter
    )

    # Simple payload-range generation
    if fig is None:
        fig = go.Figure()
    scatter = go.Scatter(
        x=BL_ranges, y=BL_payloads, mode="lines+markers", name=name, showlegend=False
    )
    scatter2 = go.Scatter(x=[2500], y=[17000 / 10 ** 3], mode="markers", name="CERAS design point")

    fig.add_trace(scatter)
    fig.add_trace(scatter2)

    fig = go.FigureWidget(fig)
    fig.update_layout(
        title_text="Payload range diagram", xaxis_title="range [NM]", yaxis_title="Payload [tonnes]"
    )
    if x_axis is not None:
        fig.update_xaxes(range=[x_axis[0],x_axis[1]])
    if y_axis is not None:
        fig.update_yaxes(range=[y_axis[0],y_axis[1]])

    return fig


def grid_generation(
        aircraft_file_path: str,
        propulsion_id: str = "fastoad.wrapper.propulsion.rubber_engine",
        sizing_name: str = "sizing",
        name=None,
        fig=None,
        file_formatter=None,
        n_intervals_payloads=8,
        range_step=500,
        show_grid: bool=True,
        x_axis=None,
        y_axis=None,
):
    """
           Returns a figure of the payload range using the corrected leduc-breguet formula,
           generates a grid and then whith the values of the range and paylaod, genrates a mission
           in order to retrieve the burnt fuel/ passenger/km
           Different designs can be superposed by providing an existing fig.
           Each design can be provided a name.

           :param aircraft_file_path: path of data file
           :param propulsion_id: name the model for the engine
           :param sizing_name: name of the siizing mission : default sizing
           :param name: name to give to the trace added to the figure
           :param fig: existing figure to which add the plot
           :param file_formatter: the formatter that defines the format of data file. If not provided,
                                  default format will be assumed.
           :param n_intervals_payloads : number of intervals between 0.45* max_payload and 0.95 max_payload for the grid
                                          defaults is 8
           :param range_step: defines the step between 2 grid points in the range axis. default is 500 [NM]
           :param show_grid: states if the grid points are to be shown on the fig
           :param x_axis: defines the x axis if the user wants to
           :param y_axis: defines the y axis if the user wants to
           :return: wing plot figure
           """

    BL_ranges, BL_payloads = breguet_leduc_points(
        aircraft_file_path, propulsion_id, sizing_name, file_formatter
    )
    max_payload = BL_payloads[0]
    payload_c = BL_payloads[2]

    ra_b = BL_ranges[1]
    ra_c = BL_ranges[2]
    ra_d = BL_ranges[3]

    """
    # Grid generation
        # step 0 : define the number of grid points
    """

    val_payloads = np.linspace(0.4 * max_payload, 0.95 * max_payload, n_intervals_payloads)
    ra_c_id = np.where(val_payloads >= payload_c)[0][0]
    """
        # step 1 : compute the max range and the boundaries
    """

    max_range = np.zeros(n_intervals_payloads)
    max_range[0:ra_c_id] = (ra_c - ra_d) / payload_c * (val_payloads[0:ra_c_id]) + ra_d
    max_range[ra_c_id:] = (ra_b - ra_c) / (max_payload - payload_c) * (
            val_payloads[ra_c_id:] - payload_c
    ) + ra_c
    max_range *= 0.95  # safety margin

    min_range = 0.1 * ra_b  # safety margin
    if min_range < range_step:
        min_range = range_step
    """
        # step 2 : grid generation through grid_ranges and grid_payloads
    """

    grid_ranges = np.array([])  # to stock the ranges of the grid x
    grid_payloads = np.array([])  # to stock the payloads of the grid y
    n_values_ranges = np.zeros(n_intervals_payloads)
    for i in range(n_intervals_payloads):
        range_add = np.arange(min_range, max_range[i], range_step)
        n_values_ranges[i] = len(range_add)
        grid_ranges = np.append(grid_ranges, range_add)
        grid_payloads = np.append(grid_payloads, np.ones(len(range_add)) * val_payloads[i])
    grid = np.array(
        [grid_ranges, grid_payloads, np.zeros(len(grid_ranges))]
    )  # [range, payload, total_fuel or consumption/kg/km]
    print("number of calculation points : ", len(grid[0]))

    # Simple payload-range generation
    if fig is None:
        fig = go.Figure()
    scatter1 = go.Scatter(
        x=BL_ranges, y=BL_payloads, mode="markers+lines", name=name, showlegend=False
    )
    scatter2 = go.Scatter(x=[2500], y=[17000 / 10 ** 3], mode="markers", name="Sizing point")

    fig.add_trace(scatter1)
    fig.add_trace(scatter2)

    if (show_grid==True):
        scatter3 = go.Scatter(x=grid[0], y=grid[1], mode="markers", name="Grid points")
        fig.add_trace(scatter3)

    fig = go.FigureWidget(fig)
    fig.update_layout(
        title_text="Payload range diagram", xaxis_title="range [NM]", yaxis_title="Payload [tonnes]"
    )

    if x_axis is not None:
        fig.update_xaxes(range=[x_axis[0], x_axis[1]])
    if y_axis is not None:
        fig.update_yaxes(range=[y_axis[0], y_axis[1]])

    return fig, grid, n_values_ranges.astype(int)


def payload_range_grid_plot(
        aircraft_file_path: str,
        propulsion_id: str = "fastoad.wrapper.propulsion.rubber_engine",
        sizing_name: str = "sizing",
        name=None,
        fig=None,
        file_formatter=None,
        n_intervals_payloads=8,
        range_step=500,
):
    return grid_generation(
        aircraft_file_path,
        propulsion_id,
        sizing_name,
        name,
        fig,
        file_formatter,
        n_intervals_payloads,
        range_step,show_grid=True
    )[0]


def payload_range_loop_computation(
        aircraft_file_path: str,
        propulsion_id: str = "fastoad.wrapper.propulsion.rubber_engine",
        sizing_name: str = "sizing",
        name=None,
        fig=None,
        file_formatter=None,
        n_intervals_payloads=8,
        range_step=500,
        file_save: str = "loop_results.txt",
):
    """
    Returns a figure of the payload range using the corrected leduc-breguet formula,
    generates a grid and then whith the values of the range and paylaod, genrates a mission
    in order to retrieve the burnt fuel/ passenger/km
    Different designs can be superposed by providing an existing fig.
    Each design can be provided a name.

    :param aircraft_file_path: path of data file
    :param propulsion_id: name the model for the engine
    :param sizing_name: name of the siizing mission : default sizing
    :param name: name to give to the trace added to the figure
    :param fig: existing figure to which add the plot
    :param file_formatter: the formatter that defines the format of data file. If not provided,
                           default format will be assumed.
    :param n_intervals_payloads : number of intervals between 0.45* max_payload and 0.95 max_payload for the grid
                                   defaults is 8
    :param range_step: defines the step between 2 grid points in the range axis. default is 500 [NM]
    :param file_save: sets the name where the results are saved

    :return: wing plot figure
    """

    fig, grid, dummy_variable = grid_generation(
        aircraft_file_path,
        propulsion_id,
        sizing_name,
        name,
        fig,
        file_formatter,
        n_intervals_payloads,
        range_step,
    )
    """
    # File generation before launching a mission
    """

    CONFIG_MISSION_FILE = pth.join("workdir", "mission_file_conf.yml")  # modular
    SOURCE_FILE = pth.join("workdir", "problem_outputs.xml")  # modular
    input_file_mission = oad.generate_inputs(CONFIG_MISSION_FILE, SOURCE_FILE, overwrite=True)
    input_file_mission = oad.DataFile(input_file_mission)

    """
    # Need change: thrust rate settings for the rubber engine
    """

    input_file_mission["data:propulsion:climb:thrust_rate"].value = 0.93
    input_file_mission["data:propulsion:initial_climb:thrust_rate"].value = 1.00
    input_file_mission["data:propulsion:descent:thrust_rate"].value = 0.18
    input_file_mission["data:propulsion:taxi:thrust_rate"].value = 0.3

    """
    # Parameters for the mission
    """

    input_file_mission["data:mission:op_mission:diversion:distance"].value = 370400
    input_file_mission["data:mission:op_mission:holding:duration"].value = 1800
    input_file_mission["data:mission:op_mission:takeoff:V2"].value = 82.3
    input_file_mission["data:mission:op_mission:takeoff:altitude"].value = 458.1
    input_file_mission["data:mission:op_mission:takeoff:fuel"].value = 82.4
    input_file_mission["data:mission:op_mission:taxi_in:duration"].value = 600
    input_file_mission["data:mission:op_mission:taxi_out:duration"].value = 300
    input_file_mission["data:mission:op_mission:taxi_out:thrust_rate"].value = 0.3

    """
    # Run a mission on each grid point and generate the fuel consumption/km/kg_payload
    """
    grid_ranges = grid[0]
    grid_payloads = grid[1]
    time_begin_loop = time.perf_counter()

    for i in range(len(grid_ranges)):
        """
        # change the data
        """
        time_begin = time.perf_counter()
        input_file_mission["data:mission:op_mission:payload"].value = grid_payloads[i]
        input_file_mission["data:mission:op_mission:main_route:range"].value = (
                grid_ranges[i] * 10 ** 3 * 1.852
        )
        input_file_mission.save()

        """
        #Evaluate the problem and retrieve the data
        """
        mission_problem = oad.evaluate_problem(CONFIG_MISSION_FILE, overwrite=True)
        MISSION_OUTPUT_FILE = pth.join("workdir", "mission_outputs.xml")
        mission_variables = VariableIO(MISSION_OUTPUT_FILE, file_formatter).read()

        main_route_fuel = mission_variables["data:mission:op_mission:main_route:fuel"].value[0]
        take_off_fuel = mission_variables["data:mission:op_mission:takeoff:fuel"].value[0]
        taxi_in_fuel = mission_variables["data:mission:op_mission:taxi_in:fuel"].value[0]
        taxi_out_fuel = mission_variables["data:mission:op_mission:taxi_out:fuel"].value[0]

        grid[2, i] = main_route_fuel + take_off_fuel + taxi_in_fuel + taxi_out_fuel

        time_end = time.perf_counter()
        print(
            "Computation : ",
            i,
            " Time to evaluate mission : ",
            time_end - time_begin,
            " Time since beginning of the  loop: ",
            time_end - time_begin_loop,
        )

    """
    Consumption computation and saving
    """
    grid[2] = grid[2] / (grid[1] * grid[0] * 1.852 * 10 ** 3)  # kg_fuel/kg_payload/km
    np.savetxt(pth.join("data", file_save), grid.T)


def payload_range_full(
        aircraft_file_path: str,
        propulsion_id: str = "fastoad.wrapper.propulsion.rubber_engine",
        sizing_name: str = "sizing",
        name=None,
        fig=None,
        file_formatter=None,
        n_intervals_payloads=8,
        range_step=500,
        file_save: str = "loop_results.txt",
        show_grid: bool = True,
        x_axis=None,
        y_axis= None,
) -> go.FigureWidget:
    """
        Returns a figure of the payload range using the corrected leduc-breguet formula,
        generates a grid and then whith the values of the range and paylaod, genrates a mission
        in order to retrieve the burnt fuel/ passenger/km
        Different designs can be superposed by providing an existing fig.
        Each design can be provided a name.

        :param aircraft_file_path: path of data file
        :param propulsion_id: name the model for the engine
        :param sizing_name: name of the siizing mission : default sizing
        :param name: name to give to the trace added to the figure
        :param fig: existing figure to which add the plot
        :param file_formatter: the formatter that defines the format of data file. If not provided,
                               default format will be assumed.
        :param n_intervals_payloads : number of intervals between 0.45* max_payload and 0.95 max_payload for the grid
                                       defaults is 8
        :param range_step: defines the step between 2 grid points in the range axis. default is 500 [NM]
        :param file_save: sets the name where the results are saved
        :param show_grid: states if the grid points are to be shown on the fig
        :param x_axis: defines the x axis if the user wants to
        :param y_axis: defines the y axis if the user wants to
        :return: wing plot figure
        """

    fig, grid, n_values_y = grid_generation(
        aircraft_file_path,
        propulsion_id,
        sizing_name,
        name,
        fig,
        file_formatter,
        n_intervals_payloads,
        range_step,
        show_grid,
        x_axis,
        y_axis,
    )

    try:
        rst = np.loadtxt(pth.join("data", file_save))
        rst = rst.T
        n_points_x = int(max(rst[0]) / range_step)
        x = np.linspace(min(rst[0]), max(rst[0]), n_points_x).tolist()
        y = np.linspace(min(rst[1]), max(rst[1]), n_intervals_payloads)
        y = y
        y = y.tolist()

        z = [[None] * n_points_x for _ in range(n_intervals_payloads)]

        for i in range(len(n_values_y)):
            z[i][0: n_values_y[i]] = rst[
                                     2, sum(n_values_y[0:i]): sum(n_values_y[0:i]) + n_values_y[i]
                                     ]

        fig.add_trace(go.Contour(z=z, x=x, y=y))

    except:
        print(
            "No results were found in the data folder, you first need to run the function "
            "payload_range_loop_computation"
        )

    fig.update_layout(
        title_text="Payload range diagram with specific consumption",
        xaxis_title="range [NM]",
        yaxis_title="Payload [tonnes]",
    )

    if x_axis is not None:
        fig.update_xaxes(range=[x_axis[0], x_axis[1]])
    if y_axis is not None:
        fig.update_yaxes(range=[y_axis[0], y_axis[1]])

    return fig
