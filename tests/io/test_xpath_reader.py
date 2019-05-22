#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path as pth

import pytest

from fastoad.io.xml import XPathReader

model: XPathReader = None


@pytest.fixture(scope="module")
def input_xml():
    return XPathReader(pth.join(pth.dirname(__file__), "data", "foobar.xml"))


def test_has_element(input_xml):
    assert input_xml.has_element("/root")
    assert input_xml.has_element("/root/foo")
    assert input_xml.has_element("/root/foo/bar")
    assert input_xml.has_element("/root/bar")
    assert input_xml.has_element("/toto") is False
    assert input_xml.has_element("/root/foot") is False
    assert input_xml.has_element("/root/foo/bart") is False


def test_get_text(input_xml):
    assert input_xml.get_text("/root") == ""
    got_key_error = False
    try:
        _ = input_xml.get_text("/root/foot")
    except KeyError:
        got_key_error = True
    assert got_key_error

    assert input_xml.get_text("/root/bar") == "another non-numeric value"
    assert input_xml.get_text("/root/foo") == "4.e-2"
    assert input_xml.get_text("/root/foo/bar") == "42"


def test_get_float(input_xml):
    assert input_xml.get_float("/root") is None
    got_key_error = False
    try:
        _ = input_xml.get_float("/root/foot")
    except KeyError:
        got_key_error = True
    assert got_key_error

    assert input_xml.get_float("/root/bar") is None
    assert input_xml.get_float("/root/foo") == 4.e-2
    assert input_xml.get_float("/root/foo/bar") == 42.


def test_get_unit(input_xml):
    assert input_xml.get_unit("/root") is None
    got_key_error = False
    try:
        _ = input_xml.get_unit("/root/foot")
    except KeyError:
        got_key_error = True
    assert got_key_error

    assert input_xml.get_unit("/root/bar") is None
    assert input_xml.get_unit("/root/foo") == "kg.K/Hz"
    assert input_xml.get_unit("/root/foo/bar") == "attoparsec"


def test_get_values_and_units(input_xml):
    assert len(input_xml.get_values_and_units("/root/foot")) == 0
    assert input_xml.get_values_and_units("/root") == [("", None)]

    assert input_xml.get_values_and_units("/root/bar") == [("another non-numeric value", None)]
    assert input_xml.get_values_and_units("/root/foo") == [(4.e-2, "kg.K/Hz"), ('', None), ('', None), ('', None)]
    assert input_xml.get_values_and_units("/root/foo/bar") == [(42, "attoparsec")
        , (70, None)
        , ("non-numeric value", None)]
