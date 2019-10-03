"""
XML reading based on XPath
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
from typing import Optional, List, Tuple, Union

from lxml import etree
from lxml.etree import _ElementTree  # pylint: disable=protected-access  # Useful for type hinting

from fastoad.utils.strings import get_float_list_from_string
from .constants import UNIT_ATTRIBUTE


class XPathReader:
    """
    Helper class for easing usage of XPath in FAST context. Assumption is
    that values are provided through dedicated tags (whatever the hierarchy
    depth) with an optional "unit" attribute.

    e.g.: in ``my_file.xml``:

    .. code-block:: xml

       <root>
            <foo>
                <bar unit="attoparsec">42</bar>
            </foo>
       </root>

    can be accessed through:

    .. code-block:: python

        >>> XPathReader('my_file.xml').get_float('/root/foo/bar')
        42.0
        >>> XPathReader('my_file.xml').get_units('/root/foo/bar')
        'attoparsec'


    See https://www.w3.org/TR/1999/REC-xpath-19991116/ for more info on XPath
    """

    def __init__(self, filename: str):
        """
        Constructor. Will parse the whole indicated file.
        :param filename: XML file
        """
        self.tree: _ElementTree = etree.parse(filename)
        self.unit_attribute_name = UNIT_ATTRIBUTE
        """The element tree provided by :meth:`lxml.etree.parse`"""

    def has_element(self, xpath: str) -> bool:
        """
        :param xpath:XML Path
        :return: True if XPath actually exists
        """
        return len(self.tree.xpath(xpath)) > 0

    def get_text(self, xpath: str) -> str:
        """
        Assumes provided XPath matches only one element.
        Will return the first one anyway.

        :param xpath: XML Path
        :return: value of provided XPath as a string.
        :raises KeyError:  if provided XPath does not exist
        """
        element = self._get_element(xpath)
        return element.text.strip()

    def get_float(self, xpath: str) -> Optional[float]:
        """
        Assumes provided XPath matches only one element.
        Will return the first one anyway.

        :param xpath:XML Path
        :return: value of provided XPath as a float.
        Returns None if value could not be converted.
        :raises KeyError:  if provided XPath does not exist
        """
        text = self.get_text(xpath)

        try:
            return float(text)
        except ValueError:
            return None

    def get_units(self, xpath: str) -> Optional[str]:
        """
        Assumes provided XPath matches only one element.

        :param xpath:XML Path
        :return:content of the "unit" attribute, if it exists.
        Returns None otherwise
        """
        element = self._get_element(xpath)
        if UNIT_ATTRIBUTE in element.attrib:
            return element.attrib[self.unit_attribute_name]

        return None

    def get_values_and_units(self, xpath: str) -> Tuple[Optional[List[Union[str, float]]],
                                                        Optional[str]]:
        """
        Returns a tuple with a list of values and a string for units from provided XPath.

        For each element that matches XPath, the value will be converted as a list of floats if
        possible. If not, it will be kept as a single string.
        Returned list will the concatenation of obtained results for all element that matches Xpath.

        String for units will be retrieved from first element that matches XPath. Will be None if
        no tag is present.

        If required XPath does not exist, None will be returned

        :param xpath:XML Path
        :return: a tuple (list, string) or (None, None) if XPath is not found
        """

        elements = self.tree.xpath(xpath)

        # Units are retrieved from first element only
        if not elements:
            return None, None

        values = []
        units = elements[0].attrib.get(self.unit_attribute_name, None)

        for element in elements:
            value = element.text.strip()
            if value != '':
                float_list = get_float_list_from_string(value)
                if float_list is None:
                    values.append(value)
                else:
                    values += float_list

        return values, units

    def _get_element(self, xpath: str):
        """
        Returns the first element that matches provided XPath
        Will return the first one anyway.

        :param xpath: XML Path
        :return: element for provided XPath.
        :raises KeyError:  if provided XPath does not exist
        """
        if self.has_element(xpath):
            return self.tree.xpath(xpath)[0]

        raise KeyError('XPath not found')

    def get_all_elements_with_no_child_xpath(self):
        """
        Returns the xpath of elements that have no child.

        :return: list of xpaths of element with no child
        """
        xpaths = []
        for elem in self.tree.iter():
            value = elem.text.strip()
            if value != '':
                xpaths.append(self.tree.getelementpath(elem))

        return xpaths
