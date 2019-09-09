"""
Test module for geometry global groups
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
from openmdao.core.problem import Problem

from tests.testing_utilities import run_system

from fastoad.io.xml import XPathReader
from fastoad.io.xml.openmdao_legacy_io import OpenMdaoLegacy1XmlIO
from fastoad.modules.geometry import GetCG, Geometry

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

def test_geometry_get_cg(input_xml):
    """ Tests computation of the cg estimation """

    input_list = []

    input_vars = input_xml.read(only=input_list)

    component = GetCG()

    problem = run_system(component, input_vars)

    area_pf = problem['geometry:wing_area_pf']
    assert area_pf == pytest.approx(100.303, abs=1e-3)
