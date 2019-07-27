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
from tests.testing_utilities import run_system

import pytest
from openmdao.core.indepvarcomp import IndepVarComp
from openmdao.core.problem import Problem

from fastoad.io.xml import XPathReader
from fastoad.io.xml.openmdao_basic_io import OpenMdaoXmlIO
from fastoad.io.xml.openmdao_legacy_io import OpenMdaoLegacy1XmlIO
from fastoad.modules.geometry.geom_components.fuselage \
    import ComputeFuselageGeometry
from fastoad.modules.geometry.geom_components.ht.components \
    import ComputeHTArea, ComputeHTcg, ComputeHTMAC, ComputeHTChord, \
            ComputeHTClalpha, ComputeHTSweep, ComputeHTVolCoeff
from fastoad.modules.geometry.geom_components.ht \
    import ComputeHorizontalTailGeometry
from fastoad.modules.geometry.geom_components.vt.components \
    import ComputeVTArea, ComputeVTcg, ComputeVTMAC, ComputeVTChords, \
            ComputeVTClalpha, ComputeCnBeta, ComputeVTSweep, \
                ComputeVTVolCoeff, ComputeVTDistance
from fastoad.modules.geometry.geom_components.vt \
    import ComputeVerticalTailGeometry

from fastoad.modules.geometry.geom_components.wing.components \
    import ComputeB50

@pytest.fixture(scope="module")
def xpath_reader() -> XPathReader:
    """
    :return: access to the sample xml data
    """
    return XPathReader(
        pth.join(pth.dirname(__file__), "data", "CeRAS01_baseline.xml"))

@pytest.fixture(scope="module")
def input_xml() -> OpenMdaoLegacy1XmlIO:
    """
    :return: access to the sample xml data
    """
    # TODO: have more consistency in input data (no need for the whole CeRAS01_baseline.xml)
    return OpenMdaoLegacy1XmlIO(
        pth.join(pth.dirname(__file__), "data", "CeRAS01_baseline.xml"))

