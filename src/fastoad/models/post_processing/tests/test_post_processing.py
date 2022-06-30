"""
Test module for geometry functions of cg components
"""
#  This file is part of FAST-OAD_CS25
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

# pylint: disable=redefined-outer-name  # needed for pytest fixtures

import os.path as pth
import plotly
import plotly.graph_objects as go
import pytest
import numpy as np
from fastoad._utils.testing import run_system
from fastoad.io import VariableIO
from scipy.optimize import fsolve

from ..speed_altitude_diagram import SpeedAltitudeDiagram
from ..ceiling_computation import CeilingComputation
from ..ceiling_mass_diagram import CeilingMassDiagram
from ..available_power_diagram import AvailablepowerDiagram


@pytest.fixture(scope="module")
def input_xml() -> VariableIO:
    """
    :return: access to the sample xml data
    """
    # TODO: have more consistency in input data (no need for the whole geometry_inputs_full.xml)
    return VariableIO(pth.join(pth.dirname(__file__), "data", "data_post_processing.xml"))


# def test_speed_altitude_diagram(input_xml):
#    # Doit contenir toutes les entrees dont le modèle a besoin
#    input_list = [
#        "data:geometry:wing:area",
#        "data:weight:aircraft:MTOW",
#        "data:weight:aircraft:MZFW",
#        "data:aerodynamics:aircraft:cruise:CL",
#        "data:propulsion:rubber_engine:bypass_ratio",
#        "data:propulsion:rubber_engine:overall_pressure_ratio",
#        "data:propulsion:rubber_engine:turbine_inlet_temperature",
#        "data:propulsion:rubber_engine:maximum_mach",
#        "data:propulsion:MTO_thrust",
#        "data:propulsion:rubber_engine:design_altitude",
#        "data:aerodynamics:aircraft:cruise:CD",
#        "data:aerodynamics:aircraft:landing:CL_max_clean",
#        "data:performance:ceiling:MTOW",
#        "data:performance:ceiling:MZFW",
#        "data:TLAR:cruise_mach",
#    ]
#
#    input_vars = input_xml.read(only=input_list).to_ivc()
#
#    expected_v_min_mtow = np.array(
#        [
#            77.18234811,
#            77.65210433,
#            78.12607528,
#            78.60431101,
#            79.0868623,
#            79.57378071,
#            80.06511853,
#            80.56092887,
#            81.0612656,
#            81.56618341,
#            82.07573783,
#            82.5899852,
#            83.10898275,
#            83.63278853,
#            84.16146152,
#            84.69506158,
#            85.23364949,
#            85.77728696,
#            86.32603665,
#            86.87996221,
#            87.43912825,
#            88.0036004,
#            88.57344531,
#            89.14873068,
#            89.72952526,
#            90.31589889,
#            90.90792252,
#            91.5056682,
#            92.10920917,
#            92.71861978,
#            93.33397562,
#            93.95535347,
#            94.58283133,
#            95.2164885,
#            95.85640552,
#            96.50266428,
#            97.15534796,
#            97.81454115,
#            98.48032979,
#            99.15280124,
#            99.83204431,
#            100.51814929,
#            101.21120795,
#            101.9113136,
#            102.61856111,
#            103.33304695,
#            104.05486918,
#            104.78412757,
#            105.52092354,
#            106.26536024,
#            107.01754259,
#            107.7775773,
#            108.54557292,
#            109.32163986,
#            110.10589044,
#            110.89843893,
#            111.69940159,
#            112.50889672,
#            113.32704467,
#            114.15396792,
#            114.98979112,
#            115.83464111,
#            116.688647,
#            117.55194017,
#            118.4246544,
#            119.30692583,
#            120.19889307,
#            121.10069724,
#            122.012482,
#            122.93439365,
#            123.86658115,
#            124.8091962,
#            125.76239329,
#            126.72632974,
#            127.70116583,
#            128.68706479,
#            129.6841929,
#            130.69271957,
#            131.71281739,
#            132.7446622,
#            133.78843319,
#            134.84431294,
#            135.91248752,
#            136.99314658,
#            138.08648339,
#            139.19269498,
#            140.31198217,
#            141.44454971,
#            142.82091812,
#            144.24944278,
#            145.69225585,
#            147.14950023,
#            148.62132028,
#            150.10786178,
#            151.60927197,
#            153.12569959,
#            154.65729483,
#            156.2042094,
#            157.76659654,
#            159.344611,
#        ]
#    )
#
#    expected_v_max_mtow = np.array(
#        [
#            274.12559654,
#            274.73558286,
#            275.35513669,
#            275.98425539,
#            276.62293641,
#            277.26767335,
#            277.92115216,
#            278.58411283,
#            279.25655244,
#            279.93846908,
#            280.62986211,
#            281.33073239,
#            282.04108254,
#            282.76091723,
#            283.42691717,
#            283.00632684,
#            282.58511051,
#            282.1632654,
#            281.74078866,
#            281.31767745,
#            280.89392892,
#            280.46954016,
#            280.04450827,
#            279.61883031,
#            279.19250333,
#            278.76552436,
#            278.33789039,
#            277.9095984,
#            277.48064533,
#            277.05102813,
#            276.6207437,
#            276.18978891,
#            275.75816063,
#            275.32585568,
#            274.89287088,
#            274.45920301,
#            274.02484882,
#            273.58980504,
#            273.15406839,
#            272.71763554,
#            272.28050313,
#            271.84266781,
#            271.40412616,
#            270.96487475,
#            270.52491013,
#            270.08422882,
#            269.6428273,
#            269.20070202,
#            268.75784941,
#            268.31426588,
#            267.86994779,
#            267.42489148,
#            266.97909326,
#            266.5325494,
#            266.08525616,
#            265.63720974,
#            265.18840633,
#            264.73884209,
#            264.28851311,
#            263.8374155,
#            263.3855453,
#            262.93289852,
#            262.47947116,
#            262.02525915,
#            261.57025842,
#            261.11446483,
#            260.65787423,
#            260.20048242,
#            259.74228517,
#            259.28327821,
#            258.82345723,
#            258.36281789,
#            257.9013558,
#            257.43906653,
#            256.97594563,
#            256.51198858,
#            256.04719084,
#            255.58154784,
#            255.11505492,
#            254.64770744,
#            254.17950066,
#            253.71042984,
#            253.24049018,
#            252.76967682,
#            252.29798488,
#            251.82540942,
#            251.35194545,
#            250.87758795,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#        ]
#    )
#
#    expected_v_min_mzfw = np.array(
#        [
#            70.070686,
#            70.53896959,
#            71.01186791,
#            71.48944116,
#            71.97175054,
#            72.45885821,
#            72.95082738,
#            73.44772228,
#            73.94960821,
#            74.45655154,
#            74.96861975,
#            75.48588142,
#            76.00840629,
#            76.53626527,
#            77.06953047,
#            77.60827517,
#            78.15257395,
#            78.7025026,
#            79.25813824,
#            79.81955928,
#            80.38684549,
#            80.960078,
#            81.53933933,
#            82.12471346,
#            82.7162858,
#            83.31414325,
#            83.91837424,
#            84.52906875,
#            85.14631832,
#            85.77021614,
#            86.40085704,
#            87.03833751,
#            87.68275581,
#            88.33421191,
#            88.99280761,
#            89.65864653,
#            90.33183418,
#            91.01247796,
#            91.70068725,
#            92.39657342,
#            93.10024988,
#            93.81183215,
#            94.53143786,
#            95.25918684,
#            95.99520114,
#            96.73960509,
#            97.49252536,
#            98.254091,
#            99.0244335,
#            99.80368684,
#            100.59198756,
#            101.38947479,
#            102.19629035,
#            103.01257878,
#            103.83848741,
#            104.67416642,
#            105.51976892,
#            106.37545104,
#            107.24137192,
#            108.11769388,
#            109.00458242,
#            109.90220633,
#            110.81073778,
#            111.73035235,
#            112.66122919,
#            113.60355102,
#            114.55750428,
#            115.52327918,
#            116.50106983,
#            117.4910743,
#            118.49349475,
#            119.50853749,
#            120.53641312,
#            121.57733662,
#            122.63152746,
#            123.69920971,
#            124.78061219,
#            125.87596852,
#            126.9855173,
#            128.10950222,
#            129.40969772,
#            130.83105289,
#            132.26801934,
#            133.72076853,
#            135.1894738,
#            136.67431042,
#            138.17545555,
#            139.69308832,
#            141.22738982,
#            142.77854313,
#            144.34673334,
#            145.93214757,
#            147.53497499,
#            149.15540687,
#            150.79363656,
#            152.44985954,
#            154.12427343,
#            155.81707805,
#            157.52847536,
#            159.2586696,
#        ]
#    )
#
#    expected_v_max_mzfw = np.array(
#        [
#            275.05809491,
#            275.74975061,
#            276.45336222,
#            277.16894119,
#            277.89649976,
#            278.63605127,
#            279.38761052,
#            280.15119411,
#            280.92658082,
#            281.71043103,
#            282.50629353,
#            283.3141931,
#            283.77522659,
#            283.31413715,
#            282.85229607,
#            282.38969966,
#            281.92634421,
#            281.46222596,
#            280.99734114,
#            280.53168593,
#            280.06525649,
#            279.59804895,
#            279.1300594,
#            278.6612839,
#            278.19171848,
#            277.72135913,
#            277.2502018,
#            276.77824243,
#            276.3054769,
#            275.83190107,
#            275.35751076,
#            274.88230176,
#            274.40626979,
#            273.92941059,
#            273.45171982,
#            272.97319311,
#            272.49382605,
#            272.01361422,
#            271.53255312,
#            271.05063824,
#            270.56786501,
#            270.08422882,
#            269.59972504,
#            269.11434898,
#            268.6280959,
#            268.14096105,
#            267.6529396,
#            267.1640267,
#            266.67421744,
#            266.18350687,
#            265.69189,
#            265.1993618,
#            264.70591716,
#            264.21155097,
#            263.71625803,
#            263.22003311,
#            262.72287094,
#            262.22476618,
#            261.72571346,
#            261.22570733,
#            260.72474231,
#            260.22281287,
#            259.71991341,
#            259.21603829,
#            258.7111818,
#            258.20533819,
#            257.69850166,
#            257.19066632,
#            256.68182624,
#            256.17197545,
#            255.6611079,
#            255.14921747,
#            254.636298,
#            254.12234326,
#            253.60734695,
#            253.09130272,
#            252.57420414,
#            252.05604472,
#            251.53681791,
#            251.01651708,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#            250.81000996,
#        ]
#    )
#
#    problem = run_system(
#        SpeedAltitudeDiagram(propulsion_id="fastoad.wrapper.propulsion.rubber_engine"), input_vars
#    )
#    # assert problem["data:performance:speed_altitude_diagram:v_min_mtow"] == pytest.approx(expected_v_min, abs=1e-5)
#    # assert problem["data:performance:speed_altitude_diagram:v_max_mtow"] == pytest.approx(expected_v_max, abs=1e-5)
#    # assert problem["data:performance:speed_altitude_diagram:v_min_mzfw"] == pytest.approx(expected_v_min, abs=1e-5)
#    # assert problem["data:performance:speed_altitude_diagram:v_max_mzfw"] == pytest.approx(expected_v_max, abs=1e-5)


