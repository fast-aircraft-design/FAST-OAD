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
from typing import List

from lxml import etree
# pylint: disable=protected-access  # Useful for type hinting
from lxml.etree import _Element
from openmdao.core.indepvarcomp import IndepVarComp
from openmdao.vectors.vector import Vector

from fastoad.io.serialize import AbstractOpenMDAOVariableIO, SystemSubclass
from fastoad.io.xml.constants import UNIT_ATTRIBUTE, ROOT_TAG

PATH_SEPARATOR = ':'


class OpenMdaoXmlIO(AbstractOpenMDAOVariableIO):
    """
    Basic serializer for OpenMDAO variables

    OpenMDAO variables named like "foo:bar" are read and written in XML at XPath "/aircraft/foo/bar"

    """

    def read(self) -> IndepVarComp:
        context = etree.iterparse(self._data_source, events=("start", "end"))

        ivc = IndepVarComp()
        current_path = []
        elem: _Element
        for action, elem in context:
            if action == 'start':
                current_path.append(elem.tag)
                units = elem.attrib.get(UNIT_ATTRIBUTE, None)
                try:
                    value = float(elem.text)
                except ValueError:
                    value = None
                if value is not None:
                    # FIXME : if a list of values is provided
                    # FIXME : if the path has already been encountered -> append ?
                    ivc.add_output(name=PATH_SEPARATOR.join(current_path[1:]), val=value,
                                   units=units)
            elif action == 'end':
                current_path.pop(-1)

        ivc.setup()
        return ivc

    def write(self, system: SystemSubclass):

        outputs = self.__get_outputs(system)
        root = etree.Element(ROOT_TAG)

        for output in outputs:
            path_components = output.name.split(':')
            element = root

            # Create path if needed
            for path_component in path_components:
                parent = element

                children = element.xpath(path_component)
                if not children:
                    new_element = etree.Element(path_component)
                    element.append(new_element)
                    element = new_element
                else:
                    element = children[0]

            # Set value and units
            if not children:
                # Element has just been created
                element.text = str(output.value)
                if output.units:
                    element.attrib[UNIT_ATTRIBUTE] = output.units
            else:
                # Elements with same path already existed : append
                new_element = etree.Element(path_component)
                new_element.text = output.value
                if output.units:
                    new_element.attrib[UNIT_ATTRIBUTE] = output.units
                parent.append(new_element)

        tree = etree.ElementTree(root)
        tree.write(self._data_source, pretty_print=True)

    @staticmethod
    def __get_outputs(system: SystemSubclass) -> List['OutputVariable']:
        """ returns the list of outputs from p """
        outputs: List[OutputVariable] = []
        if isinstance(system, IndepVarComp):
            # Outputs are accessible using private member
            # pylint: disable=protected-access
            for (name, value, attributes) in system._indep_external:
                outputs.append(OutputVariable(name, value, attributes['units']))
        else:
            # Using .list_outputs(), that requires the model to have run
            for (name, attributes) in system.list_outputs():
                outputs.append(OutputVariable(name, attributes['value'], attributes['units']))
        return outputs


class OutputVariable:
    def __init__(self, name: str, value: Vector, units: str):
        self.name = name
        self.value = value
        self.units = units
