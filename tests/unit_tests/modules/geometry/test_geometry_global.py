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

from fastoad.io.xml import XPathReader
from fastoad.io.xml.openmdao_legacy_io import OMLegacy1XmlIO
from fastoad.modules.geometry import GetCG, Geometry
from tests.testing_utilities import run_system


@pytest.fixture(scope="module")
def xpath_reader() -> XPathReader:
    """
    :return: access to the sample xml data
    """
    return XPathReader(
        pth.join(pth.dirname(__file__), "data", "CeRAS01_baseline.xml"))

@pytest.fixture(scope="module")
def input_xml() -> OMLegacy1XmlIO:
    """
    :return: access to the sample xml data
    """
    # TODO: have more consistency in input data (no need for the whole CeRAS01_baseline.xml)
    return OMLegacy1XmlIO(
        pth.join(pth.dirname(__file__), "data", "CeRAS01_baseline.xml"))

def test_geometry_get_cg():
    """ Tests computation of the cg estimation """

    input_xml_file_name = pth.join(pth.dirname(__file__), "data", "get_cg_inputs.xml")

    input_xml = OMLegacy1XmlIO(input_xml_file_name)

    input_vars = input_xml.read()

    input_vars.add_output('geometry:fuselage_Lcabin', val=0.81*37.507, units='m')

    problem = Problem()
    model = problem.model

    # model.add_subsystem('inputs', input_vars, promotes=['*'])
    # model.add_subsystem('geometry', GetCG(), promotes=['*'])

    problem = run_system(GetCG(), input_vars)

    # problem.run_model()
    cg_ratio = problem['cg_ratio']
    assert cg_ratio == pytest.approx(0.387185, abs=1e-6)
    cg_airframe_a51 = problem['cg_airframe:A51']
    assert cg_airframe_a51 == pytest.approx(18.11, abs=1e-1)


def test_geometry_geometry_global():
    """ Tests computation of the global geometry """

    input_xml_file_name = pth.join(pth.dirname(__file__), "data", "global_geometry_inputs.xml")

    input_xml = OMLegacy1XmlIO(input_xml_file_name)

    input_vars = input_xml.read()

    problem = Problem()
    model = problem.model

    model.add_subsystem('inputs', input_vars, promotes=['*'])
    model.add_subsystem('geometry', Geometry(), promotes=['*'])

    problem.setup(mode='fwd')
    problem.run_model()
    static_margin = problem['static_margin']
    # TODO: see if this static margin is correct
    assert static_margin == pytest.approx(-0.008870, abs=1e-6)
    cg_global = problem['cg:CG']
    assert cg_global == pytest.approx(17.3, abs=1e-1)
