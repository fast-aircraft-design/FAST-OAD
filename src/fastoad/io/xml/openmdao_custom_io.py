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

import logging
import os
import os.path as pth
from typing import Sequence, List

import numpy as np
import openmdao.api as om
from lxml import etree
from lxml.etree import XPathEvalError
from lxml.etree import _Element  # pylint: disable=protected-access  # Useful for type hinting
from openmdao.vectors.vector import Vector

from fastoad.exceptions import XPathError
from fastoad.io.serialize import AbstractOMFileIO
from fastoad.io.xml.exceptions import FastMissingTranslatorError
from fastoad.io.xml.translator import VarXpathTranslator
from fastoad.openmdao.types import Variable, SystemSubclass
from .constants import UNIT_ATTRIBUTE, ROOT_TAG
from .xpath_reader import XPathReader

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

        self.use_promoted_names = True
        """If True, promoted names will be used instead of "real" ones."""

        self._translator = None
        self.xml_unit_attribute = UNIT_ATTRIBUTE

    def set_translator(self, translator: VarXpathTranslator):
        """
        Sets the VarXpathTranslator() instance that rules how OpenMDAO variable are matched to
        XML Path.

        :param translator:
        """
        self._translator = translator

    def read(self, only: Sequence[str] = None, ignore: Sequence[str] = None) -> om.IndepVarComp:

        variables = self._read_values(only=only, ignore=ignore)

        ivc = om.IndepVarComp()
        for variable in variables:
            ivc.add_output(variable.name, variable.value, units=variable.units)

        return ivc

    def _read_values(self, only: Sequence[str] = None,
                     ignore: Sequence[str] = None) -> List[Variable]:
        """
        Reads variables from provided data source file.

        :param only: List of OpenMDAO variable names that should be read. Other names will be
                     ignored. If None, all variables will be read.
        :param ignore: List of OpenMDAO variable names that should be ignored when reading.
        :return: a list of Variable instance
        :raise ValueError: if translation table is not set or does not contain a required variable
        """

        if self._translator is None:
            raise FastMissingTranslatorError('Missing translator instance')

        reader = XPathReader(self._data_source)
        reader.unit_attribute_name = self.xml_unit_attribute

        variables = []

        if only is not None:
            var_names = only
        else:
            xpaths = reader.get_all_elements_with_no_child_xpath()
            var_names = []
            for xpath in xpaths:
                try:
                    var_names.append(self._translator.get_variable_name(xpath))
                except XPathError as err:
                    _LOGGER.warning('The xpath %s does not have any variable '
                                    'affected in the translator.', err.xpath)
                    continue

        if ignore is not None:
            var_names = [name for name in var_names if name not in ignore]

        for var_name in var_names:

            xpath = self._translator.get_xpath(var_name)

            values, units = reader.get_values_and_units(xpath)

            # For compatibility with legacy files
            if units is not None:
                units = units.replace('²', '**2')
                units = units.replace('°', 'deg')
                units = units.replace('kt', 'kn')

            variables.append(Variable(var_name, values, units))

        return variables

    def write(self, ivc: om.IndepVarComp, only: Sequence[str] = None, ignore: Sequence[str] = None):

        variables = self._get_variables(ivc)
        used_variables = self._filter_variables(variables, only=only, ignore=ignore)
        self._write(used_variables)

    def _write(self, variables: Sequence[Variable]):
        """
        Writes variables to defined data source file.
        :param variables:
        :raise ValueError: if translation table is not set or does nto contain a required xpath
       """
        if self._translator is None:
            raise ValueError('Missing translator instance')

        root = etree.Element(ROOT_TAG)

        for variable in variables:

            xpath = self._translator.get_xpath(variable.name)
            element = self._create_xpath(root, xpath)

            # Set value and units
            if variable.units:
                element.attrib[UNIT_ATTRIBUTE] = variable.units

            # Filling value for already created element
            if not isinstance(variable.value, (np.ndarray, Vector, list)):
                # Here, it should be a float
                element.text = str(variable.value)
            else:
                element.text = str(variable.value[0])

                # But if more than one value, create additional elements
                parent = element.getparent()
                if len(variable.value) > 1:
                    for value in variable.value[1:]:
                        element = etree.Element(element.tag)
                        parent.append(element)
                        element.text = str(value)
                        if variable.units:
                            element.attrib[UNIT_ATTRIBUTE] = variable.units
        # Write
        tree = etree.ElementTree(root)
        dirname = pth.dirname(self._data_source)
        if not pth.exists(dirname):
            os.makedirs(dirname)
        tree.write(self._data_source, pretty_print=True)

    @staticmethod
    def _get_variables(system: SystemSubclass) -> List[Variable]:
        """ returns the list of variables from provided system """

        variables: List[Variable] = []

        # Outputs are accessible using private member
        # pylint: disable=protected-access
        for (name, value, attributes) in system._indep_external:
            variables.append(Variable(name, value, attributes['units']))

        return variables

    @staticmethod
    def _create_xpath(root: _Element, xpath: str) -> _Element:
        """
        Creates required XML Path from provided root element

        :param root:
        :param xpath:
        :return: created element
        """
        input_xpath = xpath

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
                _LOGGER.error(
                    'Could not evaluate provided XPath %s', input_xpath)
                raise
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
        # At this point, unicity of OpenMDAO variables makes that element should have been
        # created just now, meaning that 'children' list should be empty.
        assert not children, "XPath %s has already been processed" % xpath

        return element

    @staticmethod
    def _filter_variables(variables: Sequence[Variable], only: Sequence[str] = None,
                          ignore: Sequence[str] = None) -> Sequence[Variable]:
        """
        filters the variables such that the ones in arg only are kept and the ones in
        arg ignore are removed.

        :param variables:
        :param only: List of OpenMDAO variable names that should be written. Other names will be
                     ignored. If None, all variables will be written.
        :param ignore: List of OpenMDAO variable names that should be ignored when writing
        :return: filtered variables
        """
        if only is None:
            used_variables = variables
        else:
            used_variables = [variable for variable in variables if variable.name in only]

        if ignore is not None:
            used_variables = [variable for variable in used_variables
                              if variable.name not in ignore]

        return used_variables
