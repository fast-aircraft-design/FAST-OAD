"""
Test module for geometry functions
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
from openmdao.core.indepvarcomp import IndepVarComp
from openmdao.core.problem import Problem

from fastoad.io.xml import XPathReader
from fastoad.io.xml.openmdao_basic_io import OpenMdaoXmlIO
from fastoad.modules.geometry.cg_components.compute_aero_center \
    import ComputeAeroCenter
from fastoad.modules.geometry.cg_components.compute_cg_control_surfaces \
    import ComputeControlSurfacesCG
from fastoad.modules.geometry.cg_components.compute_cg_loadcase1 \
    import ComputeCGLoadCase1
from fastoad.modules.geometry.cg_components.compute_cg_loadcase2 \
    import ComputeCGLoadCase2
from fastoad.modules.geometry.cg_components.compute_cg_loadcase3 \
    import ComputeCGLoadCase3
from fastoad.modules.geometry.cg_components.compute_cg_loadcase4 \
    import ComputeCGLoadCase4
from fastoad.modules.geometry.cg_components.compute_cg_others \
    import ComputeOthersCG
from fastoad.modules.geometry.cg_components.compute_cg_ratio_aft \
    import ComputeCGratioAft



@pytest.fixture(scope="module")
def input_xml() -> XPathReader:
    """
    :return: access to the sample xml data
    """
    return XPathReader(
        pth.join(pth.dirname(__file__), "data", "CeRAS01_baseline.xml"))


def test_compute_aero_center(input_xml: XPathReader):
    """ Tests computation of aerodynamic center """
    inputs = {
        'geometry:wing_x0': input_xml.get_float(
            'Aircraft/geometry/wing/x0_wing'),
        'geometry:wing_l0': input_xml.get_float(
            'Aircraft/geometry/wing/l0_wing'),
        'geometry:wing_l1': input_xml.get_float(
            'Aircraft/geometry/wing/l1_wing'),
        'geometry:fuselage_width_max': input_xml.get_float(
            'Aircraft/geometry/fuselage/width_max'),
        'geometry:fuselage_length': input_xml.get_float(
            'Aircraft/geometry/fuselage/fus_length'),
        'geometry:wing_position': input_xml.get_float(
            'Aircraft/geometry/wing/fa_length'),
        'geometry:wing_area': input_xml.get_float(
            'Aircraft/geometry/wing/wing_area'),
        'geometry:ht_area': input_xml.get_float(
            'Aircraft/geometry/ht/area'),
        'geometry:ht_lp': input_xml.get_float(
            'Aircraft/geometry/ht/lp'),
        'aerodynamics:Cl_alpha': input_xml.get_float(
            'Aircraft/aerodynamics/CL_alpha'),
        'aerodynamics:Cl_alpha_ht': input_xml.get_float(
            'Aircraft/aerodynamics/CL_alpha_ht')
    }
    component = ComputeAeroCenter()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    x_ac_ratio = outputs['x_ac_ratio']
    print(x_ac_ratio)
    assert x_ac_ratio == pytest.approx(0.537521, abs=1e-6)

def test_compute_cg_control_surfaces(input_xml: XPathReader):
    """ Tests computation of control surfaces center of gravity """
    inputs = {
        'geometry:wing_x0': input_xml.get_float(
            'Aircraft/geometry/wing/x0_wing'),
        'geometry:wing_l0': input_xml.get_float(
            'Aircraft/geometry/wing/l0_wing'),
        'geometry:wing_y0': input_xml.get_float(
            'Aircraft/geometry/wing/y0_wing'),
        'geometry:wing_l2': input_xml.get_float(
            'Aircraft/geometry/wing/l2_wing'),
        'geometry:wing_l3': input_xml.get_float(
            'Aircraft/geometry/wing/l3_wing'),
        'geometry:wing_y2': input_xml.get_float(
            'Aircraft/geometry/wing/y2_wing'),
        'geometry:wing_x3': input_xml.get_float(
            'Aircraft/geometry/wing/x3_wing'),
        'geometry:wing_y3': input_xml.get_float(
            'Aircraft/geometry/wing/y3_wing'),
        'geometry:wing_position': input_xml.get_float(
            'Aircraft/geometry/wing/fa_length')
    }
    component = ComputeControlSurfacesCG()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    x_cg_control_absolute = outputs['cg_airframe:A4']
    assert x_cg_control_absolute == pytest.approx(19.24, abs=1e-2)

def test_compute_cg_loadcase1(input_xml: XPathReader):
    """ Tests computation of center of gravity for load case 1 """
    
    inputs = {
        'geometry:wing_l0': input_xml.get_float(
            'Aircraft/geometry/wing/l0_wing'),
        'geometry:wing_position': input_xml.get_float(
            'Aircraft/geometry/wing/fa_length'),
        'cg:cg_pax': input_xml.get_float(
            'Aircraft/balance/PayLoad/CG_PAX'),
        'cg:cg_rear_fret': input_xml.get_float(
            'Aircraft/balance/PayLoad/CG_rear_fret'),
        'cg:cg_front_fret': input_xml.get_float(
            'Aircraft/balance/PayLoad/CG_front_fret'),
        'tlar:NPAX': input_xml.get_float(
            'Aircraft/TLAR/NPAX'),
        'x_cg_plane_up': 699570.01,
        'x_cg_plane_down': 40979.11
    }

    component = ComputeCGLoadCase1()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    cg_ratio_lc1 = outputs['cg_ratio_lc1']
    assert cg_ratio_lc1 == pytest.approx(0.364924, abs=1e-6)

def test_compute_cg_loadcase2(input_xml: XPathReader):
    """ Tests computation of center of gravity for load case 2 """
    
    inputs = {
        'geometry:wing_l0': input_xml.get_float(
            'Aircraft/geometry/wing/l0_wing'),
        'geometry:wing_position': input_xml.get_float(
            'Aircraft/geometry/wing/fa_length'),
        'cg:cg_pax': input_xml.get_float(
            'Aircraft/balance/PayLoad/CG_PAX'),
        'cg:cg_rear_fret': input_xml.get_float(
            'Aircraft/balance/PayLoad/CG_rear_fret'),
        'cg:cg_front_fret': input_xml.get_float(
            'Aircraft/balance/PayLoad/CG_front_fret'),
        'tlar:NPAX': input_xml.get_float(
            'Aircraft/TLAR/NPAX'),
        'weight:MFW': input_xml.get_float(
            'Aircraft/weight/MFW'),
        'cg:cg_tank': input_xml.get_float(
            'Aircraft/balance/tank/CG_tank'),
        'x_cg_plane_up': 699570.01,
        'x_cg_plane_down': 40979.11
    }

    component = ComputeCGLoadCase2()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    cg_ratio_lc2 = outputs['cg_ratio_lc2']
    assert cg_ratio_lc2 == pytest.approx(0.285139, abs=1e-6)

def test_compute_cg_loadcase3(input_xml: XPathReader):
    """ Tests computation of center of gravity for load case 3 """
    
    inputs = {
        'geometry:wing_l0': input_xml.get_float(
            'Aircraft/geometry/wing/l0_wing'),
        'geometry:wing_position': input_xml.get_float(
            'Aircraft/geometry/wing/fa_length'),
        'cg:cg_pax': input_xml.get_float(
            'Aircraft/balance/PayLoad/CG_PAX'),
        'cg:cg_rear_fret': input_xml.get_float(
            'Aircraft/balance/PayLoad/CG_rear_fret'),
        'cg:cg_front_fret': input_xml.get_float(
            'Aircraft/balance/PayLoad/CG_front_fret'),
        'tlar:NPAX': input_xml.get_float(
            'Aircraft/TLAR/NPAX'),
        'x_cg_plane_up': 699570.01,
        'x_cg_plane_down': 40979.11
    }

    component = ComputeCGLoadCase3()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    cg_ratio_lc3 = outputs['cg_ratio_lc3']
    assert cg_ratio_lc3 == pytest.approx(0.386260, abs=1e-6)

def test_compute_cg_loadcase4(input_xml: XPathReader):
    """ Tests computation of center of gravity for load case 4 """
    
    inputs = {
        'geometry:wing_l0': input_xml.get_float(
            'Aircraft/geometry/wing/l0_wing'),
        'geometry:wing_position': input_xml.get_float(
            'Aircraft/geometry/wing/fa_length'),
        'cg:cg_pax': input_xml.get_float(
            'Aircraft/balance/PayLoad/CG_PAX'),
        'cg:cg_rear_fret': input_xml.get_float(
            'Aircraft/balance/PayLoad/CG_rear_fret'),
        'cg:cg_front_fret': input_xml.get_float(
            'Aircraft/balance/PayLoad/CG_front_fret'),
        'tlar:NPAX': input_xml.get_float(
            'Aircraft/TLAR/NPAX'),
        'x_cg_plane_up': 699570.01,
        'x_cg_plane_down': 40979.11
    }

    component = ComputeCGLoadCase4()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    cg_ratio_lc4 = outputs['cg_ratio_lc4']
    assert cg_ratio_lc4 == pytest.approx(0.388971, abs=1e-6)

def test_compute_cg_others(input_xml: XPathReader):
    """ Tests computation of other components center of gravity """
    inputs = {
        'geometry:wing_x0': input_xml.get_float(
            'Aircraft/geometry/wing/x0_wing'),
        'geometry:wing_l0': input_xml.get_float(
            'Aircraft/geometry/wing/l0_wing'),
        'geometry:wing_l2': input_xml.get_float(
            'Aircraft/geometry/wing/l2_wing'),
        'geometry:fuselage_length': input_xml.get_float(
            'Aircraft/geometry/fuselage/fus_length'),
        'geometry:wing_position': input_xml.get_float(
            'Aircraft/geometry/wing/fa_length'),
        'geometry:fuselage_LAV': input_xml.get_float(
            'Aircraft/geometry/fuselage/LAV'),
        'geometry:fuselage_LAR': input_xml.get_float(
            'Aircraft/geometry/fuselage/LAR'),
        'cg_propulsion:B1': input_xml.get_float(
            'Aircraft/balance/propulsion/CG_B1'),
        'cg_furniture:D2': input_xml.get_float(
            'Aircraft/balance/furniture/CG_D2'),
        'weight_propulsion:B1': input_xml.get_float(
            'Aircraft/weight/propulsion/weight_B1'),
        'cabin:NPAX1': input_xml.get_float(
            'Aircraft/cabin/NPAX1'),
        'cabin:front_seat_number_eco': input_xml.get_float(
            'Aircraft/cabin/eco/front_seat_number'),
        'cabin:LSeco': input_xml.get_float(
            'Aircraft/cabin/eco/LS'),
    }

    component = ComputeOthersCG()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    x_cg_a2 = outputs['cg_airframe:A2']
    assert x_cg_a2 == pytest.approx(16.88, abs=1e-2)
    x_cg_a52 = outputs['cg_airframe:A52']
    assert x_cg_a52 == pytest.approx(5.18, abs=1e-2)
    x_cg_a6 = outputs['cg_airframe:A6']
    assert x_cg_a6 == pytest.approx(13.5, abs=1e-1)
    x_cg_a7 = outputs['cg_airframe:A7']
    assert x_cg_a7 == pytest.approx(0.0, abs=1e-1)

    x_cg_b2 = outputs['cg_propulsion:B2']
    assert x_cg_b2 == pytest.approx(13.5, abs=1e-1)
    x_cg_b3 = outputs['cg_propulsion:B3']
    assert x_cg_b3 == pytest.approx(13.5, abs=1e-1)

    x_cg_c11 = outputs['cg_systems:C11']
    assert x_cg_c11 == pytest.approx(35.63, abs=1e-2)
    x_cg_c12 = outputs['cg_systems:C12']
    assert x_cg_c12 == pytest.approx(18.75, abs=1e-2)
    x_cg_c13 = outputs['cg_systems:C13']
    assert x_cg_c13 == pytest.approx(18.75, abs=1e-2)
    x_cg_c21 = outputs['cg_systems:C21']
    assert x_cg_c21 == pytest.approx(16.88, abs=1e-2)
    x_cg_c22 = outputs['cg_systems:C22']
    assert x_cg_c22 == pytest.approx(16.62, abs=1e-2)
    x_cg_c23 = outputs['cg_systems:C23']
    assert x_cg_c23 == pytest.approx(15.79, abs=1e-2)
    x_cg_c24 = outputs['cg_systems:C24']
    assert x_cg_c24 == pytest.approx(16.88, abs=1e-2)
    x_cg_c25 = outputs['cg_systems:C25']
    assert x_cg_c25 == pytest.approx(16.62, abs=1e-2)
    x_cg_c26 = outputs['cg_systems:C26']
    assert x_cg_c26 == pytest.approx(16.62, abs=1e-2)
    x_cg_c27 = outputs['cg_systems:C27']
    assert x_cg_c27 == pytest.approx(16.1, abs=1e-1)
    x_cg_c3 = outputs['cg_systems:C3']
    assert x_cg_c3 == pytest.approx(5.52, abs=1e-2)
    x_cg_c4 = outputs['cg_systems:C4']
    assert x_cg_c4 == pytest.approx(18.75, abs=1e-2)
    x_cg_c51 = outputs['cg_systems:C51']
    assert x_cg_c51 == pytest.approx(0.75, abs=1e-2)
    x_cg_c52 = outputs['cg_systems:C52']
    assert x_cg_c52 == pytest.approx(16.62, abs=1e-2)

    x_cg_d1 = outputs['cg_furniture:D1']
    assert x_cg_d1 == pytest.approx(0.0, abs=1e-1)
    x_cg_d3 = outputs['cg_furniture:D3']
    assert x_cg_d3 == pytest.approx(29.4, abs=1e-1)
    x_cg_d4 = outputs['cg_furniture:D4']
    assert x_cg_d4 == pytest.approx(16.62, abs=1e-2)
    x_cg_d5 = outputs['cg_furniture:D5']
    assert x_cg_d5 == pytest.approx(16.62, abs=1e-2)
    x_cg_pl = outputs['cg:cg_pax']
    assert x_cg_pl == pytest.approx(16.62, abs=1e-2)
    x_cg_rear_fret = outputs['cg:cg_rear_fret']
    assert x_cg_rear_fret == pytest.approx(20.87, abs=1e-2)
    x_cg_front_fret = outputs['cg:cg_front_fret']
    assert x_cg_front_fret == pytest.approx(9.94, abs=1e-2)

def test_compute_cg_ratio_aft(input_xml: XPathReader):
    """ Tests computation of center of gravity with aft estimation """
    inputs = {
        'cg_airframe:A1': input_xml.get_float(
            'Aircraft/balance/airframe/CG_A1'),
        'cg_airframe:A2': input_xml.get_float(
            'Aircraft/balance/airframe/CG_A2'),
        'cg_airframe:A31': input_xml.get_float(
            'Aircraft/balance/airframe/CG_A31'),
        'cg_airframe:A32': input_xml.get_float(
            'Aircraft/balance/airframe/CG_A32'),
        'cg_airframe:A4': input_xml.get_float(
            'Aircraft/balance/airframe/CG_A4'),
        'cg_airframe:A51': input_xml.get_float(
            'Aircraft/balance/airframe/CG_A51'),
        'cg_airframe:A52': input_xml.get_float(
            'Aircraft/balance/airframe/CG_A52'),
        'cg_airframe:A6': input_xml.get_float(
            'Aircraft/balance/airframe/CG_A6'),
        'cg_airframe:A7': input_xml.get_float(
            'Aircraft/balance/airframe/CG_A7'),
        'weight_airframe:A1': input_xml.get_float(
            'Aircraft/weight/airframe/weight_A1'),
        'weight_airframe:A2': input_xml.get_float(
            'Aircraft/weight/airframe/weight_A2'),
        'weight_airframe:A31': input_xml.get_float(
            'Aircraft/weight/airframe/weight_A31'),
        'weight_airframe:A32': input_xml.get_float(
            'Aircraft/weight/airframe/weight_A32'),
        'weight_airframe:A4': input_xml.get_float(
            'Aircraft/weight/airframe/weight_A4'),
        'weight_airframe:A51': input_xml.get_float(
            'Aircraft/weight/airframe/weight_A51'),
        'weight_airframe:A52': input_xml.get_float(
            'Aircraft/weight/airframe/weight_A52'),
        'weight_airframe:A6': input_xml.get_float(
            'Aircraft/weight/airframe/weight_A6'),
        'weight_airframe:A7': input_xml.get_float(
            'Aircraft/weight/airframe/weight_A7'),
        'cg_propulsion:B1': input_xml.get_float(
            'Aircraft/balance/propulsion/CG_B1'),
        'cg_propulsion:B2': input_xml.get_float(
            'Aircraft/balance/propulsion/CG_B2'),
        'cg_propulsion:B3': input_xml.get_float(
            'Aircraft/balance/propulsion/CG_B3'),
        'weight_propulsion:B1': input_xml.get_float(
            'Aircraft/weight/propulsion/weight_B1'),
        'weight_propulsion:B2': input_xml.get_float(
            'Aircraft/weight/propulsion/weight_B2'),
        'weight_propulsion:B3': input_xml.get_float(
            'Aircraft/weight/propulsion/weight_B3'),
        'cg_systems:C11': input_xml.get_float(
            'Aircraft/balance/systems/CG_C11'),
        'cg_systems:C12': input_xml.get_float(
            'Aircraft/balance/systems/CG_C12'),
        'cg_systems:C13': input_xml.get_float(
            'Aircraft/balance/systems/CG_C13'),
        'cg_systems:C21': input_xml.get_float(
            'Aircraft/balance/systems/CG_C21'),
        'cg_systems:C22': input_xml.get_float(
            'Aircraft/balance/systems/CG_C22'),
        'cg_systems:C23': input_xml.get_float(
            'Aircraft/balance/systems/CG_C23'),
        'cg_systems:C24': input_xml.get_float(
            'Aircraft/balance/systems/CG_C24'),
        'cg_systems:C25': input_xml.get_float(
            'Aircraft/balance/systems/CG_C25'),
        'cg_systems:C26': input_xml.get_float(
            'Aircraft/balance/systems/CG_C26'),
        'cg_systems:C27': input_xml.get_float(
            'Aircraft/balance/systems/CG_C27'),
        'cg_systems:C3': input_xml.get_float(
            'Aircraft/balance/systems/CG_C3'),
        'cg_systems:C4': input_xml.get_float(
            'Aircraft/balance/systems/CG_C4'),
        'cg_systems:C51': input_xml.get_float(
            'Aircraft/balance/systems/CG_C51'),
        'cg_systems:C52': input_xml.get_float(
            'Aircraft/balance/systems/CG_C52'),
        'cg_systems:C6': input_xml.get_float(
            'Aircraft/balance/systems/CG_C6'),
        'weight_systems:C11': input_xml.get_float(
            'Aircraft/weight/systems/weight_C11'),
        'weight_systems:C12': input_xml.get_float(
            'Aircraft/weight/systems/weight_C12'),
        'weight_systems:C13': input_xml.get_float(
            'Aircraft/weight/systems/weight_C13'),
        'weight_systems:C21': input_xml.get_float(
            'Aircraft/weight/systems/weight_C21'),
        'weight_systems:C22': input_xml.get_float(
            'Aircraft/weight/systems/weight_C22'),
        'weight_systems:C23': input_xml.get_float(
            'Aircraft/weight/systems/weight_C23'),
        'weight_systems:C24': input_xml.get_float(
            'Aircraft/weight/systems/weight_C24'),
        'weight_systems:C25': input_xml.get_float(
            'Aircraft/weight/systems/weight_C25'),
        'weight_systems:C26': input_xml.get_float(
            'Aircraft/weight/systems/weight_C26'),
        'weight_systems:C27': input_xml.get_float(
            'Aircraft/weight/systems/weight_C27'),
        'weight_systems:C3': input_xml.get_float(
            'Aircraft/weight/systems/weight_C3'),
        'weight_systems:C4': input_xml.get_float(
            'Aircraft/weight/systems/weight_C4'),
        'weight_systems:C51': input_xml.get_float(
            'Aircraft/weight/systems/weight_C51'),
        'weight_systems:C52': input_xml.get_float(
            'Aircraft/weight/systems/weight_C52'),
        'weight_systems:C6': input_xml.get_float(
            'Aircraft/weight/systems/weight_C6'),
        'cg_furniture:D1': input_xml.get_float(
            'Aircraft/balance/furniture/CG_D1'),
        'cg_furniture:D2': input_xml.get_float(
            'Aircraft/balance/furniture/CG_D2'),
        'cg_furniture:D3': input_xml.get_float(
            'Aircraft/balance/furniture/CG_D3'),
        'cg_furniture:D4': input_xml.get_float(
            'Aircraft/balance/furniture/CG_D4'),
        'cg_furniture:D5': input_xml.get_float(
            'Aircraft/balance/furniture/CG_D5'),
        'weight_furniture:D1': input_xml.get_float(
            'Aircraft/weight/furniture/weight_D1'),
        'weight_furniture:D2': input_xml.get_float(
            'Aircraft/weight/furniture/weight_D2'),
        'weight_furniture:D3': input_xml.get_float(
            'Aircraft/weight/furniture/weight_D3'),
        'weight_furniture:D4': input_xml.get_float(
            'Aircraft/weight/furniture/weight_D4'),
        'weight_furniture:D5': input_xml.get_float(
            'Aircraft/weight/furniture/weight_D5'),
        'geometry:wing_l0': input_xml.get_float(
            'Aircraft/geometry/wing/l0_wing'),
        'geometry:wing_position': input_xml.get_float(
            'Aircraft/geometry/wing/fa_length')
    }

    component = ComputeCGratioAft()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    x_cg_plane_up = outputs['x_cg_plane_up']
    assert x_cg_plane_up == pytest.approx(699570.03, abs=1e-2)
    x_cg_plane_down = outputs['x_cg_plane_down']
    assert x_cg_plane_down == pytest.approx(40979.11, abs=1e-2)
    cg_ratio_aft = outputs['cg_ratio_aft']
    assert cg_ratio_aft == pytest.approx(0.387846, abs=1e-6)