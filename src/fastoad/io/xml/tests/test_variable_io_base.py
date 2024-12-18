"""
Tests custom XML serializer for OpenMDAO variables
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
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

import shutil
from pathlib import Path

import pytest
from pytest import approx

from fastoad.openmdao.variables import VariableList

from .. import VariableXmlBaseFormatter
from ..translator import VarXpathTranslator
from ...variable_io import VariableIO

DATA_FOLDER_PATH = Path(__file__).parent / "data"
RESULTS_FOLDER_PATH = Path(__file__).parent / "results" / Path(__file__).stem


@pytest.fixture(scope="module")
def cleanup():
    shutil.rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


def _check_basic_vars(outputs: VariableList):
    """Checks that provided IndepVarComp instance matches content of data/custom.xml file"""

    assert len(outputs) == 5

    # Using pytest.approx for numerical reason, but also because it works even if sequence types
    # are different (lists, tuples, numpy arrays)
    assert outputs["geometry:total_surface"].value == approx([780.3])
    assert outputs["geometry:total_surface"].units == "m**2"

    assert outputs["geometry:wing:span"].value == approx([42])
    assert outputs["geometry:wing:span"].units == "m"

    assert outputs["geometry:wing:aspect_ratio"].value == approx([9.8])
    assert outputs["geometry:wing:aspect_ratio"].units is None

    assert outputs["geometry:wing:chord"].value == approx([5.0, 3.5, 2.0])
    assert outputs["geometry:wing:chord"].units == "m"
    assert outputs["geometry:wing:chord"].description == "test with multiple values"

    assert outputs["geometry:fuselage:length"].value == approx([40.0])
    assert outputs["geometry:fuselage:length"].units == "m"


def test_custom_xml_read_and_write_from_ivc(cleanup):
    """
    Tests the creation of an XML file from an IndepVarComp instance
    """
    result_folder = RESULTS_FOLDER_PATH / "custom_xml"

    var_names = [
        "geometry:total_surface",
        "geometry:wing:span",
        "geometry:wing:chord",
        "geometry:wing:aspect_ratio",
        "geometry:fuselage:length",
    ]

    xpaths = ["total_area", "wing/span", "wing/chord", "wing/aspect_ratio", "fuselage_length"]

    # test read ---------------------------------------------------------------

    file_path = DATA_FOLDER_PATH / "custom.xml"

    translator = VarXpathTranslator(variable_names=var_names, xpaths=xpaths)
    xml_read = VariableIO(file_path, formatter=VariableXmlBaseFormatter(translator))
    var_list = xml_read.read()
    _check_basic_vars(var_list)

    # test with a non-exhaustive translation table (missing variable name in the translator)
    # we expect that the variable is not included in the ivc
    file_path = DATA_FOLDER_PATH / "custom_additional_var.xml"
    xml_read = VariableIO(file_path, formatter=VariableXmlBaseFormatter(translator))
    var_list = xml_read.read()
    _check_basic_vars(var_list)

    # test with setting a translation with an additional var not present in the xml
    file_path = DATA_FOLDER_PATH / "custom.xml"
    xml_read = VariableIO(
        file_path,
        formatter=VariableXmlBaseFormatter(
            VarXpathTranslator(
                variable_names=var_names + ["additional_var"], xpaths=xpaths + ["bad:xpath"]
            )
        ),
    )
    var_list = xml_read.read()
    _check_basic_vars(var_list)

    # Check using text file object --------------------
    with open(file_path) as text_file_io:
        var_list_2 = VariableIO(text_file_io, formatter=VariableXmlBaseFormatter(translator)).read()
    assert var_list_2 == var_list

    # Check using binary file object --------------------
    with open(file_path, "rb") as binary_file_io:
        var_list_3 = VariableIO(
            binary_file_io, formatter=VariableXmlBaseFormatter(translator)
        ).read()
    assert var_list_3 == var_list

    # test write --------------------------------------------------------------
    new_filename = result_folder / "custom.xml"
    translator = VarXpathTranslator(variable_names=var_names, xpaths=xpaths)
    xml_write = VariableIO(new_filename, formatter=VariableXmlBaseFormatter(translator))
    xml_write.write(var_list)

    # check written data
    assert new_filename.is_file()
    translator.set(var_names, xpaths)
    xml_check = VariableIO(new_filename, formatter=VariableXmlBaseFormatter(translator))
    new_ivc = xml_check.read()
    _check_basic_vars(new_ivc)


def test_custom_xml_read_and_write_with_translation_table(cleanup):
    """
    Tests the creation of an XML file with a translation table
    """
    result_folder = RESULTS_FOLDER_PATH / "custom_xml_with_translation_table"

    # test read ---------------------------------------------------------------

    # test after setting translation table
    filename = DATA_FOLDER_PATH / "custom.xml"
    translator = VarXpathTranslator(source=DATA_FOLDER_PATH / "custom_translation.txt")
    xml_read = VariableIO(filename, formatter=VariableXmlBaseFormatter(translator))
    vars = xml_read.read()
    _check_basic_vars(vars)

    new_filename = result_folder / "custom.xml"
    xml_write = VariableIO(new_filename, formatter=VariableXmlBaseFormatter(translator))
    xml_write.write(vars)


def test_custom_xml_read_and_write_with_only_or_ignore(cleanup):
    """
    Tests the creation of an XML file with only and ignore options
    """

    var_names = [
        "geometry:total_surface",
        "geometry:wing:span",
        "geometry:wing:aspect_ratio",
        "geometry:fuselage:length",
    ]

    xpaths = ["total_area", "wing/span", "wing/aspect_ratio", "fuselage_length"]

    # test read ---------------------------------------------------------------
    filename = DATA_FOLDER_PATH / "custom.xml"

    translator = VarXpathTranslator(variable_names=var_names, xpaths=xpaths)
    xml_read = VariableIO(filename, formatter=VariableXmlBaseFormatter(translator))

    # test with "only"
    outputs = xml_read.read(only=["geometry:wing:span"])
    assert len(outputs) == 1
    assert outputs[0].name == "geometry:wing:span"
    assert outputs[0].value == approx([42])
    assert outputs[0].units == "m"

    # test with "ignore"
    outputs = xml_read.read(
        ignore=["geometry:total_surface", "geometry:wing:aspect_ratio", "geometry:fuselage:length"]
    )
    assert len(outputs) == 1
    assert outputs[0].name == "geometry:wing:span"
    assert outputs[0].value == approx([42])
    assert outputs[0].units == "m"

    # test with patterns in "only"
    outputs = xml_read.read(only=["*:wing:*"])
    assert len(outputs) == 2
    assert outputs[0].name == "geometry:wing:span"
    assert outputs[0].value == approx([42])
    assert outputs[0].units == "m"
    assert outputs[1].name == "geometry:wing:aspect_ratio"
    assert outputs[1].value == approx([9.8])
    assert outputs[1].units is None

    # test with patterns in "ignore"
    outputs = xml_read.read(ignore=["geometry:*u*", "geometry:wing:aspect_ratio"])
    assert len(outputs) == 1
    assert outputs[0].name == "geometry:wing:span"
    assert outputs[0].value == approx([42])
    assert outputs[0].units == "m"
