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

from typing import Sequence, Dict

import numpy as np
from lxml import etree
from lxml.etree import _Element  # pylint: disable=protected-access  # Useful for type hinting
from openmdao.core.indepvarcomp import IndepVarComp
from openmdao.core.problem import Problem

from fastoad.io.serialize import SystemSubclass
from fastoad.io.xml.constants import UNIT_ATTRIBUTE
from fastoad.io.xml.translator import VarXpathTranslator
from fastoad.openmdao.connections_utils import build_ivc_of_unconnected_inputs
from fastoad.utils.strings import get_float_list_from_string
from .openmdao_custom_io import OpenMdaoCustomXmlIO, Variable


class OpenMdaoXmlIO(OpenMdaoCustomXmlIO):
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

        self.path_separator = '/'
        """
        The separator that will be used in OpenMDAO variable names to match XML path.
        Warning: The dot "." can be used when writing, but not when reading.
        """

    def read(self, only: Sequence[str] = None, ignore: Sequence[str] = None) -> IndepVarComp:
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

    def write(self, system: SystemSubclass, only: Sequence[str] = None,
              ignore: Sequence[str] = None):
        variables = self._get_outputs(system)

        names = []
        xpaths = []
        for variable in variables:
            path_components = variable.name.split(self.path_separator)
            xpath = '/'.join(path_components)
            names.append(variable.name)
            xpaths.append(xpath)

        translator = VarXpathTranslator()
        translator.set(names, xpaths)
        self.set_translator(translator)

        used_variables = self._filter_variables(variables, only=only, ignore=ignore)

        self._write(used_variables)

    def write_inputs(self, problem: Problem, optional_inputs: bool = True):
        """
        Write inputs of a Problem to an xml file

        :param problem: OpenMDAO Problem instance to read.
        :param optional_inputs: if True, inputs with non-NaN values will also
                                be written.
        """
        ivc_inputs = build_ivc_of_unconnected_inputs(problem, with_optional_inputs=optional_inputs)
        self.write(ivc_inputs)

    def _read_xml(self) -> Sequence[Variable]:
        """
        Reads self.data_source as a XML file

        Variable value will be a list of one or more values.
        Variable units will be a string, or None if no unit provided.

        :return: list of Variables (name, value, units) from data source
        """

        context = etree.iterparse(self._data_source, events=("start", "end"))

        # Intermediate storing as a dict for easy access according to name when appending new values
        outputs: Dict[str, Variable] = {}

        current_path = []

        elem: _Element
        for action, elem in context:
            if action == 'start':
                current_path.append(elem.tag)
                units = elem.attrib.get(UNIT_ATTRIBUTE, None)
                value = None
                if elem.text:
                    value = get_float_list_from_string(elem.text)
                if value:
                    name = self.path_separator.join(current_path[1:])
                    if name not in outputs:
                        # Add Variable
                        outputs[name] = Variable(name, value, units)
                    else:
                        # Variable already exists: append values (here the dict is useful)
                        outputs[name].value.extend(value)
            else:  # action == 'end':
                current_path.pop(-1)

        return list(outputs.values())

    def _create_openmdao_code(self) -> str:  # pragma: no cover
        """dev utility for generating code"""
        outputs = self._read_xml()

        lines = ['ivc = IndepVarComp()']
        for name, value, units in outputs:
            lines.append("ivc.add_output('%s', val=%s%s)" %
                         (name, value, ", units='%s'" % units if units else ''))

        return '\n'.join(lines)
