"""
Test module for variable_io_legacy.py
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

import pytest
from numpy.testing import assert_allclose

from .. import VariableLegacy1XmlFormatter
from ... import VariableIO

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(
    pth.dirname(__file__), "results", pth.splitext(pth.basename(__file__))[0]
)


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


def test_legacy1(cleanup):
    """ Tests class OMLegacy1XmlIO """
    result_folder = pth.join(RESULTS_FOLDER_PATH, "legacy1_xml")

    # test read ---------------------------------------------------------------
    filename = pth.join(DATA_FOLDER_PATH, "CeRAS01_baseline.xml")

    xml_read = VariableIO(filename, formatter=VariableLegacy1XmlFormatter())
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

    # test write ---------------------------------------------------------------
    new_filename = pth.join(result_folder, "CeRAS01_baseline.xml")
    xml_write = VariableIO(new_filename, formatter=VariableLegacy1XmlFormatter())
    xml_write.write(var_list)

    # check by reading without conversion table
    # -> this will give the actual number of entries in the file
    xml_check = VariableIO(new_filename)
    check_vars = xml_check.read()
    assert len(check_vars) == entry_count
