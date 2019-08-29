"""
Test module for aerodynamics groups
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2019  ONERA/ISAE
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

from openmdao.core.group import Group
from pytest import approx

from fastoad.io.xml import OpenMdaoXmlIO
from fastoad.modules.aerodynamics.aerodynamics_2d import Aerodynamics2d
from fastoad.modules.aerodynamics.aerodynamics_high_speed import AerodynamicsHighSpeed
from fastoad.modules.aerodynamics.aerodynamics_low_speed import AerodynamicsLowSpeed
from fastoad.modules.aerodynamics.components.high_lift_aero import ComputeDeltaHighLift
from tests.testing_utilities import run_system


def get_indep_var_comp(var_names):
    """ Reads required input data and returns an IndepVarcomp() instance"""
    reader = OpenMdaoXmlIO(
        pth.join(pth.dirname(__file__), "data", "aerodynamics_inputs.xml"))
    reader.path_separator = ':'
    ivc = reader.read(only=var_names)
    return ivc


def test_aerodynamics_high_speed():
    """ Tests AerodynamicsHighSpeed """
    input_list = [
        'geometry:engine_number',
        'geometry:fan_length',
        'geometry:flap_chord_ratio',
        'geometry:flap_span_ratio',
        'geometry:fuselage_height_max',
        'geometry:fuselage_length',
        'geometry:fuselage_wet_area',
        'geometry:fuselage_width_max',
        'geometry:ht_length',
        'geometry:ht_sweep_25',
        'geometry:ht_toc',
        'geometry:ht_wet_area',
        'geometry:nacelle_length',
        'geometry:nacelle_wet_area',
        'geometry:pylon_length',
        'geometry:pylon_wet_area',
        'geometry:S_total',
        'geometry:slat_chord_ratio',
        'geometry:slat_span_ratio',
        'geometry:vt_length',
        'geometry:vt_sweep_25',
        'geometry:vt_toc',
        'geometry:vt_wet_area',
        'geometry:wing_area',
        'geometry:wing_l0',
        'geometry:wing_l2',
        'geometry:wing_l4',
        'geometry:wing_span',
        'geometry:wing_sweep_0',
        'geometry:wing_sweep_100_outer',
        'geometry:wing_sweep_25',
        'geometry:wing_toc_aero',
        'geometry:wing_wet_area',
        'kfactors_aero:K_Cd',
        'kfactors_aero:K_Cl',
        'kfactors_aero:K_HL_LDG',
        'kfactors_aero:K_winglet_Cd',
        'kfactors_aero:K_winglet_Cl',
        'kfactors_aero:Offset_Cd',
        'kfactors_aero:Offset_Cl',
        'kfactors_aero:Offset_winglet_Cd',
        'kfactors_aero:Offset_winglet_Cl',
        'sizing_mission:cruise_altitude',
        'sizing_mission:flap_angle_landing',
        'sizing_mission:slat_angle_landing',
        'tlar:cruise_Mach',
        'tlar:v_approach',
    ]

    ivc = get_indep_var_comp(input_list)
    system = Group()
    system.add_subsystem('aero_2d', Aerodynamics2d(), promotes=['*'])
    system.add_subsystem('delta_cl_landing', ComputeDeltaHighLift(landing_flag=True),
                         promotes=['*'])
    system.add_subsystem('aero_high_speed', AerodynamicsHighSpeed(), promotes=['*'])

    problem = run_system(system, ivc)

    cd = problem['aerodynamics:ClCd'][0, :]
    cl = problem['aerodynamics:ClCd'][1, :]

    assert cd[cl == 0.] == approx(0.02030, abs=1e-5)
    assert cd[cl == 0.2] == approx(0.02209, abs=1e-5)
    assert cd[cl == 0.42] == approx(0.02897, abs=1e-5)
    assert cd[cl == 0.85] == approx(0.11782, abs=1e-5)

    assert problem['aerodynamics:Cl_opt'] == approx(0.54, abs=1e-3)
    assert problem['aerodynamics:Cd_opt'] == approx(0.03550, abs=1e-5)


def test_aerodynamics_low_speed():
    input_list = [
        'geometry:engine_number',
        'geometry:fan_length',
        'geometry:flap_chord_ratio',
        'geometry:flap_span_ratio',
        'geometry:fuselage_height_max',
        'geometry:fuselage_length',
        'geometry:fuselage_wet_area',
        'geometry:fuselage_width_max',
        'geometry:ht_length',
        'geometry:ht_sweep_25',
        'geometry:ht_toc',
        'geometry:ht_wet_area',
        'geometry:nacelle_length',
        'geometry:nacelle_wet_area',
        'geometry:pylon_length',
        'geometry:pylon_wet_area',
        'geometry:S_total',
        'geometry:slat_chord_ratio',
        'geometry:slat_span_ratio',
        'geometry:vt_length',
        'geometry:vt_sweep_25',
        'geometry:vt_toc',
        'geometry:vt_wet_area',
        'geometry:wing_area',
        'geometry:wing_aspect_ratio',
        'geometry:wing_l0',
        'geometry:wing_l2',
        'geometry:wing_l4',
        'geometry:wing_span',
        'geometry:wing_sweep_0',
        'geometry:wing_sweep_100_outer',
        'geometry:wing_sweep_25',
        'geometry:wing_toc_aero',
        'geometry:wing_toc_tip',
        'geometry:wing_wet_area',
        'kfactors_aero:K_Cd',
        'kfactors_aero:K_Cl',
        'kfactors_aero:K_winglet_Cd',
        'kfactors_aero:K_winglet_Cl',
        'kfactors_aero:Offset_Cd',
        'kfactors_aero:Offset_Cl',
        'kfactors_aero:Offset_winglet_Cd',
        'kfactors_aero:Offset_winglet_Cl',
        'sizing_mission:flap_angle_landing',
        'sizing_mission:slat_angle_landing',
        'tlar:v_approach',
    ]

    ivc = get_indep_var_comp(input_list)
    system = Group()
    system.add_subsystem('aero_2d', Aerodynamics2d(), promotes=['*'])
    system.add_subsystem('delta_cl_landing', ComputeDeltaHighLift(landing_flag=True),
                         promotes=['*'])
    system.add_subsystem('aero_high_speed', AerodynamicsLowSpeed(), promotes=['*'])

    problem = run_system(system, ivc)

    cd = problem['aerodynamics:ClCd_low_speed'][0, :]
    cl = problem['aerodynamics:ClCd_low_speed'][1, :]

    assert cd[cl == 0.] == approx(0.02173, abs=1e-5)
    assert cd[cl == 0.2] == approx(0.02339, abs=1e-5)
    assert cd[cl == 0.42] == approx(0.02974, abs=1e-5)
    assert cd[cl == 0.85] == approx(0.06010, abs=1e-5)