# def test_ceiling_computation(input_xml):
# # Doit contenir toutes les entrees dont le modèle a besoin
# input_list = [
#     "data:geometry:wing:area",
#     "data:weight:aircraft:MTOW",
#     "data:weight:aircraft:MZFW",
#     "data:propulsion:rubber_engine:bypass_ratio",
#     "data:propulsion:rubber_engine:overall_pressure_ratio",
#     "data:propulsion:rubber_engine:turbine_inlet_temperature",
#     "data:propulsion:rubber_engine:maximum_mach",
#     "data:propulsion:rubber_engine:design_altitude",
#     "data:propulsion:MTO_thrust",
#     "data:aerodynamics:aircraft:cruise:CD",
#     "data:aerodynamics:aircraft:landing:CL_max_clean",
#     "data:aerodynamics:aircraft:cruise:CL",
#     "data:TLAR:cruise_mach",
# ]
#
# input_vars = input_xml.read(only=input_list).to_ivc()
#
# expected_ceiling_mtow = 41000
# expected_ceiling_mzfw = 45000
#
# problem = run_system(
#     CeilingComputation(propulsion_id="fastoad.wrapper.propulsion.rubber_engine"), input_vars
# )
# #assert problem["data:performance:ceiling:MTOW"] == pytest.approx(expected_ceiling_mtow, abs=1e-5)
# #assert problem["data:performance:ceiling:MZFW"] == pytest.approx(expected_ceiling_mzfw, abs=1e-5)


