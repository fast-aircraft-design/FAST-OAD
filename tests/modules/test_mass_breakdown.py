#!/usr/bin/env python
# -*- coding: utf-8 -*-

#      This file is part of FAST : A framework for rapid Overall Aircraft Design
#      Copyright (C) 2019  ONERA/ISAE
#      FAST is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.
import os.path as pth

import pytest
from openmdao.core.indepvarcomp import IndepVarComp
from openmdao.core.problem import Problem

from fastoad.io.xml import XPathReader
from fastoad.modules.mass_breakdown.cs25 import Loads
from fastoad.modules.mass_breakdown.functions_A import EmpennageWeight, FlightControlsWeight, \
    FuselageWeight, \
    LandingGearWeight, PaintWeight, PylonsWeight, WingWeight
from fastoad.modules.mass_breakdown.functions_B import EngineWeight, FuelLinesWeight, \
    UnconsumablesWeight
from fastoad.modules.mass_breakdown.functions_C import FixedOperationalSystemsWeight, \
    FlightKitWeight, \
    LifeSupportSystemsWeight, NavigationSystemsWeight, PowerSystemsWeight, TransmissionSystemsWeight
from fastoad.modules.mass_breakdown.functions_D import CargoConfigurationWeight, \
    PassengerSeatsWeight, FoodWaterWeight, \
    ToiletsWeight, SecurityKitWeight
from fastoad.modules.mass_breakdown.functions_E import CrewWeight
from fastoad.modules.mass_breakdown.mass_breakdown import MassBreakdown
from fastoad.modules.mass_breakdown.owe import OperatingEmptyWeight


@pytest.fixture(scope="module")
def input_xml():
    return XPathReader(pth.join(pth.dirname(__file__), "data", "A320_baseline.xml"))


def test_compute_loads(input_xml):
    [(lc1_u_gust, _)
        , (lc2_u_gust, _)] = input_xml.get_values_and_units(
        'Aircraft/weight/sizing_cases/SizingCase/U_gust')
    [(lc1_alt, _)
        , (lc1_alt, _)] = input_xml.get_values_and_units(
        'Aircraft/weight/sizing_cases/SizingCase/altitude')
    [(lc1_vc_eas, _)
        , (lc1_vc_eas, _)] = input_xml.get_values_and_units(
        'Aircraft/weight/sizing_cases/SizingCase/Vc_EAS')
    inputs = {
        'geometry:wing_area': input_xml.get_float('Aircraft/geometry/wing/wing_area'),
        'geometry:wing_span': input_xml.get_float('Aircraft/geometry/wing/span'),
        'weight:MZFW': input_xml.get_float('Aircraft/weight/MZFW'),
        'weight:MFW': input_xml.get_float('Aircraft/weight/MFW'),
        'weight:MTOW': input_xml.get_float('Aircraft/weight/MTOW'),
        'aerodynamics:Cl_alpha': input_xml.get_float('Aircraft/aerodynamics/CL_alpha'),
        'loadcase1:U_gust': lc1_u_gust,
        'loadcase1:altitude': lc1_alt,
        'loadcase1:Vc_EAS': lc1_vc_eas,
        'loadcase2:U_gust': lc2_u_gust,
        'loadcase2:altitude': lc1_alt,
        'loadcase2:Vc_EAS': lc1_vc_eas
    }
    component = Loads()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    n1m1 = outputs['n1m1']
    assert n1m1 == pytest.approx(240968, abs=10)
    n2m2 = outputs['n2m2']
    assert n2m2 == pytest.approx(254130, abs=10)


def test_compute_wing_weight(input_xml):
    inputs = {
        'n1m1': 241000,  # output from load computation is expected to be slightly different
        'n2m2': 250000,  # output from load computation is expected to be slightly different
        'geometry:wing_area': input_xml.get_float('Aircraft/geometry/wing/wing_area'),
        'geometry:wing_span': input_xml.get_float('Aircraft/geometry/wing/span'),
        'geometry:wing_toc_root': input_xml.get_float('Aircraft/geometry/wing/toc/root'),
        'geometry:wing_toc_kink': input_xml.get_float('Aircraft/geometry/wing/toc/kink'),
        'geometry:wing_toc_tip': input_xml.get_float('Aircraft/geometry/wing/toc/tip'),
        'geometry:wing_l2': input_xml.get_float('Aircraft/geometry/wing/l2_wing'),
        'geometry:wing_sweep_25': input_xml.get_float('Aircraft/geometry/wing/sweep_25'),
        'geometry:wing_area_pf': input_xml.get_float('Aircraft/geometry/wing/S_pf'),
        'weight:MTOW': input_xml.get_float('Aircraft/weight/MTOW'),
        'weight:MLW': input_xml.get_float('Aircraft/weight/MLW'),
        'kfactors_a1:K_A1': input_xml.get_float('Aircraft/weight/k_factors/Wing_A1/A1/k'),
        'kfactors_a1:offset_A1': input_xml.get_float('Aircraft/weight/k_factors/Wing_A1/A1/offset'),
        'kfactors_a1:K_A11': input_xml.get_float('Aircraft/weight/k_factors/Wing_A1/A11/k'),
        'kfactors_a1:offset_A11': input_xml.get_float(
            'Aircraft/weight/k_factors/Wing_A1/A11/offset'),
        'kfactors_a1:K_A12': input_xml.get_float('Aircraft/weight/k_factors/Wing_A1/A12/k'),
        'kfactors_a1:offset_A12': input_xml.get_float(
            'Aircraft/weight/k_factors/Wing_A1/A12/offset'),
        'kfactors_a1:K_A13': input_xml.get_float('Aircraft/weight/k_factors/Wing_A1/A13/k'),
        'kfactors_a1:offset_A13': input_xml.get_float(
            'Aircraft/weight/k_factors/Wing_A1/A13/offset'),
        'kfactors_a1:K_A14': input_xml.get_float('Aircraft/weight/k_factors/Wing_A1/A14/k'),
        'kfactors_a1:offset_A14': input_xml.get_float(
            'Aircraft/weight/k_factors/Wing_A1/A14/offset'),
        'kfactors_a1:K_A15': input_xml.get_float('Aircraft/weight/k_factors/Wing_A1/A15/k'),
        'kfactors_a1:offset_A15': input_xml.get_float(
            'Aircraft/weight/k_factors/Wing_A1/A15/offset'),
        'kfactors_a1:K_voil': input_xml.get_float('Aircraft/weight/k_factors/Wing_A1/K_voil'),
        'kfactors_a1:K_mvo': input_xml.get_float('Aircraft/weight/k_factors/Wing_A1/K_mvo'),
    }
    component = WingWeight()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    val = outputs['weight_airframe:A1']
    assert val == pytest.approx(7681, abs=1)


