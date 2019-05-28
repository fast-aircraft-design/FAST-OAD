"""
Tests basic XML serializer for OpenMDAO variables
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

import os.path as pth

from fastoad.io.xml.openmdao_basic_io import OpenMdaoXmlIO


def test_basic_xlm_read():
    """
    Tests the creation of an IndepVarComp() instance from XML file
    """
    filename = pth.join(pth.dirname(__file__), 'data', 'basic_openmdao.xml')
    xml_io = OpenMdaoXmlIO(filename)

    ivc = xml_io.read()

    names = []
    values = []
    units = []

    # pylint: disable=protected-access
    for (name, value, attribs) in ivc._indep_external:
        names.append(name)
        values.append(value)
        units.append(attribs['units'])

    assert names[0] == 'geometry:total_surface'
    assert values[0] == 780.3
    assert units[0] == 'm**2'

    assert names[2] == 'geometry:wing:aspect_ratio'
    assert values[2] == 9.8
    assert units[2] is None

    assert names[3] == 'geometry:fuselage:length'
    assert values[3] == 40.
    assert units[3] == 'm'
