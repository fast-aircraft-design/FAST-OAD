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
import openmdao.api as om
from lxml import etree
from lxml.etree import _Element  # pylint: disable=protected-access  # Useful for type hinting

from fastoad.io.xml.constants import UNIT_ATTRIBUTE
from fastoad.io.xml.exceptions import FastXPathEvalError
from fastoad.io.xml.openmdao_custom_io import OMCustomXmlIO, Variable
from fastoad.io.xml.translator import VarXpathTranslator
from fastoad.utils.strings import get_float_list_from_string


class OMXmlIO(OMCustomXmlIO):
    """
    Basic serializer for OpenMDAO variables

    Assuming self.path_separator is defined as ``:`` (default), an OpenMDAO variable named like
    ``foo:bar`` with units ``m/s`` will be read and written as:

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
        super(OMXmlIO, self).__init__(*args, **kwargs)

        self._translator: BasicVarXpathTranslator = BasicVarXpathTranslator(':')

    @property
    def path_separator(self):
        """
        The separator that will be used in OpenMDAO variable names to match XML path.
        Warning: The dot "." can be used when writing, but not when reading.
        """
        return self._translator.path_separator

    @path_separator.setter
    def path_separator(self, separator):
        self._translator.path_separator = separator

    def read(self, only: Sequence[str] = None, ignore: Sequence[str] = None) -> om.IndepVarComp:
        # Check separator, as OpenMDAO won't accept the dot.
        if self.path_separator == '.':
            raise ValueError('Cannot use dot "." in OpenMDAO variables.')

        variables = self._read_variables()

        # Create IndepVarComp instance
        ivc = om.IndepVarComp()
        for name, value, units in variables:
            if (only is None or name in only) and not (ignore is not None and name in ignore):
                ivc.add_output(name, val=np.array(value), units=units)

        return ivc

    def write(self, ivc: om.IndepVarComp, only: Sequence[str] = None, ignore: Sequence[str] = None):
        try:
            super().write(ivc, only, ignore)
        except FastXPathEvalError as err:
            # Trying to help...
            raise FastXPathEvalError(err.args[0] +
                                     ' : self.path_separator is "%s". It is correct?'
                                     % self.path_separator)

    def _read_variables(self) -> Sequence[Variable]:
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
                    name = self._translator.get_variable_name('/'.join(current_path[1:]))
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
        outputs = self._read_variables()

        lines = ['ivc = IndepVarComp()']
        for name, value, units in outputs:
            lines.append("ivc.add_output('%s', val=%s%s)" %
                         (name, value, ", units='%s'" % units if units else ''))

        return '\n'.join(lines)


class BasicVarXpathTranslator(VarXpathTranslator):
    """
    Dedicated VarXpathTranslator that builds variable names by simply converting
    the '/' separator of XPaths into the desired separator.
    """

    def __init__(self, path_separator):
        super().__init__()
        self.path_separator = path_separator

    def get_variable_name(self, xpath: str) -> str:
        path_components = xpath.split('/')
        name = self.path_separator.join(path_components)
        return name

    def get_xpath(self, var_name: str) -> str:
        path_components = var_name.split(self.path_separator)
        xpath = '/'.join(path_components)
        return xpath
