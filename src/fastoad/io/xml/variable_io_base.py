"""
Defines how OpenMDAO variables are serialized to XML using a conversion table
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

import json
import logging
import re
from os import PathLike
from pathlib import Path
from typing import IO, Union, Optional

import numpy as np
from lxml import etree
from lxml.etree import (
    XPathEvalError,
    _Comment,
    _Element,
)  # pylint: disable=protected-access  # Useful for type hinting
from openmdao.vectors.vector import Vector

from fastoad._utils.files import make_parent_dir
from fastoad._utils.strings import get_float_list_from_string
from fastoad.io.formatter import IVariableIOFormatter
from fastoad.io.xml.exceptions import (
    FastXPathEvalError,
    FastXmlFormatterDuplicateVariableError,
    FastXpathTranslatorVariableError,
    FastXpathTranslatorXPathError,
)
from fastoad.io.xml.translator import VarXpathTranslator
from fastoad.openmdao.variables import VariableList
from .constants import DEFAULT_IO_ATTRIBUTE, DEFAULT_UNIT_ATTRIBUTE, ROOT_TAG

_LOGGER = logging.getLogger(__name__)  # Logger for this module


class VariableXmlBaseFormatter(IVariableIOFormatter):
    """
    Customizable formatter for variables

    User must provide at instantiation a VarXpathTranslator instance that tells how
    variable names should be converted from/to XPath.

    Note: XPath are always considered relatively to the root. Therefore, "foo/bar" should be
    provided to match following XML structure:

    .. code-block:: xml

        <root>
            <foo>
                <bar>
                    "some value"
                </bar>
            </foo>
        </root>

    :param translator: the VarXpathTranslator instance
    """

    def __init__(self, translator: VarXpathTranslator):
        self._translator = translator

        #: The XML attribute key for specifying units
        self.xml_unit_attribute = DEFAULT_UNIT_ATTRIBUTE

        #: The XML attribute key for specifying I/O status
        self.xml_io_attribute = DEFAULT_IO_ATTRIBUTE

        #: Used for converting read units in units recognized by OpenMDAO.
        #  Regular expressions can be used in dict keys.
        self.unit_translation = {
            "²": "**2",
            "³": "**3",
            "°": "deg",
            "°C": "degC",
            "kt": "kn",
            r"\bin\b": "inch",
        }

    def read_variables(self, data_source: Union[str, PathLike, IO]) -> VariableList:
        variables = VariableList()

        # If there is a comment, it will be used as description if the previous
        # element described a variable.
        previous_variable_name = None

        if isinstance(data_source, Path):
            data_source = data_source.as_posix()

        root = etree.parse(
            data_source,
            etree.XMLParser(remove_blank_text=True, remove_comments=False),
        ).getroot()

        for elem in root.iter():
            if isinstance(elem, _Comment) and previous_variable_name is not None:
                variables[previous_variable_name].description = elem.text.strip()
                previous_variable_name = None
                continue

            units = self._read_units(elem)

            value = None
            if elem.text:
                value = get_float_list_from_string(elem.text)

            previous_variable_name = None
            if value is None:
                continue

            variable_name = self._get_matching_variable_name(elem)
            if variable_name is None:
                continue

            if variable_name in variables.names():
                raise FastXmlFormatterDuplicateVariableError(
                    f"Variable {variable_name} is defined in more than one "
                    f"place in file {data_source}"
                )

            # Add Variable
            is_input = elem.attrib.get(self.xml_io_attribute, None)
            if is_input is not None:
                is_input = is_input == "True"

            variables[variable_name] = {"val": value, "units": units, "is_input": is_input}
            previous_variable_name = variable_name

        return variables

    def write_variables(self, data_source: Union[str, PathLike, IO], variables: VariableList):

        root = etree.Element(ROOT_TAG)

        for variable in variables:

            try:
                xpath = self._translator.get_xpath(variable.name)
            except FastXpathTranslatorVariableError as exc:
                _LOGGER.warning("No translation found: %s", exc)
                continue
            element = self._create_xpath(root, xpath)

            # Set value, units and io
            if variable.units:
                element.attrib[self.xml_unit_attribute] = variable.units
            if variable.is_input is not None:
                element.attrib[self.xml_io_attribute] = str(variable.is_input)

            # Filling value for already created element
            element.text = str(variable.value)
            if not isinstance(variable.value, (np.ndarray, Vector, list)):
                # Here, it should be a float
                element.text = str(variable.value)
            elif len(np.squeeze(variable.value).shape) == 0:
                element.text = str(np.squeeze(variable.value).item())
            else:
                element.text = json.dumps(np.asarray(variable.value).tolist())
            if variable.description:
                element.append(etree.Comment(variable.description))
        # Write
        tree = etree.ElementTree(root)
        if isinstance(data_source, (str, PathLike)):
            make_parent_dir(data_source)
        if isinstance(data_source, Path):
            data_source = data_source.as_posix()

        tree.write(data_source, pretty_print=True)

    def _read_units(self, elem) -> Optional[str]:
        units = elem.attrib.get(self.xml_unit_attribute, None)
        if units:
            # Ensures compatibility with OpenMDAO units
            for legacy_chars, om_chars in self.unit_translation.items():
                units = re.sub(legacy_chars, om_chars, units)
                units = units.replace(legacy_chars, om_chars)
        return units

    def _get_matching_variable_name(self, elem: _Element) -> Optional[str]:
        path_tags = [ancestor.tag for ancestor in elem.iterancestors()]
        path_tags.reverse()
        path_tags.append(elem.tag)
        xpath = "/".join(path_tags[1:])  # Do not use root tag
        try:
            variable_name = self._translator.get_variable_name(xpath)
        except FastXpathTranslatorXPathError as err:
            _LOGGER.warning(
                "The xpath %s does not have any variable affected in the translator.",
                err.xpath,
            )
            variable_name = None
        return variable_name

    @staticmethod
    def _create_xpath(root: _Element, xpath: str) -> _Element:
        """
        Creates required XML Path from provided root element

        :param root:
        :param xpath:
        :return: created element
        """
        if xpath.startswith("/"):
            xpath = xpath[1:]  # needed to avoid empty string at first place after split
        path_components = xpath.split("/")
        element = root
        children = []
        # Create XML path if needed
        for path_component in path_components:
            try:
                children = element.xpath(path_component)
            except XPathEvalError as err:
                raise FastXPathEvalError(f'Could not resolve XPath "{path_component}"') from err
            if not children:
                # Build path
                new_element = etree.Element(path_component)
                element.append(new_element)
                element = new_element
            else:
                # Use existing path
                # (Unicity of OpenMDAO variables makes that children should not have more that
                # one element)
                element = children[0]

        return element
