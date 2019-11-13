"""
Test module for openmdao_legacy_io.py
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

import pytest

from fastoad.io.xml import OMXmlIO
from fastoad.io.xml.openmdao_legacy_io import OMLegacy1XmlIO, CONVERSION_FILE_1

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), 'data')
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__),
                               'results', pth.splitext(pth.basename(__file__))[0])


@pytest.fixture(scope='module')
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)


def test_legacy1(cleanup):
    """ Tests class OMLegacy1XmlIO """
    result_folder = pth.join(RESULTS_FOLDER_PATH, 'legacy1_xml')

    # test read ---------------------------------------------------------------
    filename = pth.join(DATA_FOLDER_PATH, 'CeRAS01_baseline.xml')
    xml_read = OMLegacy1XmlIO(filename)
    ivc = xml_read.read()
    inputs = ivc._indep_external  # pylint: disable=protected-access

    # check that here are as many inputs as lines in conversion file
    with open(CONVERSION_FILE_1) as conversion_file:
        conversion_count = len(conversion_file.readlines())

    assert len(inputs) == conversion_count

    for inp in inputs:
        assert inp[1] is not None  # check that a value has been read

    # test write ---------------------------------------------------------------
    new_filename = pth.join(result_folder, 'CeRAS01_baseline.xml')
    xml_write = OMLegacy1XmlIO(new_filename)
    xml_write.write(ivc)

    # check by reading without conversion table
    # -> this will give the actual number of entries in the file
    xml_check = OMXmlIO(new_filename)
    check_ivc = xml_check.read()
    assert len(check_ivc._indep_external) == conversion_count  # pylint: disable=protected-access
