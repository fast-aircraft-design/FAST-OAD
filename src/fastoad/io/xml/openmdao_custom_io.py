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
from collections import namedtuple
from typing import Sequence, List

import numpy as np
from lxml import etree
from lxml.etree import XPathEvalError
from lxml.etree import _Element  # pylint: disable=protected-access  # Useful for type hinting
from openmdao.core.indepvarcomp import IndepVarComp
from openmdao.vectors.vector import Vector

from fastoad.io.serialize import AbstractOpenMDAOVariableIO, SystemSubclass
from fastoad.io.xml.translator import VarXpathTranslator
from .constants import UNIT_ATTRIBUTE, ROOT_TAG
from .xpath_reader import XPathReader

# Logger for this module
_LOGGER = logging.getLogger(__name__)

OutputVariable = namedtuple('_OutputVariable', ['name', 'value', 'units'])
""" Simple structure for standard OpenMDAO variable """


class OpenMdaoCustomXmlIO(AbstractOpenMDAOVariableIO):
    """
    Customizable serializer for OpenMDAO variables

    user must provide, using :meth:`set_translator`, a VarXpathTranslator instance that tells how
    OpenMDAO variable names should be converted from/to XPath.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.use_promoted_names = True
        """If True, promoted names will be used instead of "real" ones."""

        self._translator = None
        self._xml_unit_attribute = UNIT_ATTRIBUTE

    def set_translator(self, translator: VarXpathTranslator):
        """
        Sets the VarXpathTranslator() instance that rules how OpenMDAO variable are matched to
        XML Path.

        :param translator:
        """
        self._translator = translator

    def read(self, only: Sequence[str] = None, ignore: Sequence[str] = None) -> IndepVarComp:
        outputs = self._read_values(only=only, ignore=ignore)

        ivc = IndepVarComp()
        for output in outputs:
            ivc.add_output(output.name, output.value, units=output.units)

        return ivc

    def _read_values(self, only: Sequence[str] = None,
                     ignore: Sequence[str] = None) -> List[OutputVariable]:
        """
        Reads output variables from provided system.

        :param only: List of OpenMDAO variable names that should be read. Other names will be
                     ignored. If None, all variables will be read.
        :param ignore: List of OpenMDAO variable names that should be ignored when reading.
        :return: a list of OutputVariable instance
        :raise ValueError: if translation table is not set or does not contain a required variable
        """

        if self._translator is None:
            raise ValueError('Missing translator instance')

        reader = XPathReader(self._data_source)
        reader.unit_attribute_name = self._xml_unit_attribute

        root_tag = reader.tree.getroot().tag

        outputs = []

        if only is not None:
            var_names = only
        else:
            var_names = self._translator.variable_names

        if ignore is not None:
            var_names = [name for name in var_names if name not in ignore]

        for var_name in var_names:
            xpath = self._translator.get_xpath(var_name)
            if not xpath.startswith('/'):
                xpath = '/' + root_tag + '/' + xpath

            values, units = reader.get_values_and_units(xpath)
            if values is None:
                raise ValueError('XPath "%" not found' % xpath)

            outputs.append(OutputVariable(var_name, values, units))

        return outputs

    def write(self, system: SystemSubclass, only: Sequence[str] = None,
              ignore: Sequence[str] = None):
        outputs = self._get_outputs(system)
        self._write(outputs, ignore, only)

    def _write(self, outputs: Sequence[OutputVariable], only: Sequence[str] = None,
               ignore: Sequence[str] = None):
        """
        Writes outputs to defined XML

        :param outputs:
        :param only: List of OpenMDAO variable names that should be written. Other names will be
                     ignored. If None, all variables will be written.
        :param ignore: List of OpenMDAO variable names that should be ignored when writing
        :raise ValueError: if translation table is not set or does nto contain a required xpath
       """
        if self._translator is None:
            raise ValueError('Missing translator instance')

        root = etree.Element(ROOT_TAG)

        if only is None:
            used_outputs = outputs
        else:
            used_outputs = [output for output in outputs if output.name in only]

        if ignore is not None:
            used_outputs = [output for output in used_outputs if output.name not in ignore]

        for output in used_outputs:

            xpath = self._translator.get_xpath(output.name)
            element = self._create_xpath(root, xpath)

            # Set value and units
            if output.units:
                element.attrib[UNIT_ATTRIBUTE] = output.units

            # Filling value for already created element
            if not isinstance(output.value, (np.ndarray, Vector, list)):
                # Here, it should be a float
                element.text = str(output.value)
            else:
                element.text = str(output.value[0])

                # But if more than one value, create additional elements
                parent = element.getparent()
                if len(output.value) > 1:
                    for value in output.value[1:]:
                        element = etree.Element(element.tag)
                        parent.append(element)
                        element.text = str(value)
                        if output.units:
                            element.attrib[UNIT_ATTRIBUTE] = output.units
        # Write
        tree = etree.ElementTree(root)
        dirname = pth.dirname(self._data_source)
        if not pth.exists(dirname):
            os.makedirs(dirname)
        tree.write(self._data_source, pretty_print=True)

    def _get_outputs(self, system: SystemSubclass) -> List[OutputVariable]:
        """ returns the list of outputs from provided system """

        outputs: List[OutputVariable] = []
        if isinstance(system, IndepVarComp):
            # Outputs are accessible using private member
            # pylint: disable=protected-access
            for (name, value, attributes) in system._indep_external:
                outputs.append(OutputVariable(name, value, attributes['units']))
        else:
            # Using .list_outputs(), that requires the model to have run
            for (name, attributes) in system.list_outputs(prom_name=self.use_promoted_names,
                                                          units=True,
                                                          out_stream=None):
                if self.use_promoted_names:
                    name = attributes['prom_name']
                outputs.append(
                    OutputVariable(name, attributes['value'], attributes.get('units', None)))
        return outputs

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
            xpath = xpath[1:]
        path_components = xpath.split('/')
        element = root
        children = []
        # Create XML path if needed
        for path_component in path_components:
            try:
                children = element.xpath(path_component)
            except XPathEvalError:
                _LOGGER.error(
                    'Could not evaluate provided XPath %s' % input_xpath)
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
        assert not children, "XPath %s has already be processed" % xpath

        return element