# def test_ceiling_mass_diagram(input_xml):
#    # Doit contenir toutes les entrees dont le modèle a besoin
#    input_list = [
#        "data:geometry:wing:area",
#        "data:weight:aircraft:MTOW",
#        "data:weight:aircraft:MZFW",
#        "data:propulsion:rubber_engine:bypass_ratio",
#        "data:propulsion:rubber_engine:overall_pressure_ratio",
#        "data:propulsion:rubber_engine:turbine_inlet_temperature",
#        "data:propulsion:rubber_engine:maximum_mach",
#        "data:propulsion:rubber_engine:design_altitude",
#        "data:propulsion:MTO_thrust",
#        "data:aerodynamics:aircraft:cruise:CD",
#        "data:aerodynamics:aircraft:landing:CL_max_clean",
#        "data:aerodynamics:aircraft:cruise:CL",
#        "data:TLAR:cruise_mach",
#    ]
#
#    input_vars = input_xml.read(only=input_list).to_ivc()
#
#    expected_ceiling_cruise = np.zeros(45)
#    expected_ceiling_climb = np.zeros(45)
#    expected_ceiling_buffeting = np.zeros(45)
#
#    problem = run_system(
#        CeilingComputation(propulsion_id="fastoad.wrapper.propulsion.rubber_engine"), input_vars
#    )
#
#    # assert problem["data:performance:ceiling:MTOW"] == pytest.approx(expected_ceiling_mtow, abs=1e-5)
#    # assert problem["data:performance:ceiling:MZFW"] == pytest.approx(expected_ceiling_mzfw, abs=1e-5)


