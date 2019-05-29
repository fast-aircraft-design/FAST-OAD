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
from collections import namedtuple
from typing import List

from lxml import etree
from openmdao.core.indepvarcomp import IndepVarComp
from openmdao.core.problem import Problem
from openmdao.drivers.scipy_optimizer import ScipyOptimizeDriver
from pytest import approx

from fastoad.io.xml.openmdao_basic_io import OpenMdaoXmlIO
from tests.sellar_example.sellar import Sellar

_OutputVariable = namedtuple('_OutputVariable', ['name', 'value', 'units'])


def _check_basic_ivc(ivc: IndepVarComp):
    """ Checks that provided IndepVarComp instance matches content of data/basic.xml file """

    outputs: List[_OutputVariable] = []
    for (name, value, attributes) in ivc._indep_external:
        outputs.append(_OutputVariable(name, value, attributes['units']))

    assert len(outputs) == 9

    # Using pytest.approx for numerical reason, but also because it works even if sequence types
    # are different (lists, tuples, numpy arrays)
    assert outputs[0].name == 'geometry:total_surface'
    assert outputs[0].value == approx([780.3])
    assert outputs[0].units == 'm**2'

    assert outputs[1].name == 'geometry:wing:span'
    assert outputs[1].value == approx([42])
    assert outputs[1].units is 'm'

    assert outputs[2].name == 'geometry:wing:aspect_ratio'
    assert outputs[2].value == approx([9.8])
    assert outputs[2].units is None

    assert outputs[3].name == 'geometry:fuselage:length'
    assert outputs[3].value == approx([40.])
    assert outputs[3].units == 'm'

    assert outputs[4].name == 'constants:k1'
    assert outputs[4].value == approx([1., 2., 3.])
    assert outputs[4].units == 'kg'

    assert outputs[5].name == 'constants:k2'
    assert outputs[5].value == approx([10., 20.])
    assert outputs[5].units is None

    assert outputs[6].name == 'constants:k3'
    assert outputs[6].value == approx([100., 200., 300., 400.])
    assert outputs[6].units == 'm/s'

    assert outputs[7].name == 'constants:k4'
    assert outputs[7].value == approx([-1, -2, -3])
    assert outputs[7].units is None

    assert outputs[8].name == 'constants:k5'
    assert outputs[8].value == approx([100, 200, 400, 500, 600])
    assert outputs[8].units is None


def test_basic_xml_read_and_write_from_indepvarcomp():
    """
    Tests the creation of an XML file from an IndepVarComp instance
    """

    # Check reading
    filename = pth.join(pth.dirname(__file__), 'data', 'basic.xml')
    xml_read = OpenMdaoXmlIO(filename)
    ivc = xml_read.read()
    _check_basic_ivc(ivc)

    # write it
    new_filename = pth.join(pth.dirname(__file__), 'results', 'basic.xml')
    xml_write = OpenMdaoXmlIO(new_filename)
    xml_write.write(ivc)

    # check (read another IndepVarComp instance from new xml)
    xml_check = OpenMdaoXmlIO(new_filename)
    new_ivc = xml_check.read()
    _check_basic_ivc(new_ivc)


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


if __name__ == '__main__':
    test_basic_xml_read_and_write_from_indepvarcomp()