def test_compute_fuselage(xpath_reader: XPathReader, input_xml):
    """ Tests computation of the fuselage """

    input_list = [
        'cabin:WSeco',
        'cabin:LSeco',
        'cabin:front_seat_number_eco',
        'cabin:Waisle',
        'cabin:Wexit',
        'tlar:NPAX',
        'geometry:engine_number'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeFuselageGeometry(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    NPAX1 = problem['cabin:NPAX1']
    assert NPAX1 == pytest.approx(157, abs=1)
    Nrows = problem['cabin:Nrows']
    assert Nrows == pytest.approx(26, abs=1)
    cg_systems_c6 = problem['cg_systems:C6']
    assert cg_systems_c6 == pytest.approx(7.47, abs=1e-2)
    cg_furniture_d2 = problem['cg_furniture:D2']
    assert cg_furniture_d2 == pytest.approx(16.62, abs=1e-2)
    cg_pl_cg_pax = problem['cg_pl:CG_PAX']
    assert cg_pl_cg_pax == pytest.approx(16.62, abs=1e-2)
    fuselage_length = problem['geometry:fuselage_length']
    assert fuselage_length == pytest.approx(37.507, abs=1e-3)
    fuselage_width_max = problem['geometry:fuselage_width_max']
    assert fuselage_width_max == pytest.approx(3.92, abs=1e-2)
    fuselage_height_max = problem['geometry:fuselage_height_max']
    assert fuselage_height_max == pytest.approx(4.06, abs=1e-2)
    fuselage_LAV = problem['geometry:fuselage_LAV']
    assert fuselage_LAV == pytest.approx(6.902, abs=1e-3)
    fuselage_LAR = problem['geometry:fuselage_LAR']
    assert fuselage_LAR == pytest.approx(14.616, abs=1e-3)
    fuselage_Lpax = problem['geometry:fuselage_Lpax']
    assert fuselage_Lpax == pytest.approx(22.87, abs=1e-2)
    fuselage_Lcabin = problem['geometry:fuselage_Lcabin']
    assert fuselage_Lcabin == pytest.approx(30.38, abs=1e-2)
    fuselage_wet_area = problem['geometry:fuselage_wet_area']
    assert fuselage_wet_area == pytest.approx(401.956, abs=1e-3)
    pnc = problem['cabin:PNC']
    assert pnc == pytest.approx(4, abs=1)


def test_compute_ht_area(xpath_reader: XPathReader, input_xml):
    """ Tests computation of the horizontal tail area """

    input_list = [
        'geometry:fuselage_length',
        'geometry:wing_position',
        'geometry:ht_vol_coeff',
        'geometry:wing_l0',
        'geometry:wing_area',
        'geometry:ht_area'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeHTArea(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    lp = problem['geometry:ht_lp']
    assert lp == pytest.approx(17.675, abs=1e-3)
    wet_area = problem['geometry:ht_wet_area']
    assert wet_area == pytest.approx(70.34, abs=1e-2)
    delta_cm_takeoff = problem['delta_cm_takeoff']
    assert delta_cm_takeoff == pytest.approx(0.000177, abs=1e-6)


def test_compute_ht_cg(xpath_reader: XPathReader, input_xml):
    """ Tests computation of the horizontal tail center of gravity """

    input_list = [
        'geometry:ht_root_chord',
        'geometry:ht_tip_chord',
        'geometry:ht_lp',
        'geometry:ht_span',
        'geometry:wing_position',
        'geometry:ht_sweep_25',
        'geometry:ht_length'
    ]

    input_vars = input_xml.read(only=input_list)

    input_vars.add_output('geometry:ht_x0', 1.656)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeHTcg(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    cg_a31 = problem['cg_airframe:A31']
    assert cg_a31 == pytest.approx(34.58, abs=1e-2)


def test_compute_ht_mac(xpath_reader: XPathReader, input_xml):
    """ Tests computation of the horizontal tail mac """

    input_list = [
        'geometry:ht_root_chord',
        'geometry:ht_tip_chord',
        'geometry:ht_span',
        'geometry:ht_sweep_25'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeHTMAC(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    length = problem['geometry:ht_length']
    assert length == pytest.approx(3.141, abs=1e-3)
    x0 = problem['geometry:ht_x0']
    assert x0 == pytest.approx(1.656, abs=1e-3)
    y0 = problem['geometry:ht_y0']
    assert y0 == pytest.approx(2.519, abs=1e-3)


def test_compute_ht_chord(xpath_reader: XPathReader, input_xml):
    """ Tests computation of the horizontal tail chords """

    input_list = [
        'geometry:ht_aspect_ratio',
        'geometry:ht_area',
        'geometry:ht_taper_ratio'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeHTChord(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    span = problem['geometry:ht_span']
    assert span == pytest.approx(12.28, abs=1e-2)
    root_chord = problem['geometry:ht_root_chord']
    assert root_chord == pytest.approx(4.406, abs=1e-3)
    tip_chord = problem['geometry:ht_tip_chord']
    assert tip_chord == pytest.approx(1.322, abs=1e-3)


def test_compute_ht_cl(xpath_reader: XPathReader, input_xml):
    """ Tests computation of the horizontal tail lift coefficient """

    input_list = [
        'geometry:ht_aspect_ratio',
        'tlar:cruise_Mach',
        'geometry:ht_sweep_25'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeHTClalpha(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    cl = problem['aerodynamics:Cl_alpha_ht']
    assert cl == pytest.approx(3.47, abs=1e-2)


def test_compute_ht_sweep(xpath_reader: XPathReader, input_xml):
    """ Tests computation of the horizontal tail sweep """

    input_list = [
        'geometry:ht_root_chord',
        'geometry:ht_tip_chord',
        'geometry:ht_span',
        'geometry:ht_sweep_25'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeHTSweep(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    sweep_0 = problem['geometry:ht_sweep_0']
    assert sweep_0 == pytest.approx(33.317, abs=1e-3)
    sweep_100 = problem['geometry:ht_sweep_100']
    assert sweep_100 == pytest.approx(8.81, abs=1e-2)


def test_compute_ht_vol_co(xpath_reader: XPathReader, input_xml):
    """ Tests computation of the horizontal volume coeeficient """

    input_list = [
        'cg_airframe:A51',
        'cg_airframe:A52',
        'weight:MTOW',
        'geometry:wing_area',
        'geometry:wing_l0',
        'cg:required_cg_range'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeHTVolCoeff(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    delta_lg = problem['delta_lg']
    assert delta_lg == pytest.approx(12.93, abs=1e-2)
    vol_coeff = problem['geometry:ht_vol_coeff']
    assert vol_coeff == pytest.approx(1.117, abs=1e-3)


def test_geometry_global_ht(xpath_reader: XPathReader, input_xml):
    """ Tests computation of the global HT geometry components """

    input_list = [
        'cg_airframe:A51',
        'cg_airframe:A52',
        'weight:MTOW',
        'geometry:wing_area',
        'geometry:wing_l0',
        'cg:required_cg_range',
        'geometry:fuselage_length',
        'geometry:wing_position',
        'geometry:ht_area',
        'geometry:ht_taper_ratio',
        'geometry:ht_aspect_ratio',
        'geometry:ht_sweep_25',
        'tlar:cruise_Mach'        
    ]

    input_vars = input_xml.read(only=input_list)

    problem = Problem()
    model = problem.model
    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', ComputeHorizontalTailGeometry(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()

    delta_lg = problem['delta_lg']
    assert delta_lg == pytest.approx(12.93, abs=1e-2)
    vol_coeff = problem['geometry:ht_vol_coeff']
    assert vol_coeff == pytest.approx(1.117, abs=1e-3)
    lp = problem['geometry:ht_lp']
    assert lp == pytest.approx(17.675, abs=1e-3)
    wet_area = problem['geometry:ht_wet_area']
    assert wet_area == pytest.approx(70.34, abs=1e-2)
    delta_cm_takeoff = problem['delta_cm_takeoff']
    assert delta_cm_takeoff == pytest.approx(0.000138, abs=1e-6)
    span = problem['geometry:ht_span']
    assert span == pytest.approx(12.28, abs=1e-2)
    root_chord = problem['geometry:ht_root_chord']
    assert root_chord == pytest.approx(4.406, abs=1e-3)
    tip_chord = problem['geometry:ht_tip_chord']
    assert tip_chord == pytest.approx(1.322, abs=1e-3)
    length = problem['geometry:ht_length']
    assert length == pytest.approx(3.141, abs=1e-3)
    x0 = problem['geometry:ht_x0']
    assert x0 == pytest.approx(1.656, abs=1e-3)
    y0 = problem['geometry:ht_y0']
    assert y0 == pytest.approx(2.519, abs=1e-3)
    cg_a31 = problem['cg_airframe:A31']
    assert cg_a31 == pytest.approx(34.58, abs=1e-2)
    sweep_0 = problem['geometry:ht_sweep_0']
    assert sweep_0 == pytest.approx(33.317, abs=1e-3)
    sweep_100 = problem['geometry:ht_sweep_100']
    assert sweep_100 == pytest.approx(8.81, abs=1e-2)
    cl = problem['aerodynamics:Cl_alpha_ht']
    assert cl == pytest.approx(3.47, abs=1e-2)


def test_compute_vt_cn(xpath_reader: XPathReader, input_xml):
    """ Tests computation of the yawing moment due to sideslip """

    input_list = [
        'geometry:fuselage_length',
        'geometry:fuselage_width_max',
        'geometry:fuselage_height_max',
        'geometry:fuselage_LAV',
        'geometry:fuselage_LAR',
        'tlar:cruise_Mach',
        'geometry:wing_area',
        'geometry:wing_span'
    ]

    input_vars = input_xml.read(only=input_list)

    component = ComputeCnBeta()

    problem = run_system(component, input_vars)

    dcn_beta = problem['dcn_beta']
    assert dcn_beta == pytest.approx(0.258348, abs=1e-6)

def test_compute_vt_area(xpath_reader: XPathReader, input_xml):
    """ Tests computation of the vertical tail area """

    input_list = [
        'geometry:wing_l0',
        'geometry:wing_area',
        'geometry:wing_span',
        'geometry:vt_lp', 
        'geometry:vt_area', 
        'aerodynamics:Cl_alpha_vt'
    ]

    input_vars = input_xml.read(only=input_list)

    input_vars.add_output('cg_ratio', 0.364924)
    input_vars.add_output('dcn_beta', 0.258348)

    component = ComputeVTArea()

    problem = run_system(component, input_vars)

    wet_area = problem['geometry:vt_wet_area']
    assert wet_area == pytest.approx(52.75, abs=1e-2)
    delta_cn = problem['delta_cn']
    assert delta_cn == pytest.approx(0.002014, abs=1e-6)


def test_compute_vt_cg(xpath_reader: XPathReader, input_xml):
    """ Tests computation of the vertical tail center of gravity """

    input_list = [
        'geometry:vt_root_chord',
        'geometry:vt_tip_chord',
        'geometry:vt_lp',
        'geometry:vt_span',
        'geometry:wing_position',
        'geometry:vt_sweep_25',
        'geometry:vt_length'
    ]

    input_vars = input_xml.read(only=input_list)

    input_vars.add_output('geometry:vt_x0', 2.321)

    component = ComputeVTcg()

    problem = run_system(component, input_vars)

    cg_a32 = problem['cg_airframe:A32']
    assert cg_a32 == pytest.approx(35.11, abs=1e-2)


def test_compute_vt_mac(xpath_reader: XPathReader, input_xml):
    """ Tests computation of the vertical tail mac """

    input_list = [
        'geometry:vt_root_chord',
        'geometry:vt_tip_chord',
        'geometry:vt_span',
        'geometry:vt_sweep_25'
    ]

    input_vars = input_xml.read(only=input_list)

    component = ComputeVTMAC()

    problem = run_system(component, input_vars)

    length = problem['geometry:vt_length']
    assert length == pytest.approx(4.161, abs=1e-3)
    x0 = problem['geometry:vt_x0']
    assert x0 == pytest.approx(2.321, abs=1e-3)
    z0 = problem['geometry:vt_z0']
    assert z0 == pytest.approx(2.716, abs=1e-3)


def test_compute_vt_chords(xpath_reader: XPathReader, input_xml):
    """ Tests computation of the vertical tail chords """

    input_list = [
        'geometry:vt_aspect_ratio',
        'geometry:vt_area',
        'geometry:vt_taper_ratio'
    ]

    input_vars = input_xml.read(only=input_list)

    component = ComputeVTChords()

    problem = run_system(component, input_vars)

    span = problem['geometry:vt_span']
    assert span == pytest.approx(6.62, abs=1e-2)
    root_chord = problem['geometry:vt_root_chord']
    assert root_chord == pytest.approx(5.837, abs=1e-3)
    tip_chord = problem['geometry:vt_tip_chord']
    assert tip_chord == pytest.approx(1.751, abs=1e-3)


def test_compute_vt_sweep(xpath_reader: XPathReader, input_xml):
    """ Tests computation of the vertical tail sweep """

    input_list = [
        'geometry:vt_root_chord',
        'geometry:vt_tip_chord',
        'geometry:vt_span',
        'geometry:vt_sweep_25'
    ]

    input_vars = input_xml.read(only=input_list)

    component = ComputeVTSweep()

    problem = run_system(component, input_vars)

    sweep_0 = problem['geometry:vt_sweep_0']
    assert sweep_0 == pytest.approx(40.515, abs=1e-3)
    sweep_100 = problem['geometry:vt_sweep_100']
    assert sweep_100 == pytest.approx(13.35, abs=1e-2)


def test_compute_vt_distance(xpath_reader: XPathReader, input_xml):
    """ Tests computation of the vertical tail distance """

    input_list = [
        'geometry:fuselage_length',
        'geometry:wing_position'
    ]

    input_vars = input_xml.read(only=input_list)


    component = ComputeVTDistance()

    problem = run_system(component, input_vars)

    lp_vt = problem['geometry:vt_lp']
    assert lp_vt == pytest.approx(16.55, abs=1e-2)
    k_ar_effective = problem['k_ar_effective']
    assert k_ar_effective == pytest.approx(1.55, abs=1e-2)

def test_compute_vt_cl(xpath_reader: XPathReader, input_xml):
    """ Tests computation of the vertical tail lift coefficient """

    input_list = [
        'geometry:vt_aspect_ratio',
        'tlar:cruise_Mach',
        'geometry:vt_sweep_25'
    ]

    input_vars = input_xml.read(only=input_list)

    input_vars.add_output('k_ar_effective', 1.55)

    component = ComputeVTClalpha()

    problem = run_system(component, input_vars)

    cl = problem['aerodynamics:Cl_alpha_vt']
    assert cl == pytest.approx(2.55, abs=1e-2)


def test_compute_vt_vol_co(xpath_reader: XPathReader, input_xml):
    """ Tests computation of the vertical volume coefficient """

    input_list = [
        'geometry:vt_area',
        'geometry:vt_lp',
        'geometry:wing_area',
        'geometry:wing_span',
    ]

    input_vars = input_xml.read(only=input_list)

    component = ComputeVTVolCoeff()

    problem = run_system(component, input_vars)
    
    vol_coeff = problem['geometry:vt_vol_coeff']
    assert vol_coeff == pytest.approx(0.105, abs=1e-3)


def test_geometry_global_vt(xpath_reader: XPathReader, input_xml):
    """ Tests computation of the global VT geometry components """

    input_list = [
        'geometry:wing_area',
        'geometry:fuselage_length',
        'geometry:wing_position',
        'geometry:vt_area',
        'geometry:vt_taper_ratio',
        'geometry:vt_aspect_ratio',
        'geometry:vt_sweep_25',
        'geometry:fuselage_LAR',
        'geometry:fuselage_LAV',
        'geometry:fuselage_height_max',
        'geometry:fuselage_width_max',
        'geometry:wing_span',
        'tlar:cruise_Mach',
        'geometry:wing_l0'
    ]

    input_vars = input_xml.read(only=input_list)

    input_vars.add_output('cg_ratio', 0.364924)

    component = ComputeVerticalTailGeometry()

    problem = run_system(component, input_vars)

    dcn_beta = problem['dcn_beta']
    assert dcn_beta == pytest.approx(0.258348, abs=1e-6)
    wet_area = problem['geometry:vt_wet_area']
    assert wet_area == pytest.approx(52.75, abs=1e-2)
    delta_cn = problem['delta_cn']
    assert delta_cn == pytest.approx(0.001641, abs=1e-6)
    length = problem['geometry:vt_length']
    assert length == pytest.approx(4.161, abs=1e-3)
    x0 = problem['geometry:vt_x0']
    assert x0 == pytest.approx(2.321, abs=1e-3)
    z0 = problem['geometry:vt_z0']
    assert z0 == pytest.approx(2.716, abs=1e-3)
    # cg_a32 = problem['cg_airframe:A32']
    # assert cg_a32 == pytest.approx(35.11, abs=1e-2)
    span = problem['geometry:vt_span']
    assert span == pytest.approx(6.62, abs=1e-2)
    root_chord = problem['geometry:vt_root_chord']
    assert root_chord == pytest.approx(5.837, abs=1e-3)
    tip_chord = problem['geometry:vt_tip_chord']
    assert tip_chord == pytest.approx(1.751, abs=1e-3)
    sweep_0 = problem['geometry:vt_sweep_0']
    assert sweep_0 == pytest.approx(40.514, abs=1e-3)
    sweep_100 = problem['geometry:vt_sweep_100']
    assert sweep_100 == pytest.approx(13.35, abs=1e-2)
    lp_vt = problem['geometry:vt_lp']
    assert lp_vt == pytest.approx(16.55, abs=1e-2)
    k_ar_effective = problem['k_ar_effective']
    assert k_ar_effective == pytest.approx(1.55, abs=1e-2)    
    cl = problem['aerodynamics:Cl_alpha_vt']
    assert cl == pytest.approx(2.55, abs=1e-2)
    vol_coeff = problem['geometry:vt_vol_coeff']
    assert vol_coeff == pytest.approx(0.105, abs=1e-3)

def test_geometry_wing_b50(xpath_reader: XPathReader, input_xml):
    """ Tests computation of the wing B50 """

    input_list = [
        'geometry:wing_x4',
        'geometry:wing_y2',
        'geometry:wing_y4',
        'geometry:wing_l1',
        'geometry:wing_l4',
        'geometry:wing_span'
    ]

    input_vars = input_xml.read(only=input_list)

    component = ComputeB50()

    problem = run_system(component, input_vars)

    wing_b_50 = problem['geometry:wing_b_50']
    assert wing_b_50 == pytest.approx(34.166, abs=1e-3)