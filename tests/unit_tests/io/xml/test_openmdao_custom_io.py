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
from shutil import rmtree
from typing import List

import pytest
from openmdao.core.indepvarcomp import IndepVarComp
from pytest import approx

from fastoad.io.xml import OMCustomXmlIO
from fastoad.io.xml.exceptions import FastMissingTranslatorError
from fastoad.io.xml.translator import VarXpathTranslator
from fastoad.openmdao.variables import Variable

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), 'data')
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__),
                               'results', pth.splitext(pth.basename(__file__))[0])


@pytest.fixture(scope='module')
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


def _check_basic2_ivc(ivc: IndepVarComp):
    """ Checks that provided IndepVarComp instance matches content of data/custom.xml file """

    outputs: List[Variable] = []
    for (name, value, attributes) in ivc._indep_external:  # pylint: disable=protected-access
        outputs.append(Variable(name, value, attributes['units']))

    assert len(outputs) == 5

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

    assert outputs[3].name == 'geometry:wing:chord'
    assert outputs[3].value == approx([5., 3.5, 2.])
    assert outputs[3].units == 'm'

    assert outputs[4].name == 'geometry:fuselage:length'
    assert outputs[4].value == approx([40.])
    assert outputs[4].units == 'm'


def test_custom_xml_read_and_write_from_ivc(cleanup):
    """
    Tests the creation of an XML file from an IndepVarComp instance
    """
    result_folder = pth.join(RESULTS_FOLDER_PATH, 'custom_xml')

    var_names = ['geometry:total_surface',
                 'geometry:wing:span',
                 'geometry:wing:chord',
                 'geometry:wing:aspect_ratio',
                 'geometry:fuselage:length']

    xpaths = ['total_area',
              'wing/span',
              'wing/chord',
              'wing/aspect_ratio',
              'fuselage_length']

    # test read ---------------------------------------------------------------

    # test without setting translation table
    filename = pth.join(DATA_FOLDER_PATH, 'custom.xml')
    xml_read = OMCustomXmlIO(filename)
    with pytest.raises(FastMissingTranslatorError):
        xml_read.read()

    # test after setting translation table
    translator = VarXpathTranslator(variable_names=var_names, xpaths=xpaths)
    xml_read.set_translator(translator)
    ivc = xml_read.read()
    _check_basic2_ivc(ivc)

    # test with setting a non-exhaustive translation table (missing variable name in the translator)
    # we expect that the variable is not included in the ivc
    filename = pth.join(DATA_FOLDER_PATH, 'custom_additional_var.xml')
    xml_read = OMCustomXmlIO(filename)
    xml_read.set_translator(VarXpathTranslator(variable_names=var_names,
                                               xpaths=xpaths))
    ivc = xml_read.read()
    _check_basic2_ivc(ivc)

    # test with setting a bad translation with an additional var not present in the xml
    # we expect that all goes on well
    filename = pth.join(DATA_FOLDER_PATH, 'custom.xml')
    xml_read = OMCustomXmlIO(filename)
    xml_read.set_translator(VarXpathTranslator(variable_names=var_names + ['additional_var'],
                                               xpaths=xpaths + ['bad:xpath']))
    ivc = xml_read.read()
    _check_basic2_ivc(ivc)

    # test write --------------------------------------------------------------
    new_filename = pth.join(result_folder, 'custom.xml')
    xml_write = OMCustomXmlIO(new_filename)

    # test without setting translation table
    with pytest.raises(FastMissingTranslatorError):
        xml_write.write(ivc)

    # test after setting translation table
    xml_write.set_translator(translator)
    xml_write.write(ivc)

    # check written data
    assert pth.isfile(new_filename)
    xml_check = OMCustomXmlIO(new_filename)

    translator.set(var_names, xpaths)
    xml_check.set_translator(translator)
    new_ivc = xml_check.read()
    _check_basic2_ivc(new_ivc)


def test_custom_xml_read_and_write_with_translation_table(cleanup):
    """
    Tests the creation of an XML file with a translation table
    """
    result_folder = pth.join(RESULTS_FOLDER_PATH, 'custom_xml_with_translation_table')

    # test read ---------------------------------------------------------------
    filename = pth.join(DATA_FOLDER_PATH, 'custom.xml')
    xml_read = OMCustomXmlIO(filename)

    # test after setting translation table
    translator = VarXpathTranslator(source=pth.join(DATA_FOLDER_PATH, 'custom_translation.txt'))
    xml_read.set_translator(translator)
    ivc = xml_read.read()
    _check_basic2_ivc(ivc)

    new_filename = pth.join(result_folder, 'custom.xml')
    xml_write = OMCustomXmlIO(new_filename)
    xml_write.set_translator(translator)
    xml_write.write(ivc)


def test_custom_xml_read_and_write_with_only_or_ignore(cleanup):
    """
    Tests the creation of an XML file with only and ignore options
    """
    result_folder = pth.join(RESULTS_FOLDER_PATH, 'custom_xml_with_translation_table')

    var_names = ['geometry:total_surface',
                 'geometry:wing:span',
                 'geometry:wing:aspect_ratio',
                 'geometry:fuselage:length']

    xpaths = ['total_area',
              'wing/span',
              'wing/aspect_ratio',
              'fuselage_length']

    # test read ---------------------------------------------------------------
    filename = pth.join(DATA_FOLDER_PATH, 'custom.xml')
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

    # test with patterns in "only"
    ivc = xml_read.read(only=['*:wing:*'])
    outputs: List[Variable] = []
    for (name, value, attributes) in ivc._indep_external:  # pylint: disable=protected-access
        outputs.append(Variable(name, value, attributes['units']))
    assert len(outputs) == 2
    assert outputs[0].name == 'geometry:wing:span'
    assert outputs[0].value == approx([42])
    assert outputs[0].units == 'm'
    assert outputs[1].name == 'geometry:wing:aspect_ratio'
    assert outputs[1].value == approx([9.8])
    assert outputs[1].units is None

    # test with patterns in "ignore"
    ivc = xml_read.read(ignore=['geometry:*u*', 'geometry:wing:aspect_ratio'])
    outputs: List[Variable] = []
    for (name, value, attributes) in ivc._indep_external:  # pylint: disable=protected-access
        outputs.append(Variable(name, value, attributes['units']))
    assert len(outputs) == 1
    assert outputs[0].name == 'geometry:wing:span'
    assert outputs[0].value == approx([42])
    assert outputs[0].units == 'm'
