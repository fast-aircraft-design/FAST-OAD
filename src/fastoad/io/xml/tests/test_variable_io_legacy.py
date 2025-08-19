"""
Test module for variable_io_legacy.py
"""

import shutil
from pathlib import Path

import pytest
from numpy.testing import assert_allclose

from .. import VariableLegacy1XmlFormatter
from ... import VariableIO

DATA_FOLDER_PATH = Path(__file__).parent / "data"
RESULTS_FOLDER_PATH = Path(__file__).parent / "results" / Path(__file__).stem


@pytest.fixture(scope="module")
def cleanup():
    shutil.rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


def test_legacy1(cleanup):
    """Tests class OMLegacy1XmlIO"""
    result_folder = RESULTS_FOLDER_PATH / "legacy1_xml"

    # test read ---------------------------------------------------------------
    file_path = DATA_FOLDER_PATH / "CeRAS01_baseline.xml"

    xml_read = VariableIO(file_path, formatter=VariableLegacy1XmlFormatter())
    var_list = xml_read.read()

    entry_count = len(var_list)
    # Entry count may vary according to changes in translation table, but
    # we check that enough values are actually read.
    assert entry_count > 400

    # Check some random fields
    assert_allclose(var_list["data:geometry:wing:MAC:at25percent:x"].value, 16.457)
    assert var_list["data:geometry:wing:MAC:at25percent:x"].units == "m"
    assert_allclose(var_list["data:TLAR:NPAX"].value, 150)
    assert var_list["data:TLAR:NPAX"].units is None
    assert_allclose(var_list["data:geometry:wing:wetted_area"].value, 200.607)
    assert var_list["data:geometry:wing:wetted_area"].units == "m**2"

    # Check using text file object --------------------
    with open(file_path, encoding="utf-8") as text_file_io:
        var_list_2 = VariableIO(text_file_io, formatter=VariableLegacy1XmlFormatter()).read()
    assert var_list_2 == var_list

    # Check using binary file object --------------------
    with open(file_path, "rb") as binary_file_io:
        var_list_3 = VariableIO(binary_file_io, formatter=VariableLegacy1XmlFormatter()).read()
    assert var_list_3 == var_list

    # test write ---------------------------------------------------------------
    new_filename = result_folder / "CeRAS01_baseline.xml"
    xml_write = VariableIO(new_filename, formatter=VariableLegacy1XmlFormatter())
    xml_write.write(var_list)

    # check by reading without conversion table
    # -> this will give the actual number of entries in the file
    xml_check = VariableIO(new_filename)
    check_vars = xml_check.read()
    assert len(check_vars) == entry_count
