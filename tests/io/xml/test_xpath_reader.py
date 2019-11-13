# -*- coding: utf-8 -*-
"""
Test module for xpath_reader.py
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

# pylint: disable=missing-docstring  # All looks self-explanatory enough
# pylint: disable=redefined-outer-name  # needed for fixtures

import os.path as pth

import pytest

from fastoad.io.xml import XPathReader

model: XPathReader = None


@pytest.fixture(scope='module')
def input_xml() -> XPathReader:
    return XPathReader(pth.join(pth.dirname(__file__), 'data', 'foobar.xml'))


def test_has_element(input_xml: XPathReader):
    assert input_xml.has_element('/root')
    assert input_xml.has_element('/root/foo')
    assert input_xml.has_element('/root/foo/bar')
    assert input_xml.has_element('/root/bar')
    assert input_xml.has_element('/toto') is False
    assert input_xml.has_element('/root/foot') is False
    assert input_xml.has_element('/root/foo/bart') is False


def test_get_text(input_xml: XPathReader):
    assert input_xml.get_text('/root') == ""
    got_key_error = False
    try:
        _ = input_xml.get_text('/root/foot')
    except KeyError:
        got_key_error = True
    assert got_key_error

    assert input_xml.get_text('/root/bar') == 'another non-numeric value'
    assert input_xml.get_text('/root/foo') == '4.e-2'
    assert input_xml.get_text('/root/foo/bar') == '42'


def test_get_float(input_xml: XPathReader):
    assert input_xml.get_float('/root') is None
    got_key_error = False
    try:
        _ = input_xml.get_float('/root/foot')
    except KeyError:
        got_key_error = True
    assert got_key_error

    assert input_xml.get_float('/root/bar') is None
    assert input_xml.get_float('/root/foo') == 4.e-2
    assert input_xml.get_float('/root/foo/bar') == 42.


def test_get_unit(input_xml: XPathReader):
    assert input_xml.get_units('/root') is None
    got_key_error = False
    try:
        _ = input_xml.get_units('/root/foot')
    except KeyError:
        got_key_error = True
    assert got_key_error

    assert input_xml.get_units('/root/bar') is None
    assert input_xml.get_units('/root/foo') == 'kg.K/Hz'
    assert input_xml.get_units('/root/foo/bar') == 'attoparsec'


def test_get_values_and_units(input_xml: XPathReader):
    assert input_xml.get_values_and_units('/root/foot') == (None, None)
    assert input_xml.get_values_and_units('/root') == ([], None)

    assert input_xml.get_values_and_units('/root/bar') == (['another non-numeric value'], None)
    assert input_xml.get_values_and_units('/root/foo') == ([4.e-2], 'kg.K/Hz')
    assert input_xml.get_values_and_units('/root/foo/bar') == ([42, 70, 'non-numeric value'],
                                                               'attoparsec')
