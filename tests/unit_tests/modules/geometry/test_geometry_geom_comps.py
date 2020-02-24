"""
Test module for geometry functions of cg components
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA/ISAE
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

import pytest

from fastoad.io.xml.openmdao_legacy_io import OMLegacy1XmlIO
from fastoad.modules.geometry.geom_components import ComputeTotalArea, UpdateMLG
from fastoad.modules.geometry.geom_components.fuselage import ComputeFuselageGeometryBasic, \
    ComputeFuselageGeometryCabinSizing
from fastoad.modules.geometry.geom_components.fuselage.compute_cnbeta_fuselage import \
    ComputeCnBetaFuselage
from fastoad.modules.geometry.geom_components.ht import ComputeHorizontalTailGeometry
from fastoad.modules.geometry.geom_components.ht.components import ComputeHTArea, ComputeHTcg, \
    ComputeHTMAC, ComputeHTChord, ComputeHTClalpha, ComputeHTSweep, ComputeHTVolCoeff
from fastoad.modules.geometry.geom_components.nacelle_pylons.compute_nacelle_pylons import \
    ComputeNacelleAndPylonsGeometry
from fastoad.modules.geometry.geom_components.vt import ComputeVerticalTailGeometry
from fastoad.modules.geometry.geom_components.vt.components import ComputeVTArea, ComputeVTcg, \
    ComputeVTMAC, ComputeVTChords, ComputeVTClalpha, ComputeVTSweep, ComputeVTVolCoeff, \
    ComputeVTDistance
from fastoad.modules.geometry.geom_components.wing import ComputeWingGeometry
from fastoad.modules.geometry.geom_components.wing.components import ComputeB50, ComputeCLalpha, \
    ComputeL1AndL4Wing, ComputeL2AndL3Wing, ComputeMACWing, ComputeMFW, ComputeSweepWing, \
    ComputeToCWing, ComputeWetAreaWing, ComputeXWing, ComputeYWing
from tests.testing_utilities import run_system


# pylint: disable=redefined-outer-name  # needed for pytest fixtures


@pytest.fixture(scope="module")
def input_xml() -> OMLegacy1XmlIO:
    """
    :return: access to the sample xml data
    """
    # TODO: have more consistency in input data (no need for the whole geometry_inputs_full.xml)
    return OMLegacy1XmlIO(
        pth.join(pth.dirname(__file__), "data", "geometry_inputs_full.xml"))


def test_compute_fuselage_cabin_sizing(input_xml):
    """ Tests computation of the fuselage with cabin sizing """

    input_list = [
        'geometry:cabin:seats:economical:width',
        'geometry:cabin:seats:economical:length',
        'geometry:cabin:seats:economical:count_by_row',
        'geometry:cabin:aisle_width',
        'geometry:cabin:exit_width',
        'TLAR:NPAX',
        'geometry:propulsion:engine:count'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = run_system(ComputeFuselageGeometryCabinSizing(), input_vars)

    npax1 = problem['geometry:cabin:NPAX1']
    assert npax1 == pytest.approx(157, abs=1)
    n_rows = problem['geometry:cabin:seat_rows:count']
    assert n_rows == pytest.approx(26, abs=1)
    cg_systems_c6 = problem['weight:systems:flight_kit:CG:x']
    assert cg_systems_c6 == pytest.approx(7.47, abs=1e-2)
    cg_furniture_d2 = problem['weight:furniture:passenger_seats:CG:x']
    assert cg_furniture_d2 == pytest.approx(16.62, abs=1e-2)
    fuselage_length = problem['geometry:fuselage:length']
    assert fuselage_length == pytest.approx(37.507, abs=1e-3)
    fuselage_width_max = problem['geometry:fuselage:maximum_width']
    assert fuselage_width_max == pytest.approx(3.92, abs=1e-2)
    fuselage_height_max = problem['geometry:fuselage:maximum_height']
    assert fuselage_height_max == pytest.approx(4.06, abs=1e-2)
    fuselage_lav = problem['geometry:fuselage:front_length']
    assert fuselage_lav == pytest.approx(6.902, abs=1e-3)
    fuselage_lar = problem['geometry:fuselage:rear_length']
    assert fuselage_lar == pytest.approx(14.616, abs=1e-3)
    fuselage_lpax = problem['geometry:fuselage:PAX_length']
    assert fuselage_lpax == pytest.approx(22.87, abs=1e-2)
    fuselage_lcabin = problem['geometry:cabin:length']
    assert fuselage_lcabin == pytest.approx(30.38, abs=1e-2)
    fuselage_wet_area = problem['geometry:fuselage:wetted_area']
    assert fuselage_wet_area == pytest.approx(401.956, abs=1e-3)
    pnc = problem['geometry:cabin:crew_count:commercial']
    assert pnc == pytest.approx(4, abs=1)


def test_compute_fuselage_basic(input_xml):
    """ Tests computation of the fuselage with no cabin sizing """

    input_list = [
        'geometry:cabin:NPAX1',
        'geometry:fuselage:length',
        'geometry:fuselage:maximum_width',
        'geometry:fuselage:maximum_height',
        'geometry:fuselage:front_length',
        'geometry:fuselage:rear_length',
        'geometry:fuselage:PAX_length'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = run_system(ComputeFuselageGeometryBasic(), input_vars)

    cg_systems_c6 = problem['weight:systems:flight_kit:CG:x']
    assert cg_systems_c6 == pytest.approx(9.19, abs=1e-2)
    cg_furniture_d2 = problem['weight:furniture:passenger_seats:CG:x']
    assert cg_furniture_d2 == pytest.approx(14.91, abs=1e-2)
    cg_pl_cg_pax = problem['cg_pl:CG_PAX']
    assert cg_pl_cg_pax == pytest.approx(18.34, abs=1e-2)
    fuselage_lcabin = problem['geometry:cabin:length']
    assert fuselage_lcabin == pytest.approx(30.38, abs=1e-2)
    fuselage_wet_area = problem['geometry:fuselage:wetted_area']
    assert fuselage_wet_area == pytest.approx(401.962, abs=1e-3)
    pnc = problem['geometry:cabin:crew_count:commercial']
    assert pnc == pytest.approx(4, abs=1)


def test_compute_ht_area(input_xml):
    """ Tests computation of the horizontal tail area """

    input_list = [
        'geometry:fuselage:length',
        'geometry:wing:MAC:x',
        'geometry:horizontal_tail:volume_coefficient',
        'geometry:wing:MAC:length',
        'geometry:wing:area',
    ]

    input_vars = input_xml.read(only=input_list)

    problem = run_system(ComputeHTArea(), input_vars)

    ht_lp = problem['geometry:horizontal_tail:distance_from_wing']
    assert ht_lp == pytest.approx(17.675, abs=1e-3)
    wet_area = problem['geometry:horizontal_tail:wetted_area']
    assert wet_area == pytest.approx(70.34, abs=1e-2)
    ht_area = problem['geometry:horizontal_tail:area']
    assert ht_area == pytest.approx(35.165, abs=1e-3)


def test_compute_ht_cg(input_xml):
    """ Tests computation of the horizontal tail center of gravity """

    input_list = [
        'geometry:horizontal_tail:root_chord',
        'geometry:horizontal_tail:tip_chord',
        'geometry:horizontal_tail:distance_from_wing',
        'geometry:horizontal_tail:span',
        'geometry:wing:MAC:x',
        'geometry:horizontal_tail:sweep_25',
        'geometry:horizontal_tail:MAC:length'
    ]

    input_vars = input_xml.read(only=input_list)
    input_vars.add_output('geometry:horizontal_tail:MAC:x', 1.656, units='m')

    problem = run_system(ComputeHTcg(), input_vars)

    cg_a31 = problem['weight:airframe:horizontal_tail:CG:x']
    assert cg_a31 == pytest.approx(34.58, abs=1e-2)


def test_compute_ht_mac(input_xml):
    """ Tests computation of the horizontal tail mac """

    input_list = [
        'geometry:horizontal_tail:root_chord',
        'geometry:horizontal_tail:tip_chord',
        'geometry:horizontal_tail:span',
        'geometry:horizontal_tail:sweep_25'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = run_system(ComputeHTMAC(), input_vars)

    length = problem['geometry:horizontal_tail:MAC:length']
    assert length == pytest.approx(3.141, abs=1e-3)
    ht_x0 = problem['geometry:horizontal_tail:MAC:x']
    assert ht_x0 == pytest.approx(1.656, abs=1e-3)
    ht_y0 = problem['geometry:horizontal_tail:MAC:y']
    assert ht_y0 == pytest.approx(2.519, abs=1e-3)


def test_compute_ht_chord(input_xml):
    """ Tests computation of the horizontal tail chords """

    input_list = [
        'geometry:horizontal_tail:aspect_ratio',
        'geometry:horizontal_tail:area',
        'geometry:horizontal_tail:taper_ratio'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = run_system(ComputeHTChord(), input_vars)

    span = problem['geometry:horizontal_tail:span']
    assert span == pytest.approx(12.28, abs=1e-2)
    root_chord = problem['geometry:horizontal_tail:root_chord']
    assert root_chord == pytest.approx(4.406, abs=1e-3)
    tip_chord = problem['geometry:horizontal_tail:tip_chord']
    assert tip_chord == pytest.approx(1.322, abs=1e-3)


def test_compute_ht_cl(input_xml):
    """ Tests computation of the horizontal tail lift coefficient """

    input_list = [
        'geometry:horizontal_tail:aspect_ratio',
        'TLAR:cruise_mach',
        'geometry:horizontal_tail:sweep_25'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = run_system(ComputeHTClalpha(), input_vars)

    cl_alpha = problem['aerodynamics:horizontal_tail:cruise:CL_alpha']
    assert cl_alpha == pytest.approx(3.47, abs=1e-2)


def test_compute_ht_sweep(input_xml):
    """ Tests computation of the horizontal tail sweep """

    input_list = [
        'geometry:horizontal_tail:root_chord',
        'geometry:horizontal_tail:tip_chord',
        'geometry:horizontal_tail:span',
        'geometry:horizontal_tail:sweep_25'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = run_system(ComputeHTSweep(), input_vars)

    sweep_0 = problem['geometry:horizontal_tail:sweep_0']
    assert sweep_0 == pytest.approx(33.317, abs=1e-3)
    sweep_100 = problem['geometry:horizontal_tail:sweep_100']
    assert sweep_100 == pytest.approx(8.81, abs=1e-2)


def test_compute_ht_vol_co(input_xml):
    """ Tests computation of the horizontal volume coeeficient """

    input_list = [
        'weight:airframe:landing_gear:main:CG:x',
        'weight:airframe:landing_gear:front:CG:x',
        'weight:aircraft:MTOW',
        'geometry:wing:area',
        'geometry:wing:MAC:length',
        'requirements:CG_range'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = run_system(ComputeHTVolCoeff(), input_vars)

    delta_lg = problem['geometry:landing_gear:front:distance_to_main']
    assert delta_lg == pytest.approx(12.93, abs=1e-2)
    vol_coeff = problem['geometry:horizontal_tail:volume_coefficient']
    assert vol_coeff == pytest.approx(1.117, abs=1e-3)


def test_geometry_global_ht(input_xml):
    """ Tests computation of the global HT geometry components """

    input_list = [
        'weight:airframe:landing_gear:main:CG:x',
        'weight:airframe:landing_gear:front:CG:x',
        'weight:aircraft:MTOW',
        'geometry:wing:area',
        'geometry:wing:MAC:length',
        'requirements:CG_range',
        'geometry:fuselage:length',
        'geometry:wing:MAC:x',
        'geometry:horizontal_tail:taper_ratio',
        'geometry:horizontal_tail:aspect_ratio',
        'geometry:horizontal_tail:sweep_25',
        'TLAR:cruise_mach'
    ]

    input_vars = input_xml.read(only=input_list)

    problem = run_system(ComputeHorizontalTailGeometry(), input_vars)

    delta_lg = problem['geometry:landing_gear:front:distance_to_main']
    assert delta_lg == pytest.approx(12.93, abs=1e-2)
    vol_coeff = problem['geometry:horizontal_tail:volume_coefficient']
    assert vol_coeff == pytest.approx(1.117, abs=1e-3)
    ht_lp = problem['geometry:horizontal_tail:distance_from_wing']
    assert ht_lp == pytest.approx(17.675, abs=1e-3)
    wet_area = problem['geometry:horizontal_tail:wetted_area']
    assert wet_area == pytest.approx(70.34, abs=1e-2)
    ht_area = problem['geometry:horizontal_tail:area']
    assert ht_area == pytest.approx(35.167, abs=1e-3)
    span = problem['geometry:horizontal_tail:span']
    assert span == pytest.approx(12.28, abs=1e-2)
    root_chord = problem['geometry:horizontal_tail:root_chord']
    assert root_chord == pytest.approx(4.406, abs=1e-3)
    tip_chord = problem['geometry:horizontal_tail:tip_chord']
    assert tip_chord == pytest.approx(1.322, abs=1e-3)
    length = problem['geometry:horizontal_tail:MAC:length']
    assert length == pytest.approx(3.141, abs=1e-3)
    ht_x0 = problem['geometry:horizontal_tail:MAC:x']
    assert ht_x0 == pytest.approx(1.656, abs=1e-3)
    ht_y0 = problem['geometry:horizontal_tail:MAC:y']
    assert ht_y0 == pytest.approx(2.519, abs=1e-3)
    sweep_0 = problem['geometry:horizontal_tail:sweep_0']
    assert sweep_0 == pytest.approx(33.317, abs=1e-3)
    sweep_100 = problem['geometry:horizontal_tail:sweep_100']
    assert sweep_100 == pytest.approx(8.81, abs=1e-2)
    cl_alpha = problem['aerodynamics:horizontal_tail:cruise:CL_alpha']
    assert cl_alpha == pytest.approx(3.47, abs=1e-2)


def test_compute_fuselage_cnbeta(input_xml):
    """ Tests computation of the yawing moment due to sideslip """

    input_list = [
        'geometry:fuselage:length',
        'geometry:fuselage:maximum_width',
        'geometry:fuselage:maximum_height',
        'geometry:fuselage:front_length',
        'geometry:fuselage:rear_length',
        'geometry:wing:area',
        'geometry:wing:span'
    ]

    input_vars = input_xml.read(only=input_list)

    component = ComputeCnBetaFuselage()

    problem = run_system(component, input_vars)

    cn_beta = problem['aerodynamics:fuselage:cruise:CnBeta']
    assert cn_beta == pytest.approx(-0.117901, abs=1e-6)


def test_compute_vt_area(input_xml):
    """ Tests computation of the vertical tail area """

    input_list = [
        'TLAR:cruise_mach',
        'geometry:wing:MAC:length',
        'geometry:wing:MAC:length',
        'geometry:wing:area',
        'geometry:wing:span',
        'geometry:vertical_tail:distance_from_wing',
        'aerodynamics:vertical_tail:cruise:CL_alpha'
    ]

    input_vars = input_xml.read(only=input_list)

    input_vars.add_output('weight:aircraft:CG:ratio', 0.364924)
    input_vars.add_output('aerodynamics:fuselage:cruise:CnBeta', -0.117901)

    component = ComputeVTArea()

    problem = run_system(component, input_vars)

    cn_beta_vt = problem['aerodynamics:vertical_tail:cruise:CnBeta']
    assert cn_beta_vt == pytest.approx(0.258348, abs=1e-6)
    wet_area = problem['geometry:vertical_tail:wetted_area']
    assert wet_area == pytest.approx(52.34, abs=1e-2)
    vt_area = problem['geometry:vertical_tail:area']
    assert vt_area == pytest.approx(24.92, abs=1e-2)


def test_compute_vt_cg(input_xml):
    """ Tests computation of the vertical tail center of gravity """

    input_list = [
        'geometry:vertical_tail:root_chord',
        'geometry:vertical_tail:tip_chord',
        'geometry:vertical_tail:distance_from_wing',
        'geometry:vertical_tail:span',
        'geometry:wing:MAC:x',
        'geometry:vertical_tail:sweep_25',
        'geometry:vertical_tail:MAC:length'
    ]

    input_vars = input_xml.read(only=input_list)

    input_vars.add_output('geometry:vertical_tail:MAC:x', 2.321, units='m')

    component = ComputeVTcg()

    problem = run_system(component, input_vars)

    cg_a32 = problem['weight:airframe:vertical_tail:CG:x']
    assert cg_a32 == pytest.approx(34.265, abs=1e-3)


def test_compute_vt_mac(input_xml):
    """ Tests computation of the vertical tail mac """

    input_list = [
        'geometry:vertical_tail:root_chord',
        'geometry:vertical_tail:tip_chord',
        'geometry:vertical_tail:span',
        'geometry:vertical_tail:sweep_25'
    ]

    input_vars = input_xml.read(only=input_list)

    component = ComputeVTMAC()

    problem = run_system(component, input_vars)

    length = problem['geometry:vertical_tail:MAC:length']
    assert length == pytest.approx(4.161, abs=1e-3)
    vt_x0 = problem['geometry:vertical_tail:MAC:x']
    assert vt_x0 == pytest.approx(2.321, abs=1e-3)
    vt_z0 = problem['geometry:vertical_tail:MAC:z']
    assert vt_z0 == pytest.approx(2.716, abs=1e-3)


def test_compute_vt_chords(input_xml):
    """ Tests computation of the vertical tail chords """

    input_list = [
        'geometry:vertical_tail:aspect_ratio',
        'geometry:vertical_tail:area',
        'geometry:vertical_tail:taper_ratio'
    ]

    input_vars = input_xml.read(only=input_list)

    component = ComputeVTChords()

    problem = run_system(component, input_vars)

    span = problem['geometry:vertical_tail:span']
    assert span == pytest.approx(6.62, abs=1e-2)
    root_chord = problem['geometry:vertical_tail:root_chord']
    assert root_chord == pytest.approx(5.837, abs=1e-3)
    tip_chord = problem['geometry:vertical_tail:tip_chord']
    assert tip_chord == pytest.approx(1.751, abs=1e-3)


def test_compute_vt_sweep(input_xml):
    """ Tests computation of the vertical tail sweep """

    input_list = [
        'geometry:vertical_tail:root_chord',
        'geometry:vertical_tail:tip_chord',
        'geometry:vertical_tail:span',
        'geometry:vertical_tail:sweep_25'
    ]

    input_vars = input_xml.read(only=input_list)

    component = ComputeVTSweep()

    problem = run_system(component, input_vars)

    sweep_0 = problem['geometry:vertical_tail:sweep_0']
    assert sweep_0 == pytest.approx(40.515, abs=1e-3)
    sweep_100 = problem['geometry:vertical_tail:sweep_100']
    assert sweep_100 == pytest.approx(13.35, abs=1e-2)


def test_compute_vt_distance(input_xml):
    """ Tests computation of the vertical tail distance """

    input_list = [
        'geometry:fuselage:length',
        'geometry:wing:MAC:x'
    ]

    input_vars = input_xml.read(only=input_list)

    component = ComputeVTDistance()

    problem = run_system(component, input_vars)

    lp_vt = problem['geometry:vertical_tail:distance_from_wing']
    assert lp_vt == pytest.approx(16.55, abs=1e-2)


def test_compute_vt_cl(input_xml):
    """ Tests computation of the vertical tail lift coefficient """

    input_list = [
        'geometry:vertical_tail:aspect_ratio',
        'TLAR:cruise_mach',
        'geometry:vertical_tail:sweep_25'
    ]

    input_vars = input_xml.read(only=input_list)

    input_vars.add_output('k_ar_effective', 1.55)

    component = ComputeVTClalpha()

    problem = run_system(component, input_vars)

    cl_alpha = problem['aerodynamics:vertical_tail:cruise:CL_alpha']
    assert cl_alpha == pytest.approx(2.55, abs=1e-2)


def test_compute_vt_vol_co(input_xml):
    """ Tests computation of the vertical volume coefficient """

    input_list = [
        'geometry:vertical_tail:area',
        'geometry:vertical_tail:distance_from_wing',
        'geometry:wing:area',
        'geometry:wing:span',
    ]

    input_vars = input_xml.read(only=input_list)

    component = ComputeVTVolCoeff()

    problem = run_system(component, input_vars)

    vol_coeff = problem['geometry:vertical_tail:volume_coefficient']
    assert vol_coeff == pytest.approx(0.105, abs=1e-3)


def test_geometry_global_vt(input_xml):
    """ Tests computation of the global VT geometry components """

    input_list = [
        'geometry:wing:area',
        'geometry:fuselage:length',
        'geometry:wing:MAC:x',
        'geometry:vertical_tail:taper_ratio',
        'geometry:vertical_tail:aspect_ratio',
        'geometry:vertical_tail:sweep_25',
        'geometry:fuselage:rear_length',
        'geometry:fuselage:front_length',
        'geometry:fuselage:maximum_height',
        'geometry:fuselage:maximum_width',
        'geometry:wing:span',
        'TLAR:cruise_mach',
        'geometry:wing:MAC:length'
    ]

    input_vars = input_xml.read(only=input_list)

    input_vars.add_output('weight:aircraft:CG:ratio', 0.364924)

    component = ComputeVerticalTailGeometry()

    problem = run_system(component, input_vars)

    cn_beta_vt = problem['aerodynamics:vertical_tail:cruise:CnBeta']
    assert cn_beta_vt == pytest.approx(0.258348, abs=1e-6)
    cn_beta_fuselage = problem['aerodynamics:fuselage:cruise:CnBeta']
    assert cn_beta_fuselage == pytest.approx(-0.117901, abs=1e-6)
    wet_area = problem['geometry:vertical_tail:wetted_area']
    assert wet_area == pytest.approx(52.41, abs=1e-2)
    vt_area = problem['geometry:vertical_tail:area']
    assert vt_area == pytest.approx(24.96, abs=1e-2)
    length = problem['geometry:vertical_tail:MAC:length']
    assert length == pytest.approx(4.15, abs=1e-2)
    vt_x0 = problem['geometry:vertical_tail:MAC:x']
    assert vt_x0 == pytest.approx(2.31, abs=1e-2)
    vt_z0 = problem['geometry:vertical_tail:MAC:z']
    assert vt_z0 == pytest.approx(2.71, abs=1e-2)
    span = problem['geometry:vertical_tail:span']
    assert span == pytest.approx(6.60, abs=1e-2)
    root_chord = problem['geometry:vertical_tail:root_chord']
    assert root_chord == pytest.approx(5.82, abs=1e-2)
    tip_chord = problem['geometry:vertical_tail:tip_chord']
    assert tip_chord == pytest.approx(1.75, abs=1e-2)
    sweep_0 = problem['geometry:vertical_tail:sweep_0']
    assert sweep_0 == pytest.approx(40.514, abs=1e-3)
    sweep_100 = problem['geometry:vertical_tail:sweep_100']
    assert sweep_100 == pytest.approx(13.35, abs=1e-2)
    lp_vt = problem['geometry:vertical_tail:distance_from_wing']
    assert lp_vt == pytest.approx(16.55, abs=1e-2)
    cl_alpha = problem['aerodynamics:vertical_tail:cruise:CL_alpha']
    assert cl_alpha == pytest.approx(2.55, abs=1e-2)
    vol_coeff = problem['geometry:vertical_tail:volume_coefficient']
    assert vol_coeff == pytest.approx(0.105, abs=1e-3)


def test_geometry_wing_b50(input_xml):
    """ Tests computation of the wing B50 """

    input_list = [
        'geometry:wing:tip:leading_edge:x',
        'geometry:wing:root:y',
        'geometry:wing:tip:y',
        'geometry:wing:root:virtual_chord',
        'geometry:wing:tip:chord',
        'geometry:wing:span'
    ]

    input_vars = input_xml.read(only=input_list)

    component = ComputeB50()

    problem = run_system(component, input_vars)

    wing_b_50 = problem['geometry:wing:b_50']
    assert wing_b_50 == pytest.approx(34.166, abs=1e-3)


def test_geometry_wing_cl_alpha(input_xml):
    """ Tests computation of the wing lift coefficient """

    input_list = [
        'TLAR:cruise_mach',
        'geometry:fuselage:maximum_width',
        'geometry:fuselage:maximum_height',
        'geometry:wing:area',
        'geometry:wing:root:chord',
        'geometry:wing:tip:chord',
        'geometry:wing:tip:thickness_ratio',
        'geometry:wing:sweep_25',
        'geometry:wing:aspect_ratio',
        'geometry:wing:span',
    ]

    input_vars = input_xml.read(only=input_list)

    component = ComputeCLalpha()

    problem = run_system(component, input_vars)

    cl_alpha = problem['aerodynamics:aircraft:cruise:CL_alpha']
    assert cl_alpha == pytest.approx(6.49, abs=1e-2)


def test_geometry_wing_l1_l4(input_xml):
    """ Tests computation of the wing chords (l1 and l4) """

    input_list = [
        'geometry:wing:area',
        'geometry:wing:root:y',
        'geometry:wing:kink:y',
        'geometry:wing:span',
        'geometry:fuselage:maximum_width',
        'geometry:wing:taper_ratio',
        'geometry:wing:sweep_25',
    ]

    input_vars = input_xml.read(only=input_list)

    component = ComputeL1AndL4Wing()

    problem = run_system(component, input_vars)

    wing_l1 = problem['geometry:wing:root:virtual_chord']
    assert wing_l1 == pytest.approx(4.953, abs=1e-3)
    wing_l4 = problem['geometry:wing:tip:chord']
    assert wing_l4 == pytest.approx(1.882, abs=1e-3)


def test_geometry_wing_l2_l3(input_xml):
    """ Tests computation of the wing chords (l2 and l3) """

    input_list = [
        'geometry:wing:span',
        'geometry:fuselage:maximum_width',
        'geometry:wing:taper_ratio',
        'geometry:wing:sweep_25',
        'geometry:wing:root:virtual_chord',
        'geometry:wing:tip:chord',
        'geometry:wing:root:y',
        'geometry:wing:kink:y',
        'geometry:wing:tip:y'
    ]

    input_vars = input_xml.read(only=input_list)

    component = ComputeL2AndL3Wing()

    problem = run_system(component, input_vars)

    wing_l2 = problem['geometry:wing:root:chord']
    assert wing_l2 == pytest.approx(6.26, abs=1e-2)
    wing_l3 = problem['geometry:wing:kink:chord']
    assert wing_l3 == pytest.approx(3.985, abs=1e-3)


def test_geometry_wing_mac(input_xml):
    """ Tests computation of the wing mean aerodynamic chord """

    input_list = [
        'geometry:wing:area',
        'geometry:wing:kink:leading_edge:x',
        'geometry:wing:tip:leading_edge:x',
        'geometry:wing:root:y',
        'geometry:wing:kink:y',
        'geometry:wing:tip:y',
        'geometry:wing:root:chord',
        'geometry:wing:kink:chord',
        'geometry:wing:tip:chord'
    ]

    input_vars = input_xml.read(only=input_list)

    component = ComputeMACWing()

    problem = run_system(component, input_vars)

    wing_l0 = problem['geometry:wing:MAC:length']
    assert wing_l0 == pytest.approx(4.457, abs=1e-3)
    wing_x0 = problem['geometry:wing:root:leading_edge:x']
    assert wing_x0 == pytest.approx(2.361, abs=1e-3)
    wing_y0 = problem['geometry:wing:MAC:y']
    assert wing_y0 == pytest.approx(6.293, abs=1e-3)


def test_geometry_wing_mfw(input_xml):
    """ Tests computation of the wing max fuel weight """

    input_list = [
        'geometry:wing:area',
        'geometry:wing:aspect_ratio',
        'geometry:wing:root:thickness_ratio',
        'geometry:wing:tip:thickness_ratio'
    ]

    input_vars = input_xml.read(only=input_list)

    component = ComputeMFW()

    problem = run_system(component, input_vars)

    mfw = problem['weight:aircraft:MFW']
    assert mfw == pytest.approx(19284.7, abs=1e-1)


def test_geometry_wing_sweep(input_xml):
    """ Tests computation of the wing sweeps """

    input_list = [
        'geometry:wing:kink:leading_edge:x',
        'geometry:wing:tip:leading_edge:x',
        'geometry:wing:root:y',
        'geometry:wing:kink:y',
        'geometry:wing:tip:y',
        'geometry:wing:root:chord',
        'geometry:wing:kink:chord',
        'geometry:wing:tip:chord'
    ]

    input_vars = input_xml.read(only=input_list)

    component = ComputeSweepWing()

    problem = run_system(component, input_vars)

    sweep_0 = problem['geometry:wing:sweep_0']
    assert sweep_0 == pytest.approx(27.55, abs=1e-2)
    sweep_100_inner = problem['geometry:wing:sweep_100_inner']
    assert sweep_100_inner == pytest.approx(0.0, abs=1e-1)
    sweep_100_outer = problem['geometry:wing:sweep_100_outer']
    assert sweep_100_outer == pytest.approx(16.7, abs=1e-1)


def test_geometry_wing_toc(input_xml):
    """ Tests computation of the wing ToC (Thickness of Chord) """

    input_list = [
        'TLAR:cruise_mach',
        'geometry:wing:sweep_25'
    ]

    input_vars = input_xml.read(only=input_list)

    component = ComputeToCWing()

    problem = run_system(component, input_vars)

    toc_aero = problem['geometry:wing:thickness_ratio']
    assert toc_aero == pytest.approx(0.128, abs=1e-3)
    toc_root = problem['geometry:wing:root:thickness_ratio']
    assert toc_root == pytest.approx(0.159, abs=1e-3)
    toc_kink = problem['geometry:wing:kink:thickness_ratio']
    assert toc_kink == pytest.approx(0.121, abs=1e-3)
    toc_tip = problem['geometry:wing:tip:thickness_ratio']
    assert toc_tip == pytest.approx(0.11, abs=1e-2)


def test_geometry_wing_wet_area(input_xml):
    """ Tests computation of the wing wet area """

    input_list = [
        'geometry:wing:root:chord',
        'geometry:wing:root:y',
        'geometry:wing:area',
        'geometry:fuselage:maximum_width'
    ]

    input_vars = input_xml.read(only=input_list)

    component = ComputeWetAreaWing()

    problem = run_system(component, input_vars)

    area_pf = problem['geometry:wing:outer_area']
    assert area_pf == pytest.approx(100.303, abs=1e-3)
    wet_area = problem['geometry:wing:wetted_area']
    assert wet_area == pytest.approx(200.607, abs=1e-3)


def test_geometry_wing_x(input_xml):
    """ Tests computation of the wing Xs """

    input_list = [
        'geometry:wing:root:virtual_chord',
        'geometry:wing:kink:chord',
        'geometry:wing:tip:chord',
        'geometry:wing:root:y',
        'geometry:wing:kink:y',
        'geometry:wing:tip:y',
        'geometry:wing:sweep_25'
    ]

    input_vars = input_xml.read(only=input_list)

    component = ComputeXWing()

    problem = run_system(component, input_vars)

    wing_x3 = problem['geometry:wing:kink:leading_edge:x']
    assert wing_x3 == pytest.approx(2.275, abs=1e-3)
    wing_x4 = problem['geometry:wing:tip:leading_edge:x']
    assert wing_x4 == pytest.approx(7.222, abs=1e-3)


def test_geometry_wing_y(input_xml):
    """ Tests computation of the wing Ys """

    input_list = [
        'geometry:wing:aspect_ratio',
        'geometry:fuselage:maximum_width',
        'geometry:wing:area',
        'geometry:wing:kink:span_ratio'
    ]

    input_vars = input_xml.read(only=input_list)

    component = ComputeYWing()

    problem = run_system(component, input_vars)

    span = problem['geometry:wing:span']
    assert span == pytest.approx(34.4, abs=1e-1)
    wing_y2 = problem['geometry:wing:root:y']
    assert wing_y2 == pytest.approx(1.96, abs=1e-2)
    wing_y3 = problem['geometry:wing:kink:y']
    assert wing_y3 == pytest.approx(6.88, abs=1e-2)
    wing_y4 = problem['geometry:wing:tip:y']
    assert wing_y4 == pytest.approx(17.2, abs=1e-1)


# TODO: One module for drawing the wing shall be externalized from OpenMDAO

def test_geometry_global_wing(input_xml):
    """ Tests computation of the global wing geometry components """

    input_list = [
        'TLAR:cruise_mach',
        'geometry:fuselage:maximum_width',
        'geometry:fuselage:maximum_height',
        'geometry:wing:area',
        'geometry:wing:sweep_25',
        'geometry:wing:aspect_ratio',
        'geometry:wing:taper_ratio',
        'geometry:wing:kink:span_ratio'
    ]

    input_vars = input_xml.read(only=input_list)

    component = ComputeWingGeometry()

    problem = run_system(component, input_vars)

    wing_b_50 = problem['geometry:wing:b_50']
    assert wing_b_50 == pytest.approx(37.330, abs=1e-3)
    cl_alpha = problem['aerodynamics:aircraft:cruise:CL_alpha']
    assert cl_alpha == pytest.approx(6.42, abs=1e-2)
    wing_l1 = problem['geometry:wing:root:virtual_chord']
    assert wing_l1 == pytest.approx(4.426, abs=1e-3)
    wing_l4 = problem['geometry:wing:tip:chord']
    assert wing_l4 == pytest.approx(1.682, abs=1e-3)
    wing_l2 = problem['geometry:wing:root:chord']
    assert wing_l2 == pytest.approx(6.055, abs=1e-2)
    wing_l3 = problem['geometry:wing:kink:chord']
    assert wing_l3 == pytest.approx(3.540, abs=1e-3)
    wing_l0 = problem['geometry:wing:MAC:length']
    assert wing_l0 == pytest.approx(4.182, abs=1e-3)
    wing_x0 = problem['geometry:wing:root:leading_edge:x']
    assert wing_x0 == pytest.approx(2.524, abs=1e-3)
    wing_y0 = problem['geometry:wing:MAC:y']
    assert wing_y0 == pytest.approx(6.710, abs=1e-3)
    mfw = problem['weight:aircraft:MFW']
    assert mfw == pytest.approx(19322.5, abs=1e-1)
    sweep_0 = problem['geometry:wing:sweep_0']
    assert sweep_0 == pytest.approx(27.08, abs=1e-2)
    sweep_100_inner = problem['geometry:wing:sweep_100_inner']
    assert sweep_100_inner == pytest.approx(0.0, abs=1e-1)
    sweep_100_outer = problem['geometry:wing:sweep_100_outer']
    assert sweep_100_outer == pytest.approx(18.3, abs=1e-1)
    toc_aero = problem['geometry:wing:thickness_ratio']
    assert toc_aero == pytest.approx(0.128, abs=1e-3)
    toc_root = problem['geometry:wing:root:thickness_ratio']
    assert toc_root == pytest.approx(0.159, abs=1e-3)
    toc_kink = problem['geometry:wing:kink:thickness_ratio']
    assert toc_kink == pytest.approx(0.121, abs=1e-3)
    toc_tip = problem['geometry:wing:tip:thickness_ratio']
    assert toc_tip == pytest.approx(0.11, abs=1e-2)
    area_pf = problem['geometry:wing:outer_area']
    assert area_pf == pytest.approx(101.104, abs=1e-3)
    wet_area = problem['geometry:wing:wetted_area']
    assert wet_area == pytest.approx(202.209, abs=1e-3)
    wing_x3 = problem['geometry:wing:kink:leading_edge:x']
    assert wing_x3 == pytest.approx(2.516, abs=1e-3)
    wing_x4 = problem['geometry:wing:tip:leading_edge:x']
    assert wing_x4 == pytest.approx(7.793, abs=1e-3)
    span = problem['geometry:wing:span']
    assert span == pytest.approx(34.4, abs=1e-1)
    wing_y2 = problem['geometry:wing:root:y']
    assert wing_y2 == pytest.approx(1.96, abs=1e-2)
    wing_y3 = problem['geometry:wing:kink:y']
    assert wing_y3 == pytest.approx(6.88, abs=1e-2)
    wing_y4 = problem['geometry:wing:tip:y']
    assert wing_y4 == pytest.approx(17.2, abs=1e-1)


def test_geometry_nacelle_pylons(input_xml):
    """ Tests computation of the nacelle and pylons component """

    input_list = [
        'propulsion:MTO_thrust',
        'geometry:propulsion:engine:y_ratio',
        'geometry:wing:span',
        'geometry:wing:MAC:length',
        'geometry:wing:root:leading_edge:x',
        'geometry:wing:root:chord',
        'geometry:wing:root:y',
        'geometry:wing:kink:chord',
        'geometry:wing:kink:y',
        'geometry:wing:kink:leading_edge:x',
        'geometry:wing:MAC:x',
        'geometry:fuselage:length',
        'geometry:fuselage:maximum_width'
    ]

    input_vars = input_xml.read(only=input_list)

    component = ComputeNacelleAndPylonsGeometry()

    problem = run_system(component, input_vars)

    pylon_length = problem['geometry:propulsion:pylon:length']
    assert pylon_length == pytest.approx(5.733, abs=1e-3)
    fan_length = problem['geometry:propulsion:fan:length']
    assert fan_length == pytest.approx(3.127, abs=1e-3)
    nacelle_length = problem['geometry:propulsion:nacelle:length']
    assert nacelle_length == pytest.approx(5.211, abs=1e-3)
    nacelle_dia = problem['geometry:propulsion:nacelle:diameter']
    assert nacelle_dia == pytest.approx(2.172, abs=1e-3)
    lg_height = problem['geometry:landing_gear:height']
    assert lg_height == pytest.approx(3.041, abs=1e-3)
    y_nacell = problem['geometry:propulsion:nacelle:y']
    assert y_nacell == pytest.approx(5.373, abs=1e-3)
    pylon_wet_area = problem['geometry:propulsion:pylon:wetted_area']
    assert pylon_wet_area == pytest.approx(7.563, abs=1e-3)
    nacelle_wet_area = problem['geometry:propulsion:nacelle:wetted_area']
    assert nacelle_wet_area == pytest.approx(21.609, abs=1e-3)
    cg_b1 = problem['weight:propulsion:engine:CG:x']
    assert cg_b1 == pytest.approx(13.5, abs=1e-1)


def test_geometry_total_area(input_xml):
    """ Tests computation of the total area """

    input_list = [
        'geometry:wing:wetted_area',
        'geometry:fuselage:wetted_area',
        'geometry:horizontal_tail:wetted_area',
        'geometry:vertical_tail:wetted_area',
        'geometry:propulsion:nacelle:wetted_area',
        'geometry:propulsion:pylon:wetted_area',
        'geometry:propulsion:engine:count',
    ]

    input_vars = input_xml.read(only=input_list)

    component = ComputeTotalArea()

    problem = run_system(component, input_vars)

    total_surface = problem['geometry:aircraft:wetted_area']
    assert total_surface == pytest.approx(783.997, abs=1e-3)


def test_geometry_update_mlg(input_xml):
    """ Tests computation of the main landing gear """

    input_list = [
        'geometry:wing:MAC:length',
        'geometry:wing:MAC:x',
    ]

    input_vars = input_xml.read(only=input_list)

    input_vars.add_output('weight:aircraft:CG:ratio', 0.364924)
    input_vars.add_output('geometry:landing_gear:front:distance_to_main', 12.93)

    problem = run_system(UpdateMLG(), input_vars)

    cg_a51 = problem['weight:airframe:landing_gear:main:CG:x']
    assert cg_a51 == pytest.approx(18.00, abs=1e-2)
