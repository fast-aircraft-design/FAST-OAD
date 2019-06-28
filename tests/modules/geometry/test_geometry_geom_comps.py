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
        'tlar:NPAX',
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

    input_vars.add_output('geometry:ht_x0', 3.141)

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
    assert length == pytest.approx(3.141, abs=1e-3)
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


def test_compute_vol_co(xpath_reader: XPathReader, input_xml):
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