def test_compute_fuselage_weight(input_xml):
    inputs = {
        'n1m1': 241000,  # output from load computation is expected to be slightly different
        'geometry:fuselage_wet_area': input_xml.get_float('Aircraft/geometry/fuselage/S_mbf'),
        'geometry:fuselage_width_max': input_xml.get_float('Aircraft/geometry/fuselage/width_max'),
        'geometry:fuselage_height_max': input_xml.get_float(
            'Aircraft/geometry/fuselage/height_max'),
        'kfactors_a2:K_A2': input_xml.get_float('Aircraft/weight/k_factors/fuselage_A2/A2/k'),
        'kfactors_a2:offset_A2': input_xml.get_float(
            'Aircraft/weight/k_factors/fuselage_A2/A2/offset'),
        'kfactors_a2:K_tr': input_xml.get_float('Aircraft/weight/k_factors/fuselage_A2/K_tr'),
        'kfactors_a2:K_fus': input_xml.get_float('Aircraft/weight/k_factors/fuselage_A2/K_fus'),
    }
    component = FuselageWeight()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    val = outputs['weight_airframe:A2']
    assert val == pytest.approx(8828, abs=1)


def test_compute_empennage_weight(input_xml):
    inputs = {
        'geometry:ht_area': input_xml.get_float('Aircraft/geometry/ht/area'),
        'geometry:vt_area': input_xml.get_float('Aircraft/geometry/vt/area'),
        'kfactors_a3:K_A31': input_xml.get_float('Aircraft/weight/k_factors/empennage_A3/A31/k'),
        'kfactors_a3:offset_A31': input_xml.get_float(
            'Aircraft/weight/k_factors/empennage_A3/A31/offset'),
        'kfactors_a3:K_A32': input_xml.get_float('Aircraft/weight/k_factors/empennage_A3/A32/k'),
        'kfactors_a3:offset_A32': input_xml.get_float(
            'Aircraft/weight/k_factors/empennage_A3/A32/offset'),
    }
    component = EmpennageWeight()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    val1 = outputs['weight_airframe:A31']
    val2 = outputs['weight_airframe:A32']
    assert val1 == pytest.approx(754, abs=1)
    assert val2 == pytest.approx(515, abs=1)


def test_compute_flight_controls_weight(input_xml):
    inputs = {
        # Flight Control Weight ----------------------------------------------------------------------------------------
        'n1m1': 241000,  # output from load computation is expected to be slightly different
        'n2m2': 250000,  # output from load computation is expected to be slightly different
        'geometry:fuselage_length': input_xml.get_float('Aircraft/geometry/fuselage/fus_length'),
        'geometry:wing_b_50': input_xml.get_float('Aircraft/geometry/wing/b_50'),
        'kfactors_a4:K_A4': input_xml.get_float(
            'Aircraft/weight/k_factors/flight_controls_A4/A4/k'),
        'kfactors_a4:offset_A4': input_xml.get_float(
            'Aircraft/weight/k_factors/flight_controls_A4/A4/offset'),
        'kfactors_a4:K_fc': input_xml.get_float(
            'Aircraft/weight/k_factors/flight_controls_A4/K_fc'),
    }
    component = FlightControlsWeight()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    val = outputs['weight_airframe:A4']
    assert val == pytest.approx(716, abs=1)


def test_compute_landing_gear_weight(input_xml):
    inputs = {
        # Landing Gear Weight ------------------------------------------------------------------------------------------
        'weight:MTOW': input_xml.get_float('Aircraft/weight/MTOW'),
        'kfactors_a5:K_A5': input_xml.get_float('Aircraft/weight/k_factors/LG_A5/A5/k'),
        'kfactors_a5:offset_A5': input_xml.get_float('Aircraft/weight/k_factors/LG_A5/A5/offset'),
    }
    component = LandingGearWeight()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    val1 = outputs['weight_airframe:A51']
    val2 = outputs['weight_airframe:A52']
    assert val1 == pytest.approx(2144, abs=1)
    assert val2 == pytest.approx(379, abs=1)


def test_compute_pylons_weight(input_xml):
    inputs = {
        # Pylon Weight -------------------------------------------------------------------------------------------------
        'geometry:pylon_wet_area': input_xml.get_float(
            'Aircraft/geometry/propulsion/wet_area_pylon'),
        'geometry:engine_number': input_xml.get_float('Aircraft/geometry/propulsion/engine_number'),
        'weight_propulsion:B1': input_xml.get_float('Aircraft/weight/propulsion/weight_B1'),
        'kfactors_a6:K_A6': input_xml.get_float('Aircraft/weight/k_factors/pylon_A6/A6/k'),
        'kfactors_a6:offset_A6': input_xml.get_float(
            'Aircraft/weight/k_factors/pylon_A6/A6/offset'),
    }
    component = PylonsWeight()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    val = outputs['weight_airframe:A6']
    assert val == pytest.approx(1212, abs=1)


def test_compute_paint_weight(input_xml):
    inputs = {
        'geometry:S_total': input_xml.get_float('Aircraft/geometry/S_total'),
        'kfactors_a7:K_A7': input_xml.get_float('Aircraft/weight/k_factors/paint_A7/A7/k'),
        'kfactors_a7:offset_A7': input_xml.get_float(
            'Aircraft/weight/k_factors/paint_A7/A7/offset'),
    }
    component = PaintWeight()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    val = outputs['weight_airframe:A7']
    assert val == pytest.approx(141.1, abs=0.1)


def test_compute_engine_weight(input_xml):
    inputs = {
        'propulsion_conventional:thrust_SL': input_xml.get_float(
            'Aircraft/propulsion/conventional/thrust_SL'),
        'geometry:engine_number': input_xml.get_float('Aircraft/geometry/propulsion/engine_number'),
        'kfactors_b1:K_B1': input_xml.get_float('Aircraft/weight/k_factors/propulsion_B1/B1/k'),
        'kfactors_b1:offset_B1': input_xml.get_float(
            'Aircraft/weight/k_factors/propulsion_B1/B1/offset'),
    }
    component = EngineWeight()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    val = outputs['weight_propulsion:B1']
    assert val == pytest.approx(7161, abs=1)


