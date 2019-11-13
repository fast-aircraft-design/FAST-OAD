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
    input_list = ['geometry:wing_area',
                  'geometry:wing_span',
                  'weight:MZFW',
                  'weight:MFW',
                  'weight:MTOW',
                  'aerodynamics:Cl_alpha',
                  'loadcase1:U_gust',
                  'loadcase1:altitude',
                  'loadcase1:Vc_EAS',
                  'loadcase2:U_gust',
                  'loadcase2:altitude',
                  'loadcase2:Vc_EAS',

                  ]
    ivc = get_indep_var_comp(input_list)
    problem = run_system(Loads(), ivc)

    n1m1 = problem['n1m1']
    n2m2 = problem['n2m2']
    assert n1m1 == pytest.approx(240968, abs=10)
    assert n2m2 == pytest.approx(254130, abs=10)


def test_compute_wing_weight():
    """ Tests wing weight computation from sample XML data """
    input_list = ['geometry:wing_area',
                  'geometry:wing_span',
                  'geometry:wing_toc_root',
                  'geometry:wing_toc_kink',
                  'geometry:wing_toc_tip',
                  'geometry:wing_l2',
                  'geometry:wing_sweep_25',
                  'geometry:wing_area_pf',
                  'weight:MTOW',
                  'weight:MLW',
                  'kfactors_a1:K_A1',
                  'kfactors_a1:offset_A1',
                  'kfactors_a1:K_A11',
                  'kfactors_a1:offset_A11',
                  'kfactors_a1:K_A12',
                  'kfactors_a1:offset_A12',
                  'kfactors_a1:K_A13',
                  'kfactors_a1:offset_A13',
                  'kfactors_a1:K_A14',
                  'kfactors_a1:offset_A14',
                  'kfactors_a1:K_A15',
                  'kfactors_a1:offset_A15',
                  'kfactors_a1:K_voil',
                  'kfactors_a1:K_mvo']

    ivc = get_indep_var_comp(input_list)
    ivc.add_output('n1m1', 241000, units='kg')
    ivc.add_output('n2m2', 250000, units='kg')

    problem = run_system(WingWeight(), ivc)

    val = problem['weight_airframe:A1']
    assert val == pytest.approx(7681, abs=1)


def test_compute_fuselage_weight():
    """ Tests fuselage weight computation from sample XML data """
    input_list = [
        'geometry:fuselage_wet_area',
        'geometry:fuselage_width_max',
        'geometry:fuselage_height_max',
        'kfactors_a2:K_A2',
        'kfactors_a2:offset_A2',
        'kfactors_a2:K_tr',
        'kfactors_a2:K_fus',
    ]

    ivc = get_indep_var_comp(input_list)
    ivc.add_output('n1m1', 241000, units='kg')

    problem = run_system(FuselageWeight(), ivc)

    val = problem['weight_airframe:A2']
    assert val == pytest.approx(8828, abs=1)


def test_compute_empennage_weight():
    """ Tests empennage weight computation from sample XML data """
    input_list = [
        'geometry:ht_area',
        'geometry:vt_area',
        'kfactors_a3:K_A31',
        'kfactors_a3:offset_A31',
        'kfactors_a3:K_A32',
        'kfactors_a3:offset_A32',
    ]

    ivc = get_indep_var_comp(input_list)
    problem = run_system(EmpennageWeight(), ivc)
    val1 = problem['weight_airframe:A31']
    val2 = problem['weight_airframe:A32']
    assert val1 == pytest.approx(754, abs=1)
    assert val2 == pytest.approx(515, abs=1)


def test_compute_flight_controls_weight():
    """ Tests flight controls weight computation from sample XML data """
    input_list = [
        'geometry:fuselage_length',
        'geometry:wing_b_50',
        'kfactors_a4:K_A4',
        'kfactors_a4:offset_A4',
        'kfactors_a4:K_fc',
    ]
    ivc = get_indep_var_comp(input_list)
    ivc.add_output('n1m1', 241000, units='kg')
    ivc.add_output('n2m2', 250000, units='kg')
    problem = run_system(FlightControlsWeight(), ivc)

    val = problem['weight_airframe:A4']
    assert val == pytest.approx(716, abs=1)


