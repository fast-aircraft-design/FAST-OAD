"""
Test module for translator.py
"""

from pathlib import Path

import pytest

from ..exceptions import (
    FastXpathTranslatorDuplicates,
    FastXpathTranslatorInconsistentLists,
    FastXpathTranslatorVariableError,
    FastXpathTranslatorXPathError,
)
from ..translator import VarXpathTranslator

DATA_FOLDER_PATH = Path(__file__).parent / "data"


def test_translator_with_set():
    """Tests VarXpathTranslator using set() for providing translation data"""

    translator = VarXpathTranslator()
    indices = range(10)
    var_list = ["var%i" % i for i in indices]
    xpath_list = ["xpath%i" % i for i in indices]

    # test with lists of different lengths -> error
    var_list2 = ["var0"] + var_list
    with pytest.raises(FastXpathTranslatorInconsistentLists):
        translator.set(var_list2, xpath_list)

    # test with duplicate var names -> error
    duplicate_vars = ["var1", "var3", "var3"]
    other_xpaths = ["xpath42", "xpath404", "xpath0"]
    var_list3 = var_list + duplicate_vars
    xpath_list3 = xpath_list + other_xpaths
    with pytest.raises(FastXpathTranslatorDuplicates) as exc_info:
        translator.set(var_list3, xpath_list3)
    assert exc_info.value.args[1] == set(duplicate_vars)

    # test with duplicate XPaths -> error
    other_vars = ["var42", "var404"]
    duplicate_xpaths = ["xpath5", "xpath2"]
    var_list4 = var_list + other_vars
    xpath_list4 = xpath_list + duplicate_xpaths
    with pytest.raises(FastXpathTranslatorDuplicates) as exc_info:
        translator.set(var_list4, xpath_list4)
    assert exc_info.value.args[1] == set(duplicate_xpaths)

    # Filling correct lists
    translator.set(var_list, xpath_list)

    assert translator.variable_names == var_list
    assert translator.xpaths == xpath_list

    for i in indices:
        assert translator.get_xpath("var%i" % i) == "xpath%i" % i
        assert translator.get_variable_name("xpath%i" % i) == "var%i" % i

    with pytest.raises(FastXpathTranslatorVariableError) as exc_info:
        _ = translator.get_xpath("unknown_var")
    assert exc_info is not None

    with pytest.raises(FastXpathTranslatorXPathError) as exc_info:
        _ = translator.get_variable_name("unknown_path")
    assert exc_info is not None


def test_translator_with_read():
    """Tests VarXpathTranslator using read() for providing translation data"""

    data_file = DATA_FOLDER_PATH / "custom_translation.txt"
    translator = VarXpathTranslator()
    translator.read_translation_table(data_file)

    var_list = [
        "geometry:total_surface",
        "geometry:wing:span",
        "geometry:wing:chord",
        "geometry:wing:aspect_ratio",
        "geometry:fuselage:length",
    ]
    xpath_list = ["total_area", "wing/span", "wing/chord", "wing/aspect_ratio", "fuselage_length"]

    assert translator.variable_names == var_list
    assert translator.xpaths == xpath_list

    for var_name, xpath in zip(var_list, xpath_list):
        assert translator.get_variable_name(xpath) == var_name
        assert translator.get_xpath(var_name) == xpath
