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

from lxml import etree
from lxml.etree import _Element
from openmdao.core.indepvarcomp import IndepVarComp

from fastoad.io.serialize import AbstractOpenMDAOVariableIO, SystemSubclass
from fastoad.io.xml.constants import UNIT_ATTRIBUTE

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
        pass
