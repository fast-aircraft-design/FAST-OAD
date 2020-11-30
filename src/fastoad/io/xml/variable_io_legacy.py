"""
Readers for legacy XML format
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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

from importlib.resources import open_text

from fastoad.io.xml import VariableXmlBaseFormatter
from fastoad.io.xml.translator import VarXpathTranslator
from . import resources

CONVERSION_FILENAME_1 = "legacy1.txt"


class VariableLegacy1XmlFormatter(VariableXmlBaseFormatter):
    """
    Formatter for legacy XML format (version "1")
    """

    def __init__(self):
        translator = VarXpathTranslator()
        with open_text(resources, CONVERSION_FILENAME_1) as translation_table:
            translator.read_translation_table(translation_table)
        super().__init__(translator)

        self.xml_unit_attribute = "unit"
