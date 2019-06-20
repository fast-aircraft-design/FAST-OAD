"""
Tests custom XML serializer for OpenMDAO variables
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
import shutil
from collections import namedtuple
from typing import List

from openmdao.core.indepvarcomp import IndepVarComp
from pytest import approx

from fastoad.io.xml import OpenMdaoCustomXmlIO

_OutputVariable = namedtuple('_OutputVariable', ['name', 'value', 'units'])


def _check_basic_ivc(ivc: IndepVarComp):
    """ Checks that provided IndepVarComp instance matches content of data/basic.xml file """

    outputs: List[_OutputVariable] = []
    for (name, value, attributes) in ivc._indep_external:  # pylint: disable=protected-access
        outputs.append(_OutputVariable(name, value, attributes['units']))

    assert len(outputs) == 4

    # Using pytest.approx for numerical reason, but also because it works even if sequence types
    # are different (lists, tuples, numpy arrays)
    assert outputs[0].name == 'geometry:total_surface'
    assert outputs[0].value == approx([780.3])
    assert outputs[0].units == 'm**2'

    assert outputs[1].name == 'geometry:wing:span'
    assert outputs[1].value == approx([42])
    assert outputs[1].units == 'm'

    assert outputs[2].name == 'geometry:wing:aspect_ratio'
    assert outputs[2].value == approx([9.8])
    assert outputs[2].units is None

    assert outputs[3].name == 'geometry:fuselage:length'
    assert outputs[3].value == approx([40.])
    assert outputs[3].units == 'm'


def test_basic_xml_read_and_write_from_indepvarcomp():
    """
    Tests the creation of an XML file from an IndepVarComp instance
    """
    data_folder = pth.join(pth.dirname(__file__), 'data')
    result_folder = pth.join(pth.dirname(__file__), 'results', 'custom_xml')
    if pth.exists(result_folder):
        shutil.rmtree(result_folder)

    var_names = ['geometry:total_surface',
                 'geometry:wing:span',
                 'geometry:wing:aspect_ratio',
                 'geometry:fuselage:length']

    xpaths = ['total_area',
              'wing/span',
              'wing/aspect_ratio',
              'fuselage_length']

    # test read
    filename = pth.join(data_folder, 'basic2.xml')
    xml_read = OpenMdaoCustomXmlIO(filename)
    xml_read.set_translation_table(var_names, xpaths)
    ivc = xml_read.read()
    _check_basic_ivc(ivc)

    # test write
    new_filename = pth.join(result_folder, 'basic2.xml')
    xml_write = OpenMdaoCustomXmlIO(new_filename)
    xml_write.set_translation_table(var_names, xpaths)
    xml_write.write(ivc)

    # check written data
    xml_check = OpenMdaoCustomXmlIO(new_filename)
    xml_check.set_translation_table(var_names, xpaths)
    new_ivc = xml_check.read()
    _check_basic_ivc(new_ivc)