def test_compute_fuel_lines_weight(input_xml):
    inputs = {
        'geometry:wing_b_50': input_xml.get_float('Aircraft/geometry/wing/b_50'),
        'weight:MFW': input_xml.get_float('Aircraft/weight/MFW'),
        'weight_propulsion:B1': input_xml.get_float('Aircraft/weight/propulsion/weight_B1'),
        'kfactors_b2:K_B2': input_xml.get_float('Aircraft/weight/k_factors/fuel_lines_B2/B2/k'),
        'kfactors_b2:offset_B2': input_xml.get_float(
            'Aircraft/weight/k_factors/fuel_lines_B2/B2/offset'),
    }
    component = FuelLinesWeight()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    val = outputs['weight_propulsion:B2']
    assert val == pytest.approx(457, abs=1)


def test_compute_unconsumables_weight(input_xml):
    inputs = {
        'geometry:engine_number': input_xml.get_float('Aircraft/geometry/propulsion/engine_number'),
        'weight:MFW': input_xml.get_float('Aircraft/weight/MFW'),
        'kfactors_b3:K_B3': input_xml.get_float('Aircraft/weight/k_factors/unconsumables_B3/B3/k'),
        'kfactors_b3:offset_B3': input_xml.get_float(
            'Aircraft/weight/k_factors/unconsumables_B3/B3/offset'),
    }
    component = UnconsumablesWeight()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    val = outputs['weight_propulsion:B3']
    assert val == pytest.approx(122, abs=1)


def test_compute_power_systems_weight(input_xml):
    inputs = {
        # Power Systems Weight -----------------------------------------------------------------------------------------
        'cabin:NPAX1': 150,  # input_xml.get_float('Aircraft/cabin/NPAX1'),
        'weight_airframe:A4': 700,
        'weight:MTOW': input_xml.get_float('Aircraft/weight/MTOW'),
        'kfactors_c1:K_C11': input_xml.get_float(
            'Aircraft/weight/k_factors/power_systems_C1/C11/k'),
        'kfactors_c1:offset_C11': input_xml.get_float(
            'Aircraft/weight/k_factors/power_systems_C1/C11/offset'),
        'kfactors_c1:K_C12': input_xml.get_float(
            'Aircraft/weight/k_factors/power_systems_C1/C12/k'),
        'kfactors_c1:offset_C12': input_xml.get_float(
            'Aircraft/weight/k_factors/power_systems_C1/C12/offset'),
        'kfactors_c1:K_C13': input_xml.get_float(
            'Aircraft/weight/k_factors/power_systems_C1/C13/k'),
        'kfactors_c1:offset_C13': input_xml.get_float(
            'Aircraft/weight/k_factors/power_systems_C1/C13/offset'),
        'kfactors_c1:K_elec': input_xml.get_float(
            'Aircraft/weight/k_factors/power_systems_C1/K_elec'),
    }
    component = PowerSystemsWeight()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    val1 = outputs['weight_systems:C11']
    val2 = outputs['weight_systems:C12']
    val3 = outputs['weight_systems:C13']
    assert val1 == pytest.approx(279, abs=1)
    assert val2 == pytest.approx(1297, abs=1)
    assert val3 == pytest.approx(747, abs=1)


def test_compute_life_support_systems_weight(input_xml):
    inputs = {
        # Life Support Systems Weight ----------------------------------------------------------------------------------
        'geometry:fuselage_width_max': input_xml.get_float('Aircraft/geometry/fuselage/width_max'),
        'geometry:fuselage_height_max': input_xml.get_float(
            'Aircraft/geometry/fuselage/height_max'),
        'geometry:fuselage_Lcabin': 0.8 * input_xml.get_float(
            'Aircraft/geometry/fuselage/fus_length'),
        'geometry:wing_sweep_0': input_xml.get_float('Aircraft/geometry/wing/sweep_0'),
        'geometry:nacelle_dia': input_xml.get_float('Aircraft/geometry/propulsion/nacelle_dia'),
        'geometry:engine_number': input_xml.get_float('Aircraft/geometry/propulsion/engine_number'),
        'cabin:NPAX1': 150,  # input_xml.get_float('Aircraft/cabin/NPAX1'),
        'cabin:PNT': input_xml.get_float('Aircraft/cabin/PNT'),
        'cabin:PNC': input_xml.get_float('Aircraft/cabin/PNC'),
        'geometry:wing_span': input_xml.get_float('Aircraft/geometry/wing/span'),
        'weight_propulsion:B1': input_xml.get_float('Aircraft/weight/propulsion/weight_B1'),
        'kfactors_c2:K_C21': input_xml.get_float('Aircraft/weight/k_factors/LSS_C2/C21/k'),
        'kfactors_c2:offset_C21': input_xml.get_float(
            'Aircraft/weight/k_factors/LSS_C2/C21/offset'),
        'kfactors_c2:K_C22': input_xml.get_float('Aircraft/weight/k_factors/LSS_C2/C22/k'),
        'kfactors_c2:offset_C22': input_xml.get_float(
            'Aircraft/weight/k_factors/LSS_C2/C22/offset'),
        'kfactors_c2:K_C23': input_xml.get_float('Aircraft/weight/k_factors/LSS_C2/C23/k'),
        'kfactors_c2:offset_C23': input_xml.get_float(
            'Aircraft/weight/k_factors/LSS_C2/C23/offset'),
        'kfactors_c2:K_C24': input_xml.get_float('Aircraft/weight/k_factors/LSS_C2/C24/k'),
        'kfactors_c2:offset_C24': input_xml.get_float(
            'Aircraft/weight/k_factors/LSS_C2/C24/offset'),
        'kfactors_c2:K_C25': input_xml.get_float('Aircraft/weight/k_factors/LSS_C2/C25/k'),
        'kfactors_c2:offset_C25': input_xml.get_float(
            'Aircraft/weight/k_factors/LSS_C2/C25/offset'),
        'kfactors_c2:K_C26': input_xml.get_float('Aircraft/weight/k_factors/LSS_C2/C26/k'),
        'kfactors_c2:offset_C26': input_xml.get_float(
            'Aircraft/weight/k_factors/LSS_C2/C26/offset'),
        'kfactors_c2:K_C27': input_xml.get_float('Aircraft/weight/k_factors/LSS_C2/C27/k'),
        'kfactors_c2:offset_C27': input_xml.get_float(
            'Aircraft/weight/k_factors/LSS_C2/C27/offset'),
    }
    component = LifeSupportSystemsWeight()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    val1 = outputs['weight_systems:C21']
    val2 = outputs['weight_systems:C22']
    val3 = outputs['weight_systems:C23']
    val4 = outputs['weight_systems:C24']
    val5 = outputs['weight_systems:C25']
    val6 = outputs['weight_systems:C26']
    val7 = outputs['weight_systems:C27']
    assert val1 == pytest.approx(2226, abs=1)
    assert val2 == pytest.approx(920, abs=1)
    assert val3 == pytest.approx(154, abs=1)
    assert val4 == pytest.approx(168, abs=1)
    assert val5 == pytest.approx(126, abs=1)
    assert val6 == pytest.approx(275, abs=1)
    assert val7 == pytest.approx(416, abs=1)


