"""
Readers for legacy XML format
"""

from fastoad._utils.resource_management.contents import PackageReader
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
        with PackageReader(resources).open_text(CONVERSION_FILENAME_1) as translation_table:
            translator.read_translation_table(translation_table)
        super().__init__(translator)

        self.xml_unit_attribute = "unit"
