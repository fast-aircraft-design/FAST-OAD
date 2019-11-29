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
    import ComputeCGRatioAft
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
        'geometry:wing:root:leading_edge:x',
        'geometry:wing:MAC:length',
        'geometry:wing:l1',
        'geometry:fuselage:maximum_width',
        'geometry:fuselage:length',
        'geometry:wing:location',
        'geometry:wing:area',
        'geometry:horizontal_tail:area',
        'geometry:horizontal_tail:distance_from_wing',
        'aerodynamics:aircraft:cruise:CL_alpha',
        'aerodynamics:horizontal_tail:cruise:CL_alpha'
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
        'geometry:wing:root:leading_edge:x',
        'geometry:wing:MAC:length',
        'geometry:wing:MAC:y',
        'geometry:wing:root:chord',
        'geometry:wing:kink:chord',
        'geometry:wing:root:y',
        'geometry:wing:kink:leading_edge:x',
        'geometry:wing:kink:y',
        'geometry:wing:location'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeControlSurfacesCG(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    x_cg_a4 = problem['weight:airframe:flight_controls:CG:x']
    assert x_cg_a4 == pytest.approx(19.24, abs=1e-2)


def test_compute_cg_loadcase1(input_xml):
    """ Tests computation of center of gravity for load case 1 """

    input_list = [
        'geometry:wing:MAC:length',
        'geometry:wing:location',
        'weight:payload:PAX:CG:x',
        'weight:payload:rear_fret:CG:x',
        'weight:payload:front_fret:CG:x',
        'TLAR:NPAX',
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
        'geometry:wing:MAC:length',
        'geometry:wing:location',
        'weight:payload:PAX:CG:x',
        'weight:payload:rear_fret:CG:x',
        'weight:payload:front_fret:CG:x',
        'TLAR:NPAX',
        'weight:aircraft:MFW',
        'weight:fuel_tank:CG:x',
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
        'geometry:wing:MAC:length',
        'geometry:wing:location',
        'weight:payload:PAX:CG:x',
        'weight:payload:rear_fret:CG:x',
        'weight:payload:front_fret:CG:x',
        'TLAR:NPAX'
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
        'geometry:wing:MAC:length',
        'geometry:wing:location',
        'weight:payload:PAX:CG:x',
        'weight:payload:rear_fret:CG:x',
        'weight:payload:front_fret:CG:x',
        'TLAR:NPAX'
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
        'geometry:wing:root:leading_edge:x',
        'geometry:wing:MAC:length',
        'geometry:wing:root:chord',
        'geometry:fuselage:length',
        'geometry:wing:location',
        'geometry:fuselage:rear_length',
        'geometry:fuselage:front_length',
        'weight:propulsion:engine:CG:x',
        'weight:furniture:passenger_seats:CG:x',
        'weight:propulsion:engine:mass',
        'geometry:cabin:NPAX1',
        'geometry:cabin:seats:economical:count_by_row',
        'geometry:cabin:seats:economical:length'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeOthersCG(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    x_cg_a2 = problem['weight:airframe:fuselage:CG:x']
    assert x_cg_a2 == pytest.approx(16.88, abs=1e-2)
    x_cg_a52 = problem['weight:airframe:landing_gear:front:CG:x']
    assert x_cg_a52 == pytest.approx(5.18, abs=1e-2)
    x_cg_a6 = problem['weight:airframe:pylon:CG:x']
    assert x_cg_a6 == pytest.approx(13.5, abs=1e-1)
    x_cg_a7 = problem['weight:airframe:paint:CG:x']
    assert x_cg_a7 == pytest.approx(0.0, abs=1e-1)

    x_cg_b2 = problem['weight:propulsion:fuel_lines:CG:x']
    assert x_cg_b2 == pytest.approx(13.5, abs=1e-1)
    x_cg_b3 = problem['weight:propulsion:unconsumables:CG:x']
    assert x_cg_b3 == pytest.approx(13.5, abs=1e-1)

    x_cg_c11 = problem['weight:systems:power:auxiliary_power_unit:CG:x']
    assert x_cg_c11 == pytest.approx(35.63, abs=1e-2)
    x_cg_c12 = problem['weight:systems:power:electric_systems:CG:x']
    assert x_cg_c12 == pytest.approx(18.75, abs=1e-2)
    x_cg_c13 = problem['weight:systems:power:hydraulic_systems:CG:x']
    assert x_cg_c13 == pytest.approx(18.75, abs=1e-2)
    x_cg_c21 = problem['weight:systems:life_support:insulation:CG:x']
    assert x_cg_c21 == pytest.approx(16.88, abs=1e-2)
    x_cg_c22 = problem['weight:systems:life_support:air_conditioning:CG:x']
    assert x_cg_c22 == pytest.approx(16.62, abs=1e-2)
    x_cg_c23 = problem['weight:systems:life_support:de-icing:CG:x']
    assert x_cg_c23 == pytest.approx(15.79, abs=1e-2)
    x_cg_c24 = problem['weight:systems:life_support:cabin_lighting:CG:x']
    assert x_cg_c24 == pytest.approx(16.88, abs=1e-2)
    x_cg_c25 = problem['weight:systems:life_support:seats_crew_accomodation:CG:x']
    assert x_cg_c25 == pytest.approx(16.62, abs=1e-2)
    x_cg_c26 = problem['weight:systems:life_support:oxygen:CG:x']
    assert x_cg_c26 == pytest.approx(16.62, abs=1e-2)
    x_cg_c27 = problem['weight:systems:life_support:safety_equipment:CG:x']
    assert x_cg_c27 == pytest.approx(16.1, abs=1e-1)
    x_cg_c3 = problem['weight:systems:navigation:CG:x']
    assert x_cg_c3 == pytest.approx(5.52, abs=1e-2)
    x_cg_c4 = problem['weight:systems:transmission:CG:x']
    assert x_cg_c4 == pytest.approx(18.75, abs=1e-2)
    x_cg_c51 = problem['weight:systems:operational:radar:CG:x']
    assert x_cg_c51 == pytest.approx(0.75, abs=1e-2)
    x_cg_c52 = problem['weight:systems:operational:cargo_hold:CG:x']
    assert x_cg_c52 == pytest.approx(16.62, abs=1e-2)

    x_cg_d1 = problem['weight:furniture:cargo_configuration:CG:x']
    assert x_cg_d1 == pytest.approx(0.0, abs=1e-1)
    x_cg_d3 = problem['weight:furniture:food_water:CG:x']
    assert x_cg_d3 == pytest.approx(29.4, abs=1e-1)
    x_cg_d4 = problem['weight:furniture:security_kit:CG:x']
    assert x_cg_d4 == pytest.approx(16.62, abs=1e-2)
    x_cg_d5 = problem['weight:furniture:toilets:CG:x']
    assert x_cg_d5 == pytest.approx(16.62, abs=1e-2)
    x_cg_pl = problem['weight:payload:PAX:CG:x']
    assert x_cg_pl == pytest.approx(16.62, abs=1e-2)
    x_cg_rear_fret = problem['weight:payload:rear_fret:CG:x']
    assert x_cg_rear_fret == pytest.approx(20.87, abs=1e-2)
    x_cg_front_fret = problem['weight:payload:front_fret:CG:x']
    assert x_cg_front_fret == pytest.approx(9.94, abs=1e-2)

def test_compute_cg_ratio_aft(input_xml):
    """ Tests computation of center of gravity with aft estimation """

    input_list = [
        'weight:airframe:wing:CG:x',
        'weight:airframe:fuselage:CG:x',
        'weight:airframe:tail_plane:horizontal:CG:x',
        'weight:airframe:tail_plane:vertical:CG:x',
        'weight:airframe:flight_controls:CG:x',
        'weight:airframe:landing_gear:main:CG:x',
        'weight:airframe:landing_gear:front:CG:x',
        'weight:airframe:pylon:CG:x',
        'weight:airframe:paint:CG:x',
        'weight:airframe:wing:mass',
        'weight:airframe:fuselage:mass',
        'weight:airframe:tail_plane:horizontal:mass',
        'weight:airframe:tail_plane:vertical:mass',
        'weight:airframe:flight_controls:mass',
        'weight:airframe:landing_gear:main:mass',
        'weight:airframe:landing_gear:front:mass',
        'weight:airframe:pylon:mass',
        'weight:airframe:paint:mass',
        'weight:propulsion:engine:CG:x',
        'weight:propulsion:fuel_lines:CG:x',
        'weight:propulsion:unconsumables:CG:x',
        'weight:propulsion:engine:mass',
        'weight:propulsion:fuel_lines:mass',
        'weight:propulsion:unconsumables:mass',
        'weight:systems:power:auxiliary_power_unit:CG:x',
        'weight:systems:power:electric_systems:CG:x',
        'weight:systems:power:hydraulic_systems:CG:x',
        'weight:systems:life_support:insulation:CG:x',
        'weight:systems:life_support:air_conditioning:CG:x',
        'weight:systems:life_support:de-icing:CG:x',
        'weight:systems:life_support:cabin_lighting:CG:x',
        'weight:systems:life_support:seats_crew_accomodation:CG:x',
        'weight:systems:life_support:oxygen:CG:x',
        'weight:systems:life_support:safety_equipment:CG:x',
        'weight:systems:navigation:CG:x',
        'weight:systems:transmission:CG:x',
        'weight:systems:operational:radar:CG:x',
        'weight:systems:operational:cargo_hold:CG:x',
        'weight:systems:flight_kit:CG:x',
        'weight:systems:power:auxiliary_power_unit:mass',
        'weight:systems:power:electric_systems:mass',
        'weight:systems:power:hydraulic_systems:mass',
        'weight:systems:life_support:insulation:mass',
        'weight:systems:life_support:air_conditioning:mass',
        'weight:systems:life_support:de-icing:mass',
        'weight:systems:life_support:cabin_lighting:mass',
        'weight:systems:life_support:seats_crew_accomodation:mass',
        'weight:systems:life_support:oxygen:mass',
        'weight:systems:life_support:safety_equipment:mass',
        'weight:systems:navigation:mass',
        'weight:systems:transmission:mass',
        'weight:systems:operational:radar:mass',
        'weight:systems:operational:cargo_hold:mass',
        'weight:systems:flight_kit:mass',
        'weight:furniture:cargo_configuration:CG:x',
        'weight:furniture:passenger_seats:CG:x',
        'weight:furniture:food_water:CG:x',
        'weight:furniture:security_kit:CG:x',
        'weight:furniture:toilets:CG:x',
        'weight:furniture:cargo_configuration:mass',
        'weight:furniture:passenger_seats:mass',
        'weight:furniture:food_water:mass',
        'weight:furniture:security_kit:mass',
        'weight:furniture:toilets:mass',
        'geometry:wing:MAC:length',
        'geometry:wing:location'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeCGRatioAft(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    x_cg_plane_up = problem['x_cg_plane_up']
    assert x_cg_plane_up == pytest.approx(699570.03, abs=1e-2)
    x_cg_plane_down = problem['x_cg_plane_down']
    assert x_cg_plane_down == pytest.approx(41162.00, abs=1e-2)
    cg_ratio_aft = problem['cg_ratio_aft']
    assert cg_ratio_aft == pytest.approx(0.370828, abs=1e-6)


def test_compute_cg_tanks(input_xml):
    """ Tests computation of tanks center of gravity """

    input_list = [
        'geometry:wing:spar_ratio:front:root',
        'geometry:wing:spar_ratio:front:kink',
        'geometry:wing:spar_ratio:front:tip',
        'geometry:wing:spar_ratio:rear:root',
        'geometry:wing:spar_ratio:rear:kink',
        'geometry:wing:spar_ratio:rear:tip',
        'geometry:wing:MAC:length',
        'geometry:wing:root:leading_edge:x',
        'geometry:wing:root:chord',
        'geometry:wing:kink:chord',
        'geometry:wing:tip:chord',
        'geometry:wing:root:y',
        'geometry:wing:kink:leading_edge:x',
        'geometry:wing:kink:y',
        'geometry:wing:tip:y',
        'geometry:wing:tip:leading_edge:x',
        'geometry:wing:location',
        'geometry:fuselage:maximum_width'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeTanksCG(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    x_cg_tank = problem['weight:fuel_tank:CG:x']
    assert x_cg_tank == pytest.approx(16.05, abs=1e-2)


def test_compute_cg_wing(input_xml):
    """ Tests computation of wing center of gravity """

    input_list = [
        'geometry:wing:break',
        'geometry:wing:spar_ratio:front:root',
        'geometry:wing:spar_ratio:front:kink',
        'geometry:wing:spar_ratio:front:tip',
        'geometry:wing:spar_ratio:rear:root',
        'geometry:wing:spar_ratio:rear:kink',
        'geometry:wing:spar_ratio:rear:tip',
        'geometry:wing:span',
        'geometry:wing:MAC:length',
        'geometry:wing:root:leading_edge:x',
        'geometry:wing:root:chord',
        'geometry:wing:kink:chord',
        'geometry:wing:tip:chord',
        'geometry:wing:root:y',
        'geometry:wing:kink:leading_edge:x',
        'geometry:wing:kink:y',
        'geometry:wing:tip:y',
        'geometry:wing:tip:leading_edge:x',
        'geometry:wing:location'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeWingCG(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    x_cg_wing = problem['weight:airframe:wing:CG:x']
    assert x_cg_wing == pytest.approx(16.67, abs=1e-2)


def test_compute_global_cg(input_xml):
    """ Tests computation of global center of gravity """

    input_list = [
        'geometry:wing:MAC:length',
        'geometry:wing:location',
        'weight:payload:PAX:CG:x',
        'weight:payload:rear_fret:CG:x',
        'weight:payload:front_fret:CG:x',
        'TLAR:NPAX',
        'weight:aircraft:MFW',
        'weight:fuel_tank:CG:x',
        'weight:airframe:wing:CG:x',
        'weight:airframe:fuselage:CG:x',
        'weight:airframe:tail_plane:horizontal:CG:x',
        'weight:airframe:tail_plane:vertical:CG:x',
        'weight:airframe:flight_controls:CG:x',
        'weight:airframe:landing_gear:main:CG:x',
        'weight:airframe:landing_gear:front:CG:x',
        'weight:airframe:pylon:CG:x',
        'weight:airframe:paint:CG:x',
        'weight:airframe:wing:mass',
        'weight:airframe:fuselage:mass',
        'weight:airframe:tail_plane:horizontal:mass',
        'weight:airframe:tail_plane:vertical:mass',
        'weight:airframe:flight_controls:mass',
        'weight:airframe:landing_gear:main:mass',
        'weight:airframe:landing_gear:front:mass',
        'weight:airframe:pylon:mass',
        'weight:airframe:paint:mass',
        'weight:propulsion:engine:CG:x',
        'weight:propulsion:fuel_lines:CG:x',
        'weight:propulsion:unconsumables:CG:x',
        'weight:propulsion:engine:mass',
        'weight:propulsion:fuel_lines:mass',
        'weight:propulsion:unconsumables:mass',
        'weight:systems:power:auxiliary_power_unit:CG:x',
        'weight:systems:power:electric_systems:CG:x',
        'weight:systems:power:hydraulic_systems:CG:x',
        'weight:systems:life_support:insulation:CG:x',
        'weight:systems:life_support:air_conditioning:CG:x',
        'weight:systems:life_support:de-icing:CG:x',
        'weight:systems:life_support:cabin_lighting:CG:x',
        'weight:systems:life_support:seats_crew_accomodation:CG:x',
        'weight:systems:life_support:oxygen:CG:x',
        'weight:systems:life_support:safety_equipment:CG:x',
        'weight:systems:navigation:CG:x',
        'weight:systems:transmission:CG:x',
        'weight:systems:operational:radar:CG:x',
        'weight:systems:operational:cargo_hold:CG:x',
        'weight:systems:flight_kit:CG:x',
        'weight:systems:power:auxiliary_power_unit:mass',
        'weight:systems:power:electric_systems:mass',
        'weight:systems:power:hydraulic_systems:mass',
        'weight:systems:life_support:insulation:mass',
        'weight:systems:life_support:air_conditioning:mass',
        'weight:systems:life_support:de-icing:mass',
        'weight:systems:life_support:cabin_lighting:mass',
        'weight:systems:life_support:seats_crew_accomodation:mass',
        'weight:systems:life_support:oxygen:mass',
        'weight:systems:life_support:safety_equipment:mass',
        'weight:systems:navigation:mass',
        'weight:systems:transmission:mass',
        'weight:systems:operational:radar:mass',
        'weight:systems:operational:cargo_hold:mass',
        'weight:systems:flight_kit:mass',
        'weight:furniture:cargo_configuration:CG:x',
        'weight:furniture:passenger_seats:CG:x',
        'weight:furniture:food_water:CG:x',
        'weight:furniture:security_kit:CG:x',
        'weight:furniture:toilets:CG:x',
        'weight:furniture:cargo_configuration:mass',
        'weight:furniture:passenger_seats:mass',
        'weight:furniture:food_water:mass',
        'weight:furniture:security_kit:mass',
        'weight:furniture:toilets:mass'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeGlobalCG(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    cg_ratio = problem['cg_ratio']
    assert cg_ratio == pytest.approx(0.377420, abs=1e-6)


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
        'geometry:wing:MAC:length',
        'geometry:wing:location'
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
    cg_global = problem['weight:aircraft:CG:x']
    assert cg_global == pytest.approx(17.3, abs=1e-1)