def test_compute_navigation_systems_weight(input_xml):
    inputs = {
        'geometry:fuselage_length': input_xml.get_float('Aircraft/geometry/fuselage/fus_length'),
        'geometry:wing_b_50': input_xml.get_float('Aircraft/geometry/wing/b_50'),
        'kfactors_c3:K_C3': input_xml.get_float(
            'Aircraft/weight/k_factors/instrument_navigation_C3/C3/k'),
        'kfactors_c3:offset_C3': input_xml.get_float(
            'Aircraft/weight/k_factors/instrument_navigation_C3/C3/offset'),
    }
    component = NavigationSystemsWeight()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    val = outputs['weight_systems:C3']
    assert val == pytest.approx(493, abs=1)


def test_compute_transmissions_systems_weight(input_xml):
    inputs = {
        'kfactors_c4:K_C4': input_xml.get_float('Aircraft/weight/k_factors/transmissions_C4/C4/k'),
        'kfactors_c4:offset_C4': input_xml.get_float(
            'Aircraft/weight/k_factors/transmissions_C4/C4/offset'),
    }
    component = TransmissionSystemsWeight()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    val = outputs['weight_systems:C4']
    assert val == pytest.approx(200, abs=1)


def test_compute_fixed_operational_systems_weight(input_xml):
    inputs = {
        'geometry:fuselage_LAV': input_xml.get_float('Aircraft/geometry/fuselage/LAV'),
        'geometry:fuselage_LAR': input_xml.get_float('Aircraft/geometry/fuselage/LAR'),
        'geometry:fuselage_length': input_xml.get_float('Aircraft/geometry/fuselage/fus_length'),
        'cabin:front_seat_number_eco': input_xml.get_float('Aircraft/cabin/eco/front_seat_number'),
        'geometry:wing_l2': input_xml.get_float('Aircraft/geometry/wing/l2_wing'),
        'cabin:container_number_front': input_xml.get_float(
            'Aircraft/cabin/container_number_front'),
        'kfactors_c5:K_C5': input_xml.get_float('Aircraft/weight/k_factors/FOS_C5/C5/k'),
        'kfactors_c5:offset_C5': input_xml.get_float('Aircraft/weight/k_factors/FOS_C5/C5/offset'),
    }
    component = FixedOperationalSystemsWeight()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    val1 = outputs['weight_systems:C51']
    val2 = outputs['weight_systems:C52']
    assert val1 == pytest.approx(100, abs=1)
    assert val2 == pytest.approx(277, abs=1)


def test_compute_flight_kit_weight(input_xml):
    inputs = {
        'kfactors_c6:K_C6': input_xml.get_float('Aircraft/weight/k_factors/flight_kit_C6/C6/k'),
        'kfactors_c6:offset_C6': input_xml.get_float(
            'Aircraft/weight/k_factors/flight_kit_C6/C6/offset'),
    }
    component = FlightKitWeight()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    val = outputs['weight_systems:C6']
    assert val == pytest.approx(45, abs=0.1)


def test_compute_cargo_configuration_weight(input_xml):
    inputs = {
        'cabin:NPAX1': 150,  # input_xml.get_float('Aircraft/cabin/NPAX1'),
        'cabin:container_number': input_xml.get_float('Aircraft/cabin/container_number'),
        'cabin:pallet_number': input_xml.get_float('Aircraft/cabin/pallet_number'),
        'cabin:front_seat_number_eco': input_xml.get_float('Aircraft/cabin/eco/front_seat_number'),
        'kfactors_d1:K_D1': input_xml.get_float('Aircraft/weight/k_factors/cargo_cfg_D1/D1/k'),
        'kfactors_d1:offset_D1': input_xml.get_float(
            'Aircraft/weight/k_factors/cargo_cfg_D1/D1/offset'),
    }
    component = CargoConfigurationWeight()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    val = outputs['weight_furniture:D1']
    assert val == 0.

    component = CargoConfigurationWeight(ac_type=6.)
    component.setup()
    component.compute(inputs, outputs)
    val = outputs['weight_furniture:D1']
    assert val == pytest.approx(39.3, abs=0.1)


def test_compute_passenger_seats_weight(input_xml):
    inputs = {
        'tlar:NPAX': input_xml.get_float('Aircraft/TLAR/NPAX'),
        'kfactors_d2:K_D2': input_xml.get_float('Aircraft/weight/k_factors/passenger_seat_D2/D2/k'),
        'kfactors_d2:offset_D2': input_xml.get_float(
            'Aircraft/weight/k_factors/passenger_seat_D2/D2/offset'),
    }
    component = PassengerSeatsWeight()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    val = outputs['weight_furniture:D2']
    assert val == pytest.approx(1500, abs=1)

    component = PassengerSeatsWeight(ac_type=6.)
    component.setup()
    component.compute(inputs, outputs)
    val = outputs['weight_furniture:D2']
    assert val == 0.


def test_compute_food_water_weight(input_xml):
    inputs = {
        'tlar:NPAX': input_xml.get_float('Aircraft/TLAR/NPAX'),
        'kfactors_d3:K_D3': input_xml.get_float('Aircraft/weight/k_factors/food_water_D3/D3/k'),
        'kfactors_d3:offset_D3': input_xml.get_float(
            'Aircraft/weight/k_factors/food_water_D3/D3/offset'),
    }
    component = FoodWaterWeight()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    val = outputs['weight_furniture:D3']
    assert val == pytest.approx(1312, abs=1)

    component = FoodWaterWeight(ac_type=6.)
    component.setup()
    component.compute(inputs, outputs)
    val = outputs['weight_furniture:D3']
    assert val == 0.


