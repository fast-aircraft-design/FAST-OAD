"""
Test module for geometry functions of cg components
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

import os.path as pth

import pytest
from fastoad.io import VariableIO
from fastoad.models.weight.cg.cg_components import ComputeHTcg, ComputeVTcg, UpdateMLG

from tests.testing_utilities import run_system
from ..geom_components import ComputeTotalArea
from ..geom_components.fuselage import (
    ComputeFuselageGeometryBasic,
    ComputeFuselageGeometryCabinSizing,
)
from ..geom_components.fuselage.compute_cnbeta_fuselage import ComputeCnBetaFuselage
from ..geom_components.ht.components import (
    ComputeHTMAC,
    ComputeHTChord,
    ComputeHTClalpha,
    ComputeHTSweep,
)
from ..geom_components.nacelle_pylons.compute_nacelle_pylons import ComputeNacelleAndPylonsGeometry
from ..geom_components.vt.components import (
    ComputeVTMAC,
    ComputeVTChords,
    ComputeVTClalpha,
    ComputeVTSweep,
    ComputeVTDistance,
)
from ..geom_components.wing.components import (
    ComputeB50,
    ComputeCLalpha,
    ComputeL1AndL4Wing,
    ComputeL2AndL3Wing,
    ComputeMACWing,
    ComputeMFW,
    ComputeSweepWing,
    ComputeToCWing,
    ComputeWetAreaWing,
    ComputeXWing,
    ComputeYWing,
)


# pylint: disable=redefined-outer-name  # needed for pytest fixtures
@pytest.fixture(scope="module")
def input_xml() -> VariableIO:
    """
    :return: access to the sample xml data
    """
    # TODO: have more consistency in input data (no need for the whole geometry_inputs_full.xml)
    return VariableIO(pth.join(pth.dirname(__file__), "data", "geometry_inputs_full.xml"))


def test_compute_fuselage_cabin_sizing(input_xml):
    """ Tests computation of the fuselage with cabin sizing """

    input_list = [
        "data:geometry:cabin:seats:economical:width",
        "data:geometry:cabin:seats:economical:length",
        "data:geometry:cabin:seats:economical:count_by_row",
        "data:geometry:cabin:aisle_width",
        "data:geometry:cabin:exit_width",
        "data:TLAR:NPAX",
        "data:geometry:propulsion:engine:count",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    problem = run_system(ComputeFuselageGeometryCabinSizing(), input_vars)

    npax1 = problem["data:geometry:cabin:NPAX1"]
    assert npax1 == pytest.approx(157, abs=1)
    cg_systems_c6 = problem["data:weight:systems:flight_kit:CG:x"]
    assert cg_systems_c6 == pytest.approx(7.47, abs=1e-2)
    cg_furniture_d2 = problem["data:weight:furniture:passenger_seats:CG:x"]
    assert cg_furniture_d2 == pytest.approx(16.62, abs=1e-2)
    fuselage_length = problem["data:geometry:fuselage:length"]
    assert fuselage_length == pytest.approx(37.507, abs=1e-3)
    fuselage_width_max = problem["data:geometry:fuselage:maximum_width"]
    assert fuselage_width_max == pytest.approx(3.92, abs=1e-2)
    fuselage_height_max = problem["data:geometry:fuselage:maximum_height"]
    assert fuselage_height_max == pytest.approx(4.06, abs=1e-2)
    fuselage_lav = problem["data:geometry:fuselage:front_length"]
    assert fuselage_lav == pytest.approx(6.902, abs=1e-3)
    fuselage_lar = problem["data:geometry:fuselage:rear_length"]
    assert fuselage_lar == pytest.approx(14.616, abs=1e-3)
    fuselage_lpax = problem["data:geometry:fuselage:PAX_length"]
    assert fuselage_lpax == pytest.approx(22.87, abs=1e-2)
    fuselage_lcabin = problem["data:geometry:cabin:length"]
    assert fuselage_lcabin == pytest.approx(30.38, abs=1e-2)
    fuselage_wet_area = problem["data:geometry:fuselage:wetted_area"]
    assert fuselage_wet_area == pytest.approx(401.956, abs=1e-3)
    pnc = problem["data:geometry:cabin:crew_count:commercial"]
    assert pnc == pytest.approx(4, abs=1)


def test_compute_fuselage_basic(input_xml):
    """ Tests computation of the fuselage with no cabin sizing """

    input_list = [
        "data:geometry:cabin:NPAX1",
        "data:geometry:fuselage:length",
        "data:geometry:fuselage:maximum_width",
        "data:geometry:fuselage:maximum_height",
        "data:geometry:fuselage:front_length",
        "data:geometry:fuselage:rear_length",
        "data:geometry:fuselage:PAX_length",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    problem = run_system(ComputeFuselageGeometryBasic(), input_vars)

    cg_systems_c6 = problem["data:weight:systems:flight_kit:CG:x"]
    assert cg_systems_c6 == pytest.approx(9.19, abs=1e-2)
    cg_furniture_d2 = problem["data:weight:furniture:passenger_seats:CG:x"]
    assert cg_furniture_d2 == pytest.approx(14.91, abs=1e-2)
    fuselage_lcabin = problem["data:geometry:cabin:length"]
    assert fuselage_lcabin == pytest.approx(30.38, abs=1e-2)
    fuselage_wet_area = problem["data:geometry:fuselage:wetted_area"]
    assert fuselage_wet_area == pytest.approx(401.962, abs=1e-3)
    pnc = problem["data:geometry:cabin:crew_count:commercial"]
    assert pnc == pytest.approx(4, abs=1)


def test_compute_ht_cg(input_xml):
    """ Tests computation of the horizontal tail center of gravity """

    input_list = [
        "data:geometry:horizontal_tail:root:chord",
        "data:geometry:horizontal_tail:tip:chord",
        "data:geometry:horizontal_tail:MAC:at25percent:x:from_wingMAC25",
        "data:geometry:horizontal_tail:span",
        "data:geometry:wing:MAC:at25percent:x",
        "data:geometry:horizontal_tail:sweep_25",
        "data:geometry:horizontal_tail:MAC:length",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()
    input_vars.add_output("data:geometry:horizontal_tail:MAC:at25percent:x:local", 1.656, units="m")

    problem = run_system(ComputeHTcg(), input_vars)

    cg_a31 = problem["data:weight:airframe:horizontal_tail:CG:x"]
    assert cg_a31 == pytest.approx(34.58, abs=1e-2)


def test_compute_ht_mac(input_xml):
    """ Tests computation of the horizontal tail mac """

    input_list = [
        "data:geometry:horizontal_tail:root:chord",
        "data:geometry:horizontal_tail:tip:chord",
        "data:geometry:horizontal_tail:span",
        "data:geometry:horizontal_tail:sweep_25",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    problem = run_system(ComputeHTMAC(), input_vars)

    length = problem["data:geometry:horizontal_tail:MAC:length"]
    assert length == pytest.approx(3.141, abs=1e-3)
    ht_x0 = problem["data:geometry:horizontal_tail:MAC:at25percent:x:local"]
    assert ht_x0 == pytest.approx(1.656, abs=1e-3)
    ht_y0 = problem["data:geometry:horizontal_tail:MAC:y"]
    assert ht_y0 == pytest.approx(2.519, abs=1e-3)


def test_compute_ht_chord(input_xml):
    """ Tests computation of the horizontal tail chords """

    input_list = [
        "data:geometry:horizontal_tail:aspect_ratio",
        "data:geometry:horizontal_tail:area",
        "data:geometry:horizontal_tail:taper_ratio",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    problem = run_system(ComputeHTChord(), input_vars)

    span = problem["data:geometry:horizontal_tail:span"]
    assert span == pytest.approx(12.28, abs=1e-2)
    root_chord = problem["data:geometry:horizontal_tail:root:chord"]
    assert root_chord == pytest.approx(4.406, abs=1e-3)
    tip_chord = problem["data:geometry:horizontal_tail:tip:chord"]
    assert tip_chord == pytest.approx(1.322, abs=1e-3)


def test_compute_ht_cl(input_xml):
    """ Tests computation of the horizontal tail lift coefficient """

    input_list = [
        "data:geometry:horizontal_tail:aspect_ratio",
        "data:TLAR:cruise_mach",
        "data:geometry:horizontal_tail:sweep_25",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    problem = run_system(ComputeHTClalpha(), input_vars)

    cl_alpha = problem["data:aerodynamics:horizontal_tail:cruise:CL_alpha"]
    assert cl_alpha == pytest.approx(3.47, abs=1e-2)


def test_compute_ht_sweep(input_xml):
    """ Tests computation of the horizontal tail sweep """

    input_list = [
        "data:geometry:horizontal_tail:root:chord",
        "data:geometry:horizontal_tail:tip:chord",
        "data:geometry:horizontal_tail:span",
        "data:geometry:horizontal_tail:sweep_25",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    problem = run_system(ComputeHTSweep(), input_vars)

    sweep_0 = problem["data:geometry:horizontal_tail:sweep_0"]
    assert sweep_0 == pytest.approx(33.317, abs=1e-3)
    sweep_100 = problem["data:geometry:horizontal_tail:sweep_100"]
    assert sweep_100 == pytest.approx(8.81, abs=1e-2)


def test_compute_fuselage_cnbeta(input_xml):
    """ Tests computation of the yawing moment due to sideslip """

    input_list = [
        "data:geometry:fuselage:length",
        "data:geometry:fuselage:maximum_width",
        "data:geometry:fuselage:maximum_height",
        "data:geometry:fuselage:front_length",
        "data:geometry:fuselage:rear_length",
        "data:geometry:wing:area",
        "data:geometry:wing:span",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    component = ComputeCnBetaFuselage()

    problem = run_system(component, input_vars)

    cn_beta = problem["data:aerodynamics:fuselage:cruise:CnBeta"]
    assert cn_beta == pytest.approx(-0.117901, abs=1e-6)


def test_compute_vt_cg(input_xml):
    """ Tests computation of the vertical tail center of gravity """

    input_list = [
        "data:geometry:vertical_tail:root:chord",
        "data:geometry:vertical_tail:tip:chord",
        "data:geometry:vertical_tail:MAC:at25percent:x:from_wingMAC25",
        "data:geometry:vertical_tail:span",
        "data:geometry:wing:MAC:at25percent:x",
        "data:geometry:vertical_tail:sweep_25",
        "data:geometry:vertical_tail:MAC:length",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    input_vars.add_output("data:geometry:vertical_tail:MAC:at25percent:x:local", 2.321, units="m")

    component = ComputeVTcg()

    problem = run_system(component, input_vars)

    cg_a32 = problem["data:weight:airframe:vertical_tail:CG:x"]
    assert cg_a32 == pytest.approx(34.265, abs=1e-3)


def test_compute_vt_mac(input_xml):
    """ Tests computation of the vertical tail mac """

    input_list = [
        "data:geometry:vertical_tail:root:chord",
        "data:geometry:vertical_tail:tip:chord",
        "data:geometry:vertical_tail:span",
        "data:geometry:vertical_tail:sweep_25",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    component = ComputeVTMAC()

    problem = run_system(component, input_vars)

    length = problem["data:geometry:vertical_tail:MAC:length"]
    assert length == pytest.approx(4.161, abs=1e-3)
    vt_x0 = problem["data:geometry:vertical_tail:MAC:at25percent:x:local"]
    assert vt_x0 == pytest.approx(2.321, abs=1e-3)
    vt_z0 = problem["data:geometry:vertical_tail:MAC:z"]
    assert vt_z0 == pytest.approx(2.716, abs=1e-3)


def test_compute_vt_chords(input_xml):
    """ Tests computation of the vertical tail chords """

    input_list = [
        "data:geometry:vertical_tail:aspect_ratio",
        "data:geometry:vertical_tail:area",
        "data:geometry:vertical_tail:taper_ratio",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    component = ComputeVTChords()

    problem = run_system(component, input_vars)

    span = problem["data:geometry:vertical_tail:span"]
    assert span == pytest.approx(6.62, abs=1e-2)
    root_chord = problem["data:geometry:vertical_tail:root:chord"]
    assert root_chord == pytest.approx(5.837, abs=1e-3)
    tip_chord = problem["data:geometry:vertical_tail:tip:chord"]
    assert tip_chord == pytest.approx(1.751, abs=1e-3)


def test_compute_vt_sweep(input_xml):
    """ Tests computation of the vertical tail sweep """

    input_list = [
        "data:geometry:vertical_tail:root:chord",
        "data:geometry:vertical_tail:tip:chord",
        "data:geometry:vertical_tail:span",
        "data:geometry:vertical_tail:sweep_25",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    component = ComputeVTSweep()

    problem = run_system(component, input_vars)

    sweep_0 = problem["data:geometry:vertical_tail:sweep_0"]
    assert sweep_0 == pytest.approx(40.515, abs=1e-3)
    sweep_100 = problem["data:geometry:vertical_tail:sweep_100"]
    assert sweep_100 == pytest.approx(13.35, abs=1e-2)


def test_compute_vt_distance(input_xml):
    """ Tests computation of the vertical tail distance """

    input_list = [
        "data:geometry:fuselage:length",
        "data:geometry:wing:MAC:at25percent:x",
        "data:geometry:has_T_tail",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()
    problem = run_system(ComputeVTDistance(), input_vars)

    lp_vt = problem["data:geometry:vertical_tail:MAC:at25percent:x:from_wingMAC25"]
    assert lp_vt == pytest.approx(16.55, abs=1e-2)


def test_compute_vt_cl(input_xml):
    """ Tests computation of the vertical tail lift coefficient """

    input_list = [
        "data:TLAR:cruise_mach",
        "data:geometry:vertical_tail:aspect_ratio",
        "data:geometry:vertical_tail:sweep_25",
        "data:geometry:has_T_tail",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()
    problem = run_system(ComputeVTClalpha(), input_vars)

    cl_alpha = problem["data:aerodynamics:vertical_tail:cruise:CL_alpha"]
    assert cl_alpha == pytest.approx(2.55, abs=1e-2)


def test_geometry_wing_b50(input_xml):
    """ Tests computation of the wing B50 """

    input_list = [
        "data:geometry:wing:tip:leading_edge:x:local",
        "data:geometry:wing:root:y",
        "data:geometry:wing:tip:y",
        "data:geometry:wing:root:virtual_chord",
        "data:geometry:wing:tip:chord",
        "data:geometry:wing:span",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    component = ComputeB50()

    problem = run_system(component, input_vars)

    wing_b_50 = problem["data:geometry:wing:b_50"]
    assert wing_b_50 == pytest.approx(34.166, abs=1e-3)


def test_geometry_wing_cl_alpha(input_xml):
    """ Tests computation of the wing lift coefficient """

    input_list = [
        "data:TLAR:cruise_mach",
        "data:geometry:fuselage:maximum_width",
        "data:geometry:fuselage:maximum_height",
        "data:geometry:wing:area",
        "data:geometry:wing:root:chord",
        "data:geometry:wing:tip:chord",
        "data:geometry:wing:tip:thickness_ratio",
        "data:geometry:wing:sweep_25",
        "data:geometry:wing:aspect_ratio",
        "data:geometry:wing:span",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    component = ComputeCLalpha()

    problem = run_system(component, input_vars)

    cl_alpha = problem["data:aerodynamics:aircraft:cruise:CL_alpha"]
    assert cl_alpha == pytest.approx(6.49, abs=1e-2)


def test_geometry_wing_l1_l4(input_xml):
    """ Tests computation of the wing chords (l1 and l4) """

    input_list = [
        "data:geometry:wing:area",
        "data:geometry:wing:root:y",
        "data:geometry:wing:kink:y",
        "data:geometry:wing:span",
        "data:geometry:fuselage:maximum_width",
        "data:geometry:wing:taper_ratio",
        "data:geometry:wing:sweep_25",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    component = ComputeL1AndL4Wing()

    problem = run_system(component, input_vars)

    wing_l1 = problem["data:geometry:wing:root:virtual_chord"]
    assert wing_l1 == pytest.approx(4.953, abs=1e-3)
    wing_l4 = problem["data:geometry:wing:tip:chord"]
    assert wing_l4 == pytest.approx(1.882, abs=1e-3)


def test_geometry_wing_l2_l3(input_xml):
    """ Tests computation of the wing chords (l2 and l3) """

    input_list = [
        "data:geometry:wing:span",
        "data:geometry:fuselage:maximum_width",
        "data:geometry:wing:taper_ratio",
        "data:geometry:wing:sweep_25",
        "data:geometry:wing:root:virtual_chord",
        "data:geometry:wing:tip:chord",
        "data:geometry:wing:root:y",
        "data:geometry:wing:kink:y",
        "data:geometry:wing:tip:y",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    component = ComputeL2AndL3Wing()

    problem = run_system(component, input_vars)

    wing_l2 = problem["data:geometry:wing:root:chord"]
    assert wing_l2 == pytest.approx(6.26, abs=1e-2)
    wing_l3 = problem["data:geometry:wing:kink:chord"]
    assert wing_l3 == pytest.approx(3.985, abs=1e-3)


def test_geometry_wing_mac(input_xml):
    """ Tests computation of the wing mean aerodynamic chord """

    input_list = [
        "data:geometry:wing:area",
        "data:geometry:wing:kink:leading_edge:x:local",
        "data:geometry:wing:tip:leading_edge:x:local",
        "data:geometry:wing:root:y",
        "data:geometry:wing:kink:y",
        "data:geometry:wing:tip:y",
        "data:geometry:wing:root:chord",
        "data:geometry:wing:kink:chord",
        "data:geometry:wing:tip:chord",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    component = ComputeMACWing()

    problem = run_system(component, input_vars)

    wing_l0 = problem["data:geometry:wing:MAC:length"]
    assert wing_l0 == pytest.approx(4.457, abs=1e-3)
    wing_x0 = problem["data:geometry:wing:MAC:leading_edge:x:local"]
    assert wing_x0 == pytest.approx(2.361, abs=1e-3)
    wing_y0 = problem["data:geometry:wing:MAC:y"]
    assert wing_y0 == pytest.approx(6.293, abs=1e-3)


def test_geometry_wing_mfw(input_xml):
    """ Tests computation of the wing max fuel weight """

    input_list = [
        "data:geometry:wing:area",
        "data:geometry:wing:aspect_ratio",
        "data:geometry:wing:root:thickness_ratio",
        "data:geometry:wing:tip:thickness_ratio",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    component = ComputeMFW()

    problem = run_system(component, input_vars)

    mfw = problem["data:weight:aircraft:MFW"]
    assert mfw == pytest.approx(19284.7, abs=1e-1)


def test_geometry_wing_sweep(input_xml):
    """ Tests computation of the wing sweeps """

    input_list = [
        "data:geometry:wing:kink:leading_edge:x:local",
        "data:geometry:wing:tip:leading_edge:x:local",
        "data:geometry:wing:root:y",
        "data:geometry:wing:kink:y",
        "data:geometry:wing:tip:y",
        "data:geometry:wing:root:chord",
        "data:geometry:wing:kink:chord",
        "data:geometry:wing:tip:chord",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    component = ComputeSweepWing()

    problem = run_system(component, input_vars)

    sweep_0 = problem["data:geometry:wing:sweep_0"]
    assert sweep_0 == pytest.approx(27.55, abs=1e-2)
    sweep_100_inner = problem["data:geometry:wing:sweep_100_inner"]
    assert sweep_100_inner == pytest.approx(0.0, abs=1e-1)
    sweep_100_outer = problem["data:geometry:wing:sweep_100_outer"]
    assert sweep_100_outer == pytest.approx(16.7, abs=1e-1)


def test_geometry_wing_toc(input_xml):
    """ Tests computation of the wing ToC (Thickness of Chord) """

    input_list = ["data:TLAR:cruise_mach", "data:geometry:wing:sweep_25"]

    input_vars = input_xml.read(only=input_list).to_ivc()

    component = ComputeToCWing()

    problem = run_system(component, input_vars)

    toc_aero = problem["data:geometry:wing:thickness_ratio"]
    assert toc_aero == pytest.approx(0.128, abs=1e-3)
    toc_root = problem["data:geometry:wing:root:thickness_ratio"]
    assert toc_root == pytest.approx(0.159, abs=1e-3)
    toc_kink = problem["data:geometry:wing:kink:thickness_ratio"]
    assert toc_kink == pytest.approx(0.121, abs=1e-3)
    toc_tip = problem["data:geometry:wing:tip:thickness_ratio"]
    assert toc_tip == pytest.approx(0.11, abs=1e-2)


def test_geometry_wing_wet_area(input_xml):
    """ Tests computation of the wing wet area """

    input_list = [
        "data:geometry:wing:root:chord",
        "data:geometry:wing:root:y",
        "data:geometry:wing:area",
        "data:geometry:fuselage:maximum_width",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    component = ComputeWetAreaWing()

    problem = run_system(component, input_vars)

    area_pf = problem["data:geometry:wing:outer_area"]
    assert area_pf == pytest.approx(100.303, abs=1e-3)
    wet_area = problem["data:geometry:wing:wetted_area"]
    assert wet_area == pytest.approx(200.607, abs=1e-3)


def test_geometry_wing_x(input_xml):
    """ Tests computation of the wing Xs """

    input_list = [
        "data:geometry:wing:root:virtual_chord",
        "data:geometry:wing:kink:chord",
        "data:geometry:wing:tip:chord",
        "data:geometry:wing:root:y",
        "data:geometry:wing:kink:y",
        "data:geometry:wing:tip:y",
        "data:geometry:wing:sweep_25",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    component = ComputeXWing()

    problem = run_system(component, input_vars)

    wing_x3 = problem["data:geometry:wing:kink:leading_edge:x:local"]
    assert wing_x3 == pytest.approx(2.275, abs=1e-3)
    wing_x4 = problem["data:geometry:wing:tip:leading_edge:x:local"]
    assert wing_x4 == pytest.approx(7.222, abs=1e-3)


def test_geometry_wing_y(input_xml):
    """ Tests computation of the wing Ys """

    input_list = [
        "data:geometry:wing:aspect_ratio",
        "data:geometry:fuselage:maximum_width",
        "data:geometry:wing:area",
        "data:geometry:wing:kink:span_ratio",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    component = ComputeYWing()

    problem = run_system(component, input_vars)

    span = problem["data:geometry:wing:span"]
    assert span == pytest.approx(34.4, abs=1e-1)
    wing_y2 = problem["data:geometry:wing:root:y"]
    assert wing_y2 == pytest.approx(1.96, abs=1e-2)
    wing_y3 = problem["data:geometry:wing:kink:y"]
    assert wing_y3 == pytest.approx(6.88, abs=1e-2)
    wing_y4 = problem["data:geometry:wing:tip:y"]
    assert wing_y4 == pytest.approx(17.2, abs=1e-1)


def test_geometry_nacelle_pylons(input_xml):
    """ Tests computation of the nacelle and pylons component """

    input_list = [
        "data:propulsion:MTO_thrust",
        "data:geometry:propulsion:engine:y_ratio",
        "data:geometry:propulsion:layout",
        "data:geometry:wing:span",
        "data:geometry:wing:MAC:length",
        "data:geometry:wing:MAC:leading_edge:x:local",
        "data:geometry:wing:root:chord",
        "data:geometry:wing:root:y",
        "data:geometry:wing:kink:chord",
        "data:geometry:wing:kink:y",
        "data:geometry:wing:kink:leading_edge:x:local",
        "data:geometry:wing:MAC:at25percent:x",
        "data:geometry:fuselage:length",
        "data:geometry:fuselage:maximum_width",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    component = ComputeNacelleAndPylonsGeometry()

    problem = run_system(component, input_vars)

    pylon_length = problem["data:geometry:propulsion:pylon:length"]
    assert pylon_length == pytest.approx(5.733, abs=1e-3)
    fan_length = problem["data:geometry:propulsion:fan:length"]
    assert fan_length == pytest.approx(3.127, abs=1e-3)
    nacelle_length = problem["data:geometry:propulsion:nacelle:length"]
    assert nacelle_length == pytest.approx(5.211, abs=1e-3)
    nacelle_dia = problem["data:geometry:propulsion:nacelle:diameter"]
    assert nacelle_dia == pytest.approx(2.172, abs=1e-3)
    lg_height = problem["data:geometry:landing_gear:height"]
    assert lg_height == pytest.approx(3.041, abs=1e-3)
    y_nacell = problem["data:geometry:propulsion:nacelle:y"]
    assert y_nacell == pytest.approx(5.373, abs=1e-3)
    pylon_wet_area = problem["data:geometry:propulsion:pylon:wetted_area"]
    assert pylon_wet_area == pytest.approx(7.563, abs=1e-3)
    nacelle_wet_area = problem["data:geometry:propulsion:nacelle:wetted_area"]
    assert nacelle_wet_area == pytest.approx(21.609, abs=1e-3)
    cg_b1 = problem["data:weight:propulsion:engine:CG:x"]
    assert cg_b1 == pytest.approx(13.5, abs=1e-1)


def test_geometry_total_area(input_xml):
    """ Tests computation of the total area """

    input_list = [
        "data:geometry:wing:wetted_area",
        "data:geometry:fuselage:wetted_area",
        "data:geometry:horizontal_tail:wetted_area",
        "data:geometry:vertical_tail:wetted_area",
        "data:geometry:propulsion:nacelle:wetted_area",
        "data:geometry:propulsion:pylon:wetted_area",
        "data:geometry:propulsion:engine:count",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    component = ComputeTotalArea()

    problem = run_system(component, input_vars)

    total_surface = problem["data:geometry:aircraft:wetted_area"]
    assert total_surface == pytest.approx(783.997, abs=1e-3)


def test_geometry_update_mlg(input_xml):
    """ Tests computation of the main landing gear """

    input_list = [
        "data:geometry:wing:MAC:length",
        "data:geometry:wing:MAC:at25percent:x",
    ]

    input_vars = input_xml.read(only=input_list).to_ivc()

    input_vars.add_output("data:weight:aircraft:CG:aft:MAC_position", 0.364924)
    input_vars.add_output("data:weight:airframe:landing_gear:front:CG:x", 5.07)

    problem = run_system(UpdateMLG(), input_vars)

    cg_a51 = problem["data:weight:airframe:landing_gear:main:CG:x"]
    assert cg_a51 == pytest.approx(18.00, abs=1e-2)
