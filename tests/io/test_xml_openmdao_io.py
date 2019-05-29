"""
Tests basic XML serializer for OpenMDAO variables
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

import os.path as pth

from lxml import etree
from openmdao.core.problem import Problem
from openmdao.drivers.scipy_optimizer import ScipyOptimizeDriver

from fastoad.io.xml.constants import UNIT_ATTRIBUTE
from fastoad.io.xml.openmdao_basic_io import OpenMdaoXmlIO
from tests.sellar_example.sellar import Sellar


def test_basic_xml_read():
    """
    Tests the creation of an IndepVarComp instance from XML file
    """
    filename = pth.join(pth.dirname(__file__), 'data', 'basic_openmdao.xml')
    xml_io = OpenMdaoXmlIO(filename)

    ivc = xml_io.read()

    names = []
    values = []
    units = []

    # pylint: disable=protected-access  # Only way to access defined outputs without a model run.
    for (name, value, attribs) in ivc._indep_external:
        names.append(name)
        values.append(value)
        units.append(attribs['units'])

    assert names[0] == 'geometry:total_surface'
    assert values[0] == 780.3
    assert units[0] == 'm**2'

    assert names[2] == 'geometry:wing:aspect_ratio'
    assert values[2] == 9.8
    assert units[2] is None

    assert names[3] == 'geometry:fuselage:length'
    assert values[3] == 40.
    assert units[3] == 'm'


def test_basic_xml_write_from_indepvarcomp():
    """
    Tests the creation of an XML file from an IndepVarComp instance
    """

    # Get the IndepVarComp instance
    filename = pth.join(pth.dirname(__file__), 'data', 'basic_openmdao.xml')
    xml_read = OpenMdaoXmlIO(filename)
    ivc = xml_read.read()

    # write it
    new_filename = pth.join(pth.dirname(__file__), 'results', 'basic_openmdao.xml')
    xml_write = OpenMdaoXmlIO(new_filename)
    xml_write.write(ivc)

    # check
    ref_context = etree.iterparse(filename, events=("start", "end"))
    result_context = etree.iterparse(new_filename, events=("start", "end"))

    for (ref_action, ref_elem), (result_action, result_elem) in zip(ref_context, result_context):
        assert ref_action == result_action
        try:
            assert ref_elem.text.strip() == result_elem.text.strip()  # identical text
        except AssertionError:
            assert float(ref_elem.text) == float(result_elem.text)  # identical value

        assert ref_elem.attrib.get(UNIT_ATTRIBUTE, None) == result_elem.get(UNIT_ATTRIBUTE, None)


def test_basic_xml_write_from_problem():
    """
    Tests the creation of an XML file from OpenMDAO components
    """
    # Create and run the problem
    problem = Problem()
    problem.model = Sellar()

    problem.driver = ScipyOptimizeDriver()

    problem.driver.options['optimizer'] = 'SLSQP'
    #
    problem.model.approx_totals()
    problem.model.add_design_var('x', lower=0, upper=10)
    problem.model.add_design_var('z', lower=0, upper=10)

    problem.model.add_objective('f')

    problem.model.add_constraint('g1', upper=0.)
    problem.model.add_constraint('g2', upper=0.)

    problem.setup()
    problem.run_driver()

    # Write the XML file
    filename = pth.join(pth.dirname(__file__), 'results', 'sellar.xml')
    xml_write = OpenMdaoXmlIO(filename)
    xml_write.path_separator = '.'
    xml_write.write(problem.model)

    # Check
    tree = etree.parse(filename)
    assert len(tree.xpath('/aircraft/indeps/x')) == 1
    assert len(tree.xpath('/aircraft/indeps/z')) == 2
    assert len(tree.xpath('/aircraft/Disc1/y1')) == 1
    assert len(tree.xpath('/aircraft/Disc2/y2')) == 1
    assert len(tree.xpath('/aircraft/Functions/f')) == 1
    assert len(tree.xpath('/aircraft/Functions/g1')) == 1
    assert len(tree.xpath('/aircraft/Functions/g2')) == 1
