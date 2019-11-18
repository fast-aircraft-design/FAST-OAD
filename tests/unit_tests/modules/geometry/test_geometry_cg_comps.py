"""
Test module for geometry functions of cg components
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

# pylint: disable=redefined-outer-name  # needed for pytest fixtures
import os.path as pth

import pytest
from openmdao.core.problem import Problem

from fastoad.io.xml import XPathReader
from fastoad.io.xml.openmdao_legacy_io import OMLegacy1XmlIO
from fastoad.modules.geometry.cg_components \
    import ComputeAeroCenter
from fastoad.modules.geometry.cg_components \
    import ComputeCGLoadCase1
from fastoad.modules.geometry.cg_components \
    import ComputeCGLoadCase2
from fastoad.modules.geometry.cg_components \
    import ComputeCGLoadCase3
from fastoad.modules.geometry.cg_components \
    import ComputeCGLoadCase4
from fastoad.modules.geometry.cg_components \
    import ComputeCGratioAft
from fastoad.modules.geometry.cg_components \
    import ComputeControlSurfacesCG
from fastoad.modules.geometry.cg_components \
    import ComputeGlobalCG
from fastoad.modules.geometry.cg_components \
    import ComputeMaxCGratio
from fastoad.modules.geometry.cg_components \
    import ComputeOthersCG
from fastoad.modules.geometry.cg_components \
    import ComputeStaticMargin
from fastoad.modules.geometry.cg_components \
    import ComputeTanksCG
from fastoad.modules.geometry.cg_components \
    import ComputeWingCG


@pytest.fixture(scope="module")
def xpath_reader() -> XPathReader:
    """
    :return: access to the sample xml data
    """
    return XPathReader(
        pth.join(pth.dirname(__file__), "data", "geometry_inputs_full.xml"))

@pytest.fixture(scope="module")
def input_xml() -> OMLegacy1XmlIO:
    """
    :return: access to the sample xml data
    """
    # TODO: have more consistency in input data (no need for the whole geometry_inputs_full.xml)
    return OMLegacy1XmlIO(
        pth.join(pth.dirname(__file__), "data", "geometry_inputs_full.xml"))

def test_compute_aero_center(input_xml):
    """ Tests computation of aerodynamic center """

    input_list = [
        'geometry:wing_x0',
        'geometry:wing_l0',
        'geometry:wing_l1',
        'geometry:fuselage_width_max',
        'geometry:fuselage_length',
        'geometry:wing_position',
        'geometry:wing_area',
        'geometry:ht_area',
        'geometry:ht_lp',
        'aerodynamics:Cl_alpha',
        'aerodynamics:Cl_alpha_ht'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeAeroCenter(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    x_ac_ratio = problem['x_ac_ratio']
    assert x_ac_ratio == pytest.approx(0.422638, abs=1e-6)


def test_compute_cg_control_surfaces(input_xml):
    """ Tests computation of control surfaces center of gravity """

    input_list = [
        'geometry:wing_x0',
        'geometry:wing_l0',
        'geometry:wing_y0',
        'geometry:wing_l2',
        'geometry:wing_l3',
        'geometry:wing_y2',
        'geometry:wing_x3',
        'geometry:wing_y3',
        'geometry:wing_position'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeControlSurfacesCG(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    x_cg_a4 = problem['cg_airframe:A4']
    assert x_cg_a4 == pytest.approx(19.24, abs=1e-2)


def test_compute_cg_loadcase1(input_xml):
    """ Tests computation of center of gravity for load case 1 """

    input_list = [
        'geometry:wing_l0',
        'geometry:wing_position',
        'cg:cg_pax',
        'cg:cg_rear_fret',
        'cg:cg_front_fret',
        'tlar:NPAX',
    ]

    input_vars = input_xml.read(only=input_list)

    input_vars.add_output('x_cg_plane_up', 699570.01)
    input_vars.add_output('x_cg_plane_down', 40979.11)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeCGLoadCase1(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    cg_ratio_lc1 = problem['cg_ratio_lc1']
    assert cg_ratio_lc1 == pytest.approx(0.364924, abs=1e-6)


def test_compute_cg_loadcase2(input_xml):
    """ Tests computation of center of gravity for load case 2 """

    input_list = [
        'geometry:wing_l0',
        'geometry:wing_position',
        'cg:cg_pax',
        'cg:cg_rear_fret',
        'cg:cg_front_fret',
        'tlar:NPAX',
        'weight:MFW',
        'cg:cg_tank',
    ]

    input_vars = input_xml.read(only=input_list)

    input_vars.add_output('x_cg_plane_up', 699570.01)
    input_vars.add_output('x_cg_plane_down', 40979.11)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeCGLoadCase2(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    cg_ratio_lc2 = problem['cg_ratio_lc2']
    assert cg_ratio_lc2 == pytest.approx(0.285139, abs=1e-6)


def test_compute_cg_loadcase3(input_xml):
    """ Tests computation of center of gravity for load case 3 """

    input_list = [
        'geometry:wing_l0',
        'geometry:wing_position',
        'cg:cg_pax',
        'cg:cg_rear_fret',
        'cg:cg_front_fret',
        'tlar:NPAX'
    ]

    input_vars = input_xml.read(only=input_list)

    input_vars.add_output('x_cg_plane_up', 699570.01)
    input_vars.add_output('x_cg_plane_down', 40979.11)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeCGLoadCase3(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    cg_ratio_lc3 = problem['cg_ratio_lc3']
    assert cg_ratio_lc3 == pytest.approx(0.386260, abs=1e-6)


def test_compute_cg_loadcase4(input_xml):
    """ Tests computation of center of gravity for load case 4 """

    input_list = [
        'geometry:wing_l0',
        'geometry:wing_position',
        'cg:cg_pax',
        'cg:cg_rear_fret',
        'cg:cg_front_fret',
        'tlar:NPAX'
    ]

    input_vars = input_xml.read(only=input_list)

    input_vars.add_output('x_cg_plane_up', 699570.01)
    input_vars.add_output('x_cg_plane_down', 40979.11)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeCGLoadCase4(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    cg_ratio_lc4 = problem['cg_ratio_lc4']
    assert cg_ratio_lc4 == pytest.approx(0.388971, abs=1e-6)

def test_compute_cg_others(input_xml):
    """ Tests computation of other components center of gravity """

    input_list = [
        'geometry:wing_x0',
        'geometry:wing_l0',
        'geometry:wing_l2',
        'geometry:fuselage_length',
        'geometry:wing_position',
        'geometry:fuselage_LAV',
        'geometry:fuselage_LAR',
        'cg_propulsion:B1',
        'cg_furniture:D2',
        'weight_propulsion:B1',
        'cabin:NPAX1',
        'cabin:front_seat_number_eco',
        'cabin:LSeco'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeOthersCG(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    x_cg_a2 = problem['cg_airframe:A2']
    assert x_cg_a2 == pytest.approx(16.88, abs=1e-2)
    x_cg_a52 = problem['cg_airframe:A52']
    assert x_cg_a52 == pytest.approx(5.18, abs=1e-2)
    x_cg_a6 = problem['cg_airframe:A6']
    assert x_cg_a6 == pytest.approx(13.5, abs=1e-1)
    x_cg_a7 = problem['cg_airframe:A7']
    assert x_cg_a7 == pytest.approx(0.0, abs=1e-1)

    x_cg_b2 = problem['cg_propulsion:B2']
    assert x_cg_b2 == pytest.approx(13.5, abs=1e-1)
    x_cg_b3 = problem['cg_propulsion:B3']
    assert x_cg_b3 == pytest.approx(13.5, abs=1e-1)

    x_cg_c11 = problem['cg_systems:C11']
    assert x_cg_c11 == pytest.approx(35.63, abs=1e-2)
    x_cg_c12 = problem['cg_systems:C12']
    assert x_cg_c12 == pytest.approx(18.75, abs=1e-2)
    x_cg_c13 = problem['cg_systems:C13']
    assert x_cg_c13 == pytest.approx(18.75, abs=1e-2)
    x_cg_c21 = problem['cg_systems:C21']
    assert x_cg_c21 == pytest.approx(16.88, abs=1e-2)
    x_cg_c22 = problem['cg_systems:C22']
    assert x_cg_c22 == pytest.approx(16.62, abs=1e-2)
    x_cg_c23 = problem['cg_systems:C23']
    assert x_cg_c23 == pytest.approx(15.79, abs=1e-2)
    x_cg_c24 = problem['cg_systems:C24']
    assert x_cg_c24 == pytest.approx(16.88, abs=1e-2)
    x_cg_c25 = problem['cg_systems:C25']
    assert x_cg_c25 == pytest.approx(16.62, abs=1e-2)
    x_cg_c26 = problem['cg_systems:C26']
    assert x_cg_c26 == pytest.approx(16.62, abs=1e-2)
    x_cg_c27 = problem['cg_systems:C27']
    assert x_cg_c27 == pytest.approx(16.1, abs=1e-1)
    x_cg_c3 = problem['cg_systems:C3']
    assert x_cg_c3 == pytest.approx(5.52, abs=1e-2)
    x_cg_c4 = problem['cg_systems:C4']
    assert x_cg_c4 == pytest.approx(18.75, abs=1e-2)
    x_cg_c51 = problem['cg_systems:C51']
    assert x_cg_c51 == pytest.approx(0.75, abs=1e-2)
    x_cg_c52 = problem['cg_systems:C52']
    assert x_cg_c52 == pytest.approx(16.62, abs=1e-2)

    x_cg_d1 = problem['cg_furniture:D1']
    assert x_cg_d1 == pytest.approx(0.0, abs=1e-1)
    x_cg_d3 = problem['cg_furniture:D3']
    assert x_cg_d3 == pytest.approx(29.4, abs=1e-1)
    x_cg_d4 = problem['cg_furniture:D4']
    assert x_cg_d4 == pytest.approx(16.62, abs=1e-2)
    x_cg_d5 = problem['cg_furniture:D5']
    assert x_cg_d5 == pytest.approx(16.62, abs=1e-2)
    x_cg_pl = problem['cg:cg_pax']
    assert x_cg_pl == pytest.approx(16.62, abs=1e-2)
    x_cg_rear_fret = problem['cg:cg_rear_fret']
    assert x_cg_rear_fret == pytest.approx(20.87, abs=1e-2)
    x_cg_front_fret = problem['cg:cg_front_fret']
    assert x_cg_front_fret == pytest.approx(9.94, abs=1e-2)

def test_compute_cg_ratio_aft(input_xml):
    """ Tests computation of center of gravity with aft estimation """

    input_list = [
        'cg_airframe:A1',
        'cg_airframe:A2',
        'cg_airframe:A31',
        'cg_airframe:A32',
        'cg_airframe:A4',
        'cg_airframe:A51',
        'cg_airframe:A52',
        'cg_airframe:A6',
        'cg_airframe:A7',
        'weight_airframe:A1',
        'weight_airframe:A2',
        'weight_airframe:A31',
        'weight_airframe:A32',
        'weight_airframe:A4',
        'weight_airframe:A51',
        'weight_airframe:A52',
        'weight_airframe:A6',
        'weight_airframe:A7',
        'cg_propulsion:B1',
        'cg_propulsion:B2',
        'cg_propulsion:B3',
        'weight_propulsion:B1',
        'weight_propulsion:B2',
        'weight_propulsion:B3',
        'cg_systems:C11',
        'cg_systems:C12',
        'cg_systems:C13',
        'cg_systems:C21',
        'cg_systems:C22',
        'cg_systems:C23',
        'cg_systems:C24',
        'cg_systems:C25',
        'cg_systems:C26',
        'cg_systems:C27',
        'cg_systems:C3',
        'cg_systems:C4',
        'cg_systems:C51',
        'cg_systems:C52',
        'cg_systems:C6',
        'weight_systems:C11',
        'weight_systems:C12',
        'weight_systems:C13',
        'weight_systems:C21',
        'weight_systems:C22',
        'weight_systems:C23',
        'weight_systems:C24',
        'weight_systems:C25',
        'weight_systems:C26',
        'weight_systems:C27',
        'weight_systems:C3',
        'weight_systems:C4',
        'weight_systems:C51',
        'weight_systems:C52',
        'weight_systems:C6',
        'cg_furniture:D1',
        'cg_furniture:D2',
        'cg_furniture:D3',
        'cg_furniture:D4',
        'cg_furniture:D5',
        'weight_furniture:D1',
        'weight_furniture:D2',
        'weight_furniture:D3',
        'weight_furniture:D4',
        'weight_furniture:D5',
        'geometry:wing_l0',
        'geometry:wing_position'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeCGratioAft(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    x_cg_plane_up = problem['x_cg_plane_up']
    assert x_cg_plane_up == pytest.approx(699570.03, abs=1e-2)
    x_cg_plane_down = problem['x_cg_plane_down']
    assert x_cg_plane_down == pytest.approx(40979.11, abs=1e-2)
    cg_ratio_aft = problem['cg_ratio_aft']
    assert cg_ratio_aft == pytest.approx(0.387846, abs=1e-6)


def test_compute_cg_tanks(input_xml):
    """ Tests computation of tanks center of gravity """

    input_list = [
        'geometry:wing_front_spar_ratio_root',
        'geometry:wing_front_spar_ratio_kink',
        'geometry:wing_front_spar_ratio_tip',
        'geometry:wing_rear_spar_ratio_root',
        'geometry:wing_rear_spar_ratio_kink',
        'geometry:wing_rear_spar_ratio_tip',
        'geometry:wing_l0',
        'geometry:wing_x0',
        'geometry:wing_l2',
        'geometry:wing_l3',
        'geometry:wing_l4',
        'geometry:wing_y2',
        'geometry:wing_x3',
        'geometry:wing_y3',
        'geometry:wing_y4',
        'geometry:wing_x4',
        'geometry:wing_position',
        'geometry:fuselage_width_max'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeTanksCG(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    x_cg_tank = problem['cg:cg_tank']
    assert x_cg_tank == pytest.approx(16.05, abs=1e-2)


def test_compute_cg_wing(input_xml):
    """ Tests computation of wing center of gravity """

    input_list = [
        'geometry:wing_break',
        'geometry:wing_front_spar_ratio_root',
        'geometry:wing_front_spar_ratio_kink',
        'geometry:wing_front_spar_ratio_tip',
        'geometry:wing_rear_spar_ratio_root',
        'geometry:wing_rear_spar_ratio_kink',
        'geometry:wing_rear_spar_ratio_tip',
        'geometry:wing_span',
        'geometry:wing_l0',
        'geometry:wing_x0',
        'geometry:wing_l2',
        'geometry:wing_l3',
        'geometry:wing_l4',
        'geometry:wing_y2',
        'geometry:wing_x3',
        'geometry:wing_y3',
        'geometry:wing_y4',
        'geometry:wing_x4',
        'geometry:wing_position'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeWingCG(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    x_cg_wing = problem['cg_airframe:A1']
    assert x_cg_wing == pytest.approx(16.67, abs=1e-2)


def test_compute_global_cg(input_xml):
    """ Tests computation of global center of gravity """

    input_list = [
        'geometry:wing_l0',
        'geometry:wing_position',
        'cg:cg_pax',
        'cg:cg_rear_fret',
        'cg:cg_front_fret',
        'tlar:NPAX',
        'weight:MFW',
        'cg:cg_tank',
        'cg_airframe:A1',
        'cg_airframe:A2',
        'cg_airframe:A31',
        'cg_airframe:A32',
        'cg_airframe:A4',
        'cg_airframe:A51',
        'cg_airframe:A52',
        'cg_airframe:A6',
        'cg_airframe:A7',
        'weight_airframe:A1',
        'weight_airframe:A2',
        'weight_airframe:A31',
        'weight_airframe:A32',
        'weight_airframe:A4',
        'weight_airframe:A51',
        'weight_airframe:A52',
        'weight_airframe:A6',
        'weight_airframe:A7',
        'cg_propulsion:B1',
        'cg_propulsion:B2',
        'cg_propulsion:B3',
        'weight_propulsion:B1',
        'weight_propulsion:B2',
        'weight_propulsion:B3',
        'cg_systems:C11',
        'cg_systems:C12',
        'cg_systems:C13',
        'cg_systems:C21',
        'cg_systems:C22',
        'cg_systems:C23',
        'cg_systems:C24',
        'cg_systems:C25',
        'cg_systems:C26',
        'cg_systems:C27',
        'cg_systems:C3',
        'cg_systems:C4',
        'cg_systems:C51',
        'cg_systems:C52',
        'cg_systems:C6',
        'weight_systems:C11',
        'weight_systems:C12',
        'weight_systems:C13',
        'weight_systems:C21',
        'weight_systems:C22',
        'weight_systems:C23',
        'weight_systems:C24',
        'weight_systems:C25',
        'weight_systems:C26',
        'weight_systems:C27',
        'weight_systems:C3',
        'weight_systems:C4',
        'weight_systems:C51',
        'weight_systems:C52',
        'weight_systems:C6',
        'cg_furniture:D1',
        'cg_furniture:D2',
        'cg_furniture:D3',
        'cg_furniture:D4',
        'cg_furniture:D5',
        'weight_furniture:D1',
        'weight_furniture:D2',
        'weight_furniture:D3',
        'weight_furniture:D4',
        'weight_furniture:D5'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeGlobalCG(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    cg_ratio = problem['cg_ratio']
    assert cg_ratio == pytest.approx(0.388971, abs=1e-6)


def test_compute_max_cg_ratio(input_xml):
    """ Tests computation of maximum center of gravity ratio """

    input_list = []

    input_vars = input_xml.read(only=input_list)

    input_vars.add_output('cg_ratio_aft', 0.387846)
    input_vars.add_output('cg_ratio_lc1', 0.364924)
    input_vars.add_output('cg_ratio_lc2', 0.285139)
    input_vars.add_output('cg_ratio_lc3', 0.386260)
    input_vars.add_output('cg_ratio_lc4', 0.388971)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeMaxCGratio(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    cg_ratio = problem['cg_ratio']
    assert cg_ratio == pytest.approx(0.388971, abs=1e-6)


def test_compute_static_margin(input_xml):
    """ Tests computation of static margin """

    input_list = [
        'geometry:wing_l0',
        'geometry:wing_position'
    ]

    input_vars = input_xml.read(only=input_list)

    input_vars.add_output('cg_ratio', 0.388971)
    input_vars.add_output('x_ac_ratio', 0.537521)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeStaticMargin(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    static_margin = problem['static_margin']
    assert static_margin == pytest.approx(0.098550, abs=1e-6)
    cg_global = problem['cg:CG']
    assert cg_global == pytest.approx(17.3, abs=1e-1)
