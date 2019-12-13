"""
Defines how OpenMDAO variables are serialized to XML using a conversion table
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
import json
import logging
import os
import os.path as pth
import re
from typing import Sequence, List, Dict

import numpy as np
from lxml import etree
from lxml.etree import XPathEvalError
from lxml.etree import _Element  # pylint: disable=protected-access  # Useful for type hinting
from openmdao.vectors.vector import Vector

from fastoad.exceptions import XPathError
from fastoad.io.serialize import AbstractOMFileIO
from fastoad.io.xml.exceptions import FastMissingTranslatorError, FastXPathEvalError
from fastoad.io.xml.translator import VarXpathTranslator
from fastoad.utils.strings import get_float_list_from_string
from .constants import DEFAULT_UNIT_ATTRIBUTE, ROOT_TAG
from ...openmdao.variables import Variable

# Logger for this module
_LOGGER = logging.getLogger(__name__)


class OMCustomXmlIO(AbstractOMFileIO):
    """
    Customizable serializer for OpenMDAO variables

    user must provide, using :meth:`set_translator`, a VarXpathTranslator instance that tells how
    OpenMDAO variable names should be converted from/to XPath.

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
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._translator = None
        self.xml_unit_attribute = DEFAULT_UNIT_ATTRIBUTE
        self.unit_translation = {'²': '**2',
                                 '³': '**3',
                                 '°': 'deg',
                                 '°C': 'degC',
                                 'kt': 'kn',
                                 '\bin\b': 'inch',
                                 }
        """
        Used for converting read units in units recognized by OpenMDAO
        Dict keys can use regular expressions.
        """

    def set_translator(self, translator: VarXpathTranslator):
        """
        Sets the VarXpathTranslator() instance that rules how OpenMDAO variable are matched to
        XML Path.

        :param translator:
        """
        self._translator = translator

    def read_variables(self) -> List[Variable]:

        if self._translator is None:
            raise FastMissingTranslatorError('Missing translator instance')

        context = etree.iterparse(self._data_source, events=("start", "end"))

        # Intermediate storing as a dict for easy access according to name when appending new values
        variables: Dict[str, Variable] = {}

        current_path = []

        elem: _Element
        for action, elem in context:
            if action == 'start':
                current_path.append(elem.tag)
                units = elem.attrib.get(self.xml_unit_attribute, None)
                if units:
                    # Ensures compatibility with OpenMDAO units
                    for legacy_chars, om_chars in self.unit_translation.items():
                        units = re.sub(legacy_chars, om_chars, units)
                        units = units.replace(legacy_chars, om_chars)
                value = None
                if elem.text:
                    value = get_float_list_from_string(elem.text)

                if value is not None:
                    try:
                        # FIXME: maybe a bit silly to rebuild the XPath here...
                        xpath = '/'.join(current_path[1:])
                        name = self._translator.get_variable_name(xpath)
                    except XPathError as err:
                        _LOGGER.warning('The xpath %s does not have any variable '
                                        'affected in the translator.', err.xpath)
                        continue

                    if name not in variables:
                        # Add Variable
                        variables[name] = Variable(name, value, units=units)
                    else:
                        # Variable already exists: append values (here the dict is useful)
                        variables[name].value.extend(value)
            else:  # action == 'end':
                current_path.pop(-1)

        return list(variables.values())

    def write_variables(self, variables: Sequence[Variable]):

        if self._translator is None:
            raise FastMissingTranslatorError('Missing translator instance')

        root = etree.Element(ROOT_TAG)

        for variable in variables:

            xpath = self._translator.get_xpath(variable.name)
            element = self._create_xpath(root, xpath)

            # Set value and units
            if variable.units:
                element.attrib[self.xml_unit_attribute] = variable.units

            # Filling value for already created element
            element.text = str(variable.value)
            if not isinstance(variable.value, (np.ndarray, Vector, list)):
                # Here, it should be a float
                element.text = str(variable.value)
            elif len(np.squeeze(variable.value).shape) == 0:
                element.text = str(np.squeeze(variable.value).item())
            else:
                element.text = json.dumps(np.asarray(variable.value).tolist())
            if variable.desc:
                element.append(etree.Comment(variable.desc))
        # Write
        tree = etree.ElementTree(root)
        dirname = pth.dirname(self._data_source)
        if not pth.exists(dirname):
            os.makedirs(dirname)
        tree.write(self._data_source, pretty_print=True)

    @staticmethod
    def _create_xpath(root: _Element, xpath: str) -> _Element:
        """
        Creates required XML Path from provided root element

        :param root:
        :param xpath:
        :return: created element
        """
        if xpath.startswith('/'):
            xpath = xpath[1:]  # needed to avoid empty string at first place after split
        path_components = xpath.split('/')
        element = root
        children = []
        # Create XML path if needed
        for path_component in path_components:
            try:
                children = element.xpath(path_component)
            except XPathEvalError:
                raise FastXPathEvalError('Could not resolve XPath "%s"' % path_component)
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
