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
from fastoad.modules.geometry.cg_components.compute_aero_center \
    import ComputeAeroCenter
from fastoad.modules.geometry.cg_components.compute_cg_control_surfaces \
    import ComputeControlSurfacesCG
from fastoad.modules.geometry.cg_components.compute_cg_loadcase1 \
    import ComputeCGLoadCase1
from fastoad.modules.geometry.cg_components.compute_cg_others \
    import ComputeOthersCG



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
    assert x_ac_ratio == pytest.approx(0.537520943, abs=10)

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
            'Aircraft/geometry/wing/y2_wing'),
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
    assert x_cg_control_absolute == pytest.approx(19.24, abs=10)

"""
def test_compute_cg_loadcase1(input_xml: XPathReader):
    """  """
    Tests computation of center of gravity for load case 1
    inputs = {
        'geometry:wing_l0': input_xml.get_float(
            'Aircraft/geometry/wing/l0_wing'),
        'geometry:wing_position': input_xml.get_float(
            'Aircraft/geometry/wing/fa_length'),
        'cg:cg_pax': input_xml.get_float(
            'Aircraft/balance/Payload/CG_PAX'),
        'cg:cg_rear_fret': input_xml.get_float(
            'Aircraft/balance/Payload/CG_rear_fret'),
        'cg:cg_front_fret': input_xml.get_float(
            'Aircraft/balance/Payload/CG_front_fret'),
        'tlar:NPAX': input_xml.get_float(
            'Aircraft/TLAR/NPAX'),
        'x_cg_plane_up': input_xml.get_float(
            'Aircraft/TLAR/NPAX'),
        'x_cg_plane_down': input_xml.get_float(
            'Aircraft/TLAR/NPAX')
    }
    component = ComputeCGLoadCase1()
    component.setup()
    outputs = {}
    component.compute(inputs, outputs)
    cg_ratio_lc1 = outputs['cg_ratio_lc1']
    assert cg_ratio_lc1 == pytest.approx(19.24, abs=10)
"""

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
    assert x_cg_a2 == pytest.approx(16.88, abs=10)
    x_cg_a52 = outputs['cg_airframe:A52']
    assert x_cg_a52 == pytest.approx(5.18, abs=10)
    x_cg_a6 = outputs['cg_airframe:A6']
    assert x_cg_a6 == pytest.approx(13.5, abs=10)
    x_cg_a7 = outputs['cg_airframe:A7']
    assert x_cg_a7 == pytest.approx(0.0, abs=10)

    x_cg_b2 = outputs['cg_propulsion:B2']
    assert x_cg_b2 == pytest.approx(13.5, abs=10)
    x_cg_b3 = outputs['cg_propulsion:B3']
    assert x_cg_b3 == pytest.approx(13.5, abs=10)

    x_cg_c11 = outputs['cg_systems:C11']
    assert x_cg_c11 == pytest.approx(35.63, abs=10)
    x_cg_c12 = outputs['cg_systems:C12']
    assert x_cg_c12 == pytest.approx(18.75, abs=10)
    x_cg_c13 = outputs['cg_systems:C13']
    assert x_cg_c13 == pytest.approx(18.75, abs=10)
    x_cg_c21 = outputs['cg_systems:C21']
    assert x_cg_c21 == pytest.approx(16.88, abs=10)
    x_cg_c22 = outputs['cg_systems:C22']
    assert x_cg_c22 == pytest.approx(16.62, abs=10)
    x_cg_c23 = outputs['cg_systems:C23']
    assert x_cg_c23 == pytest.approx(15.79, abs=10)
    x_cg_c24 = outputs['cg_systems:C24']
    assert x_cg_c24 == pytest.approx(16.88, abs=10)
    x_cg_c25 = outputs['cg_systems:C25']
    assert x_cg_c25 == pytest.approx(16.62, abs=10)
    x_cg_c26 = outputs['cg_systems:C26']
    assert x_cg_c26 == pytest.approx(16.62, abs=10)
    x_cg_c27 = outputs['cg_systems:C27']
    assert x_cg_c27 == pytest.approx(16.1, abs=10)
    x_cg_c3 = outputs['cg_systems:C3']
    assert x_cg_c3 == pytest.approx(5.52, abs=10)
    x_cg_c4 = outputs['cg_systems:C4']
    assert x_cg_c4 == pytest.approx(18.75, abs=10)
    x_cg_c51 = outputs['cg_systems:C51']
    assert x_cg_c51 == pytest.approx(0.75, abs=10)
    x_cg_c52 = outputs['cg_systems:C52']
    assert x_cg_c52 == pytest.approx(16.62, abs=10)

    x_cg_d1 = outputs['cg_furniture:D1']
    assert x_cg_d1 == pytest.approx(0.0, abs=10)
    x_cg_d3 = outputs['cg_furniture:D3']
    assert x_cg_d3 == pytest.approx(29.4, abs=10)
    x_cg_d4 = outputs['cg_furniture:D4']
    assert x_cg_d4 == pytest.approx(16.62, abs=10)
    x_cg_d5 = outputs['cg_furniture:D5']
    assert x_cg_d5 == pytest.approx(16.62, abs=10)
    x_cg_pl = outputs['cg:cg_pax']
    assert x_cg_pl == pytest.approx(16.62, abs=10)
    x_cg_rear_fret = outputs['cg:cg_rear_fret']
    assert x_cg_rear_fret == pytest.approx(20.87, abs=10)
    x_cg_front_fret = outputs['cg:cg_front_fret']
    assert x_cg_front_fret == pytest.approx(9.94, abs=10)

