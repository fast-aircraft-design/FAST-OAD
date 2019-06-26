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