def test_compute_landing_gear_weight():
    """ Tests landing gear weight computation from sample XML data """
    input_list = [
        'weight:MTOW',
        'kfactors_a5:K_A5',
        'kfactors_a5:offset_A5',
    ]
    ivc = get_indep_var_comp(input_list)
    problem = run_system(LandingGearWeight(), ivc)

    val1 = problem['weight_airframe:A51']
    val2 = problem['weight_airframe:A52']
    assert val1 == pytest.approx(2144, abs=1)
    assert val2 == pytest.approx(379, abs=1)


def test_compute_pylons_weight():
    """ Tests pylons weight computation from sample XML data """
    input_list = [
        'geometry:pylon_wet_area',
        'geometry:engine_number',
        'kfactors_a6:K_A6',
        'kfactors_a6:offset_A6',
    ]
    ivc = get_indep_var_comp(input_list)
    ivc.add_output('weight_propulsion:B1', 7161.33, units='kg')
    problem = run_system(PylonsWeight(), ivc)

    val = problem['weight_airframe:A6']
    assert val == pytest.approx(1212, abs=1)


def test_compute_paint_weight():
    """ Tests paint weight computation from sample XML data """
    input_list = [
        'geometry:S_total',
        'kfactors_a7:K_A7',
        'kfactors_a7:offset_A7',
    ]
    ivc = get_indep_var_comp(input_list)
    problem = run_system(PaintWeight(), ivc)

    val = problem['weight_airframe:A7']
    assert val == pytest.approx(141.1, abs=0.1)


def test_compute_engine_weight():
    """ Tests engine weight computation from sample XML data """
    input_list = [
        'propulsion:mto_thrust',
        'geometry:engine_number',
        'kfactors_b1:K_B1',
        'kfactors_b1:offset_B1',
    ]
    ivc = get_indep_var_comp(input_list)
    problem = run_system(EngineWeight(), ivc)

    val = problem['weight_propulsion:B1']
    assert val == pytest.approx(7161, abs=1)


def test_compute_fuel_lines_weight():
    """ Tests fuel lines weight computation from sample XML data """
    input_list = [
        'geometry:wing_b_50',
        'weight:MFW',
        'kfactors_b2:K_B2',
        'kfactors_b2:offset_B2',
    ]
    ivc = get_indep_var_comp(input_list)
    ivc.add_output('weight_propulsion:B1', 7161.33, units='kg')
    problem = run_system(FuelLinesWeight(), ivc)

    val = problem['weight_propulsion:B2']
    assert val == pytest.approx(457, abs=1)


def test_compute_unconsumables_weight():
    """ Tests "unconsumables" weight computation from sample XML data """
    input_list = [
        'geometry:engine_number',
        'weight:MFW',
        'kfactors_b3:K_B3',
        'kfactors_b3:offset_B3',
    ]
    ivc = get_indep_var_comp(input_list)
    problem = run_system(UnconsumablesWeight(), ivc)

    val = problem['weight_propulsion:B3']
    assert val == pytest.approx(122, abs=1)


def test_compute_power_systems_weight():
    """ Tests power systems weight computation from sample XML data """
    input_list = [
        'weight:MTOW',
        'kfactors_c1:K_C11',
        'kfactors_c1:offset_C11',
        'kfactors_c1:K_C12',
        'kfactors_c1:offset_C12',
        'kfactors_c1:K_C13',
        'kfactors_c1:offset_C13',
        'kfactors_c1:K_elec',
    ]
    ivc = get_indep_var_comp(input_list)
    ivc.add_output('cabin:NPAX1', 150)
    ivc.add_output('weight_airframe:A4', 700, units='kg')
    problem = run_system(PowerSystemsWeight(), ivc)

    val1 = problem['weight_systems:C11']
    val2 = problem['weight_systems:C12']
    val3 = problem['weight_systems:C13']
    assert val1 == pytest.approx(279, abs=1)
    assert val2 == pytest.approx(1297, abs=1)
    assert val3 == pytest.approx(747, abs=1)


