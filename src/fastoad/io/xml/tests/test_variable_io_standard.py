"""
Tests basic XML serializer for OpenMDAO variables
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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
from fastoad.io import VariableIO
from fastoad.io.xml import VariableXmlStandardFormatter
from fastoad.openmdao.variables import VariableList
from lxml import etree
from numpy.testing import assert_allclose

from ..exceptions import FastXPathEvalError

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(
    pth.dirname(__file__), "results", pth.splitext(pth.basename(__file__))[0]
)


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


def _check_basic_vars(vars: VariableList):
    """ Checks that provided IndepVarComp instance matches content of data/basic.xml file """

    # Using pytest.approx for numerical reason, but also because it works even if sequence types
    # are different (lists, tuples, numpy arrays)
    assert_allclose(780.3, vars["geometry:total_surface"].value)
    assert vars["geometry:total_surface"].units == "m**2"

    assert_allclose(42, vars["geometry:wing:span"].value)
    assert vars["geometry:wing:span"].units == "m"

    assert_allclose(9.8, vars["geometry:wing:aspect_ratio"].value)
    assert vars["geometry:wing:aspect_ratio"].units is None

    assert_allclose(40.0, vars["geometry:fuselage:length"].value)
    assert vars["geometry:fuselage:length"].units == "m"

    assert_allclose(-42.0, vars["constants"].value)
    assert vars["constants"].units is None

    assert_allclose([1.0, 2.0, 3.0], vars["constants:k1"].value)
    assert vars["constants:k1"].units == "kg"

    assert_allclose([10.0, 20.0], vars["constants:k2"].value)
    assert vars["constants:k2"].units is None

    assert_allclose([100.0, 200.0, 300.0, 400.0], vars["constants:k3"].value)
    assert vars["constants:k3"].units == "m/s"

    assert_allclose([-1, -2, -3], vars["constants:k4"].value)
    assert vars["constants:k4"].units is None

    assert_allclose([100, 200, 400, 500, 600], vars["constants:k5"].value)
    assert vars["constants:k5"].units is None

    assert_allclose([[1e2, 3.4e5], [5.4e3, 2.1]], vars["constants:k8"].value)
    assert vars["constants:k8"].units is None

    assert len(vars) == 11


def test_basic_xml_read_and_write_from_vars(cleanup):
    """
    Tests the creation of an XML file from a VariableList instance
    """
    result_folder = pth.join(RESULTS_FOLDER_PATH, "basic_xml")

    # Check write hand-made component
    vars = VariableList()
    vars["geometry/total_surface"] = {"value": [780.3], "units": "m**2"}
    vars["geometry/wing/span"] = {"value": 42.0, "units": "m", "description": "span of the wing"}
    vars["geometry/wing/aspect_ratio"] = {"value": [9.8]}
    vars["geometry/fuselage/length"] = {"value": 40.0, "units": "m"}
    vars["constants"] = {"value": [-42.0], "description": "the answer"}
    vars["constants/k1"] = {"value": [1.0, 2.0, 3.0], "units": "kg"}
    vars["constants/k2"] = {"value": [10.0, 20.0], "description": "Geronimo!"}
    vars["constants/k3"] = {"value": np.array([100.0, 200.0, 300.0, 400.0]), "units": "m/s"}
    vars["constants/k4"] = {"value": [-1.0, -2.0, -3.0]}
    vars["constants/k5"] = {"value": [100.0, 200.0, 400.0, 500.0, 600.0]}
    vars["constants/k8"] = {"value": [[1e2, 3.4e5], [5.4e3, 2.1]]}

    # Try writing with non-existing folder
    assert not pth.exists(result_folder)
    filename = pth.join(result_folder, "handmade.xml")
    xml_write = VariableIO(filename, formatter=VariableXmlStandardFormatter())
    xml_write.path_separator = "/"
    xml_write.write(vars)

    # check (read another IndepVarComp instance from  xml)
    xml_check = VariableIO(filename, formatter=VariableXmlStandardFormatter())
    xml_check.path_separator = ":"
    new_vars = xml_check.read()
    _check_basic_vars(new_vars)

    # Check reading hand-made XML (with some format twists)
    filename = pth.join(DATA_FOLDER_PATH, "basic.xml")
    xml_read = VariableIO(filename, formatter=VariableXmlStandardFormatter())
    xml_read.path_separator = ":"
    vars = xml_read.read()
    _check_basic_vars(vars)

    # write it (with existing destination folder)
    new_filename = pth.join(result_folder, "basic.xml")
    xml_write = VariableIO(new_filename, formatter=VariableXmlStandardFormatter())
    xml_write.path_separator = ":"
    xml_write.write(vars)

    # check (read another IndepVarComp instance from new xml)
    xml_check = VariableIO(new_filename, formatter=VariableXmlStandardFormatter())
    xml_check.path_separator = ":"
    new_vars = xml_check.read()
    _check_basic_vars(new_vars)

    # try to write with bad separator
    xml_write.formatter.path_separator = "/"
    with pytest.raises(FastXPathEvalError):
        xml_write.write(vars)


def test_basic_xml_partial_read_and_write_from_vars(cleanup):
    """
    Tests the creation of an XML file from an IndepVarComp instance with only and ignore options
    """
    result_folder = pth.join(RESULTS_FOLDER_PATH, "basic_partial_xml")

    # Read full IndepVarComp
    filename = pth.join(DATA_FOLDER_PATH, "basic.xml")
    xml_read = VariableIO(filename, formatter=VariableXmlStandardFormatter())
    vars = xml_read.read(ignore=["does_not_exist"])
    _check_basic_vars(vars)

    # Add something to ignore and write it
    vars["should_be_ignored:pointless"] = {"value": 0.0}
    vars["should_also_be_ignored"] = {"value": -10.0}

    badvar_filename = pth.join(result_folder, "with_bad_var.xml")
    xml_write = VariableIO(badvar_filename, formatter=VariableXmlStandardFormatter())
    xml_write.write(vars, ignore=["does_not_exist"])  # Check with non-existent var in ignore list

    tree = etree.parse(badvar_filename)
    assert float(tree.xpath("should_be_ignored/pointless")[0].text.strip()) == 0.0
    assert float(tree.xpath("should_also_be_ignored")[0].text.strip()) == -10.0

    # Check partial reading with 'ignore'
    xml_read = VariableIO(badvar_filename, formatter=VariableXmlStandardFormatter())
    new_vars = xml_read.read(ignore=["should_be_ignored:pointless", "should_also_be_ignored"])
    _check_basic_vars(new_vars)

    # Check partial reading with 'only'
    ok_vars = [
        "geometry:total_surface",
        "geometry:wing:span",
        "geometry:wing:aspect_ratio",
        "geometry:fuselage:length",
        "constants",
        "constants:k1",
        "constants:k2",
        "constants:k3",
        "constants:k4",
        "constants:k5",
        "constants:k8",
    ]
    new_vars2 = xml_read.read(only=ok_vars)
    _check_basic_vars(new_vars2)

    # Check partial writing with 'ignore'
    varok_filename = pth.join(result_folder, "with_bad_var.xml")
    xml_write = VariableIO(varok_filename, formatter=VariableXmlStandardFormatter())
    xml_write.write(vars, ignore=["should_be_ignored:pointless", "should_also_be_ignored"])

    xml_read = VariableIO(varok_filename, formatter=VariableXmlStandardFormatter())
    new_vars = xml_read.read()
    _check_basic_vars(new_vars)

    # Check partial writing with 'only'
    varok2_filename = pth.join(result_folder, "with_bad_var.xml")
    xml_write = VariableIO(varok2_filename, formatter=VariableXmlStandardFormatter())
    xml_write.write(vars, only=ok_vars)

    xml_read = VariableIO(varok2_filename, formatter=VariableXmlStandardFormatter())
    new_vars = xml_read.read()
    _check_basic_vars(new_vars)
