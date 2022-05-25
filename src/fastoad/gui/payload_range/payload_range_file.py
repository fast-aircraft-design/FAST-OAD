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
from stdatm import Atmosphere
from fastoad.openmdao.variables import VariableList

import openmdao.api as om
from fastoad.module_management._bundle_loader import BundleLoader
from fastoad.openmdao.problem import FASTOADProblem
from fastoad.module_management._plugins import FastoadLoader

import fastoad.api as oad
import os.path as pth
import time

COLS = plotly.colors.DEFAULT_PLOTLY_COLORS


def breguet_leduc_formula(mass_in, mass_out, constant_coeff, x0):
    """
    Function used internally
    param mass_in:mass at the beginning of the mission
    param mass_out: mass at the en of the mission
    param x0 : first estimation of the range in NM
    Returns the range in "NM" using the breguet leduc modified formula

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
    """
    Function used internally
    Computes the points of the payload range diagram. There are 4 points :
    A : max_payload, 0 range
    B : max_payload, MTOW ==> range
    C : MFW, MTOW ==> range
    D : 0 payload, MFW ==> range
    param aircraft_file_path: output file of the aircraft design
    param propulsion_id: name of the model for the engine
    param sizing_name: name of the sizing mission : default sizing
    param file_formatter: the formatter that defines the format of data file. If not provided,
                           default format will be assumed.
    returns 2 ndarrays containing the ranges and payloads from the breguet-leduc formula
    """
    FastoadLoader()

    variables = VariableIO(aircraft_file_path, file_formatter).read()

    glide_ratio = variables["data:aerodynamics:aircraft:cruise:L_D_max"].value[
        0
    ]  # max glide ratio during cruise
    # altitude = variables["data:mission:" + sizing_name + ":main_route:cruise:altitude"].value[
    #     0
    # ]  # cruise altitude
    altitude = convert_units(
        variables["data:mission:sizing:main_route:cruise:altitude"].value[0],
        variables["data:mission:sizing:main_route:cruise:altitude"].units,
        "m",
    )  # cruise altitude

    cruise_mach = variables["data:TLAR:cruise_mach"].value[0]
    sizing_range = variables["data:TLAR:range"].value[0]  # first approximation for the range

    max_payload = variables["data:weight:aircraft:max_payload"].value[0]
    sizing_payload = variables["data:weight:aircraft:payload"].value[0]
    mtow = variables["data:weight:aircraft:MTOW"].value[0]
    owe = variables["data:weight:aircraft:OWE"].value[0]
    mfw = variables["data:weight:aircraft:MFW"].value[0]
    fuel_burned = variables["data:mission:" + sizing_name + ":main_route:fuel"].value[0]

    g = 9.81
    atm = Atmosphere(altitude, altitude_in_feet=False)
    atm.mach = cruise_mach
    speed = atm.true_airspeed

    thrust_begin = 0.98 * mtow * g / glide_ratio  # thrust at the beginning of the cruise
    fp_begin = FlightPoint(
        altitude=altitude,
        mach=cruise_mach,
        thrust=thrust_begin,
        thrust_rate=0.7,
        thrust_is_regulated=True,
        engine_setting=EngineSetting.convert("CRUISE"),
    )
    weight_end = mtow - fuel_burned
    thrust_end = weight_end * g / glide_ratio  # thrust at the end of the cruise

    fp_end = FlightPoint(
        altitude=altitude,
        mach=cruise_mach,
        thrust=thrust_end,
        thrust_rate=0.7,
        thrust_is_regulated=True,
        engine_setting=EngineSetting.convert("CRUISE"),
    )
    flight_points_list = pd.DataFrame([fp_begin, fp_end])

    # Create a propulsion model, compute_flight_points in order to retrieve the sfc
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
    a = [0, max_payload]

    # point B max_payload, MTOW ==> range :
    # mass_in = mtow
    # mass_out = owe + max_payload
    # ra_b = breguet_leduc_formula(mass_in, mass_out, coeff, sizing_range)

    # point C  MTOW, MFW ==> range:
    mass_in = mtow
    mass_out = mtow - mfw
    payload_c = mtow - mfw - owe
    ra_c = breguet_leduc_formula(mass_in, mass_out, coeff, sizing_range*10)[0]

    # design point and point B: max_payload,MTOW
    payload_b = max_payload
    ra_b = (sizing_range - ra_c) * (payload_b - payload_c) / (sizing_payload - payload_c) + ra_c

    # point D 0 payload, MFW ==> range
    mass_in = owe + mfw
    mass_out = owe
    ra_d = breguet_leduc_formula(mass_in, mass_out, coeff, sizing_range*10)[0]

    BL_ranges = np.array([0, ra_b, ra_c, ra_d, sizing_range])
    BL_payloads = np.array([max_payload, payload_b, payload_c, 0, sizing_payload]) / 10 ** 3
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
    :param propulsion_id: name of the model for the engine
    :param sizing_name: name of the sizing mission : default sizing
    :param name: name to give to the trace added to the figure
    :param fig: existing figure to which add the plot
    :param file_formatter: the formatter that defines the format of data file. If not provided,
                           default format will be assumed.
    :param x_axis: defines the x axis if the user wants to
    :param y_axis: defines the y axis if the user wants to
    :return: plot of the payload-range diagram with the points calculated using breguet-leduc formula
    """
    BL_ranges, BL_payloads = breguet_leduc_points(
        aircraft_file_path, propulsion_id, sizing_name, file_formatter
    )

    # Figure :
    if fig is None:
        fig = go.Figure()

    scatter_BL = go.Scatter(
        x=BL_ranges[0:-1], y=BL_payloads[0:-1], mode="lines+markers", name=name, showlegend=False
    )
    scatter_SIZING = go.Scatter(
        x=[BL_ranges[-1]], y=[BL_payloads[-1]], mode="markers", name="Sizing point"
    )

    fig.add_trace(scatter_BL)
    fig.add_trace(scatter_SIZING)

    fig = go.FigureWidget(fig)
    fig.update_layout(
        title_text="Payload range diagram", xaxis_title="range [NM]", yaxis_title="Payload [tonnes]"
    )

    if x_axis is not None:
        fig.update_xaxes(range=[x_axis[0], x_axis[1]])
    if y_axis is not None:
        fig.update_yaxes(range=[y_axis[0], y_axis[1]])

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
    upper_limit_box_tolerance=0.95,
    lower_limit_box_tolerance=0.4,
    right_limit_box_tolerance=0.95,
    left_limit_box_tolerance=0.1,
    show_grid: bool = True,
    x_axis=None,
    y_axis=None,
):
    """
    Returns a figure of the payload range using the corrected leduc-breguet formula,
    generates a grid and return an array with the number of grid points on one line
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
    :param upper_limit_box_tolerance : upper limit of the grid box, Default 0.95 means 0.95*max_payload
    :param lower_limit_box_tolerance : lower limit of the grid box, default 0.4 means 0.4*max_payload
    :param left_limit_box_tolerance : left limit of the grid box, default = 0.1 means 0.1*range(point B)
    :param right_limit_box_tolerance : right limit of the grid box, default = 0.95 means 0.95* max_range, meaning there is 5% safety
    :param show_grid: states if the grid points are to be shown on the fig
    :param x_axis: defines the x axis if the user wants to
    :param y_axis: defines the y axis if the user wants to
    :returns:  fig :  figure of the BL points and the grid points
               grid : ndarray with 3 lines containing : ranges, payloads, conumption (kg_fuel/km/kg_payload)
               n_values_ranges : ndarray, for each payload in the grid saves the number of ranges for the specific payload
    """

    # Compute Breguet Leduc points
    BL_ranges, BL_payloads = breguet_leduc_points(
        aircraft_file_path, propulsion_id, sizing_name, file_formatter
    )
    max_payload = BL_payloads[0]
    payload_c = BL_payloads[2]

    ra_b = BL_ranges[1]
    ra_c = BL_ranges[2]
    ra_d = BL_ranges[3]

    # Grid generation
    # step 1 : define the number of payloads for the grid

    val_payloads = np.linspace(
        lower_limit_box_tolerance * max_payload,
        upper_limit_box_tolerance * max_payload,
        n_intervals_payloads,
    )
    ra_c_id = np.where(val_payloads >= payload_c)[0][0]  # Find for which range the breakpoint c is

    # step 2 : compute the max range and the boundaries using the breakdown point

    max_range = np.zeros(n_intervals_payloads)
    max_range[0:ra_c_id] = (ra_c - ra_d) / payload_c * (val_payloads[0:ra_c_id]) + ra_d
    max_range[ra_c_id:] = (ra_b - ra_c) / (max_payload - payload_c) * (
        val_payloads[ra_c_id:] - payload_c
    ) + ra_c
    max_range *= right_limit_box_tolerance  # safety margin

    min_range = left_limit_box_tolerance * ra_b  # safety margin
    if min_range < range_step:
        min_range = range_step

    # step 2 : grid generation through grid_ranges and grid_payloads

    grid_ranges = np.array([])  # to stock the ranges of the grid x
    grid_payloads = np.array([])  # to stock the payloads of the grid y
    n_values_ranges = np.zeros(
        n_intervals_payloads
    )  # number of ranges(x) in th grid for a specific payload (y) # used further

    for i in range(n_intervals_payloads):
        range_add = np.arange(min_range, max_range[i], range_step)
        n_values_ranges[i] = len(range_add)
        grid_ranges = np.append(grid_ranges, range_add)
        grid_payloads = np.append(grid_payloads, np.ones(len(range_add)) * val_payloads[i])

    grid = np.array(
        [grid_ranges, grid_payloads, np.zeros(len(grid_ranges))]
    )  # [range, payload, total_fuel or consumption/kg/km]
    print("number of calculation points : ", len(grid[0]))

    # Figure:
    if fig is None:
        fig = go.Figure()

    scatter_BL = go.Scatter(
        x=BL_ranges[0:-1], y=BL_payloads[0:-1], mode="lines+markers", name=name, showlegend=False
    )
    scatter_SIZING = go.Scatter(
        x=[BL_ranges[-1]], y=[BL_payloads[-1]], mode="markers", name="Sizing point"
    )

    fig.add_trace(scatter_BL)
    fig.add_trace(scatter_SIZING)

    if show_grid == True:
        scatter_GRID = go.Scatter(x=grid[0], y=grid[1], mode="markers", name="Grid points")
        fig.add_trace(scatter_GRID)

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
    upper_limit_box_tolerance=0.95,
    lower_limit_box_tolerance=0.4,
    right_limit_box_tolerance=0.95,
    left_limit_box_tolerance=0.1,
    show_grid: bool = True,
    x_axis=None,
    y_axis=None,
):
    """
    Returns a figure of the payload range using the corrected leduc-breguet formula +
    shows the grid associated
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
    :param upper_limit_box_tolerance : upper limit of the grid box, Default 0.95 means 0.95*max_payload
    :param lower_limit_box_tolerance : lower limit of the grid box, default 0.4 means 0.4*max_payload
    :param left_limit_box_tolerance : left limit of the grid box, default = 0.1 means 0.1*range(point B)
    :param right_limit_box_tolerance : right limit of the grid box, default = 0.95 means 0.95* max_range, meaning there is 5% safety
    :param show_grid: states if the grid points are to be shown on the fig
    :param x_axis: defines the x axis if the user wants to
    :param y_axis: defines the y axis if the user wants to
    :returns:  fig :  figure of the BL points and the grid point
    """
    return grid_generation(
        aircraft_file_path,
        propulsion_id,
        sizing_name,
        name,
        fig,
        file_formatter,
        n_intervals_payloads,
        range_step,
        upper_limit_box_tolerance,
        lower_limit_box_tolerance,
        right_limit_box_tolerance,
        left_limit_box_tolerance,
        show_grid,
        x_axis,
        y_axis,
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
    upper_limit_box_tolerance=0.95,
    lower_limit_box_tolerance=0.4,
    right_limit_box_tolerance=0.95,
    left_limit_box_tolerance=0.1,
    file_save: str = "loop_results.txt",
):
    """
    Returns nothing but saves the results of the loop in the specified file

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
    :param upper_limit_box_tolerance : upper limit of the grid box, Default 0.95 means 0.95*max_payload
    :param lower_limit_box_tolerance : lower limit of the grid box, default 0.4 means 0.4*max_payload
    :param left_limit_box_tolerance : left limit of the grid box, default = 0.1 means 0.1*range(point B)
    :param right_limit_box_tolerance : right limit of the grid box, default = 0.95 means 0.95* max_range, meaning there is 5% safety
    :param file_save: sets the name where the results are saved
    """

    # grid generation

    fig, grid, dummy_variable = grid_generation(
        aircraft_file_path,
        propulsion_id,
        sizing_name,
        name,
        fig,
        file_formatter,
        n_intervals_payloads,
        range_step,
        upper_limit_box_tolerance,
        lower_limit_box_tolerance,
        right_limit_box_tolerance,
        left_limit_box_tolerance,
    )

    # Configuration file generation before launching a mission
    # We need to have a mission_file_conf.yml

    CONFIG_MISSION_FILE = pth.join(
        "workdir", "mission_file_conf.yml"
    )  # defined by the configuration : can be changed and made a variable
    SOURCE_FILE = aircraft_file_path  # modular
    input_file_mission = oad.generate_inputs(CONFIG_MISSION_FILE, SOURCE_FILE, overwrite=True)
    input_file_mission = oad.DataFile(input_file_mission)

    input_file = oad.DataFile(aircraft_file_path)

    # Defined otherwise the mission would noot run

    input_file_mission["data:propulsion:climb:thrust_rate"].value = input_file[
        "data:propulsion:climb:thrust_rate"
    ].value
    input_file_mission["data:propulsion:initial_climb:thrust_rate"].value = input_file[
        "data:propulsion:initial_climb:thrust_rate"
    ].value
    input_file_mission["data:propulsion:descent:thrust_rate"].value = input_file[
        "data:propulsion:descent:thrust_rate"
    ].value
    input_file_mission["data:propulsion:taxi:thrust_rate"].value = input_file[
        "data:propulsion:taxi:thrust_rate"
    ].value

    # Set the parameters of the mission with change of units

    input_file_mission["data:mission:op_mission:diversion:distance"].value[0] = convert_units(
        input_file["data:mission:" + sizing_name + ":diversion:distance"].value[0],
        input_file["data:mission:" + sizing_name + ":diversion:distance"].units,
        "m",
    )  # in m

    input_file_mission["data:mission:op_mission:holding:duration"].value[0] = convert_units(
        input_file["data:mission:" + sizing_name + ":holding:duration"].value[0],
        input_file["data:mission:" + sizing_name + ":holding:duration"].units,
        "s",
    )  # in s

    input_file_mission["data:mission:op_mission:takeoff:V2"].value[0] = convert_units(
        input_file["data:mission:" + sizing_name + ":takeoff:V2"].value[0],
        input_file["data:mission:" + sizing_name + ":takeoff:V2"].units,
        "m/s",
    )

    input_file_mission["data:mission:op_mission:takeoff:altitude"].value = convert_units(
        input_file["data:mission:" + sizing_name + ":takeoff:altitude"].value[0],
        input_file["data:mission:" + sizing_name + ":takeoff:altitude"].units,
        "m",
    )

    input_file_mission["data:mission:op_mission:takeoff:fuel"].value = input_file[
        "data:mission:" + sizing_name + ":takeoff:fuel"
    ].value
    input_file_mission["data:mission:op_mission:taxi_in:duration"].value[0] = convert_units(
        input_file["data:mission:" + sizing_name + ":taxi_in:duration"].value[0],
        input_file["data:mission:" + sizing_name + ":taxi_in:duration"].units,
        "s",
    )
    input_file_mission["data:mission:op_mission:taxi_out:duration"].value[0] = convert_units(
        input_file["data:mission:" + sizing_name + ":taxi_out:duration"].value[0],
        input_file["data:mission:" + sizing_name + ":taxi_out:duration"].units,
        "s",
    )

    input_file_mission["data:mission:op_mission:taxi_out:thrust_rate"].value = input_file[
        "data:mission:" + sizing_name + ":taxi_out:thrust_rate"
    ].value

    # Run a mission on each grid point and generate the fuel consumption/km/kg_payload

    grid_ranges = grid[0]
    grid_payloads = grid[1]
    time_begin_loop = time.perf_counter()  # Timer

    for i in range(len(grid_ranges)):

        # Update the data

        time_begin = time.perf_counter()
        input_file_mission["data:mission:op_mission:payload"].value = grid_payloads[i]
        input_file_mission["data:mission:op_mission:main_route:range"].value = (
            grid_ranges[i] * 10 ** 3 * 1.852
        )
        input_file_mission.save()

        # Evaluate the problem and retrieve the results

        mission_problem = oad.evaluate_problem(CONFIG_MISSION_FILE, overwrite=True)
        MISSION_OUTPUT_FILE = pth.join("workdir", "mission_outputs.xml")
        mission_variables = VariableIO(MISSION_OUTPUT_FILE, file_formatter).read()

        main_route_fuel = mission_variables["data:mission:op_mission:main_route:fuel"].value[0]
        take_off_fuel = mission_variables["data:mission:op_mission:takeoff:fuel"].value[0]
        taxi_in_fuel = mission_variables["data:mission:op_mission:taxi_in:fuel"].value[0]
        taxi_out_fuel = mission_variables["data:mission:op_mission:taxi_out:fuel"].value[0]

        # Look up the fuel consumption
        grid[2, i] = main_route_fuel + take_off_fuel + taxi_in_fuel + taxi_out_fuel

        time_end = time.perf_counter()  # end the timer
        print(
            "Computation : ",
            i,
            " Time to evaluate mission : ",
            time_end - time_begin,
            " Time since beginning of the  loop: ",
            time_end - time_begin_loop,
        )

    # Specific consumption computation and saving into a file

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
    upper_limit_box_tolerance=0.95,
    lower_limit_box_tolerance=0.4,
    right_limit_box_tolerance=0.95,
    left_limit_box_tolerance=0.1,
    file_save: str = "loop_results.txt",
    show_grid: bool = True,
    x_axis=None,
    y_axis=None,
) -> go.FigureWidget:
    """
    Returns a figure of the payload range using the corrected leduc-breguet formula,
    if payload_range_loop_computation(...) hhas been run before, the specific consumption is showed
    on each grid point

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
    :param upper_limit_box_tolerance : upper limit of the grid box, Default 0.95 means 0.95*max_payload
    :param lower_limit_box_tolerance : lower limit of the grid box, default 0.4 means 0.4*max_payload
    :param left_limit_box_tolerance : left limit of the grid box, default = 0.1 means 0.1*range(point B)
    :param right_limit_box_tolerance : right limit of the grid box, default = 0.95 means 0.95* max_range, meaning there is 5% safety
    :param file_save: sets the name where the results are saved
    :param show_grid: states if the grid points are to be shown on the fig
    :param x_axis: defines the x axis if the user wants to
    :param y_axis: defines the y axis if the user wants to
    :return: fig with payload range diagram + specific consumptions
    """

    # Generate grid figure + look up for n_values_ranges
    fig, grid, n_values_ranges = grid_generation(
        aircraft_file_path,
        propulsion_id,
        sizing_name,
        name,
        fig,
        file_formatter,
        n_intervals_payloads,
        range_step,
        upper_limit_box_tolerance,
        lower_limit_box_tolerance,
        right_limit_box_tolerance,
        left_limit_box_tolerance,
        show_grid,
        x_axis,
        y_axis,
    )
    # load the results from payload_range_loop_computation(...)
    try:
        results = np.loadtxt(pth.join("data", file_save))
        results = results.T
        n_points_x = int(max(results[0]) / range_step)
        x = np.linspace(min(results[0]), max(results[0]), n_points_x).tolist()
        y = np.linspace(min(results[1]), max(results[1]), n_intervals_payloads)
        y = y
        y = y.tolist()

        z = [[None] * n_points_x for _ in range(n_intervals_payloads)]

        for i in range(len(n_values_ranges)):
            z[i][0 : n_values_ranges[i]] = results[
                2, sum(n_values_ranges[0:i]) : sum(n_values_ranges[0:i]) + n_values_ranges[i]
            ]

        fig.add_trace(
            go.Contour(
                z=z,
                x=x,
                y=y,
                colorbar=dict(
                    title="Consumption [kg_fuel/km/kg_payload]",  # title here
                    titleside="right",
                    titlefont=dict(size=10, family="Arial, sans-serif"),
                ),
            )
        )

    except:
        print(
            "No results were found in the data folder, you first need to run the function "
            "payload_range_loop_computation(...) \n attention: takes time"
        )

    fig.update_layout(
        title_text="Payload range diagram with specific consumption",
        xaxis_title="range [NM]",
        yaxis_title="Payload [tonnes]",
        showlegend=False,
    )

    if x_axis is not None:
        fig.update_xaxes(range=[x_axis[0], x_axis[1]])
    if y_axis is not None:
        fig.update_yaxes(range=[y_axis[0], y_axis[1]])

    return fig
