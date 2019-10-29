"""
Readers for legacy XML format
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

from fastoad.io.xml import OMCustomXmlIO
from fastoad.io.xml.translator import VarXpathTranslator

CONVERSION_FILE_1 = pth.join(pth.dirname(__file__), 'resources', 'legacy1.txt')


class OMLegacy1XmlIO(OMCustomXmlIO):
    """
    Reader for legacy XML format (version "1")
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        translator = VarXpathTranslator()
        translator.read_translation_table(CONVERSION_FILE_1)

        self._xml_unit_attribute = 'unit'
        self.set_translator(translator)
