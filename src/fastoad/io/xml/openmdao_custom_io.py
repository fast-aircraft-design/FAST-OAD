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
from typing import Sequence

import numpy as np
from lxml import etree
from openmdao.core.indepvarcomp import IndepVarComp
from openmdao.vectors.vector import Vector

from fastoad.io.serialize import AbstractOpenMDAOVariableIO, SystemSubclass
from . import XPathReader
from .constants import UNIT_ATTRIBUTE, ROOT_TAG

_OutputVariable = namedtuple('_OutputVariable', ['name', 'value', 'units'])
""" Simple structure for standard OpenMDAO variable """


class OpenMdaoCustomXmlIO(AbstractOpenMDAOVariableIO):

    def __init__(self, *args, **kwargs):
        super(OpenMdaoCustomXmlIO, self).__init__(*args, **kwargs)
        self.use_promoted_names = True
        """If True, promoted names will be used instead of "real" ones."""
        self._var_names = None
        self._xpaths = None
        self._units = None
        self._xml_unit_attribute = UNIT_ATTRIBUTE

    def set_translation_table(self, var_names: Sequence[str], xpaths: Sequence[str]):
        if len(var_names) != len(xpaths):
            raise IndexError('lists var_names and xpaths should have same length (%i and %i)' %
                             (len(var_names), len(xpaths)))
        self._var_names = var_names
        self._xpaths = xpaths

    def read(self, only: Sequence[str] = None, ignore: Sequence[str] = None) -> IndepVarComp:
        reader = XPathReader(self._data_source)
        reader.unit_attribute_name = self._xml_unit_attribute

        root_tag = reader.tree.getroot().tag

        ivc = IndepVarComp()

        for var_name, xpath in zip(self._var_names, self._xpaths):
            if (only is None or var_name in only) and not (
                    ignore is not None and var_name in ignore):
                if not xpath.startswith('/'):
                    xpath = '/' + root_tag + '/' + xpath
                values_units = reader.get_values_and_units(xpath)
                units = values_units[0][1]
                values = [val[0] for val in values_units]
                ivc.add_output(var_name, values, units=units)

        return ivc

    # TODO: Should unify this with OpenMdaoXmlIO.write()
    def write(self, system: SystemSubclass, only: Sequence[str] = None,
              ignore: Sequence[str] = None):
        outputs = self._get_outputs(system)
        root = etree.Element(ROOT_TAG)

        for output in outputs:
            if not (only is None or output.name in only):
                continue
            if ignore is not None and output.name in ignore:
                continue
            if output.name not in self._var_names:
                continue

            i = self._var_names.index(output.name)
            xpath = self._xpaths[i]

            if xpath.startswith('/'):
                xpath = xpath[1:]
            path_components = xpath.split('/')
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

    def _get_outputs(self, system: SystemSubclass) -> Sequence[_OutputVariable]:
        """ returns the list of outputs from provided system """

        outputs: Sequence[_OutputVariable] = []
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
