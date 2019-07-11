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

import pytest
from lxml.etree import XPathEvalError
from openmdao.core.indepvarcomp import IndepVarComp
from pytest import approx

from fastoad.io.xml import OpenMdaoCustomXmlIO
from fastoad.io.xml.translator import VarXpathTranslator


_Variable = namedtuple('_Variable', ['name', 'value', 'units'])


def _check_basic2_ivc(ivc: IndepVarComp):
    """ Checks that provided IndepVarComp instance matches content of data/custom.xml file """

    outputs: List[_Variable] = []
    for (name, value, attributes) in ivc._indep_external:  # pylint: disable=protected-access
        outputs.append(_Variable(name, value, attributes['units']))

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


def test_custom_xml_read_and_write_from_indepvarcomp():
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

    # test read ---------------------------------------------------------------
    filename = pth.join(data_folder, 'custom.xml')
    xml_read = OpenMdaoCustomXmlIO(filename)

    # test without setting translation table
    with pytest.raises(ValueError) as exc_info:
        _ = xml_read.read()
    assert exc_info is not None

    # test with setting a bad translation table (missing xpath)
    with pytest.raises(ValueError) as exc_info:
        xml_read.set_translator(VarXpathTranslator(variable_names=var_names + ['dummy_var'],
                                                   xpaths=xpaths + ['dummy_xpath']))
        _ = xml_read.read()
    assert exc_info is not None

    # test with setting a bad translation table (bad xpath)
    with pytest.raises(XPathEvalError) as exc_info:
        xml_read.set_translator(VarXpathTranslator(variable_names=var_names + ['dummy_var'],
                                                   xpaths=xpaths + ['bad:xpath']))
        _ = xml_read.read()
    assert exc_info is not None

    # test after setting translation table
    translator = VarXpathTranslator(variable_names=var_names, xpaths=xpaths)
    xml_read.set_translator(translator)
    ivc = xml_read.read()
    _check_basic2_ivc(ivc)

    # test write --------------------------------------------------------------
    new_filename = pth.join(result_folder, 'custom.xml')
    xml_write = OpenMdaoCustomXmlIO(new_filename)

    # test without setting translation table
    with pytest.raises(ValueError) as exc_info:
        xml_write.write(ivc)
    assert exc_info is not None

    # test after setting translation table
    xml_write.set_translator(translator)
    xml_write.write(ivc)

    # check written data
    assert pth.isfile(new_filename)
    xml_check = OpenMdaoCustomXmlIO(new_filename)

    xpaths = ['total_area',
              'wing/span',
              'wing/aspect_ratio',
              'fuselage_length']
    translator.set(var_names, xpaths)
    xml_check.set_translator(translator)
    new_ivc = xml_check.read()
    _check_basic2_ivc(new_ivc)


def test_custom_xml_read_and_write_with_translation_table():
    data_folder = pth.join(pth.dirname(__file__), 'data')
    result_folder = pth.join(pth.dirname(__file__), 'results', 'custom_xml_with_translation_table')
    if pth.exists(result_folder):
        shutil.rmtree(result_folder)

    # test read ---------------------------------------------------------------
    filename = pth.join(data_folder, 'custom.xml')
    xml_read = OpenMdaoCustomXmlIO(filename)

    # test after setting translation table
    translator = VarXpathTranslator(source=pth.join(data_folder, 'custom_translation.txt'))
    xml_read.set_translator(translator)
    ivc = xml_read.read()
    _check_basic2_ivc(ivc)

def test_custom_xml_read_and_write_with_only_or_ignore():
    data_folder = pth.join(pth.dirname(__file__), 'data')
    result_folder = pth.join(pth.dirname(__file__), 'results', 'custom_xml_with_translation_table')
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

    # test read ---------------------------------------------------------------
    filename = pth.join(data_folder, 'custom.xml')
    xml_read = OpenMdaoCustomXmlIO(filename)

    translator = VarXpathTranslator(variable_names=var_names, xpaths=xpaths)
    xml_read.set_translator(translator)

    # test with "only"
    ivc = xml_read.read(only=['geometry:wing:span'])
    outputs: List[_Variable] = []
    for (name, value, attributes) in ivc._indep_external:  # pylint: disable=protected-access
        outputs.append(_Variable(name, value, attributes['units']))
    assert len(outputs) == 1
    assert outputs[0].name == 'geometry:wing:span'
    assert outputs[0].value == approx([42])
    assert outputs[0].units == 'm'

    # test with "ignore"
    ivc = xml_read.read(
        ignore=['geometry:total_surface', 'geometry:wing:aspect_ratio', 'geometry:fuselage:length'])
    outputs: List[_Variable] = []
    for (name, value, attributes) in ivc._indep_external:  # pylint: disable=protected-access
        outputs.append(_Variable(name, value, attributes['units']))
    assert len(outputs) == 1
    assert outputs[0].name == 'geometry:wing:span'
    assert outputs[0].value == approx([42])
    assert outputs[0].units == 'm'


    