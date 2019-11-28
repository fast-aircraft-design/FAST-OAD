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
from fastoad.io.xml.openmdao_legacy_io import OMLegacy1XmlIO

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

    entry_count = len(inputs)
    # Entry count may vary according to changes in translation table, but
    # we check that enough values are actually read.
    assert entry_count > 400

    field_found = [False] * 3
    for inp in inputs:
        assert inp[1] is not None  # check that a value has been read

        # Check some random fields
        if inp[0] == 'geometry:wing:location':
            assert inp[1] == 16.457
            assert inp[2]['units'] == 'm'
            field_found[0] = True
        if inp[0] == 'TLAR:NPAX':
            assert inp[1] == 150
            assert inp[2]['units'] is None
            field_found[1] = True
        if inp[0] == 'geometry:wing:wet_area':
            assert inp[1] == 200.607
            assert inp[2]['units'] == 'm**2'
            field_found[2] = True

    assert all(field_found)

    # test write ---------------------------------------------------------------
    new_filename = pth.join(result_folder, 'CeRAS01_baseline.xml')
    xml_write = OMLegacy1XmlIO(new_filename)
    xml_write.write(ivc)

    # check by reading without conversion table
    # -> this will give the actual number of entries in the file
    xml_check = OMXmlIO(new_filename)
    check_ivc = xml_check.read()
    assert len(check_ivc._indep_external) == entry_count  # pylint: disable=protected-access
