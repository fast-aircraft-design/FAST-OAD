"""
Defines how OpenMDAO variables are serialized to XML
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
from typing import List, Dict

import numpy as np
from lxml import etree
from lxml.etree import _Element  # pylint: disable=protected-access  # Useful for type hinting
from openmdao.core.indepvarcomp import IndepVarComp
from openmdao.vectors.vector import Vector

from fastoad.io.serialize import AbstractOpenMDAOVariableIO, SystemSubclass
from fastoad.io.xml.constants import UNIT_ATTRIBUTE, ROOT_TAG

_OutputVariable = namedtuple('_OutputVariable', ['name', 'value', 'units'])
""" Simple structure for standard OpenMDAO variable """


class OpenMdaoXmlIO(AbstractOpenMDAOVariableIO):
    """
    Basic serializer for OpenMDAO variables

    Assuming self.path_separator is defined as ``:``, an OpenMDAO variable named like ``foo:bar``
    with units ``m/s`` will be read and written as:

    .. code:: xml

        <aircraft>
            <foo>
                <bar units="m/s" >`42.0</bar>
            </foo>
        <aircraft>

    When writing outputs of a model, OpenMDAO component hierarchy  may be used by defining

     .. code:: python

        self.path_separator = '.'  # Not allowed for writing !
        self.use_promoted_names = False

    This way an OpenMDAO variable like ``componentA.subcomponent2.my_var`` will be written as:

    .. code:: xml

        <aircraft>
            <componentA>
                <subcomponent2>
                    <my_var units="m/s" >72.0</my_var>
                </subcomponent2>
            <componentA>
        <aircraft>
    """

    def __init__(self, *args, **kwargs):
        super(OpenMdaoXmlIO, self).__init__(*args, **kwargs)

        self.use_promoted_names = True
        """If True, promoted names will be used instead of "real" ones."""

        self.path_separator = '/'
        """
        The separator that will be used in OpenMDAO variable names to match XML path.
        Warning: The dot "." can be used when writing, but not when reading.
        """

    def read(self, only: List[str] = None, ignore: List[str] = None) -> IndepVarComp:
        # Check separator, as OpenMDAO won't accept the dot.
        if self.path_separator == '.':
            # TODO: in this case, maybe try to dispatch the inputs to each component...
            raise ValueError('Cannot use dot "." in OpenMDAO variables.')

        outputs = self._read_xml()

        # Create IndepVarComp instance
        ivc = IndepVarComp()
        for name, value, units in outputs:
            if (only is None or name in only) and not (ignore is not None and name in ignore):
                ivc.add_output(name, val=np.array(value), units=units)
        return ivc

    def write(self, system: SystemSubclass, only: List[str] = None, ignore: List[str] = None):
        outputs = self._get_outputs(system)
        root = etree.Element(ROOT_TAG)

        for output in outputs:
            if (not (only is None or output.name in only)) or (
                    ignore is not None and output.name in ignore):
                continue
            path_components = output.name.split(self.path_separator)
            element = root

            children = []
            # Create XML path if needed
            for path_component in path_components:
                parent = element

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
            assert not children, "Variable %s has already be processed" % output.name

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
                if len(output.value) > 1:
                    for value in output.value[1:]:
                        element = etree.Element(path_components[-1])
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

    def _read_xml(self) -> List[_OutputVariable]:
        """
        Reads self.data_source as a XML file

        Variable value will be a list of one or more values.
        Variable units will be a string, or None if no unit provided.

        :return: list of variables (name, value, units) from data source
        """

        context = etree.iterparse(self._data_source, events=("start", "end"))

        # Intermediate storing as a dict for easy access according to name when appending new values
        outputs: Dict[str, _OutputVariable] = {}

        current_path = []

        elem: _Element
        for action, elem in context:
            if action == 'start':
                current_path.append(elem.tag)
                units = elem.attrib.get(UNIT_ATTRIBUTE, None)
                value = None
                if elem.text:
                    value = self._get_list_from_string(elem.text)
                if value:
                    name = self.path_separator.join(current_path[1:])
                    if name not in outputs:
                        # Add variable
                        outputs[name] = _OutputVariable(name, value, units)
                    else:
                        # Variable already exists: append values (here the dict is useful)
                        outputs[name].value.extend(value)
            else:  # action == 'end':
                current_path.pop(-1)

        return list(outputs.values())

    def _get_outputs(self, system: SystemSubclass) -> List[_OutputVariable]:
        """ returns the list of outputs from provided system """

        outputs: List[_OutputVariable] = []
        if isinstance(system, IndepVarComp):
            # Outputs are accessible using private member
            # pylint: disable=protected-access
            for (name, value, attributes) in system._indep_external:
                outputs.append(_OutputVariable(name, value, attributes['units']))
        else:
            # Using .list_outputs(), that requires the model to have run
            for (name, attributes) in system.list_outputs(prom_name=self.use_promoted_names,
                                                          units=True,
                                                          out_stream=None):
                if self.use_promoted_names:
                    name = attributes['prom_name']
                outputs.append(
                    _OutputVariable(name, attributes['value'], attributes.get('units', None)))
        return outputs

    @staticmethod
    def _get_list_from_string(text: str):
        """
        Parses the provided string and returns a list if possible.

        If provided text is not numeric, None is returned.
        Otherwise, accepted text patterns are:

        .. code-block::

            '[ 1, 2., 3]'
            '[ 1 2.  3]'
            ' 1, 2., 3'
            ' 1 2.  3'
        """

        text_value = text.strip().strip('[]')
        if not text_value:
            return None

        # Deals with multiple values in same element. numpy.fromstring can parse a string,
        # but we have to test with either ' ' or ',' as separator. The longest result should be
        # the good one.
        value1 = np.fromstring(text_value, dtype=float, sep=' ').tolist()
        value2 = np.fromstring(text_value, dtype=float, sep=',').tolist()

        if not value1 and not value2:
            return None

        return value1 if len(value1) > len(value2) else value2

    def _create_openmdao_code(self) -> str:  # pragma: no cover
        """dev utility for generating code"""
        outputs = self._read_xml()

        lines = ['ivc = IndepVarComp()']
        for name, value, units in outputs:
            lines.append("ivc.add_output('%s', val=%s%s)" %
                         (name, value, ", units='%s'" % units if units else ''))

        return '\n'.join(lines)