def test_compute_life_support_systems_weight():
    """ Tests life support systems weight computation from sample XML data """
    input_list = [
        'geometry:fuselage_width_max',
        'geometry:fuselage_height_max',
        'geometry:fuselage_Lcabin',
        'geometry:wing_sweep_0',
        'geometry:nacelle_dia',
        'geometry:engine_number',
        'cabin:PNT',
        'cabin:PNC',
        'geometry:wing_span',
        'kfactors_c2:K_C21',
        'kfactors_c2:offset_C21',
        'kfactors_c2:K_C22',
        'kfactors_c2:offset_C22',
        'kfactors_c2:K_C23',
        'kfactors_c2:offset_C23',
        'kfactors_c2:K_C24',
        'kfactors_c2:offset_C24',
        'kfactors_c2:K_C25',
        'kfactors_c2:offset_C25',
        'kfactors_c2:K_C26',
        'kfactors_c2:offset_C26',
        'kfactors_c2:K_C27',
        'kfactors_c2:offset_C27',
    ]
    ivc = get_indep_var_comp(input_list)
    ivc.add_output('cabin:NPAX1', 150)
    ivc.add_output('weight_propulsion:B1', 7161.33, units='kg')
    problem = run_system(LifeSupportSystemsWeight(), ivc)

    val1 = problem['weight_systems:C21']
    val2 = problem['weight_systems:C22']
    val3 = problem['weight_systems:C23']
    val4 = problem['weight_systems:C24']
    val5 = problem['weight_systems:C25']
    val6 = problem['weight_systems:C26']
    val7 = problem['weight_systems:C27']
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
        'geometry:fuselage_length',
        'geometry:wing_b_50',
        'kfactors_c3:K_C3',
        'kfactors_c3:offset_C3',
    ]
    ivc = get_indep_var_comp(input_list)
    component = NavigationSystemsWeight()

    component.options[AIRCRAFT_TYPE_OPTION] = 1.
    problem = run_system(component, ivc)
    assert problem['weight_systems:C3'] == pytest.approx(193, abs=1)

    component.options[AIRCRAFT_TYPE_OPTION] = 2.
    problem = run_system(component, ivc)
    assert problem['weight_systems:C3'] == pytest.approx(493, abs=1)

    component.options[AIRCRAFT_TYPE_OPTION] = 3.
    problem = run_system(component, ivc)
    assert problem['weight_systems:C3'] == pytest.approx(743, abs=1)

    component.options[AIRCRAFT_TYPE_OPTION] = 4.
    problem = run_system(component, ivc)
    assert problem['weight_systems:C3'] == pytest.approx(843, abs=1)

    component.options[AIRCRAFT_TYPE_OPTION] = 5.
    problem = run_system(component, ivc)
    assert problem['weight_systems:C3'] == pytest.approx(843, abs=1)

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
        'kfactors_c4:K_C4',
        'kfactors_c4:offset_C4',
    ]

    ivc = get_indep_var_comp(input_list)
    component = TransmissionSystemsWeight()

    component.options[AIRCRAFT_TYPE_OPTION] = 1.
    problem = run_system(component, ivc)
    assert problem['weight_systems:C4'] == pytest.approx(100, abs=1)
    component.options[AIRCRAFT_TYPE_OPTION] = 2.
    problem = run_system(component, ivc)
    assert problem['weight_systems:C4'] == pytest.approx(200, abs=1)
    component.options[AIRCRAFT_TYPE_OPTION] = 3.
    problem = run_system(component, ivc)
    assert problem['weight_systems:C4'] == pytest.approx(250, abs=1)
    component.options[AIRCRAFT_TYPE_OPTION] = 4.
    problem = run_system(component, ivc)
    assert problem['weight_systems:C4'] == pytest.approx(350, abs=1)
    component.options[AIRCRAFT_TYPE_OPTION] = 5.
    problem = run_system(component, ivc)
    assert problem['weight_systems:C4'] == pytest.approx(350, abs=1)

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
        'geometry:fuselage_LAV',
        'geometry:fuselage_LAR',
        'geometry:fuselage_length',
        'cabin:front_seat_number_eco',
        'geometry:wing_l2',
        'cabin:container_number_front',
        'kfactors_c5:K_C5',
        'kfactors_c5:offset_C5',
    ]

    ivc = get_indep_var_comp(input_list)
    problem = run_system(FixedOperationalSystemsWeight(), ivc)

    val1 = problem['weight_systems:C51']
    val2 = problem['weight_systems:C52']
    assert val1 == pytest.approx(100, abs=1)
    assert val2 == pytest.approx(277, abs=1)


