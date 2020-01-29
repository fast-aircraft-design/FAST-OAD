"""
Test module for aerodynamics groups
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA/ISAE
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

import os.path as pth

from pytest import approx

from fastoad.io.xml import OMXmlIO
from fastoad.modules.aerodynamics.aerodynamics_high_speed import AerodynamicsHighSpeed
from fastoad.modules.aerodynamics.aerodynamics_landing import AerodynamicsLanding
from fastoad.modules.aerodynamics.aerodynamics_low_speed import AerodynamicsLowSpeed
from tests.testing_utilities import run_system


def get_indep_var_comp(var_names):
    """ Reads required input data and returns an IndepVarcomp() instance"""
    reader = OMXmlIO(
        pth.join(pth.dirname(__file__), "data", "aerodynamics_inputs.xml"))
    reader.path_separator = ':'
    ivc = reader.read(only=var_names)
    return ivc


def test_aerodynamics_landing():
    """ Tests AerodynamicsHighSpeed """
    input_list = [
        'TLAR:approach_speed',
        'mission:sizing:landing:flap_angle',
        'mission:sizing:landing:slat_angle',
        'geometry:wing:MAC:length',
        'geometry:wing:sweep_25',
        'geometry:wing:sweep_0',
        'geometry:wing:sweep_100_outer',
        'geometry:flap:chord_ratio',
        'geometry:flap:span_ratio',
        'geometry:slat:chord_ratio',
        'geometry:slat:span_ratio',
        'xfoil:mach',
        'aerodynamics:aircraft:landing:CL_max:landing_gear_effect:k'
    ]

    ivc = get_indep_var_comp(input_list)
    problem = run_system(AerodynamicsLanding(), ivc)
    assert problem['aerodynamics:aircraft:landing:CL_max_clean'] == approx(1.56014, abs=1e-5)
    assert problem['aerodynamics:aircraft:landing:CL_max'] == approx(2.78833, abs=1e-5)

    input_list.append('aerodynamics:aircraft:landing:CL_max_clean')
    ivc = get_indep_var_comp(input_list)
    problem = run_system(AerodynamicsLanding(use_xfoil=False), ivc)
    assert problem['aerodynamics:aircraft:landing:CL_max_clean'] == approx(1.55, abs=1e-5)
    assert problem['aerodynamics:aircraft:landing:CL_max'] == approx(2.77819, abs=1e-5)


def test_aerodynamics_high_speed():
    """ Tests AerodynamicsHighSpeed """
    input_list = [
        'geometry:propulsion:engine:count',
        'geometry:propulsion:fan:length',
        'geometry:flap:chord_ratio',
        'geometry:flap:span_ratio',
        'geometry:fuselage:maximum_height',
        'geometry:fuselage:length',
        'geometry:fuselage:wetted_area',
        'geometry:fuselage:maximum_width',
        'geometry:horizontal_tail:MAC:length',
        'geometry:horizontal_tail:sweep_25',
        'geometry:horizontal_tail:thickness_ratio',
        'geometry:horizontal_tail:wetted_area',
        'geometry:propulsion:nacelle:length',
        'geometry:propulsion:nacelle:wetted_area',
        'geometry:propulsion:pylon:length',
        'geometry:propulsion:pylon:wetted_area',
        'geometry:aircraft:wetted_area',
        'geometry:slat:chord_ratio',
        'geometry:slat:span_ratio',
        'geometry:vertical_tail:length',
        'geometry:vertical_tail:sweep_25',
        'geometry:vertical_tail:thickness_ratio',
        'geometry:vertical_tail:wetted_area',
        'geometry:wing:area',
        'geometry:wing:MAC:length',
        'geometry:wing:root:chord',
        'geometry:wing:tip:chord',
        'geometry:wing:span',
        'geometry:wing:sweep_0',
        'geometry:wing:sweep_100_outer',
        'geometry:wing:sweep_25',
        'geometry:wing:thickness_ratio',
        'geometry:wing:wetted_area',
        'aerodynamics:aircraft:cruise:CD:k',
        'aerodynamics:aircraft:cruise:CL:k',
        'aerodynamics:aircraft:landing:CL_max:landing_gear_effect:k',
        'aerodynamics:aircraft:cruise:CD:winglet_effect:k',
        'aerodynamics:aircraft:cruise:CL:winglet_effect:k',
        'aerodynamics:aircraft:cruise:CD:offset',
        'aerodynamics:aircraft:cruise:CL:offset',
        'aerodynamics:aircraft:cruise:CD:winglet_effect:offset',
        'aerodynamics:aircraft:cruise:CL:winglet_effect:offset',
        'mission:sizing:cruise:altitude',
        'mission:sizing:landing:flap_angle',
        'mission:sizing:landing:slat_angle',
        'TLAR:cruise_mach',
        'TLAR:approach_speed',
    ]

    ivc = get_indep_var_comp(input_list)
    problem = run_system(AerodynamicsHighSpeed(), ivc)

    cd = problem['aerodynamics:ClCd'][0, :]
    cl = problem['aerodynamics:ClCd'][1, :]

    assert cd[cl == 0.] == approx(0.02030, abs=1e-5)
    assert cd[cl == 0.2] == approx(0.02209, abs=1e-5)
    assert cd[cl == 0.42] == approx(0.02897, abs=1e-5)
    assert cd[cl == 0.85] == approx(0.11781, abs=1e-5)

    assert problem['aerodynamics:Cl_opt'] == approx(0.54, abs=1e-3)
    assert problem['aerodynamics:Cd_opt'] == approx(0.03550, abs=1e-5)


def test_aerodynamics_low_speed():
    """ Tests AerodynamicsLowSpeed """
    input_list = [
        'geometry:propulsion:engine:count',
        'geometry:propulsion:fan:length',
        'geometry:flap:chord_ratio',
        'geometry:flap:span_ratio',
        'geometry:fuselage:maximum_height',
        'geometry:fuselage:length',
        'geometry:fuselage:wetted_area',
        'geometry:fuselage:maximum_width',
        'geometry:horizontal_tail:MAC:length',
        'geometry:horizontal_tail:sweep_25',
        'geometry:horizontal_tail:thickness_ratio',
        'geometry:horizontal_tail:wetted_area',
        'geometry:propulsion:nacelle:length',
        'geometry:propulsion:nacelle:wetted_area',
        'geometry:propulsion:pylon:length',
        'geometry:propulsion:pylon:wetted_area',
        'geometry:aircraft:wetted_area',
        'geometry:slat:chord_ratio',
        'geometry:slat:span_ratio',
        'geometry:vertical_tail:length',
        'geometry:vertical_tail:sweep_25',
        'geometry:vertical_tail:thickness_ratio',
        'geometry:vertical_tail:wetted_area',
        'geometry:wing:area',
        'geometry:wing:aspect_ratio',
        'geometry:wing:MAC:length',
        'geometry:wing:root:chord',
        'geometry:wing:tip:chord',
        'geometry:wing:span',
        'geometry:wing:sweep_0',
        'geometry:wing:sweep_100_outer',
        'geometry:wing:sweep_25',
        'geometry:wing:thickness_ratio',
        'geometry:wing:tip:thickness_ratio',
        'geometry:wing:wetted_area',
        'aerodynamics:aircraft:cruise:CD:k',
        'aerodynamics:aircraft:cruise:CL:k',
        'aerodynamics:aircraft:cruise:CD:winglet_effect:k',
        'aerodynamics:aircraft:cruise:CL:winglet_effect:k',
        'aerodynamics:aircraft:cruise:CD:offset',
        'aerodynamics:aircraft:cruise:CL:offset',
        'aerodynamics:aircraft:cruise:CD:winglet_effect:offset',
        'aerodynamics:aircraft:cruise:CL:winglet_effect:offset',
        'mission:sizing:landing:flap_angle',
        'mission:sizing:landing:slat_angle',
        'TLAR:approach_speed',
    ]

    ivc = get_indep_var_comp(input_list)
    problem = run_system(AerodynamicsLowSpeed(), ivc)

    cd = problem['aerodynamics:ClCd_low_speed'][0, :]
    cl = problem['aerodynamics:ClCd_low_speed'][1, :]

    assert cd[cl == 0.] == approx(0.02173, abs=1e-5)
    assert cd[cl == 0.2] == approx(0.02339, abs=1e-5)
    assert cd[cl == 0.42] == approx(0.02974, abs=1e-5)
    assert cd[cl == 0.85] == approx(0.06010, abs=1e-5)