def test_compute_security_kit_weight(input_xml):
    inputs = {
        'tlar:NPAX': input_xml.get_float('Aircraft/TLAR/NPAX'),
        'kfactors_d4:K_D4': input_xml.get_float('Aircraft/weight/k_factors/security_kit_D4/D4/k'),
        'kfactors_d4:offset_D4': input_xml.get_float(
            'Aircraft/weight/k_factors/security_kit_D4/D4/offset'),
    }
    component = SecurityKitWeight()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    val = outputs['weight_furniture:D4']
    assert val == pytest.approx(225, abs=1)

    component = SecurityKitWeight(ac_type=6.)
    component.setup()
    component.compute(inputs, outputs)
    val = outputs['weight_furniture:D4']
    assert val == 0.


def test_compute_toilets_weight(input_xml):
    inputs = {
        'tlar:NPAX': input_xml.get_float('Aircraft/TLAR/NPAX'),
        'kfactors_d5:K_D5': input_xml.get_float('Aircraft/weight/k_factors/toilet_D5/D5/k'),
        'kfactors_d5:offset_D5': input_xml.get_float(
            'Aircraft/weight/k_factors/toilet_D5/D5/offset'),
    }
    component = ToiletsWeight()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    val = outputs['weight_furniture:D5']
    assert val == pytest.approx(75, abs=0.1)

    component = ToiletsWeight(ac_type=6.)
    component.setup()
    component.compute(inputs, outputs)
    val = outputs['weight_furniture:D5']
    assert val == 0.


def test_compute_crew_weight(input_xml):
    inputs = {
        'cabin:PNT': input_xml.get_float('Aircraft/cabin/PNT'),
        'cabin:PNC': input_xml.get_float('Aircraft/cabin/PNC'),
    }
    component = CrewWeight()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    val = outputs['weight_crew:E']
    assert val == pytest.approx(470, abs=1)


def test_compute_weights(input_xml):
    ivc = IndepVarComp()
    inputs = __get_all_inputs(input_xml)
    for key, value in inputs.items():
        ivc.add_output(key, value)

    mass_computation = Problem()
    model = mass_computation.model
    model.add_subsystem('design_variables', ivc, promotes=['*'])
    model.add_subsystem('compute_oew', OperatingEmptyWeight(), promotes=['*'])

    mass_computation.setup(mode='fwd')
    mass_computation.run_model()

    oew = mass_computation['weight:OEW']
    assert oew == pytest.approx(41591, abs=1)


def test_compute(input_xml):
    ivc = IndepVarComp()
    inputs = __get_all_inputs(input_xml)

    # Keep initial values
    init = {k: inputs[k] for k in ('weight:MZFW', 'weight:MLW') if k in inputs}

    # Modification of inputs for looping problem
    del inputs['weight:MZFW']
    del inputs['weight:MLW']
    inputs['weight:Max_PL'] = input_xml.get_float('Aircraft/weight/Max_PL')

    for key, value in inputs.items():
        ivc.add_output(key, value)

    mass_computation = Problem()
    model = mass_computation.model
    model.add_subsystem('design_variables', ivc, promotes=['*'])
    model.add_subsystem('mass_breakdown', MassBreakdown(), promotes=['*'])

    mass_computation.setup()

    # for key, value in init.items():
    #     mass_computation[key] = value
    mass_computation.run_model()

    oew = mass_computation['weight:OEW']
    assert oew == pytest.approx(42060, abs=1)

    # owe = self.mass_breakdown.compute()
    # self.assertAlmostEqual(owe, 42024, delta=10)


