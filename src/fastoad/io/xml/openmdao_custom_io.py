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

import os
import os.path as pth
from collections import namedtuple
from typing import Sequence, List, IO, Union

import numpy as np
from lxml import etree
from lxml.etree import _Element
from openmdao.core.indepvarcomp import IndepVarComp
from openmdao.vectors.vector import Vector

from fastoad.io.serialize import AbstractOpenMDAOVariableIO, SystemSubclass
from fastoad.io.xml.translator import VarXpathTranslator
from .constants import UNIT_ATTRIBUTE, ROOT_TAG
from .xpath_reader import XPathReader

OutputVariable = namedtuple('_OutputVariable', ['name', 'value', 'units'])
""" Simple structure for standard OpenMDAO variable """


class OpenMdaoCustomXmlIO(AbstractOpenMDAOVariableIO):
    """
    Customizable serializer for OpenMDAO variables

    Using self.set_translation_table, user can tell how OpenMDAO variable names should be converted
    from/to XPath.
    """

    def __init__(self, *args, **kwargs):
        super(OpenMdaoCustomXmlIO, self).__init__(*args, **kwargs)

        self.use_promoted_names = True
        """If True, promoted names will be used instead of "real" ones."""

        self._translator = VarXpathTranslator()

        self._xml_unit_attribute = UNIT_ATTRIBUTE

    def set_translation_table(self, var_names: Sequence[str], xpaths: Sequence[str]):
        """
        Sets how OpenMDAO variable are matched to XML Path.
        Provided list must have the same length.

        :param var_names:
        :param xpaths:
        :return:
        """
        if len(var_names) != len(xpaths):
            raise IndexError('lists var_names and xpaths should have same length (%i and %i)' %
                             (len(var_names), len(xpaths)))
        self._translator.set(var_names, xpaths)

    def read_translation_table(self, source: Union[str, IO]):
        """
        Reads a file that sets how OpenMDAO variable are matched to XML Path.
        Provided file should have 2 comma-separated columns:
         - first one with OpenMDAO names
         - second one with their matching XPath

        :param source:
        :return:
        """

        arr = np.genfromtxt(source, delimiter=',')
        self._translator.set(arr[:, 0], arr[:, 1])

    def read(self, only: Sequence[str] = None, ignore: Sequence[str] = None) -> IndepVarComp:
        outputs = self.read_values()

        ivc = IndepVarComp()
        for output in outputs:
            ivc.add_output(output.name, output.value, units=output.units)

        return ivc

    def read_values(self, only: Sequence[str] = None,
                    ignore: Sequence[str] = None) -> List[OutputVariable]:
        reader = XPathReader(self._data_source)
        reader.unit_attribute_name = self._xml_unit_attribute

        root_tag = reader.tree.getroot().tag

        outputs = []

        for var_name, xpath in zip(self._translator.variable_names, self._translator.xpaths):
            if (only is None or var_name in only) and not (
                    ignore is not None and var_name in ignore):
                if not xpath.startswith('/'):
                    xpath = '/' + root_tag + '/' + xpath

                values, units = reader.get_values_and_units(xpath)
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
        """
        root = etree.Element(ROOT_TAG)
        for output in outputs:
            print(output.name)

            if not (only is None or output.name in only):
                continue
            if ignore is not None and output.name in ignore:
                continue
            if output.name not in self._translator.variable_names:
                continue

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
        if xpath.startswith('/'):
            xpath = xpath[1:]
        path_components = xpath.split('/')
        element = root
        children = []
        # Create XML path if needed
        for path_component in path_components:
            children = element.xpath(path_component)
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
