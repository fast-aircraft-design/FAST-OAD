"""
Tests basic XML serializer for OpenMDAO variables
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

import os.path as pth
from shutil import rmtree

import numpy as np
import pytest
from lxml import etree
from numpy.testing import assert_allclose
from openmdao.core.indepvarcomp import IndepVarComp

from fastoad.io.xml import OMXmlIO
from fastoad.io.xml.exceptions import FastXPathEvalError
from fastoad.openmdao.connections_utils import get_variables_from_ivc

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), 'data')
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__),
                               'results', pth.splitext(pth.basename(__file__))[0])


@pytest.fixture(scope='module')
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


def _check_basic_ivc(ivc: IndepVarComp):
    """ Checks that provided IndepVarComp instance matches content of data/basic.xml file """

    outputs = get_variables_from_ivc(ivc)

    # Using pytest.approx for numerical reason, but also because it works even if sequence types
    # are different (lists, tuples, numpy arrays)
    assert_allclose(780.3, outputs['geometry:total_surface'].value)
    assert outputs['geometry:total_surface'].units == 'm**2'

    assert_allclose(42, outputs['geometry:wing:span'].value)
    assert outputs['geometry:wing:span'].units == 'm'

    assert_allclose(9.8, outputs['geometry:wing:aspect_ratio'].value)
    assert outputs['geometry:wing:aspect_ratio'].units is None

    assert_allclose(40., outputs['geometry:fuselage:length'].value)
    assert outputs['geometry:fuselage:length'].units == 'm'

    assert_allclose(-42., outputs['constants'].value)
    assert outputs['constants'].units is None

    assert_allclose([1., 2., 3.], outputs['constants:k1'].value)
    assert outputs['constants:k1'].units == 'kg'

    assert_allclose([10., 20.], outputs['constants:k2'].value)
    assert outputs['constants:k2'].units is None

    assert_allclose([100., 200., 300., 400.], outputs['constants:k3'].value)
    assert outputs['constants:k3'].units == 'm/s'

    assert_allclose([-1, -2, -3], outputs['constants:k4'].value)
    assert outputs['constants:k4'].units is None

    assert_allclose([100, 200, 400, 500, 600], outputs['constants:k5'].value)
    assert outputs['constants:k5'].units is None

    assert_allclose([[1e2, 3.4e5], [5.4e3, 2.1]], outputs['constants:k8'].value)
    assert outputs['constants:k8'].units is None

    assert len(outputs) == 11


def test_basic_xml_read_and_write_from_ivc(cleanup):
    """
    Tests the creation of an XML file from an IndepVarComp instance
    """
    result_folder = pth.join(RESULTS_FOLDER_PATH, 'basic_xml')

    # Check write hand-made component
    ivc = IndepVarComp()
    ivc.add_output('geometry/total_surface', val=[780.3], units='m**2')
    ivc.add_output('geometry/wing/span', val=42.0, units='m', desc='span of the wing')
    ivc.add_output('geometry/wing/aspect_ratio', val=[9.8])
    ivc.add_output('geometry/fuselage/length', val=40.0, units='m')
    ivc.add_output('constants', val=[-42.], desc='the answer')
    ivc.add_output('constants/k1', val=[1.0, 2.0, 3.0], units='kg')
    ivc.add_output('constants/k2', val=[10.0, 20.0], desc='Geronimo!')
    ivc.add_output('constants/k3', val=np.array([100.0, 200.0, 300.0, 400.0]), units='m/s')
    ivc.add_output('constants/k4', val=[-1.0, -2.0, -3.0])
    ivc.add_output('constants/k5', val=[100.0, 200.0, 400.0, 500.0, 600.0])
    ivc.add_output('constants/k8', val=[[1e2, 3.4e5], [5.4e3, 2.1]])

    # Try writing with non-existing folder
    assert not pth.exists(result_folder)
    filename = pth.join(result_folder, 'handmade.xml')
    xml_write = OMXmlIO(filename)
    xml_write.path_separator = '/'
    xml_write.write(ivc)

    # check (read another IndepVarComp instance from  xml)
    xml_check = OMXmlIO(filename)
    xml_check.path_separator = ':'
    new_ivc = xml_check.read()
    _check_basic_ivc(new_ivc)

    # Check reading hand-made XML (with some format twists)
    filename = pth.join(DATA_FOLDER_PATH, 'basic.xml')
    xml_read = OMXmlIO(filename)
    xml_read.path_separator = ':'
    ivc = xml_read.read()
    _check_basic_ivc(ivc)

    # write it (with existing destination folder)
    new_filename = pth.join(result_folder, 'basic.xml')
    xml_write = OMXmlIO(new_filename)
    xml_write.path_separator = ':'
    xml_write.write(ivc)

    # check (read another IndepVarComp instance from new xml)
    xml_check = OMXmlIO(new_filename)
    xml_check.path_separator = ':'
    new_ivc = xml_check.read()
    _check_basic_ivc(new_ivc)

    # try to write with bad separator
    xml_write.path_separator = '/'
    with pytest.raises(FastXPathEvalError):
        xml_write.write(ivc)


def test_basic_xml_partial_read_and_write_from_ivc(cleanup):
    """
    Tests the creation of an XML file from an IndepVarComp instance with only and ignore options
    """
    result_folder = pth.join(RESULTS_FOLDER_PATH, 'basic_partial_xml')

    # Read full IndepVarComp
    filename = pth.join(DATA_FOLDER_PATH, 'basic.xml')
    xml_read = OMXmlIO(filename)
    xml_read.path_separator = ':'
    ivc = xml_read.read(ignore=['does_not_exist'])
    _check_basic_ivc(ivc)

    # Add something to ignore and write it
    ivc.add_output('should_be_ignored:pointless', val=0.0)
    ivc.add_output('should_also_be_ignored', val=-10.0)

    badvar_filename = pth.join(result_folder, 'with_bad_var.xml')
    xml_write = OMXmlIO(badvar_filename)
    xml_write.path_separator = ':'
    xml_write.write(ivc, ignore=['does_not_exist'])  # Check with non-existent var in ignore list

    tree = etree.parse(badvar_filename)
    assert float(tree.xpath('should_be_ignored/pointless')[0].text.strip()) == 0.0
    assert float(tree.xpath('should_also_be_ignored')[0].text.strip()) == -10.0

    # Check partial reading with 'ignore'
    xml_read = OMXmlIO(badvar_filename)
    xml_read.path_separator = ':'
    new_ivc = xml_read.read(ignore=['should_be_ignored:pointless', 'should_also_be_ignored'])
    _check_basic_ivc(new_ivc)

    # Check partial reading with 'only'
    ok_vars = ['geometry:total_surface',
               'geometry:wing:span',
               'geometry:wing:aspect_ratio',
               'geometry:fuselage:length',
               'constants',
               'constants:k1',
               'constants:k2',
               'constants:k3',
               'constants:k4',
               'constants:k5',
               'constants:k8'
               ]
    new_ivc2 = xml_read.read(only=ok_vars)
    _check_basic_ivc(new_ivc2)

    # Check partial writing with 'ignore'
    varok_filename = pth.join(result_folder, 'with_bad_var.xml')
    xml_write = OMXmlIO(varok_filename)
    xml_write.path_separator = ':'
    xml_write.write(ivc, ignore=['should_be_ignored:pointless', 'should_also_be_ignored'])

    xml_read = OMXmlIO(varok_filename)
    xml_read.path_separator = ':'
    new_ivc = xml_read.read()
    _check_basic_ivc(new_ivc)

    # Check partial writing with 'only'
    varok2_filename = pth.join(result_folder, 'with_bad_var.xml')
    xml_write = OMXmlIO(varok2_filename)
    xml_write.path_separator = ':'
    xml_write.write(ivc, only=ok_vars)

    xml_read = OMXmlIO(varok2_filename)
    xml_read.path_separator = ':'
    new_ivc = xml_read.read()
    _check_basic_ivc(new_ivc)