def test_compute_flight_kit_weight():
    """ Tests flight kit weight computation from sample XML data """
    input_list = [
        'kfactors_c6:K_C6',
        'kfactors_c6:offset_C6',
    ]
    ivc = get_indep_var_comp(input_list)
    component = FlightKitWeight()

    component.options[AIRCRAFT_TYPE_OPTION] = 1.
    problem = run_system(component, ivc)
    assert problem['weight_systems:C6'] == pytest.approx(10, abs=1)

    component.options[AIRCRAFT_TYPE_OPTION] = 5.
    problem = run_system(component, ivc)
    assert problem['weight_systems:C6'] == pytest.approx(45, abs=1)


def test_compute_cargo_configuration_weight():
    """ Tests cargo configuration weight computation from sample XML data """
    input_list = [
        'cabin:container_number',
        'cabin:pallet_number',
        'cabin:front_seat_number_eco',
        'kfactors_d1:K_D1',
        'kfactors_d1:offset_D1',
    ]
    ivc = get_indep_var_comp(input_list)
    ivc.add_output('cabin:NPAX1', 150)
    component = CargoConfigurationWeight()

    problem = run_system(component, ivc)
    val = problem['weight_furniture:D1']
    assert val == 0.

    component.options['ac_type'] = 6.
    problem = run_system(component, ivc)
    val = problem['weight_furniture:D1']
    assert val == pytest.approx(39.3, abs=0.1)


def test_compute_passenger_seats_weight():
    """ Tests passenger seats weight computation from sample XML data """
    input_list = [
        'tlar:NPAX',
        'kfactors_d2:K_D2',
        'kfactors_d2:offset_D2',
    ]

    ivc = get_indep_var_comp(input_list)
    component = PassengerSeatsWeight()

    problem = run_system(component, ivc)
    val = problem['weight_furniture:D2']
    assert val == pytest.approx(1500, abs=1)

    component.options['ac_type'] = 6.
    problem = run_system(component, ivc)
    val = problem['weight_furniture:D2']
    assert val == 0.


def test_compute_food_water_weight():
    """ Tests food water weight computation from sample XML data """
    input_list = [
        'tlar:NPAX',
        'kfactors_d3:K_D3',
        'kfactors_d3:offset_D3',
    ]

    ivc = get_indep_var_comp(input_list)
    component = FoodWaterWeight()

    problem = run_system(component, ivc)
    val = problem['weight_furniture:D3']
    assert val == pytest.approx(1312, abs=1)

    component.options['ac_type'] = 6.
    problem = run_system(component, ivc)
    val = problem['weight_furniture:D3']
    assert val == 0.


def test_compute_security_kit_weight():
    """ Tests security kit weight computation from sample XML data """
    input_list = [
        'tlar:NPAX',
        'kfactors_d4:K_D4',
        'kfactors_d4:offset_D4',
    ]

    ivc = get_indep_var_comp(input_list)
    component = SecurityKitWeight()

    problem = run_system(component, ivc)
    val = problem['weight_furniture:D4']
    assert val == pytest.approx(225, abs=1)

    component.options['ac_type'] = 6.
    problem = run_system(component, ivc)
    val = problem['weight_furniture:D4']
    assert val == 0.


def test_compute_toilets_weight():
    """ Tests toilets weight computation from sample XML data """
    input_list = [
        'tlar:NPAX',
        'kfactors_d5:K_D5',
        'kfactors_d5:offset_D5',
    ]

    ivc = get_indep_var_comp(input_list)
    component = ToiletsWeight()

    problem = run_system(component, ivc)
    val = problem['weight_furniture:D5']
    assert val == pytest.approx(75, abs=0.1)

    component.options['ac_type'] = 6.
    problem = run_system(component, ivc)
    val = problem['weight_furniture:D5']
    assert val == 0.


def test_compute_crew_weight():
    """ Tests crew weight computation from sample XML data """
    input_list = [
        'cabin:PNT',
        'cabin:PNC',
    ]
    ivc = get_indep_var_comp(input_list)
    problem = run_system(CrewWeight(), ivc)

    val = problem['weight_crew:E']
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
    input_vars = reader.read(ignore=['weight:MLW', 'weight:MZFW'])

    mass_computation = run_system(MassBreakdown(), input_vars)

    oew = mass_computation['weight:OEW']
    assert oew == pytest.approx(42060, abs=1)
