"""
Test module for geometry global groups
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

# pylint: disable=redefined-outer-name  # needed for pytest fixtures
import os.path as pth

import openmdao.api as om
import pytest

from fastoad.io.xml import XPathReader
from fastoad.io.xml.openmdao_legacy_io import OMLegacy1XmlIO
from fastoad.modules.geometry import GetCG, Geometry
from fastoad.modules.mass_breakdown import MassBreakdown
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

    input_vars.add_output('geometry:cabin:length', val=0.81 * 37.507, units='m')

    group = om.Group()
    # TODO: Inputs should contain mass breakdown data so only GetCG() is run
    group.add_subsystem('mass_breakdown', MassBreakdown(), promotes=['*'])
    group.add_subsystem('CG', GetCG(), promotes=['*'])
    group.nonlinear_solver = om.NonlinearBlockGS()
    problem = run_system(group, input_vars)

    # problem.run_model()
    cg_ratio = problem['weight:aircraft:CG:ratio']
    assert cg_ratio == pytest.approx(0.378, abs=1e-3)
    cg_airframe_a51 = problem['weight:airframe:landing_gear:main:CG:x']
    assert cg_airframe_a51 == pytest.approx(18.06, abs=1e-2)


def test_geometry_geometry_global():
    """ Tests computation of the global geometry """

    input_xml_file_name = pth.join(pth.dirname(__file__), "data", "global_geometry_inputs.xml")

    input_xml = OMLegacy1XmlIO(input_xml_file_name)

    input_vars = input_xml.read()

    group = om.Group()
    # TODO: Inputs should contain mass breakdown data so only Geometry() is run
    group.add_subsystem('mass_breakdown', MassBreakdown(), promotes=['*'])
    group.add_subsystem('geometry', Geometry(), promotes=['*'])
    group.nonlinear_solver = om.NonlinearBlockGS()
    problem = run_system(group, input_vars)

    static_margin = problem['handling_qualities:static_margin']
    # TODO: see if this static margin is correct
    assert static_margin == pytest.approx(-0.0102, abs=1e-5)
    cg_global = problem['weight:aircraft:CG:x']
    assert cg_global == pytest.approx(17.2, abs=1e-1)