# def test_available_power_diagram(input_xml):
#    # Doit contenir toutes les entrees dont le modèle a besoin
#    input_list = [
#        "data:geometry:wing:area",
#        "data:weight:aircraft:MTOW",
#        "data:weight:aircraft:MZFW",
#        "data:propulsion:rubber_engine:bypass_ratio",
#        "data:propulsion:rubber_engine:overall_pressure_ratio",
#        "data:propulsion:rubber_engine:turbine_inlet_temperature",
#        "data:propulsion:rubber_engine:maximum_mach",
#        "data:propulsion:rubber_engine:design_altitude",
#        "data:propulsion:MTO_thrust",
#        "data:aerodynamics:aircraft:cruise:CD",
#        "data:aerodynamics:aircraft:landing:CL_max_clean",
#        "data:aerodynamics:aircraft:cruise:CL",
#        "data:TLAR:cruise_mach",
#    ]
#
#    input_vars = input_xml.read(only=input_list).to_ivc()
#
#    expected_v_vector = np.zeros(100)
#    expected_thrust_max = np.zeros(100)
#    expected_thrust_available = np.zeros(100)
#
#    problem = run_system(
#        CeilingComputation(propulsion_id="fastoad.wrapper.propulsion.rubber_engine"), input_vars
#    )
#
#    # assert problem["data:performance:ceiling:MTOW"] == pytest.approx(expected_ceiling_mtow, abs=1e-5)
#    # assert problem["data:performance:ceiling:MZFW"] == pytest.approx(expected_ceiling_mzfw, abs=1e-5)

