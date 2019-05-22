#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Optional, List, Tuple, Union

from lxml import etree

UNIT_ATTRIBUTE = 'unit'
"""label of tag attribute for providing units as a string"""


class XPathReader:
    """
    Helper class for easing usage of XPath in FAST context.
    Assumption is that values are provided through dedicated tags (whatever the hierarchy depth) with an optional
    "unit" attribute.

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
        >>> XPathReader('my_file.xml').get_unit('/root/foo/bar')
        'attoparsec'


    See https://www.w3.org/TR/1999/REC-xpath-19991116/ for more info on XPath
    """

    def __init__(self, filename):
        """
        Constructor. Will parse the whole indicated file.
        :param filename: XML file
        """
        self.tree = etree.parse(filename)
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
        :return: value of provided XPath as a float. Returns None if value could not be converted.
        :raises KeyError:  if provided XPath does not exist
        """
        text = self.get_text(xpath)

        try:
            value = float(text)
        except ValueError:
            value = None
        return value

    def get_unit(self, xpath: str) -> Optional[str]:
        """
        Assumes provided XPath matches only one element.

        :param xpath:XML Path
        :return:content of the "unit" attribute, if it exists. Returns "" otherwise
        """
        element = self._get_element(xpath)
        if UNIT_ATTRIBUTE in element.attrib:
            return element.attrib[UNIT_ATTRIBUTE]

    def get_values_and_units(self, xpath: str) -> List[Tuple[Union[str, float], Optional[str]]]:
        """
        Returns a list of 2-tuples (value, unit) that match provided XPath.

        *value* may be a float if it can be converted. If not, it will be a string.

        If *value* is a float and *unit* is available, *unit* will be provided as a string.
        In other cases, *unit* will be None

        :param xpath:XML Path
        :return: a list of tuples
        """
        result = []
        elements = self.tree.xpath(xpath)
        for element in elements:
            value = element.text.strip()
            try:
                value = float(value)
                unit = element.attrib.get(UNIT_ATTRIBUTE, None)
            except ValueError:
                unit = None
            result.append((value, unit))

        return result

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
        else:
            raise KeyError("XPath not found")
