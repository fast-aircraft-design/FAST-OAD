"""
Test module for mass breakdown functions
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

from fastoad.io.xml.openmdao_basic_io import OMXmlIO
from fastoad.modules.mass_breakdown.a_airframe import EmpennageWeight, \
    FlightControlsWeight, \
    FuselageWeight, \
    PaintWeight, PylonsWeight, WingWeight, LandingGearWeight
from fastoad.modules.mass_breakdown.b_propulsion import FuelLinesWeight, \
    UnconsumablesWeight, EngineWeight
from fastoad.modules.mass_breakdown.c_systems import \
    FixedOperationalSystemsWeight, \
    FlightKitWeight, \
    LifeSupportSystemsWeight, NavigationSystemsWeight, PowerSystemsWeight, \
    TransmissionSystemsWeight
from fastoad.modules.mass_breakdown.cs25 import Loads
from fastoad.modules.mass_breakdown.d_furniture import \
    CargoConfigurationWeight, \
    PassengerSeatsWeight, FoodWaterWeight, \
    ToiletsWeight, SecurityKitWeight
from fastoad.modules.mass_breakdown.e_crew import CrewWeight
from fastoad.modules.mass_breakdown.mass_breakdown import MassBreakdown, OperatingEmptyWeight
from fastoad.modules.mass_breakdown.options import AIRCRAFT_TYPE_OPTION
from tests.testing_utilities import run_system


def get_indep_var_comp(var_names):
    """ Reads required input data and returns an IndepVarcomp() instance"""
    reader = OMXmlIO(pth.join(pth.dirname(__file__), "data", "mass_breakdown_inputs.xml"))
    reader.path_separator = ':'
    ivc = reader.read(only=var_names)
    return ivc


def test_compute_loads():
    """ Tests computation of sizing loads """
    input_list = ['geometry:wing:area',
                  'geometry:wing:span',
                  'weight:aircraft:MZFW',
                  'weight:aircraft:MFW',
                  'weight:aircraft:MTOW',
                  'aerodynamics:aircraft:cruise:CL_alpha',
                  'load_case:lc1:U_gust',
                  'load_case:lc1:altitude',
                  'load_case:lc1:Vc_EAS',
                  'load_case:lc2:U_gust',
                  'load_case:lc2:altitude',
                  'load_case:lc2:Vc_EAS',

                  ]
    ivc = get_indep_var_comp(input_list)
    problem = run_system(Loads(), ivc)

    n1m1 = problem['n1m1']
    n2m2 = problem['n2m2']
    assert n1m1 == pytest.approx(240968, abs=10)
    assert n2m2 == pytest.approx(254130, abs=10)


def test_compute_wing_weight():
    """ Tests wing weight computation from sample XML data """
    input_list = ['geometry:wing:area',
                  'geometry:wing:span',
                  'geometry:wing:root:thickness_ratio',
                  'geometry:wing:kink:thickness_ratio',
                  'geometry:wing:tip:thickness_ratio',
                  'geometry:wing:root:chord',
                  'geometry:wing:sweep_25',
                  'geometry:wing:cantilever_area',
                  'weight:aircraft:MTOW',
                  'weight:aircraft:MLW',
                  'weight:airframe:wing:mass:k',
                  'weight:airframe:wing:mass:offset',
                  'weight:airframe:wing:bending_sizing:mass:k',
                  'weight:airframe:wing:bending_sizing:mass:offset',
                  'weight:airframe:wing:shear_sizing:mass:k',
                  'weight:airframe:wing:shear_sizing:mass:offset',
                  'weight:airframe:wing:ribs:mass:k',
                  'weight:airframe:wing:ribs:mass:offset',
                  'weight:airframe:wing:reinforcements:mass:k',
                  'weight:airframe:wing:reinforcements:mass:offset',
                  'weight:airframe:wing:secondary_parts:mass:k',
                  'weight:airframe:wing:secondary_parts:mass:offset',
                  'weight:airframe:wing:mass:k_voil',
                  'weight:airframe:wing:mass:k_mvo']

    ivc = get_indep_var_comp(input_list)
    ivc.add_output('n1m1', 241000, units='kg')
    ivc.add_output('n2m2', 250000, units='kg')

    problem = run_system(WingWeight(), ivc)

    val = problem['weight:airframe:wing:mass']
    assert val == pytest.approx(7681, abs=1)


def test_compute_fuselage_weight():
    """ Tests fuselage weight computation from sample XML data """
    input_list = [
        'geometry:fuselage:wet_area',
        'geometry:fuselage:maximum_width',
        'geometry:fuselage:maximum_height',
        'weight:airframe:fuselage:mass:k',
        'weight:airframe:fuselage:mass:offset',
        'weight:airframe:fuselage:mass:k_tr',
        'weight:airframe:fuselage:mass:k_fus',
    ]

    ivc = get_indep_var_comp(input_list)
    ivc.add_output('n1m1', 241000, units='kg')

    problem = run_system(FuselageWeight(), ivc)

    val = problem['weight:airframe:fuselage:mass']
    assert val == pytest.approx(8828, abs=1)


def test_compute_empennage_weight():
    """ Tests empennage weight computation from sample XML data """
    input_list = [
        'geometry:horizontal_tail:area',
        'geometry:vertical_tail:area',
        'weight:airframe:tail_plane:horizontal:mass:k',
        'weight:airframe:tail_plane:horizontal:mass:offset',
        'weight:airframe:tail_plane:vertical:mass:k',
        'weight:airframe:tail_plane:vertical:mass:offset',
    ]

    ivc = get_indep_var_comp(input_list)
    problem = run_system(EmpennageWeight(), ivc)
    val1 = problem['weight:airframe:tail_plane:horizontal:mass']
    val2 = problem['weight:airframe:tail_plane:vertical:mass']
    assert val1 == pytest.approx(754, abs=1)
    assert val2 == pytest.approx(515, abs=1)


def test_compute_flight_controls_weight():
    """ Tests flight controls weight computation from sample XML data """
    input_list = [
        'geometry:fuselage:length',
        'geometry:wing:b_50',
        'weight:airframe:flight_controls:mass:k',
        'weight:airframe:flight_controls:mass:offset',
        'weight:airframe:flight_controls:mass:k_fc',
    ]
    ivc = get_indep_var_comp(input_list)
    ivc.add_output('n1m1', 241000, units='kg')
    ivc.add_output('n2m2', 250000, units='kg')
    problem = run_system(FlightControlsWeight(), ivc)

    val = problem['weight:airframe:flight_controls:mass']
    assert val == pytest.approx(716, abs=1)


def test_compute_landing_gear_weight():
    """ Tests landing gear weight computation from sample XML data """
    input_list = [
        'weight:aircraft:MTOW',
        'weight:airframe:landing_gear:mass:k',
        'weight:airframe:landing_gear:mass:offset',
    ]
    ivc = get_indep_var_comp(input_list)
    problem = run_system(LandingGearWeight(), ivc)

    val1 = problem['weight:airframe:landing_gear:main:mass']
    val2 = problem['weight:airframe:landing_gear:front:mass']
    assert val1 == pytest.approx(2144, abs=1)
    assert val2 == pytest.approx(379, abs=1)


def test_compute_pylons_weight():
    """ Tests pylons weight computation from sample XML data """
    input_list = [
        'geometry:propulsion:pylon:wet_area',
        'geometry:propulsion:engine:count',
        'weight:airframe:pylon:mass:k',
        'weight:airframe:pylon:mass:offset',
    ]
    ivc = get_indep_var_comp(input_list)
    ivc.add_output('weight:propulsion:engine:mass', 7161.33, units='kg')
    problem = run_system(PylonsWeight(), ivc)

    val = problem['weight:airframe:pylon:mass']
    assert val == pytest.approx(1212, abs=1)


def test_compute_paint_weight():
    """ Tests paint weight computation from sample XML data """
    input_list = [
        'geometry:aircraft:area',
        'weight:airframe:paint:mass:k',
        'weight:airframe:paint:mass:offset',
    ]
    ivc = get_indep_var_comp(input_list)
    problem = run_system(PaintWeight(), ivc)

    val = problem['weight:airframe:paint:mass']
    assert val == pytest.approx(141.1, abs=0.1)


def test_compute_engine_weight():
    """ Tests engine weight computation from sample XML data """
    input_list = [
        'propulsion:MTO_thrust',
        'geometry:propulsion:engine:count',
        'weight:propulsion:engine:mass:k',
        'weight:propulsion:engine:mass:offset',
    ]
    ivc = get_indep_var_comp(input_list)
    problem = run_system(EngineWeight(), ivc)

    val = problem['weight:propulsion:engine:mass']
    assert val == pytest.approx(7161, abs=1)


def test_compute_fuel_lines_weight():
    """ Tests fuel lines weight computation from sample XML data """
    input_list = [
        'geometry:wing:b_50',
        'weight:aircraft:MFW',
        'weight:propulsion:fuel_lines:mass:k',
        'weight:propulsion:fuel_lines:mass:offset',
    ]
    ivc = get_indep_var_comp(input_list)
    ivc.add_output('weight:propulsion:engine:mass', 7161.33, units='kg')
    problem = run_system(FuelLinesWeight(), ivc)

    val = problem['weight:propulsion:fuel_lines:mass']
    assert val == pytest.approx(457, abs=1)


def test_compute_unconsumables_weight():
    """ Tests "unconsumables" weight computation from sample XML data """
    input_list = [
        'geometry:propulsion:engine:count',
        'weight:aircraft:MFW',
        'weight:propulsion:unconsumables:mass:k',
        'weight:propulsion:unconsumables:mass:offset',
    ]
    ivc = get_indep_var_comp(input_list)
    problem = run_system(UnconsumablesWeight(), ivc)

    val = problem['weight:propulsion:unconsumables:mass']
    assert val == pytest.approx(122, abs=1)


def test_compute_power_systems_weight():
    """ Tests power systems weight computation from sample XML data """
    input_list = [
        'weight:aircraft:MTOW',
        'weight:systems:power:auxiliary_power_unit:mass:k',
        'weight:systems:power:auxiliary_power_unit:mass:offset',
        'weight:systems:power:electric_systems:mass:k',
        'weight:systems:power:electric_systems:mass:offset',
        'weight:systems:power:hydraulic_systems:mass:k',
        'weight:systems:power:hydraulic_systems:mass:offset',
        'weight:systems:power:mass:k_elec',
    ]
    ivc = get_indep_var_comp(input_list)
    ivc.add_output('geometry:cabin:NPAX1', 150)
    ivc.add_output('weight:airframe:flight_controls:mass', 700, units='kg')
    problem = run_system(PowerSystemsWeight(), ivc)

    val1 = problem['weight:systems:power:auxiliary_power_unit:mass']
    val2 = problem['weight:systems:power:electric_systems:mass']
    val3 = problem['weight:systems:power:hydraulic_systems:mass']
    assert val1 == pytest.approx(279, abs=1)
    assert val2 == pytest.approx(1297, abs=1)
    assert val3 == pytest.approx(747, abs=1)


def test_compute_life_support_systems_weight():
    """ Tests life support systems weight computation from sample XML data """
    input_list = [
        'geometry:fuselage:maximum_width',
        'geometry:fuselage:maximum_height',
        'geometry:fuselage:cabin_length',
        'geometry:wing:sweep_0',
        'geometry:propulsion:nacelle:diameter',
        'geometry:propulsion:engine:count',
        'geometry:cabin:crew_count:technical',
        'geometry:cabin:crew_count:commercial',
        'geometry:wing:span',
        'weight:systems:life_support:mass:insulation:k',
        'weight:systems:life_support:mass:insulation:offset',
        'weight:systems:life_support:mass:air_conditioning:k',
        'weight:systems:life_support:mass:air_conditioning:offset',
        'weight:systems:life_support:mass:de-icing:k',
        'weight:systems:life_support:mass:de-icing:offset',
        'weight:systems:life_support:mass:cabin_lighting:k',
        'weight:systems:life_support:mass:cabin_lighting:offset',
        'weight:systems:life_support:mass:seats_crew_accomodation:k',
        'weight:systems:life_support:mass:seats_crew_accomodation:offset',
        'weight:systems:life_support:mass:oxygen:k',
        'weight:systems:life_support:mass:oxygen:offset',
        'weight:systems:life_support:mass:safety_equipment:k',
        'weight:systems:life_support:mass:safety_equipment:offset',
    ]
    ivc = get_indep_var_comp(input_list)
    ivc.add_output('geometry:cabin:NPAX1', 150)
    ivc.add_output('weight:propulsion:engine:mass', 7161.33, units='kg')
    problem = run_system(LifeSupportSystemsWeight(), ivc)

    val1 = problem['weight:systems:life_support:insulation:mass']
    val2 = problem['weight:systems:life_support:air_conditioning:mass']
    val3 = problem['weight:systems:life_support:de-icing:mass']
    val4 = problem['weight:systems:life_support:cabin_lighting:mass']
    val5 = problem['weight:systems:life_support:seats_crew_accomodation:mass']
    val6 = problem['weight:systems:life_support:oxygen:mass']
    val7 = problem['weight:systems:life_support:safety_equipment:mass']
    assert val1 == pytest.approx(2226, abs=1)
    assert val2 == pytest.approx(920, abs=1)
    assert val3 == pytest.approx(154, abs=1)
    assert val4 == pytest.approx(168, abs=1)
    assert val5 == pytest.approx(126, abs=1)
    assert val6 == pytest.approx(275, abs=1)
    assert val7 == pytest.approx(416, abs=1)


def test_compute_navigation_systems_weight():
    """ Tests navigation systems weight computation from sample XML data """
    input_list = [
        'geometry:fuselage:length',
        'geometry:wing:b_50',
        'weight:systems:navigation:mass:k',
        'weight:systems:navigation:mass:offset',
    ]
    ivc = get_indep_var_comp(input_list)
    component = NavigationSystemsWeight()

    component.options[AIRCRAFT_TYPE_OPTION] = 1.
    problem = run_system(component, ivc)
    assert problem['weight:systems:navigation:mass'] == pytest.approx(193, abs=1)

    component.options[AIRCRAFT_TYPE_OPTION] = 2.
    problem = run_system(component, ivc)
    assert problem['weight:systems:navigation:mass'] == pytest.approx(493, abs=1)

    component.options[AIRCRAFT_TYPE_OPTION] = 3.
    problem = run_system(component, ivc)
    assert problem['weight:systems:navigation:mass'] == pytest.approx(743, abs=1)

    component.options[AIRCRAFT_TYPE_OPTION] = 4.
    problem = run_system(component, ivc)
    assert problem['weight:systems:navigation:mass'] == pytest.approx(843, abs=1)

    component.options[AIRCRAFT_TYPE_OPTION] = 5.
    problem = run_system(component, ivc)
    assert problem['weight:systems:navigation:mass'] == pytest.approx(843, abs=1)

    got_value_error = False
    try:
        component.options[AIRCRAFT_TYPE_OPTION] = 6.
        problem = run_system(component, ivc)
    except ValueError:
        got_value_error = True
    assert got_value_error


def test_compute_transmissions_systems_weight():
    """ Tests transmissions weight computation from sample XML data """
    input_list = [
        'weight:systems:transmission:mass:k',
        'weight:systems:transmission:mass:offset',
    ]

    ivc = get_indep_var_comp(input_list)
    component = TransmissionSystemsWeight()

    component.options[AIRCRAFT_TYPE_OPTION] = 1.
    problem = run_system(component, ivc)
    assert problem['weight:systems:transmission:mass'] == pytest.approx(100, abs=1)
    component.options[AIRCRAFT_TYPE_OPTION] = 2.
    problem = run_system(component, ivc)
    assert problem['weight:systems:transmission:mass'] == pytest.approx(200, abs=1)
    component.options[AIRCRAFT_TYPE_OPTION] = 3.
    problem = run_system(component, ivc)
    assert problem['weight:systems:transmission:mass'] == pytest.approx(250, abs=1)
    component.options[AIRCRAFT_TYPE_OPTION] = 4.
    problem = run_system(component, ivc)
    assert problem['weight:systems:transmission:mass'] == pytest.approx(350, abs=1)
    component.options[AIRCRAFT_TYPE_OPTION] = 5.
    problem = run_system(component, ivc)
    assert problem['weight:systems:transmission:mass'] == pytest.approx(350, abs=1)

    got_value_error = False
    try:
        component.options[AIRCRAFT_TYPE_OPTION] = 6.
        problem = run_system(component, ivc)
    except ValueError:
        got_value_error = True
    assert got_value_error


def test_compute_fixed_operational_systems_weight():
    """
    Tests fixed operational systems weight computation from sample XML data
    """
    input_list = [
        'geometry:fuselage:rear_length',
        'geometry:fuselage:front_length',
        'geometry:fuselage:length',
        'geometry:cabin:seats:economical:count_by_row',
        'geometry:wing:root:chord',
        'geometry:cabin:containers:count_by_row',
        'weight:systems:operational:mass:k',
        'weight:systems:operational:mass:offset',
    ]

    ivc = get_indep_var_comp(input_list)
    problem = run_system(FixedOperationalSystemsWeight(), ivc)

    val1 = problem['weight:systems:operational:radar:mass']
    val2 = problem['weight:systems:operational:cargo_hold:mass']
    assert val1 == pytest.approx(100, abs=1)
    assert val2 == pytest.approx(277, abs=1)


def test_compute_flight_kit_weight():
    """ Tests flight kit weight computation from sample XML data """
    input_list = [
        'weight:systems:flight_kit:mass:k',
        'weight:systems:flight_kit:mass:offset',
    ]
    ivc = get_indep_var_comp(input_list)
    component = FlightKitWeight()

    component.options[AIRCRAFT_TYPE_OPTION] = 1.
    problem = run_system(component, ivc)
    assert problem['weight:systems:flight_kit:mass'] == pytest.approx(10, abs=1)

    component.options[AIRCRAFT_TYPE_OPTION] = 5.
    problem = run_system(component, ivc)
    assert problem['weight:systems:flight_kit:mass'] == pytest.approx(45, abs=1)


def test_compute_cargo_configuration_weight():
    """ Tests cargo configuration weight computation from sample XML data """
    input_list = [
        'geometry:cabin:containers:count',
        'geometry:cabin:pallet_count',
        'geometry:cabin:seats:economical:count_by_row',
        'weight:furniture:cargo_configuration:mass:k',
        'weight:furniture:cargo_configuration:mass:offset',
    ]
    ivc = get_indep_var_comp(input_list)
    ivc.add_output('geometry:cabin:NPAX1', 150)
    component = CargoConfigurationWeight()

    problem = run_system(component, ivc)
    val = problem['weight:furniture:cargo_configuration:mass']
    assert val == 0.

    component.options['ac_type'] = 6.
    problem = run_system(component, ivc)
    val = problem['weight:furniture:cargo_configuration:mass']
    assert val == pytest.approx(39.3, abs=0.1)


def test_compute_passenger_seats_weight():
    """ Tests passenger seats weight computation from sample XML data """
    input_list = [
        'TLAR:NPAX',
        'weight:furniture:passenger_seats:mass:k',
        'weight:furniture:passenger_seats:mass:offset',
    ]

    ivc = get_indep_var_comp(input_list)
    component = PassengerSeatsWeight()

    problem = run_system(component, ivc)
    val = problem['weight:furniture:passenger_seats:mass']
    assert val == pytest.approx(1500, abs=1)

    component.options['ac_type'] = 6.
    problem = run_system(component, ivc)
    val = problem['weight:furniture:passenger_seats:mass']
    assert val == 0.


def test_compute_food_water_weight():
    """ Tests food water weight computation from sample XML data """
    input_list = [
        'TLAR:NPAX',
        'weight:furniture:food_water:mass:k',
        'weight:furniture:food_water:mass:offset',
    ]

    ivc = get_indep_var_comp(input_list)
    component = FoodWaterWeight()

    problem = run_system(component, ivc)
    val = problem['weight:furniture:food_water:mass']
    assert val == pytest.approx(1312, abs=1)

    component.options['ac_type'] = 6.
    problem = run_system(component, ivc)
    val = problem['weight:furniture:food_water:mass']
    assert val == 0.


def test_compute_security_kit_weight():
    """ Tests security kit weight computation from sample XML data """
    input_list = [
        'TLAR:NPAX',
        'weight:furniture:security_kit:mass:k',
        'weight:furniture:security_kit:mass:offset',
    ]

    ivc = get_indep_var_comp(input_list)
    component = SecurityKitWeight()

    problem = run_system(component, ivc)
    val = problem['weight:furniture:security_kit:mass']
    assert val == pytest.approx(225, abs=1)

    component.options['ac_type'] = 6.
    problem = run_system(component, ivc)
    val = problem['weight:furniture:security_kit:mass']
    assert val == 0.


def test_compute_toilets_weight():
    """ Tests toilets weight computation from sample XML data """
    input_list = [
        'TLAR:NPAX',
        'weight:furniture:toilets:mass:k',
        'weight:furniture:toilets:mass:offset',
    ]

    ivc = get_indep_var_comp(input_list)
    component = ToiletsWeight()

    problem = run_system(component, ivc)
    val = problem['weight:furniture:toilets:mass']
    assert val == pytest.approx(75, abs=0.1)

    component.options['ac_type'] = 6.
    problem = run_system(component, ivc)
    val = problem['weight:furniture:toilets:mass']
    assert val == 0.


def test_compute_crew_weight():
    """ Tests crew weight computation from sample XML data """
    input_list = [
        'geometry:cabin:crew_count:technical',
        'geometry:cabin:crew_count:commercial',
    ]
    ivc = get_indep_var_comp(input_list)
    problem = run_system(CrewWeight(), ivc)

    val = problem['weight:crew:mass']
    assert val == pytest.approx(470, abs=1)


def test_evaluate_oew():
    """
    Tests a simple evaluation of Operating Empty Weight from sample XML data.
    """
    reader = OMXmlIO(pth.join(pth.dirname(__file__), "data", "mass_breakdown_inputs.xml"))
    reader.path_separator = ':'
    input_vars = reader.read()

    mass_computation = run_system(OperatingEmptyWeight(), input_vars, setup_mode='fwd')

    oew = mass_computation['weight:OEW']
    assert oew == pytest.approx(41591, abs=1)


def test_loop_compute_oew():
    """
    Tests a weight computation loop using matching the max payload criterion.
    """
    reader = OMXmlIO(pth.join(pth.dirname(__file__), "data", "mass_breakdown_inputs.xml"))
    reader.path_separator = ':'
    input_vars = reader.read(ignore=['weight:aircraft:MLW', 'weight:aircraft:MZFW'])

    mass_computation = run_system(MassBreakdown(), input_vars)

    oew = mass_computation['weight:OEW']
    assert oew == pytest.approx(42060, abs=1)