def __get_all_inputs(input_xml):
    [(lc1_u_gust, _)
        , (lc2_u_gust, _)] = input_xml.get_values_and_units(
        'Aircraft/weight/sizing_cases/SizingCase/U_gust')
    [(lc1_alt, _)
        , (lc1_alt, _)] = input_xml.get_values_and_units(
        'Aircraft/weight/sizing_cases/SizingCase/altitude')
    [(lc1_vc_eas, _)
        , (lc1_vc_eas, _)] = input_xml.get_values_and_units(
        'Aircraft/weight/sizing_cases/SizingCase/Vc_EAS')

    inputs = {
        # Multiple use values ------------------------------------------------------------------------------------------
        # When these values are used in next "sections", they are commented out
        'tlar:NPAX': input_xml.get_float('Aircraft/TLAR/NPAX'),
        'geometry:wing_area': input_xml.get_float('Aircraft/geometry/wing/wing_area'),
        'geometry:wing_span': input_xml.get_float('Aircraft/geometry/wing/span'),
        'geometry:wing_b_50': input_xml.get_float('Aircraft/geometry/wing/b_50'),
        'geometry:wing_l2': input_xml.get_float('Aircraft/geometry/wing/l2_wing'),
        'geometry:fuselage_length': input_xml.get_float('Aircraft/geometry/fuselage/fus_length'),
        'geometry:fuselage_width_max': input_xml.get_float('Aircraft/geometry/fuselage/width_max'),
        'geometry:fuselage_height_max': input_xml.get_float(
            'Aircraft/geometry/fuselage/height_max'),
        'geometry:engine_number': input_xml.get_float('Aircraft/geometry/propulsion/engine_number'),
        'weight:MTOW': input_xml.get_float('Aircraft/weight/MTOW'),
        'weight:MFW': input_xml.get_float('Aircraft/weight/MFW'),
        'cabin:NPAX1': int(input_xml.get_float('Aircraft/TLAR/NPAX') * 1.05),
        'cabin:PNT': input_xml.get_float('Aircraft/cabin/PNT'),
        'cabin:PNC': input_xml.get_float('Aircraft/cabin/PNC'),
        'cabin:front_seat_number_eco': input_xml.get_float('Aircraft/cabin/eco/front_seat_number'),
        # Load cases ---------------------------------------------------------------------------------------------------
        # 'geometry:wing_area': input_xml.get_float('Aircraft/geometry/wing/wing_area'),
        # 'geometry:wing_span': input_xml.get_float('Aircraft/geometry/wing/span'),
        'weight:MZFW': input_xml.get_float('Aircraft/weight/MZFW'),
        # 'weight:MFW': input_xml.get_float('Aircraft/weight/MFW'),
        # 'weight:MTOW': input_xml.get_float('Aircraft/weight/MTOW'),
        'aerodynamics:Cl_alpha': input_xml.get_float('Aircraft/aerodynamics/CL_alpha'),
        'loadcase1:U_gust': lc1_u_gust,
        'loadcase1:altitude': lc1_alt,
        'loadcase1:Vc_EAS': lc1_vc_eas,
        'loadcase2:U_gust': lc2_u_gust,
        'loadcase2:altitude': lc1_alt,
        'loadcase2:Vc_EAS': lc1_vc_eas,
        # Wing Weight --------------------------------------------------------------------------------------------------
        # 'n1m1': 241000,  # output from load computation is expected to be slightly different
        # 'n2m2': 250000,  # output from load computation is expected to be slightly different
        # 'geometry:wing_area': input_xml.get_float('Aircraft/geometry/wing/wing_area'),
        # 'geometry:wing_span': input_xml.get_float('Aircraft/geometry/wing/span'),
        'geometry:wing_toc_root': input_xml.get_float('Aircraft/geometry/wing/toc/root'),
        'geometry:wing_toc_kink': input_xml.get_float('Aircraft/geometry/wing/toc/kink'),
        'geometry:wing_toc_tip': input_xml.get_float('Aircraft/geometry/wing/toc/tip'),
        # 'geometry:wing_l2': input_xml.get_float('Aircraft/geometry/wing/l2_wing'),
        'geometry:wing_sweep_25': input_xml.get_float('Aircraft/geometry/wing/sweep_25'),
        'geometry:wing_area_pf': input_xml.get_float('Aircraft/geometry/wing/S_pf'),
        # 'weight:MTOW': input_xml.get_float('Aircraft/weight/MTOW'),
        'weight:MLW': input_xml.get_float('Aircraft/weight/MLW'),
        'kfactors_a1:K_A1': input_xml.get_float('Aircraft/weight/k_factors/Wing_A1/A1/k'),
        'kfactors_a1:offset_A1': input_xml.get_float('Aircraft/weight/k_factors/Wing_A1/A1/offset'),
        'kfactors_a1:K_A11': input_xml.get_float('Aircraft/weight/k_factors/Wing_A1/A11/k'),
        'kfactors_a1:offset_A11': input_xml.get_float(
            'Aircraft/weight/k_factors/Wing_A1/A11/offset'),
        'kfactors_a1:K_A12': input_xml.get_float('Aircraft/weight/k_factors/Wing_A1/A12/k'),
        'kfactors_a1:offset_A12': input_xml.get_float(
            'Aircraft/weight/k_factors/Wing_A1/A12/offset'),
        'kfactors_a1:K_A13': input_xml.get_float('Aircraft/weight/k_factors/Wing_A1/A13/k'),
        'kfactors_a1:offset_A13': input_xml.get_float(
            'Aircraft/weight/k_factors/Wing_A1/A13/offset'),
        'kfactors_a1:K_A14': input_xml.get_float('Aircraft/weight/k_factors/Wing_A1/A14/k'),
        'kfactors_a1:offset_A14': input_xml.get_float(
            'Aircraft/weight/k_factors/Wing_A1/A14/offset'),
        'kfactors_a1:K_A15': input_xml.get_float('Aircraft/weight/k_factors/Wing_A1/A15/k'),
        'kfactors_a1:offset_A15': input_xml.get_float(
            'Aircraft/weight/k_factors/Wing_A1/A15/offset'),
        'kfactors_a1:K_voil': input_xml.get_float('Aircraft/weight/k_factors/Wing_A1/K_voil'),
        'kfactors_a1:K_mvo': input_xml.get_float('Aircraft/weight/k_factors/Wing_A1/K_mvo'),
        # Fuselage Weight ----------------------------------------------------------------------------------------------
        # 'n1m1': 241000,  # output from load computation is expected to be slightly different
        'geometry:fuselage_wet_area': input_xml.get_float('Aircraft/geometry/fuselage/S_mbf'),
        # 'geometry:fuselage_width_max': input_xml.get_float('Aircraft/geometry/fuselage/width_max'),
        # 'geometry:fuselage_height_max': input_xml.get_float('Aircraft/geometry/fuselage/height_max'),
        'kfactors_a2:K_A2': input_xml.get_float('Aircraft/weight/k_factors/fuselage_A2/A2/k'),
        'kfactors_a2:offset_A2': input_xml.get_float(
            'Aircraft/weight/k_factors/fuselage_A2/A2/offset'),
        'kfactors_a2:K_tr': input_xml.get_float('Aircraft/weight/k_factors/fuselage_A2/K_tr'),
        'kfactors_a2:K_fus': input_xml.get_float('Aircraft/weight/k_factors/fuselage_A2/K_fus'),
        # Empennage Weight ---------------------------------------------------------------------------------------------
        'geometry:ht_area': input_xml.get_float('Aircraft/geometry/ht/area'),
        'geometry:vt_area': input_xml.get_float('Aircraft/geometry/vt/area'),
        'kfactors_a3:K_A31': input_xml.get_float('Aircraft/weight/k_factors/empennage_A3/A31/k'),
        'kfactors_a3:offset_A31': input_xml.get_float(
            'Aircraft/weight/k_factors/empennage_A3/A31/offset'),
        'kfactors_a3:K_A32': input_xml.get_float('Aircraft/weight/k_factors/empennage_A3/A32/k'),
        'kfactors_a3:offset_A32': input_xml.get_float(
            'Aircraft/weight/k_factors/empennage_A3/A32/offset'),
        # Flight Control Weight ----------------------------------------------------------------------------------------
        # 'n1m1': 241000,  # output from load computation is expected to be slightly different
        # 'n2m2': 250000,  # output from load computation is expected to be slightly different
        # 'geometry:fuselage_length': input_xml.get_float('Aircraft/geometry/fuselage/fus_length'),
        # 'geometry:wing_b_50': input_xml.get_float('Aircraft/geometry/wing/b_50'),
        'kfactors_a4:K_A4': input_xml.get_float(
            'Aircraft/weight/k_factors/flight_controls_A4/A4/k'),
        'kfactors_a4:offset_A4': input_xml.get_float(
            'Aircraft/weight/k_factors/flight_controls_A4/A4/offset'),
        'kfactors_a4:K_fc': input_xml.get_float(
            'Aircraft/weight/k_factors/flight_controls_A4/K_fc'),
        # Landing Gear Weight ------------------------------------------------------------------------------------------
        # 'weight:MTOW': input_xml.get_float('Aircraft/weight/MTOW'),
        'kfactors_a5:K_A5': input_xml.get_float('Aircraft/weight/k_factors/LG_A5/A5/k'),
        'kfactors_a5:offset_A5': input_xml.get_float('Aircraft/weight/k_factors/LG_A5/A5/offset'),
        # Pylon Weight -------------------------------------------------------------------------------------------------
        'geometry:pylon_wet_area': input_xml.get_float(
            'Aircraft/geometry/propulsion/wet_area_pylon'),
        # 'geometry:engine_number': input_xml.get_float('Aircraft/geometry/propulsion/engine_number'),
        # 'weight_propulsion:B1': input_xml.get_float('Aircraft/weight/propulsion/weight_B1'),
        'kfactors_a6:K_A6': input_xml.get_float('Aircraft/weight/k_factors/pylon_A6/A6/k'),
        'kfactors_a6:offset_A6': input_xml.get_float(
            'Aircraft/weight/k_factors/pylon_A6/A6/offset'),
        # Paint Weight -------------------------------------------------------------------------------------------------
        'geometry:S_total': input_xml.get_float('Aircraft/geometry/S_total'),
        'kfactors_a7:K_A7': input_xml.get_float('Aircraft/weight/k_factors/paint_A7/A7/k'),
        'kfactors_a7:offset_A7': input_xml.get_float(
            'Aircraft/weight/k_factors/paint_A7/A7/offset'),
        # Engine Weight ------------------------------------------------------------------------------------------------
        'propulsion_conventional:thrust_SL': input_xml.get_float(
            'Aircraft/propulsion/conventional/thrust_SL'),
        # 'geometry:engine_number': input_xml.get_float('Aircraft/geometry/propulsion/engine_number'),
        'kfactors_b1:K_B1': input_xml.get_float('Aircraft/weight/k_factors/propulsion_B1/B1/k'),
        'kfactors_b1:offset_B1': input_xml.get_float(
            'Aircraft/weight/k_factors/propulsion_B1/B1/offset'),
        # Fuel Lines Weight --------------------------------------------------------------------------------------------
        # 'geometry:wing_b_50': input_xml.get_float('Aircraft/geometry/wing/b_50'),
        # 'weight:MFW': input_xml.get_float('Aircraft/weight/MFW'),
        # 'weight_propulsion:B1': input_xml.get_float('Aircraft/weight/propulsion/weight_B1'),
        'kfactors_b2:K_B2': input_xml.get_float('Aircraft/weight/k_factors/fuel_lines_B2/B2/k'),
        'kfactors_b2:offset_B2': input_xml.get_float(
            'Aircraft/weight/k_factors/fuel_lines_B2/B2/offset'),
        # Unconsumables Weight -----------------------------------------------------------------------------------------
        # 'geometry:engine_number': input_xml.get_float('Aircraft/geometry/propulsion/engine_number'),
        # 'weight:MFW': input_xml.get_float('Aircraft/weight/MFW'),
        'kfactors_b3:K_B3': input_xml.get_float('Aircraft/weight/k_factors/unconsumables_B3/B3/k'),
        'kfactors_b3:offset_B3': input_xml.get_float(
            'Aircraft/weight/k_factors/unconsumables_B3/B3/offset'),
        # Power Systems Weight -----------------------------------------------------------------------------------------
        # 'cabin:NPAX1': 150,  # input_xml.get_float('Aircraft/cabin/NPAX1'),
        # 'weight_airframe:A4': 700,
        # 'weight:MTOW': input_xml.get_float('Aircraft/weight/MTOW'),
        'kfactors_c1:K_C11': input_xml.get_float(
            'Aircraft/weight/k_factors/power_systems_C1/C11/k'),
        'kfactors_c1:offset_C11': input_xml.get_float(
            'Aircraft/weight/k_factors/power_systems_C1/C11/offset'),
        'kfactors_c1:K_C12': input_xml.get_float(
            'Aircraft/weight/k_factors/power_systems_C1/C12/k'),
        'kfactors_c1:offset_C12': input_xml.get_float(
            'Aircraft/weight/k_factors/power_systems_C1/C12/offset'),
        'kfactors_c1:K_C13': input_xml.get_float(
            'Aircraft/weight/k_factors/power_systems_C1/C13/k'),
        'kfactors_c1:offset_C13': input_xml.get_float(
            'Aircraft/weight/k_factors/power_systems_C1/C13/offset'),
        'kfactors_c1:K_elec': input_xml.get_float(
            'Aircraft/weight/k_factors/power_systems_C1/K_elec'),
        # Life Support Systems Weight ----------------------------------------------------------------------------------
        # 'geometry:fuselage_width_max': input_xml.get_float('Aircraft/geometry/fuselage/width_max'),
        # 'geometry:fuselage_height_max': input_xml.get_float('Aircraft/geometry/fuselage/height_max'),
        'geometry:fuselage_Lcabin': 0.8 * input_xml.get_float(
            'Aircraft/geometry/fuselage/fus_length'),
        'geometry:wing_sweep_0': input_xml.get_float('Aircraft/geometry/wing/sweep_0'),
        'geometry:nacelle_dia': input_xml.get_float('Aircraft/geometry/propulsion/nacelle_dia'),
        # 'geometry:engine_number': input_xml.get_float('Aircraft/geometry/propulsion/engine_number'),
        # 'cabin:NPAX1': 150,  # input_xml.get_float('Aircraft/cabin/NPAX1'),
        # 'cabin:PNT': input_xml.get_float('Aircraft/cabin/PNT'),
        # 'cabin:PNC': input_xml.get_float('Aircraft/cabin/PNC'),
        # 'geometry:wing_span': input_xml.get_float('Aircraft/geometry/wing/span'),
        # 'weight_propulsion:B1': input_xml.get_float('Aircraft/weight/propulsion/weight_B1'),
        'kfactors_c2:K_C21': input_xml.get_float('Aircraft/weight/k_factors/LSS_C2/C21/k'),
        'kfactors_c2:offset_C21': input_xml.get_float(
            'Aircraft/weight/k_factors/LSS_C2/C21/offset'),
        'kfactors_c2:K_C22': input_xml.get_float('Aircraft/weight/k_factors/LSS_C2/C22/k'),
        'kfactors_c2:offset_C22': input_xml.get_float(
            'Aircraft/weight/k_factors/LSS_C2/C22/offset'),
        'kfactors_c2:K_C23': input_xml.get_float('Aircraft/weight/k_factors/LSS_C2/C23/k'),
        'kfactors_c2:offset_C23': input_xml.get_float(
            'Aircraft/weight/k_factors/LSS_C2/C23/offset'),
        'kfactors_c2:K_C24': input_xml.get_float('Aircraft/weight/k_factors/LSS_C2/C24/k'),
        'kfactors_c2:offset_C24': input_xml.get_float(
            'Aircraft/weight/k_factors/LSS_C2/C24/offset'),
        'kfactors_c2:K_C25': input_xml.get_float('Aircraft/weight/k_factors/LSS_C2/C25/k'),
        'kfactors_c2:offset_C25': input_xml.get_float(
            'Aircraft/weight/k_factors/LSS_C2/C25/offset'),
        'kfactors_c2:K_C26': input_xml.get_float('Aircraft/weight/k_factors/LSS_C2/C26/k'),
        'kfactors_c2:offset_C26': input_xml.get_float(
            'Aircraft/weight/k_factors/LSS_C2/C26/offset'),
        'kfactors_c2:K_C27': input_xml.get_float('Aircraft/weight/k_factors/LSS_C2/C27/k'),
        'kfactors_c2:offset_C27': input_xml.get_float(
            'Aircraft/weight/k_factors/LSS_C2/C27/offset'),
        # Navigation Systems Weight ------------------------------------------------------------------------------------
        # 'geometry:fuselage_length': input_xml.get_float('Aircraft/geometry/fuselage/fus_length'),
        # 'geometry:wing_b_50': input_xml.get_float('Aircraft/geometry/wing/b_50'),
        'kfactors_c3:K_C3': input_xml.get_float(
            'Aircraft/weight/k_factors/instrument_navigation_C3/C3/k'),
        'kfactors_c3:offset_C3': input_xml.get_float(
            'Aircraft/weight/k_factors/instrument_navigation_C3/C3/offset'),
        # Transmission Systems Weight ----------------------------------------------------------------------------------
        'kfactors_c4:K_C4': input_xml.get_float('Aircraft/weight/k_factors/transmissions_C4/C4/k'),
        'kfactors_c4:offset_C4': input_xml.get_float(
            'Aircraft/weight/k_factors/transmissions_C4/C4/offset'),
        # Fixed Operational Systems Weight -----------------------------------------------------------------------------
        'geometry:fuselage_LAV': input_xml.get_float('Aircraft/geometry/fuselage/LAV'),
        'geometry:fuselage_LAR': input_xml.get_float('Aircraft/geometry/fuselage/LAR'),
        # 'geometry:fuselage_length': input_xml.get_float('Aircraft/geometry/fuselage/fus_length'),
        # 'cabin:front_seat_number_eco': input_xml.get_float('Aircraft/cabin/eco/front_seat_number'),
        # 'geometry:wing_l2': input_xml.get_float('Aircraft/geometry/wing/l2_wing'),
        'cabin:container_number_front': input_xml.get_float(
            'Aircraft/cabin/container_number_front'),
        'kfactors_c5:K_C5': input_xml.get_float('Aircraft/weight/k_factors/FOS_C5/C5/k'),
        'kfactors_c5:offset_C5': input_xml.get_float('Aircraft/weight/k_factors/FOS_C5/C5/offset'),
        # Flight Kit Weight --------------------------------------------------------------------------------------------
        'kfactors_c6:K_C6': input_xml.get_float('Aircraft/weight/k_factors/flight_kit_C6/C6/k'),
        'kfactors_c6:offset_C6': input_xml.get_float(
            'Aircraft/weight/k_factors/flight_kit_C6/C6/offset'),
        # Cargo configuration Weight -----------------------------------------------------------------------------------
        # 'cabin:NPAX1': 150,  # input_xml.get_float('Aircraft/cabin/NPAX1'),
        'cabin:container_number': input_xml.get_float('Aircraft/cabin/container_number'),
        'cabin:pallet_number': input_xml.get_float('Aircraft/cabin/pallet_number'),
        # 'cabin:front_seat_number_eco': input_xml.get_float('Aircraft/cabin/eco/front_seat_number'),
        'kfactors_d1:K_D1': input_xml.get_float('Aircraft/weight/k_factors/cargo_cfg_D1/D1/k'),
        'kfactors_d1:offset_D1': input_xml.get_float(
            'Aircraft/weight/k_factors/cargo_cfg_D1/D1/offset'),
        # Passenger Seats Weight ---------------------------------------------------------------------------------------
        # 'tlar:NPAX': input_xml.get_float('Aircraft/TLAR/NPAX'),
        'kfactors_d2:K_D2': input_xml.get_float('Aircraft/weight/k_factors/passenger_seat_D2/D2/k'),
        'kfactors_d2:offset_D2': input_xml.get_float(
            'Aircraft/weight/k_factors/passenger_seat_D2/D2/offset'),
        # Food Water Weight --------------------------------------------------------------------------------------------
        # 'tlar:NPAX': input_xml.get_float('Aircraft/TLAR/NPAX'),
        'kfactors_d3:K_D3': input_xml.get_float('Aircraft/weight/k_factors/food_water_D3/D3/k'),
        'kfactors_d3:offset_D3': input_xml.get_float(
            'Aircraft/weight/k_factors/food_water_D3/D3/offset'),
        # Security Kit Weight ------------------------------------------------------------------------------------------
        # 'tlar:NPAX': input_xml.get_float('Aircraft/TLAR/NPAX'),
        'kfactors_d4:K_D4': input_xml.get_float('Aircraft/weight/k_factors/security_kit_D4/D4/k'),
        'kfactors_d4:offset_D4': input_xml.get_float(
            'Aircraft/weight/k_factors/security_kit_D4/D4/offset'),
        # Toilets Weight -----------------------------------------------------------------------------------------------
        # 'tlar:NPAX': input_xml.get_float('Aircraft/TLAR/NPAX'),
        'kfactors_d5:K_D5': input_xml.get_float('Aircraft/weight/k_factors/toilet_D5/D5/k'),
        'kfactors_d5:offset_D5': input_xml.get_float(
            'Aircraft/weight/k_factors/toilet_D5/D5/offset'),
        # Crew Weight --------------------------------------------------------------------------------------------------
        # 'cabin:PNT': input_xml.get_float('Aircraft/cabin/PNT'),
        # 'cabin:PNC': input_xml.get_float('Aircraft/cabin/PNC'),

    }
    return inputs
