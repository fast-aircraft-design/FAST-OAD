"""
Test module for mass breakdown functions
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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

import openmdao.api as om
import pytest
from fastoad.io import VariableIO

from tests.testing_utilities import run_system
from ..a_airframe import (
    EmpennageWeight,
    FlightControlsWeight,
    FuselageWeight,
    PaintWeight,
    PylonsWeight,
    WingWeight,
    LandingGearWeight,
)
from ..b_propulsion import FuelLinesWeight, UnconsumablesWeight, EngineWeight
from ..c_systems import (
    FixedOperationalSystemsWeight,
    FlightKitWeight,
    LifeSupportSystemsWeight,
    NavigationSystemsWeight,
    PowerSystemsWeight,
    TransmissionSystemsWeight,
)
from ..cs25 import Loads
from ..d_furniture import (
    CargoConfigurationWeight,
    PassengerSeatsWeight,
    FoodWaterWeight,
    ToiletsWeight,
    SecurityKitWeight,
)
from ..e_crew import CrewWeight
from ..mass_breakdown import MassBreakdown, OperatingWeightEmpty
from ..payload import ComputePayload


def get_indep_var_comp(var_names):
    """ Reads required input data and returns an IndepVarcomp() instance"""
    reader = VariableIO(pth.join(pth.dirname(__file__), "data", "mass_breakdown_inputs.xml"))
    reader.path_separator = ":"
    ivc = reader.read(only=var_names).to_ivc()
    return ivc


def test_compute_payload():
    ivc = om.IndepVarComp()
    ivc.add_output("data:TLAR:NPAX", val=150)
    problem = run_system(ComputePayload(), ivc)
    assert problem["data:weight:aircraft:payload"] == pytest.approx(13608.0, abs=0.1)
    assert problem["data:weight:aircraft:max_payload"] == pytest.approx(19608.0, abs=0.1)

    ivc = om.IndepVarComp()
    ivc.add_output("data:TLAR:NPAX", val=150)
    ivc.add_output(
        "settings:weight:aircraft:payload:design_mass_per_passenger", val=1.0, units="kg"
    )
    ivc.add_output("settings:weight:aircraft:payload:max_mass_per_passenger", val=2.0, units="kg")
    problem = run_system(ComputePayload(), ivc)
    assert problem["data:weight:aircraft:payload"] == pytest.approx(150.0, abs=0.1)
    assert problem["data:weight:aircraft:max_payload"] == pytest.approx(300.0, abs=0.1)


def test_compute_loads():
    """ Tests computation of sizing loads """
    input_list = [
        "data:geometry:wing:area",
        "data:geometry:wing:span",
        "data:weight:aircraft:MZFW",
        "data:weight:aircraft:MFW",
        "data:weight:aircraft:MTOW",
        "data:aerodynamics:aircraft:cruise:CL_alpha",
        "data:load_case:lc1:U_gust",
        "data:load_case:lc1:altitude",
        "data:load_case:lc1:Vc_EAS",
        "data:load_case:lc2:U_gust",
        "data:load_case:lc2:altitude",
        "data:load_case:lc2:Vc_EAS",
    ]
    ivc = get_indep_var_comp(input_list)
    problem = run_system(Loads(), ivc)

    n1m1 = problem["data:mission:sizing:cs25:sizing_load_1"]
    n2m2 = problem["data:mission:sizing:cs25:sizing_load_2"]
    assert n1m1 == pytest.approx(240968, abs=10)
    assert n2m2 == pytest.approx(254130, abs=10)


def test_compute_wing_weight():
    """ Tests wing weight computation from sample XML data """
    input_list = [
        "data:geometry:wing:area",
        "data:geometry:wing:span",
        "data:geometry:wing:root:thickness_ratio",
        "data:geometry:wing:kink:thickness_ratio",
        "data:geometry:wing:tip:thickness_ratio",
        "data:geometry:wing:root:chord",
        "data:geometry:wing:sweep_25",
        "data:geometry:wing:outer_area",
        "data:weight:aircraft:MTOW",
        "data:weight:aircraft:MLW",
        "tuning:weight:airframe:wing:mass:k",
        "tuning:weight:airframe:wing:mass:offset",
        "tuning:weight:airframe:wing:bending_sizing:mass:k",
        "tuning:weight:airframe:wing:bending_sizing:mass:offset",
        "tuning:weight:airframe:wing:shear_sizing:mass:k",
        "tuning:weight:airframe:wing:shear_sizing:mass:offset",
        "tuning:weight:airframe:wing:ribs:mass:k",
        "tuning:weight:airframe:wing:ribs:mass:offset",
        "tuning:weight:airframe:wing:reinforcements:mass:k",
        "tuning:weight:airframe:wing:reinforcements:mass:offset",
        "tuning:weight:airframe:wing:secondary_parts:mass:k",
        "tuning:weight:airframe:wing:secondary_parts:mass:offset",
        "settings:weight:airframe:wing:mass:k_voil",
        "settings:weight:airframe:wing:mass:k_mvo",
    ]

    ivc = get_indep_var_comp(input_list)
    ivc.add_output("data:mission:sizing:cs25:sizing_load_1", 241000, units="kg")
    ivc.add_output("data:mission:sizing:cs25:sizing_load_2", 250000, units="kg")

    problem = run_system(WingWeight(), ivc)

    val = problem["data:weight:airframe:wing:mass"]
    assert val == pytest.approx(7681, abs=1)


def test_compute_fuselage_weight():
    """ Tests fuselage weight computation from sample XML data """
    input_list = [
        "data:geometry:fuselage:wetted_area",
        "data:geometry:fuselage:maximum_width",
        "data:geometry:fuselage:maximum_height",
        "tuning:weight:airframe:fuselage:mass:k",
        "tuning:weight:airframe:fuselage:mass:offset",
        "settings:weight:airframe:fuselage:mass:k_lg",
        "settings:weight:airframe:fuselage:mass:k_fus",
    ]

    ivc = get_indep_var_comp(input_list)
    ivc.add_output("data:mission:sizing:cs25:sizing_load_1", 241000, units="kg")

    problem = run_system(FuselageWeight(), ivc)

    val = problem["data:weight:airframe:fuselage:mass"]
    assert val == pytest.approx(8828, abs=1)


def test_compute_empennage_weight():
    """ Tests empennage weight computation from sample XML data """
    input_list = [
        "data:geometry:has_T_tail",
        "data:geometry:horizontal_tail:area",
        "data:geometry:vertical_tail:area",
        "data:geometry:propulsion:layout",
        "tuning:weight:airframe:horizontal_tail:mass:k",
        "tuning:weight:airframe:horizontal_tail:mass:offset",
        "tuning:weight:airframe:vertical_tail:mass:k",
        "tuning:weight:airframe:vertical_tail:mass:offset",
    ]

    ivc = get_indep_var_comp(input_list)
    problem = run_system(EmpennageWeight(), ivc)
    val1 = problem["data:weight:airframe:horizontal_tail:mass"]
    val2 = problem["data:weight:airframe:vertical_tail:mass"]
    assert val1 == pytest.approx(754, abs=1)
    assert val2 == pytest.approx(515, abs=1)


def test_compute_flight_controls_weight():
    """ Tests flight controls weight computation from sample XML data """
    input_list = [
        "data:geometry:fuselage:length",
        "data:geometry:wing:b_50",
        "tuning:weight:airframe:flight_controls:mass:k",
        "tuning:weight:airframe:flight_controls:mass:offset",
        "settings:weight:airframe:flight_controls:mass:k_fc",
    ]
    ivc = get_indep_var_comp(input_list)
    ivc.add_output("data:mission:sizing:cs25:sizing_load_1", 241000, units="kg")
    ivc.add_output("data:mission:sizing:cs25:sizing_load_2", 250000, units="kg")
    problem = run_system(FlightControlsWeight(), ivc)

    val = problem["data:weight:airframe:flight_controls:mass"]
    assert val == pytest.approx(716, abs=1)


def test_compute_landing_gear_weight():
    """ Tests landing gear weight computation from sample XML data """
    input_list = [
        "data:weight:aircraft:MTOW",
        "tuning:weight:airframe:landing_gear:mass:k",
        "tuning:weight:airframe:landing_gear:mass:offset",
    ]
    ivc = get_indep_var_comp(input_list)
    problem = run_system(LandingGearWeight(), ivc)

    val1 = problem["data:weight:airframe:landing_gear:main:mass"]
    val2 = problem["data:weight:airframe:landing_gear:front:mass"]
    assert val1 == pytest.approx(2144, abs=1)
    assert val2 == pytest.approx(379, abs=1)


def test_compute_pylons_weight():
    """ Tests pylons weight computation from sample XML data """
    input_list = [
        "data:geometry:propulsion:pylon:wetted_area",
        "data:geometry:propulsion:engine:count",
        "data:geometry:propulsion:layout",
        "tuning:weight:airframe:pylon:mass:k",
        "tuning:weight:airframe:pylon:mass:offset",
    ]
    ivc = get_indep_var_comp(input_list)
    ivc.add_output("data:weight:propulsion:engine:mass", 7161.33, units="kg")
    problem = run_system(PylonsWeight(), ivc)

    val = problem["data:weight:airframe:pylon:mass"]
    assert val == pytest.approx(1212, abs=1)


def test_compute_paint_weight():
    """ Tests paint weight computation from sample XML data """
    input_list = [
        "data:geometry:aircraft:wetted_area",
        "tuning:weight:airframe:paint:mass:k",
        "tuning:weight:airframe:paint:mass:offset",
    ]
    ivc = get_indep_var_comp(input_list)
    problem = run_system(PaintWeight(), ivc)

    val = problem["data:weight:airframe:paint:mass"]
    assert val == pytest.approx(141.1, abs=0.1)


def test_compute_engine_weight():
    """ Tests engine weight computation from sample XML data """
    input_list = [
        "data:propulsion:MTO_thrust",
        "data:geometry:propulsion:engine:count",
        "tuning:weight:propulsion:engine:mass:k",
        "tuning:weight:propulsion:engine:mass:offset",
    ]
    ivc = get_indep_var_comp(input_list)
    problem = run_system(EngineWeight(), ivc)

    val = problem["data:weight:propulsion:engine:mass"]
    assert val == pytest.approx(7161, abs=1)


def test_compute_fuel_lines_weight():
    """ Tests fuel lines weight computation from sample XML data """
    input_list = [
        "data:geometry:wing:b_50",
        "data:weight:aircraft:MFW",
        "tuning:weight:propulsion:fuel_lines:mass:k",
        "tuning:weight:propulsion:fuel_lines:mass:offset",
    ]
    ivc = get_indep_var_comp(input_list)
    ivc.add_output("data:weight:propulsion:engine:mass", 7161.33, units="kg")
    problem = run_system(FuelLinesWeight(), ivc)

    val = problem["data:weight:propulsion:fuel_lines:mass"]
    assert val == pytest.approx(457, abs=1)


def test_compute_unconsumables_weight():
    """ Tests "unconsumables" weight computation from sample XML data """
    input_list = [
        "data:geometry:propulsion:engine:count",
        "data:weight:aircraft:MFW",
        "tuning:weight:propulsion:unconsumables:mass:k",
        "tuning:weight:propulsion:unconsumables:mass:offset",
    ]
    ivc = get_indep_var_comp(input_list)
    problem = run_system(UnconsumablesWeight(), ivc)

    val = problem["data:weight:propulsion:unconsumables:mass"]
    assert val == pytest.approx(122, abs=1)


def test_compute_power_systems_weight():
    """ Tests power systems weight computation from sample XML data """
    input_list = [
        "data:weight:aircraft:MTOW",
        "tuning:weight:systems:power:auxiliary_power_unit:mass:k",
        "tuning:weight:systems:power:auxiliary_power_unit:mass:offset",
        "tuning:weight:systems:power:electric_systems:mass:k",
        "tuning:weight:systems:power:electric_systems:mass:offset",
        "tuning:weight:systems:power:hydraulic_systems:mass:k",
        "tuning:weight:systems:power:hydraulic_systems:mass:offset",
        "settings:weight:systems:power:mass:k_elec",
    ]
    ivc = get_indep_var_comp(input_list)
    ivc.add_output("data:geometry:cabin:NPAX1", 150)
    ivc.add_output("data:weight:airframe:flight_controls:mass", 700, units="kg")
    problem = run_system(PowerSystemsWeight(), ivc)

    val1 = problem["data:weight:systems:power:auxiliary_power_unit:mass"]
    val2 = problem["data:weight:systems:power:electric_systems:mass"]
    val3 = problem["data:weight:systems:power:hydraulic_systems:mass"]
    assert val1 == pytest.approx(279, abs=1)
    assert val2 == pytest.approx(1297, abs=1)
    assert val3 == pytest.approx(747, abs=1)


def test_compute_life_support_systems_weight():
    """ Tests life support systems weight computation from sample XML data """
    input_list = [
        "data:TLAR:range",
        "data:geometry:fuselage:maximum_width",
        "data:geometry:fuselage:maximum_height",
        "data:geometry:cabin:length",
        "data:geometry:wing:sweep_0",
        "data:geometry:propulsion:nacelle:diameter",
        "data:geometry:propulsion:engine:count",
        "data:geometry:cabin:crew_count:technical",
        "data:geometry:cabin:crew_count:commercial",
        "data:geometry:wing:span",
        "tuning:weight:systems:life_support:insulation:mass:k",
        "tuning:weight:systems:life_support:insulation:mass:offset",
        "tuning:weight:systems:life_support:air_conditioning:mass:k",
        "tuning:weight:systems:life_support:air_conditioning:mass:offset",
        "tuning:weight:systems:life_support:de-icing:mass:k",
        "tuning:weight:systems:life_support:de-icing:mass:offset",
        "tuning:weight:systems:life_support:cabin_lighting:mass:k",
        "tuning:weight:systems:life_support:cabin_lighting:mass:offset",
        "tuning:weight:systems:life_support:seats_crew_accommodation:mass:k",
        "tuning:weight:systems:life_support:seats_crew_accommodation:mass:offset",
        "tuning:weight:systems:life_support:oxygen:mass:k",
        "tuning:weight:systems:life_support:oxygen:mass:offset",
        "tuning:weight:systems:life_support:safety_equipment:mass:k",
        "tuning:weight:systems:life_support:safety_equipment:mass:offset",
    ]
    ivc = get_indep_var_comp(input_list)
    ivc.add_output("data:geometry:cabin:NPAX1", 150)
    ivc.add_output("data:weight:propulsion:engine:mass", 7161.33, units="kg")
    problem = run_system(LifeSupportSystemsWeight(), ivc)

    val1 = problem["data:weight:systems:life_support:insulation:mass"]
    val2 = problem["data:weight:systems:life_support:air_conditioning:mass"]
    val3 = problem["data:weight:systems:life_support:de-icing:mass"]
    val4 = problem["data:weight:systems:life_support:cabin_lighting:mass"]
    val5 = problem["data:weight:systems:life_support:seats_crew_accommodation:mass"]
    val6 = problem["data:weight:systems:life_support:oxygen:mass"]
    val7 = problem["data:weight:systems:life_support:safety_equipment:mass"]
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
        "data:geometry:fuselage:length",
        "data:geometry:wing:b_50",
        "tuning:weight:systems:navigation:mass:k",
        "tuning:weight:systems:navigation:mass:offset",
    ]
    component = NavigationSystemsWeight()

    ivc = get_indep_var_comp(input_list)
    ivc.add_output("data:TLAR:range", 2000.0, units="km")
    problem = run_system(component, ivc)
    assert problem["data:weight:systems:navigation:mass"] == pytest.approx(193, abs=1)

    ivc = get_indep_var_comp(input_list)
    ivc.add_output("data:TLAR:range", 2000.0, units="NM")
    problem = run_system(component, ivc)
    assert problem["data:weight:systems:navigation:mass"] == pytest.approx(493, abs=1)

    ivc = get_indep_var_comp(input_list)
    ivc.add_output("data:TLAR:range", 4000.0, units="NM")
    problem = run_system(component, ivc)
    assert problem["data:weight:systems:navigation:mass"] == pytest.approx(743, abs=1)

    ivc = get_indep_var_comp(input_list)
    ivc.add_output("data:TLAR:range", 5000.0, units="NM")
    problem = run_system(component, ivc)
    assert problem["data:weight:systems:navigation:mass"] == pytest.approx(843, abs=1)

    ivc = get_indep_var_comp(input_list)
    ivc.add_output("data:TLAR:range", 8000.0, units="NM")
    problem = run_system(component, ivc)
    assert problem["data:weight:systems:navigation:mass"] == pytest.approx(843, abs=1)


def test_compute_transmissions_systems_weight():
    """ Tests transmissions weight computation from sample XML data """
    input_list = [
        "tuning:weight:systems:transmission:mass:k",
        "tuning:weight:systems:transmission:mass:offset",
    ]

    component = TransmissionSystemsWeight()

    ivc = get_indep_var_comp(input_list)
    ivc.add_output("data:TLAR:range", 2000.0, units="km")
    problem = run_system(component, ivc)
    assert problem["data:weight:systems:transmission:mass"] == pytest.approx(100, abs=1)

    ivc = get_indep_var_comp(input_list)
    ivc.add_output("data:TLAR:range", 2000.0, units="NM")
    problem = run_system(component, ivc)
    assert problem["data:weight:systems:transmission:mass"] == pytest.approx(200, abs=1)

    ivc = get_indep_var_comp(input_list)
    ivc.add_output("data:TLAR:range", 4000.0, units="NM")
    problem = run_system(component, ivc)
    assert problem["data:weight:systems:transmission:mass"] == pytest.approx(250, abs=1)

    ivc = get_indep_var_comp(input_list)
    ivc.add_output("data:TLAR:range", 5000.0, units="NM")
    problem = run_system(component, ivc)
    assert problem["data:weight:systems:transmission:mass"] == pytest.approx(350, abs=1)

    ivc = get_indep_var_comp(input_list)
    ivc.add_output("data:TLAR:range", 8000.0, units="NM")
    problem = run_system(component, ivc)
    assert problem["data:weight:systems:transmission:mass"] == pytest.approx(350, abs=1)


def test_compute_fixed_operational_systems_weight():
    """
    Tests fixed operational systems weight computation from sample XML data
    """
    input_list = [
        "data:geometry:fuselage:front_length",
        "data:geometry:fuselage:rear_length",
        "data:geometry:fuselage:length",
        "data:geometry:cabin:seats:economical:count_by_row",
        "data:geometry:wing:root:chord",
        "data:geometry:cabin:containers:count_by_row",
        "tuning:weight:systems:operational:mass:k",
        "tuning:weight:systems:operational:mass:offset",
    ]

    ivc = get_indep_var_comp(input_list)
    problem = run_system(FixedOperationalSystemsWeight(), ivc)

    val1 = problem["data:weight:systems:operational:radar:mass"]
    val2 = problem["data:weight:systems:operational:cargo_hold:mass"]
    assert val1 == pytest.approx(100, abs=1)
    assert val2 == pytest.approx(277, abs=1)


def test_compute_flight_kit_weight():
    """ Tests flight kit weight computation from sample XML data """
    input_list = [
        "tuning:weight:systems:flight_kit:mass:k",
        "tuning:weight:systems:flight_kit:mass:offset",
    ]
    component = FlightKitWeight()

    ivc = get_indep_var_comp(input_list)
    ivc.add_output("data:TLAR:range", 2000.0, units="km")
    problem = run_system(component, ivc)
    assert problem["data:weight:systems:flight_kit:mass"] == pytest.approx(10, abs=1)

    ivc = get_indep_var_comp(input_list)
    ivc.add_output("data:TLAR:range", 2000.0, units="NM")
    problem = run_system(component, ivc)
    assert problem["data:weight:systems:flight_kit:mass"] == pytest.approx(45, abs=1)


def test_compute_cargo_configuration_weight():
    """ Tests cargo configuration weight computation from sample XML data """
    input_list = [
        "data:geometry:cabin:containers:count",
        "data:geometry:cabin:pallet_count",
        "data:geometry:cabin:seats:economical:count_by_row",
        "tuning:weight:furniture:cargo_configuration:mass:k",
        "tuning:weight:furniture:cargo_configuration:mass:offset",
    ]
    component = CargoConfigurationWeight()

    ivc = get_indep_var_comp(input_list)
    ivc.add_output("data:geometry:cabin:NPAX1", 150)
    problem = run_system(component, ivc)
    val = problem["data:weight:furniture:cargo_configuration:mass"]
    assert val == pytest.approx(39.3, abs=0.1)


def test_compute_passenger_seats_weight():
    """ Tests passenger seats weight computation from sample XML data """
    input_list = [
        "data:TLAR:range",
        "data:TLAR:NPAX",
        "tuning:weight:furniture:passenger_seats:mass:k",
        "tuning:weight:furniture:passenger_seats:mass:offset",
    ]

    ivc = get_indep_var_comp(input_list)
    component = PassengerSeatsWeight()

    problem = run_system(component, ivc)
    val = problem["data:weight:furniture:passenger_seats:mass"]
    assert val == pytest.approx(1500, abs=1)


def test_compute_food_water_weight():
    """ Tests food water weight computation from sample XML data """
    input_list = [
        "data:TLAR:range",
        "data:TLAR:NPAX",
        "tuning:weight:furniture:food_water:mass:k",
        "tuning:weight:furniture:food_water:mass:offset",
    ]

    ivc = get_indep_var_comp(input_list)
    component = FoodWaterWeight()

    problem = run_system(component, ivc)
    val = problem["data:weight:furniture:food_water:mass"]
    assert val == pytest.approx(1312, abs=1)


def test_compute_security_kit_weight():
    """ Tests security kit weight computation from sample XML data """
    input_list = [
        "data:TLAR:range",
        "data:TLAR:NPAX",
        "tuning:weight:furniture:security_kit:mass:k",
        "tuning:weight:furniture:security_kit:mass:offset",
    ]

    ivc = get_indep_var_comp(input_list)
    component = SecurityKitWeight()

    problem = run_system(component, ivc)
    val = problem["data:weight:furniture:security_kit:mass"]
    assert val == pytest.approx(225, abs=1)


def test_compute_toilets_weight():
    """ Tests toilets weight computation from sample XML data """
    input_list = [
        "data:TLAR:range",
        "data:TLAR:NPAX",
        "tuning:weight:furniture:toilets:mass:k",
        "tuning:weight:furniture:toilets:mass:offset",
    ]

    ivc = get_indep_var_comp(input_list)
    component = ToiletsWeight()

    problem = run_system(component, ivc)
    val = problem["data:weight:furniture:toilets:mass"]
    assert val == pytest.approx(75, abs=0.1)


def test_compute_crew_weight():
    """ Tests crew weight computation from sample XML data """
    input_list = [
        "data:geometry:cabin:crew_count:technical",
        "data:geometry:cabin:crew_count:commercial",
    ]
    ivc = get_indep_var_comp(input_list)
    problem = run_system(CrewWeight(), ivc)

    val = problem["data:weight:crew:mass"]
    assert val == pytest.approx(470, abs=1)


def test_evaluate_oew():
    """
    Tests a simple evaluation of Operating Empty Weight from sample XML data.
    """
    reader = VariableIO(pth.join(pth.dirname(__file__), "data", "mass_breakdown_inputs.xml"))
    reader.path_separator = ":"
    input_vars = reader.read().to_ivc()

    mass_computation = run_system(OperatingWeightEmpty(), input_vars)

    oew = mass_computation["data:weight:aircraft:OWE"]
    assert oew == pytest.approx(41591, abs=1)


def test_loop_compute_oew():
    """
    Tests a weight computation loop matching the max payload criterion.
    """
    # With payload from npax
    reader = VariableIO(pth.join(pth.dirname(__file__), "data", "mass_breakdown_inputs.xml"))
    reader.path_separator = ":"
    input_vars = reader.read(
        ignore=[
            "data:weight:aircraft:MLW",
            "data:weight:aircraft:MZFW",
            "data:weight:aircraft:max_payload",
        ]
    ).to_ivc()
    mass_computation = run_system(MassBreakdown(), input_vars)
    oew = mass_computation["data:weight:aircraft:OWE"]
    assert oew == pytest.approx(41591, abs=1)

    # with payload as input
    reader = VariableIO(pth.join(pth.dirname(__file__), "data", "mass_breakdown_inputs.xml"))
    reader.path_separator = ":"
    input_vars = reader.read(
        ignore=["data:weight:aircraft:MLW", "data:weight:aircraft:MZFW",]
    ).to_ivc()
    mass_computation = run_system(MassBreakdown(payload_from_npax=False), input_vars)
    oew = mass_computation["data:weight:aircraft:OWE"]
    assert oew == pytest.approx(42060, abs=1)