# pylint: disable=too-many-statements
def _add_outputs(ivc: IndepVarComp, input_xml: XPathReader):
    """
    Add outputs needed for weight computation to ivc from given XML sample
    data.
    """
    [(lc1_u_gust, _)
        , (lc2_u_gust, _)] = input_xml.get_values_and_units(
        'Aircraft/weight/sizing_cases/SizingCase/U_gust')
    [(lc1_alt, _)
        , (lc1_alt, _)] = input_xml.get_values_and_units(
        'Aircraft/weight/sizing_cases/SizingCase/altitude')
    [(lc1_vc_eas, _)
        , (lc1_vc_eas, _)] = input_xml.get_values_and_units(
        'Aircraft/weight/sizing_cases/SizingCase/Vc_EAS')

    # Multiple use values -------------------------------------------------
    # When these values are used in next "sections", they are commented out
    ivc.add_output('tlar:NPAX',
                   val=input_xml.get_float('Aircraft/TLAR/NPAX'))
    ivc.add_output('geometry:wing_area', val=input_xml.get_float(
        'Aircraft/geometry/wing/wing_area'), units='m**2')
    ivc.add_output('geometry:wing_span', val=input_xml.get_float(
        'Aircraft/geometry/wing/span'), units='m')
    ivc.add_output('geometry:wing_b_50', val=input_xml.get_float(
        'Aircraft/geometry/wing/b_50'), units='m')
    ivc.add_output('geometry:wing_l2', val=input_xml.get_float(
        'Aircraft/geometry/wing/l2_wing'), units='m')
    ivc.add_output('geometry:fuselage_length', val=input_xml.get_float(
        'Aircraft/geometry/fuselage/fus_length'), units='m')
    ivc.add_output('geometry:fuselage_width_max', val=input_xml.get_float(
        'Aircraft/geometry/fuselage/width_max'), units='m')
    ivc.add_output('geometry:fuselage_height_max',
                   val=input_xml.get_float(
                       'Aircraft/geometry/fuselage/height_max'), units='m')
    ivc.add_output('geometry:engine_number', val=input_xml.get_float(
        'Aircraft/geometry/propulsion/engine_number'))
    ivc.add_output('weight:MTOW',
                   val=input_xml.get_float('Aircraft/weight/MTOW'), units='kg')
    ivc.add_output('weight:MFW',
                   val=input_xml.get_float('Aircraft/weight/MFW'), units='kg')
    ivc.add_output('cabin:NPAX1', val=int(
        input_xml.get_float('Aircraft/TLAR/NPAX') * 1.05))
    ivc.add_output('cabin:PNT',
                   val=input_xml.get_float('Aircraft/cabin/PNT'))
    ivc.add_output('cabin:PNC',
                   val=input_xml.get_float('Aircraft/cabin/PNC'))
    ivc.add_output('cabin:front_seat_number_eco', val=input_xml.get_float(
        'Aircraft/cabin/eco/front_seat_number'))
    # Load cases ----------------------------------------------------------
    # ivc.add_output('geometry:wing_area'
    # , val=input_xml.get_float('Aircraft/geometry/wing/wing_area'))
    # ivc.add_output('geometry:wing_span'
    # , val=input_xml.get_float('Aircraft/geometry/wing/span'))
    # ivc.add_output('weight:MZFW',
    #                val=input_xml.get_float('Aircraft/weight/MZFW'))
    # ivc.add_output('weight:MFW'
    # , val=input_xml.get_float('Aircraft/weight/MFW'))
    # ivc.add_output('weight:MTOW'
    # , val=input_xml.get_float('Aircraft/weight/MTOW'))
    ivc.add_output('aerodynamics:Cl_alpha', val=input_xml.get_float(
        'Aircraft/aerodynamics/CL_alpha'))
    ivc.add_output('loadcase1:U_gust', val=lc1_u_gust, units='m/s')
    ivc.add_output('loadcase1:altitude', val=lc1_alt, units='ft')
    ivc.add_output('loadcase1:Vc_EAS', val=lc1_vc_eas, units='kt')
    ivc.add_output('loadcase2:U_gust', val=lc2_u_gust, units='m/s')
    ivc.add_output('loadcase2:altitude', val=lc1_alt, units='ft')
    ivc.add_output('loadcase2:Vc_EAS', val=lc1_vc_eas, units='kt')
    # Wing Weight ---------------------------------------------------------
    # ivc.add_output('n1m1', val=241000)
    # ivc.add_output('n2m2', val=250000)
    # ivc.add_output('geometry:wing_area'
    # , val=input_xml.get_float('Aircraft/geometry/wing/wing_area'))
    # ivc.add_output('geometry:wing_span'
    # , val=input_xml.get_float('Aircraft/geometry/wing/span'))
    ivc.add_output('geometry:wing_toc_root', val=input_xml.get_float(
        'Aircraft/geometry/wing/toc/root'))
    ivc.add_output('geometry:wing_toc_kink', val=input_xml.get_float(
        'Aircraft/geometry/wing/toc/kink'))
    ivc.add_output('geometry:wing_toc_tip', val=input_xml.get_float(
        'Aircraft/geometry/wing/toc/tip'))
    # ivc.add_output('geometry:wing_l2'
    # , val=input_xml.get_float('Aircraft/geometry/wing/l2_wing'))
    ivc.add_output('geometry:wing_sweep_25', val=input_xml.get_float(
        'Aircraft/geometry/wing/sweep_25'), units='deg')
    ivc.add_output('geometry:wing_area_pf', val=input_xml.get_float(
        'Aircraft/geometry/wing/S_pf'), units='m**2')
    # ivc.add_output('weight:MTOW'
    # , val=input_xml.get_float('Aircraft/weight/MTOW'))
    # ivc.add_output('weight:MLW',
    #                 val=input_xml.get_float('Aircraft/weight/MLW'))
    ivc.add_output('kfactors_a1:K_A1', val=input_xml.get_float(
        'Aircraft/weight/k_factors/Wing_A1/A1/k'))
    ivc.add_output('kfactors_a1:offset_A1', val=input_xml.get_float(
        'Aircraft/weight/k_factors/Wing_A1/A1/offset'), units='kg')
    ivc.add_output('kfactors_a1:K_A11', val=input_xml.get_float(
        'Aircraft/weight/k_factors/Wing_A1/A11/k'))
    ivc.add_output('kfactors_a1:offset_A11', val=input_xml.get_float(
        'Aircraft/weight/k_factors/Wing_A1/A11/offset'), units='kg')
    ivc.add_output('kfactors_a1:K_A12', val=input_xml.get_float(
        'Aircraft/weight/k_factors/Wing_A1/A12/k'))
    ivc.add_output('kfactors_a1:offset_A12', val=input_xml.get_float(
        'Aircraft/weight/k_factors/Wing_A1/A12/offset'), units='kg')
    ivc.add_output('kfactors_a1:K_A13', val=input_xml.get_float(
        'Aircraft/weight/k_factors/Wing_A1/A13/k'))
    ivc.add_output('kfactors_a1:offset_A13', val=input_xml.get_float(
        'Aircraft/weight/k_factors/Wing_A1/A13/offset'), units='kg')
    ivc.add_output('kfactors_a1:K_A14', val=input_xml.get_float(
        'Aircraft/weight/k_factors/Wing_A1/A14/k'))
    ivc.add_output('kfactors_a1:offset_A14', val=input_xml.get_float(
        'Aircraft/weight/k_factors/Wing_A1/A14/offset'), units='kg')
    ivc.add_output('kfactors_a1:K_A15', val=input_xml.get_float(
        'Aircraft/weight/k_factors/Wing_A1/A15/k'))
    ivc.add_output('kfactors_a1:offset_A15', val=input_xml.get_float(
        'Aircraft/weight/k_factors/Wing_A1/A15/offset'), units='kg')
    ivc.add_output('kfactors_a1:K_voil', val=input_xml.get_float(
        'Aircraft/weight/k_factors/Wing_A1/K_voil'))
    ivc.add_output('kfactors_a1:K_mvo', val=input_xml.get_float(
        'Aircraft/weight/k_factors/Wing_A1/K_mvo'))
    # Fuselage Weight -----------------------------------------------------
    # ivc.add_output('n1m1', val=241000)
    ivc.add_output('geometry:fuselage_wet_area', input_xml.get_float(
        'Aircraft/geometry/fuselage/S_mbf'), units='m**2')
    # ivc.add_output('geometry:fuselage_width_max'
    # , val=input_xml.get_float('Aircraft/geometry/fuselage/width_max'))
    # ivc.add_output('geometry:fuselage_height_max'
    # , val=input_xml.get_float('Aircraft/geometry/fuselage/height_max'))
    ivc.add_output('kfactors_a2:K_A2', val=input_xml.get_float(
        'Aircraft/weight/k_factors/fuselage_A2/A2/k'))
    ivc.add_output('kfactors_a2:offset_A2', val=input_xml.get_float(
        'Aircraft/weight/k_factors/fuselage_A2/A2/offset'), units='kg')
    ivc.add_output('kfactors_a2:K_tr', val=input_xml.get_float(
        'Aircraft/weight/k_factors/fuselage_A2/K_tr'))
    ivc.add_output('kfactors_a2:K_fus', val=input_xml.get_float(
        'Aircraft/weight/k_factors/fuselage_A2/K_fus'))
    # Empennage Weight ----------------------------------------------------
    ivc.add_output('geometry:ht_area',
                   val=input_xml.get_float('Aircraft/geometry/ht/area'),
                   units='m**2')
    ivc.add_output('geometry:vt_area',
                   val=input_xml.get_float('Aircraft/geometry/vt/area'),
                   units='m**2')
    ivc.add_output('kfactors_a3:K_A31', val=input_xml.get_float(
        'Aircraft/weight/k_factors/empennage_A3/A31/k'))
    ivc.add_output('kfactors_a3:offset_A31', val=input_xml.get_float(
        'Aircraft/weight/k_factors/empennage_A3/A31/offset'), units='kg')
    ivc.add_output('kfactors_a3:K_A32', val=input_xml.get_float(
        'Aircraft/weight/k_factors/empennage_A3/A32/k'))
    ivc.add_output('kfactors_a3:offset_A32', val=input_xml.get_float(
        'Aircraft/weight/k_factors/empennage_A3/A32/offset'), units='kg')
    # Flight Control Weight -----------------------------------------------
    # ivc.add_output('n1m1', val=241000 )
    # ivc.add_output('n2m2': 250000 )
    # ivc.add_output('geometry:fuselage_length'
    # , val=input_xml.get_float('Aircraft/geometry/fuselage/fus_length'))
    # ivc.add_output('geometry:wing_b_50'
    # , val=input_xml.get_float('Aircraft/geometry/wing/b_50'))
    ivc.add_output('kfactors_a4:K_A4', val=input_xml.get_float(
        'Aircraft/weight/k_factors/flight_controls_A4/A4/k'))
    ivc.add_output('kfactors_a4:offset_A4', val=input_xml.get_float(
        'Aircraft/weight/k_factors/flight_controls_A4/A4/offset'), units='kg')
    ivc.add_output('kfactors_a4:K_fc', val=input_xml.get_float(
        'Aircraft/weight/k_factors/flight_controls_A4/K_fc'))
    # Landing Gear Weight -------------------------------------------------
    # ivc.add_output('weight:MTOW'
    # , val=input_xml.get_float('Aircraft/weight/MTOW'))
    ivc.add_output('kfactors_a5:K_A5', val=input_xml.get_float(
        'Aircraft/weight/k_factors/LG_A5/A5/k'))
    ivc.add_output('kfactors_a5:offset_A5', val=input_xml.get_float(
        'Aircraft/weight/k_factors/LG_A5/A5/offset'), units='kg')
    # Pylon Weight --------------------------------------------------------
    ivc.add_output('geometry:pylon_wet_area', val=input_xml.get_float(
        'Aircraft/geometry/propulsion/wet_area_pylon'), units='m**2')
    # ivc.add_output('geometry:engine_number'
    # , val=input_xml.get_float('Aircraft/geometry/propulsion/engine_number'))
    # ivc.add_output('weight_propulsion:B1'
    # , val=input_xml.get_float('Aircraft/weight/propulsion/weight_B1'))
    ivc.add_output('kfactors_a6:K_A6', val=input_xml.get_float(
        'Aircraft/weight/k_factors/pylon_A6/A6/k'))
    ivc.add_output('kfactors_a6:offset_A6', val=input_xml.get_float(
        'Aircraft/weight/k_factors/pylon_A6/A6/offset'), units='kg')
    # Paint Weight --------------------------------------------------------
    ivc.add_output('geometry:S_total',
                   val=input_xml.get_float('Aircraft/geometry/S_total'),
                   units='m**2')
    ivc.add_output('kfactors_a7:K_A7', val=input_xml.get_float(
        'Aircraft/weight/k_factors/paint_A7/A7/k'))
    ivc.add_output('kfactors_a7:offset_A7', val=input_xml.get_float(
        'Aircraft/weight/k_factors/paint_A7/A7/offset'), units='kg')
    # Engine Weight -------------------------------------------------------
    ivc.add_output('propulsion_conventional:thrust_SL',
                   val=input_xml.get_float(
                       'Aircraft/propulsion/conventional/thrust_SL'),
                   units='lbf')
    # ivc.add_output('geometry:engine_number'
    # , val=input_xml.get_float('Aircraft/geometry/propulsion/engine_number'))
    ivc.add_output('kfactors_b1:K_B1', val=input_xml.get_float(
        'Aircraft/weight/k_factors/propulsion_B1/B1/k'))
    ivc.add_output('kfactors_b1:offset_B1', val=input_xml.get_float(
        'Aircraft/weight/k_factors/propulsion_B1/B1/offset'), units='kg')
    # Fuel Lines Weight ---------------------------------------------------
    # ivc.add_output('geometry:wing_b_50'
    # , val=input_xml.get_float('Aircraft/geometry/wing/b_50'))
    # ivc.add_output('weight:MFW'
    # , val=input_xml.get_float('Aircraft/weight/MFW'))
    # ivc.add_output('weight_propulsion:B1'
    # , val=input_xml.get_float('Aircraft/weight/propulsion/weight_B1'))
    ivc.add_output('kfactors_b2:K_B2', val=input_xml.get_float(
        'Aircraft/weight/k_factors/fuel_lines_B2/B2/k'))
    ivc.add_output('kfactors_b2:offset_B2', val=input_xml.get_float(
        'Aircraft/weight/k_factors/fuel_lines_B2/B2/offset'), units='kg')
    # Unconsumables Weight ------------------------------------------------
    # ivc.add_output('geometry:engine_number'
    # , val=input_xml.get_float('Aircraft/geometry/propulsion/engine_number'))
    # ivc.add_output('weight:MFW'
    # , val=input_xml.get_float('Aircraft/weight/MFW'))
    ivc.add_output('kfactors_b3:K_B3', val=input_xml.get_float(
        'Aircraft/weight/k_factors/unconsumables_B3/B3/k'))
    ivc.add_output('kfactors_b3:offset_B3', val=input_xml.get_float(
        'Aircraft/weight/k_factors/unconsumables_B3/B3/offset'), units='kg')
    # Power Systems Weight ------------------------------------------------
    # ivc.add_output('cabin:NPAX1'
    # , val=150)  # input_xml.get_float('Aircraft/cabin/NPAX1'))
    # ivc.add_output('weight_airframe:A4', val=700,
    # ivc.add_output('weight:MTOW'
    # , val=input_xml.get_float('Aircraft/weight/MTOW'))
    ivc.add_output('kfactors_c1:K_C11', val=input_xml.get_float(
        'Aircraft/weight/k_factors/power_systems_C1/C11/k'))
    ivc.add_output('kfactors_c1:offset_C11', val=input_xml.get_float(
        'Aircraft/weight/k_factors/power_systems_C1/C11/offset'), units='kg')
    ivc.add_output('kfactors_c1:K_C12', val=input_xml.get_float(
        'Aircraft/weight/k_factors/power_systems_C1/C12/k'))
    ivc.add_output('kfactors_c1:offset_C12', val=input_xml.get_float(
        'Aircraft/weight/k_factors/power_systems_C1/C12/offset'), units='kg')
    ivc.add_output('kfactors_c1:K_C13', val=input_xml.get_float(
        'Aircraft/weight/k_factors/power_systems_C1/C13/k'))
    ivc.add_output('kfactors_c1:offset_C13', val=input_xml.get_float(
        'Aircraft/weight/k_factors/power_systems_C1/C13/offset'), units='kg')
    ivc.add_output('kfactors_c1:K_elec', val=input_xml.get_float(
        'Aircraft/weight/k_factors/power_systems_C1/K_elec'))
    # Life Support Systems Weight -----------------------------------------
    # ivc.add_output('geometry:fuselage_width_max'
    # , val=input_xml.get_float('Aircraft/geometry/fuselage/width_max'))
    # ivc.add_output('geometry:fuselage_height_max'
    # , val=input_xml.get_float('Aircraft/geometry/fuselage/height_max'))
    ivc.add_output('geometry:fuselage_Lcabin',
                   val=0.8 * input_xml.get_float(
                       'Aircraft/geometry/fuselage/fus_length'), units='m')
    ivc.add_output('geometry:wing_sweep_0', val=input_xml.get_float(
        'Aircraft/geometry/wing/sweep_0'), units='deg')
    ivc.add_output('geometry:nacelle_dia', val=input_xml.get_float(
        'Aircraft/geometry/propulsion/nacelle_dia'), units='m')
    # ivc.add_output('geometry:engine_number'
    # , val=input_xml.get_float('Aircraft/geometry/propulsion/engine_number'))
    # ivc.add_output('cabin:NPAX1'
    # , val=150,  # input_xml.get_float('Aircraft/cabin/NPAX1'))
    # ivc.add_output('cabin:PNT'
    # , val=input_xml.get_float('Aircraft/cabin/PNT'))
    # ivc.add_output('cabin:PNC'
    # , val=input_xml.get_float('Aircraft/cabin/PNC'))
    # ivc.add_output('geometry:wing_span'
    # , val=input_xml.get_float('Aircraft/geometry/wing/span'))
    # ivc.add_output('weight_propulsion:B1'
    # , val=input_xml.get_float('Aircraft/weight/propulsion/weight_B1'))
    ivc.add_output('kfactors_c2:K_C21', val=input_xml.get_float(
        'Aircraft/weight/k_factors/LSS_C2/C21/k'))
    ivc.add_output('kfactors_c2:offset_C21', val=input_xml.get_float(
        'Aircraft/weight/k_factors/LSS_C2/C21/offset'), units='kg')
    ivc.add_output('kfactors_c2:K_C22', val=input_xml.get_float(
        'Aircraft/weight/k_factors/LSS_C2/C22/k'))
    ivc.add_output('kfactors_c2:offset_C22', val=input_xml.get_float(
        'Aircraft/weight/k_factors/LSS_C2/C22/offset'), units='kg')
    ivc.add_output('kfactors_c2:K_C23', val=input_xml.get_float(
        'Aircraft/weight/k_factors/LSS_C2/C23/k'))
    ivc.add_output('kfactors_c2:offset_C23', val=input_xml.get_float(
        'Aircraft/weight/k_factors/LSS_C2/C23/offset'), units='kg')
    ivc.add_output('kfactors_c2:K_C24', val=input_xml.get_float(
        'Aircraft/weight/k_factors/LSS_C2/C24/k'))
    ivc.add_output('kfactors_c2:offset_C24', val=input_xml.get_float(
        'Aircraft/weight/k_factors/LSS_C2/C24/offset'), units='kg')
    ivc.add_output('kfactors_c2:K_C25', val=input_xml.get_float(
        'Aircraft/weight/k_factors/LSS_C2/C25/k'))
    ivc.add_output('kfactors_c2:offset_C25', val=input_xml.get_float(
        'Aircraft/weight/k_factors/LSS_C2/C25/offset'), units='kg')
    ivc.add_output('kfactors_c2:K_C26', val=input_xml.get_float(
        'Aircraft/weight/k_factors/LSS_C2/C26/k'))
    ivc.add_output('kfactors_c2:offset_C26', val=input_xml.get_float(
        'Aircraft/weight/k_factors/LSS_C2/C26/offset'), units='kg')
    ivc.add_output('kfactors_c2:K_C27', val=input_xml.get_float(
        'Aircraft/weight/k_factors/LSS_C2/C27/k'))
    ivc.add_output('kfactors_c2:offset_C27', val=input_xml.get_float(
        'Aircraft/weight/k_factors/LSS_C2/C27/offset'), units='kg')
    # Navigation Systems Weight -------------------------------------------
    # ivc.add_output('geometry:fuselage_length'
    # , val=input_xml.get_float('Aircraft/geometry/fuselage/fus_length'))
    # ivc.add_output('geometry:wing_b_50'
    # , val=input_xml.get_float('Aircraft/geometry/wing/b_50'))
    ivc.add_output('kfactors_c3:K_C3', val=input_xml.get_float(
        'Aircraft/weight/k_factors/instrument_navigation_C3/C3/k'))
    ivc.add_output('kfactors_c3:offset_C3', val=input_xml.get_float(
        'Aircraft/weight/k_factors/instrument_navigation_C3/C3/offset'),
                   units='kg')
    # Transmission Systems Weight -----------------------------------------
    ivc.add_output('kfactors_c4:K_C4', val=input_xml.get_float(
        'Aircraft/weight/k_factors/transmissions_C4/C4/k'))
    ivc.add_output('kfactors_c4:offset_C4', val=input_xml.get_float(
        'Aircraft/weight/k_factors/transmissions_C4/C4/offset'), units='kg')
    # Fixed Operational Systems Weight ------------------------------------
    ivc.add_output('geometry:fuselage_LAV', val=input_xml.get_float(
        'Aircraft/geometry/fuselage/LAV'), units='m')
    ivc.add_output('geometry:fuselage_LAR', val=input_xml.get_float(
        'Aircraft/geometry/fuselage/LAR'), units='m')
    # ivc.add_output('geometry:fuselage_length'
    # , val=input_xml.get_float('Aircraft/geometry/fuselage/fus_length'))
    # ivc.add_output('cabin:front_seat_number_eco'
    # , val=input_xml.get_float('Aircraft/cabin/eco/front_seat_number'))
    # ivc.add_output('geometry:wing_l2'
    # , val=input_xml.get_float('Aircraft/geometry/wing/l2_wing'))
    ivc.add_output('cabin:container_number_front',
                   val=input_xml.get_float(
                       'Aircraft/cabin/container_number_front'))
    ivc.add_output('kfactors_c5:K_C5', val=input_xml.get_float(
        'Aircraft/weight/k_factors/FOS_C5/C5/k'))
    ivc.add_output('kfactors_c5:offset_C5', val=input_xml.get_float(
        'Aircraft/weight/k_factors/FOS_C5/C5/offset'), units='kg')
    # Flight Kit Weight ---------------------------------------------------
    ivc.add_output('kfactors_c6:K_C6', val=input_xml.get_float(
        'Aircraft/weight/k_factors/flight_kit_C6/C6/k'))
    ivc.add_output('kfactors_c6:offset_C6', val=input_xml.get_float(
        'Aircraft/weight/k_factors/flight_kit_C6/C6/offset'), units='kg')
    # Cargo configuration Weight ------------------------------------------
    # ivc.add_output('cabin:NPAX1'
    # , val=150)  # input_xml.get_float('Aircraft/cabin/NPAX1'))
    ivc.add_output('cabin:container_number', val=input_xml.get_float(
        'Aircraft/cabin/container_number'))
    ivc.add_output('cabin:pallet_number', val=input_xml.get_float(
        'Aircraft/cabin/pallet_number'))
    # ivc.add_output('cabin:front_seat_number_eco'
    # , val=input_xml.get_float('Aircraft/cabin/eco/front_seat_number'))
    ivc.add_output('kfactors_d1:K_D1', val=input_xml.get_float(
        'Aircraft/weight/k_factors/cargo_cfg_D1/D1/k'))
    ivc.add_output('kfactors_d1:offset_D1', val=input_xml.get_float(
        'Aircraft/weight/k_factors/cargo_cfg_D1/D1/offset'), units='kg')
    # Passenger Seats Weight ----------------------------------------------
    # ivc.add_output('tlar:NPAX'
    # , val=input_xml.get_float('Aircraft/TLAR/NPAX'))
    ivc.add_output('kfactors_d2:K_D2', val=input_xml.get_float(
        'Aircraft/weight/k_factors/passenger_seat_D2/D2/k'))
    ivc.add_output('kfactors_d2:offset_D2', val=input_xml.get_float(
        'Aircraft/weight/k_factors/passenger_seat_D2/D2/offset'), units='kg')
    # Food Water Weight ---------------------------------------------------
    # ivc.add_output('tlar:NPAX'
    # , val=input_xml.get_float('Aircraft/TLAR/NPAX'))
    ivc.add_output('kfactors_d3:K_D3', val=input_xml.get_float(
        'Aircraft/weight/k_factors/food_water_D3/D3/k'))
    ivc.add_output('kfactors_d3:offset_D3', val=input_xml.get_float(
        'Aircraft/weight/k_factors/food_water_D3/D3/offset'), units='kg')
    # Security Kit Weight -------------------------------------------------
    # ivc.add_output('tlar:NPAX'
    # , val=input_xml.get_float('Aircraft/TLAR/NPAX'))
    ivc.add_output('kfactors_d4:K_D4', val=input_xml.get_float(
        'Aircraft/weight/k_factors/security_kit_D4/D4/k'))
    ivc.add_output('kfactors_d4:offset_D4', val=input_xml.get_float(
        'Aircraft/weight/k_factors/security_kit_D4/D4/offset'), units='kg')
    # Toilets Weight ------------------------------------------------------
    # ivc.add_output('tlar:NPAX'
    # , val=input_xml.get_float('Aircraft/TLAR/NPAX'))
    ivc.add_output('kfactors_d5:K_D5', val=input_xml.get_float(
        'Aircraft/weight/k_factors/toilet_D5/D5/k'))
    ivc.add_output('kfactors_d5:offset_D5', val=input_xml.get_float(
        'Aircraft/weight/k_factors/toilet_D5/D5/offset'), units='kg')
    # Crew Weight ---------------------------------------------------------
    # ivc.add_output('cabin:PNT'
    # , val=input_xml.get_float('Aircraft/cabin/PNT'))
    # ivc.add_output('cabin:PNC'
    # , val=input_xml.get_float('Aircraft/cabin/PNC'))
