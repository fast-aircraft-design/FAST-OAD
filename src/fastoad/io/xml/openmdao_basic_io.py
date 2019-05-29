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
from collections import namedtuple
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

import numpy as np
from lxml import etree
# pylint: disable=protected-access  # Useful for type hinting
from lxml.etree import _Element
from openmdao.core.indepvarcomp import IndepVarComp
from openmdao.vectors.vector import Vector

from fastoad.io.serialize import AbstractOpenMDAOVariableIO, SystemSubclass
from fastoad.io.xml.constants import UNIT_ATTRIBUTE, ROOT_TAG

PATH_SEPARATOR = ':'

_OutputVariable = namedtuple('_OutputVariable', ['name', 'value', 'units'])
""" Simple structure for standard OpenMDAO variable """


class OpenMdaoXmlIO(AbstractOpenMDAOVariableIO):
    """
    Basic serializer for OpenMDAO variables

    Assuming self.path_separator is defined as ":", OpenMDAO variables named like "foo:bar" are
    read and written in XML at XPath "/aircraft/foo/bar".
    """

    def __init__(self, *args, **kwargs):
        super(OpenMdaoXmlIO, self).__init__(*args, **kwargs)

        self.path_separator = PATH_SEPARATOR
        """ The separator that will be used in OpenMDAO variable names to match XML path """

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
                    ivc.add_output(name=self.path_separator.join(current_path[1:]), val=value,
                                   units=units)
            elif action == 'end':
                current_path.pop(-1)

        ivc.setup()
        return ivc

    def write(self, system: SystemSubclass):

        outputs = self.__get_outputs(system)
        root = etree.Element(ROOT_TAG)

        for output in outputs:
            path_components = output.name.split(self.path_separator)
            element = root

            # Create path if needed
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
            if children:
                raise ValueError("Variable %s has already be processed")

            # Set value and units
            if output.units:
                element.attrib[UNIT_ATTRIBUTE] = output.units

            if not isinstance(output.value, (np.ndarray, Vector, list)):
                # Here, it should be a float
                element.text = str(output.value)
            else:
                element.text = str(output.value[0])

                # in that case, it may have several values
                if len(output.value) > 1:
                    # several values : create additional elements
                    for value in output.value[1:]:
                        element = etree.Element(path_components[-1])
                        parent.append(element)
                        element.text = str(value)
                        if output.units:
                            element.attrib[UNIT_ATTRIBUTE] = output.units

            # Write
            tree = etree.ElementTree(root)
            tree.write(self._data_source, pretty_print=True)

    @staticmethod
    def __get_outputs(system: SystemSubclass) -> List[_OutputVariable]:
        """ returns the list of outputs from provided system """

        outputs: List[_OutputVariable] = []
        if isinstance(system, IndepVarComp):
            # Outputs are accessible using private member
            # pylint: disable=protected-access
            for (name, value, attributes) in system._indep_external:
                outputs.append(_OutputVariable(name, value, attributes['units']))
        else:
            # Using .list_outputs(), that requires the model to have run
            for (name, attributes) in system.list_outputs():
                outputs.append(
                    _OutputVariable(name, attributes['value'], attributes.get('units', None)))
        return outputs
