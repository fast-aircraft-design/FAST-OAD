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
from typing import List

import pytest
from pytest import approx
from openmdao.core.indepvarcomp import IndepVarComp

from fastoad.io.xml import OMCustomXmlIO
from fastoad.io.xml.translator import VarXpathTranslator
from fastoad.openmdao.types import Variable

def _check_basic2_ivc(ivc: IndepVarComp):
    """ Checks that provided IndepVarComp instance matches content of data/custom.xml file """

    outputs: List[Variable] = []
    for (name, value, attributes) in ivc._indep_external:  # pylint: disable=protected-access
        outputs.append(Variable(name, value, attributes['units']))

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


def test_custom_xml_read_and_write_from_ivc():
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
    xml_read = OMCustomXmlIO(filename)

    # test without setting translation table
    with pytest.raises(ValueError) as exc_info:
        _ = xml_read.read()
    assert exc_info is not None

    # test with setting a non-exhaustive translation table (missing variable name in the translator)
    # we expect that the variable is not included in the ivc
    filename = pth.join(data_folder, 'custom_additional_var.xml')
    xml_read = OMCustomXmlIO(filename)
    xml_read.set_translator(VarXpathTranslator(variable_names=var_names,
                                               xpaths=xpaths))
    ivc = xml_read.read()
    _check_basic2_ivc(ivc)

    filename = pth.join(data_folder, 'custom.xml')
    xml_read = OMCustomXmlIO(filename)

    # test with setting a bad translation with an additional var not present in the xml
    # we expect that all goes on well
    xml_read.set_translator(VarXpathTranslator(variable_names=var_names + ['additional_var'],
                                               xpaths=xpaths + ['bad:xpath']))
    ivc = xml_read.read()
    _check_basic2_ivc(ivc)

    # test after setting translation table
    translator = VarXpathTranslator(variable_names=var_names, xpaths=xpaths)
    xml_read.set_translator(translator)
    ivc = xml_read.read()
    _check_basic2_ivc(ivc)

    # test write --------------------------------------------------------------
    new_filename = pth.join(result_folder, 'custom.xml')
    xml_write = OMCustomXmlIO(new_filename)

    # test without setting translation table
    with pytest.raises(ValueError) as exc_info:
        xml_write.set_system(ivc)
        xml_write.write()
    assert exc_info is not None

    # test after setting translation table
    xml_write.set_translator(translator)
    xml_write.set_system(ivc)
    xml_write.write()

    # check written data
    assert pth.isfile(new_filename)
    xml_check = OMCustomXmlIO(new_filename)

    xpaths = ['total_area',
              'wing/span',
              'wing/aspect_ratio',
              'fuselage_length']
    translator.set(var_names, xpaths)
    xml_check.set_translator(translator)
    new_ivc = xml_check.read()
    _check_basic2_ivc(new_ivc)


def test_custom_xml_read_and_write_with_translation_table():
    """
    Tests the creation of an XML file with a translation table
    """
    data_folder = pth.join(pth.dirname(__file__), 'data')
    result_folder = pth.join(pth.dirname(__file__), 'results', 'custom_xml_with_translation_table')
    if pth.exists(result_folder):
        shutil.rmtree(result_folder)

    # test read ---------------------------------------------------------------
    filename = pth.join(data_folder, 'custom.xml')
    xml_read = OMCustomXmlIO(filename)

    # test after setting translation table
    translator = VarXpathTranslator(source=pth.join(data_folder, 'custom_translation.txt'))
    xml_read.set_translator(translator)
    ivc = xml_read.read()
    _check_basic2_ivc(ivc)

def test_custom_xml_read_and_write_with_only_or_ignore():
    """
    Tests the creation of an XML file with only and ignore options
    """
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
    xml_read = OMCustomXmlIO(filename)

    translator = VarXpathTranslator(variable_names=var_names, xpaths=xpaths)
    xml_read.set_translator(translator)

    # test with "only"
    ivc = xml_read.read(only=['geometry:wing:span'])
    outputs: List[Variable] = []
    for (name, value, attributes) in ivc._indep_external:  # pylint: disable=protected-access
        outputs.append(Variable(name, value, attributes['units']))
    assert len(outputs) == 1
    assert outputs[0].name == 'geometry:wing:span'
    assert outputs[0].value == approx([42])
    assert outputs[0].units == 'm'

    # test with "ignore"
    ivc = xml_read.read(
        ignore=['geometry:total_surface', 'geometry:wing:aspect_ratio', 'geometry:fuselage:length'])
    outputs: List[Variable] = []
    for (name, value, attributes) in ivc._indep_external:  # pylint: disable=protected-access
        outputs.append(Variable(name, value, attributes['units']))
    assert len(outputs) == 1
    assert outputs[0].name == 'geometry:wing:span'
    assert outputs[0].value == approx([42])
    assert outputs[0].units == 'm'

def test_custom_xml_update():
    """
    Tests the update of an XML file
    """
    data_folder = pth.join(pth.dirname(__file__), 'data')
    result_folder = pth.join(pth.dirname(__file__), 'results', 'xml_update')

    var_names = ['geometry:total_surface',
                 'geometry:wing:span',
                 'geometry:wing:aspect_ratio',
                 'geometry:fuselage:length']

    xpaths = ['total_area',
              'wing/span',
              'wing/aspect_ratio',
              'fuselage_length']

    filename_original = pth.join(data_folder, 'custom.xml')
    xml_original = OMCustomXmlIO(filename_original)

    translator = VarXpathTranslator(variable_names=var_names, xpaths=xpaths)
    xml_original.set_translator(translator)
    xml_original.read()

    filename_ref = pth.join(data_folder, 'custom_ref.xml')
    xml_ref = OMCustomXmlIO(filename_ref)
    xml_ref.set_translator(translator)
    xml_ref.read()

    filename_updated = pth.join(result_folder, 'custom_updated.xml')

    xml_original.update(xml_ref)

    xml_read = OMCustomXmlIO(filename_updated)
    xml_read.set_translator(translator)
    xml_read.set_system(xml_original.get_system())

    ivc = xml_read.read(only=['geometry:fuselage:length'])
    outputs: List[Variable] = []
    for (name, value, attributes) in ivc._indep_external:  # pylint: disable=protected-access
        outputs.append(Variable(name, value, attributes['units']))
    assert len(outputs) == 1
    assert outputs[0].name == 'geometry:fuselage:length'
    # The value shall have been modified with respect to ref file
    assert outputs[0].value == approx([80.0])
    assert outputs[0].units == 'm'
