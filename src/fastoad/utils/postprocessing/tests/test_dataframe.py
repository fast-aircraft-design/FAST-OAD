"""
Tests for FAST-OAD dataframe
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

import pandas as pd
from pandas.util.testing import assert_frame_equal

from fastoad.io.xml import OMXmlIO
from fastoad.utils.postprocessing.dataframe import FASTOADDataFrame

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), 'data')


def test_xml_to_df():
    """
    Basic tests for testing the conversion of xml to dataframe.
    """
    col_names = ['Name', 'Value', 'Unit', 'Description']
    ref_df = pd.DataFrame()

    ref_df = ref_df.append([{
        'Name': 'data:geometry:cabin:seats:economical:width',
        'Value': 0.46,
        'Unit': 'm',
        'Description': 'width of economical class seats'
    }
    ])[col_names]

    ref_df = ref_df.append([{
        'Name': 'data:geometry:cabin:seats:economical:length',
        'Value': 0.86,
        'Unit': 'm',
        'Description': 'length of economical class seats'
    }
    ])[col_names]

    ref_df = ref_df.append([{
        'Name': 'data:geometry:cabin:aisle_width',
        'Value': 0.48,
        'Unit': 'm',
        'Description': 'width of aisles'
    }
    ])[col_names]

    ref_df = ref_df.append([{
        'Name': 'data:geometry:propulsion:engine:count',
        'Value': 2.0,
        'Unit': None,
        'Description': 'number of engines'
    }
    ])[col_names]

    filename = pth.join(DATA_FOLDER_PATH, 'light_data.xml')

    xml = OMXmlIO(filename)

    resulting_df = FASTOADDataFrame.xml_to_df(xml)

    assert_frame_equal(ref_df, resulting_df)





