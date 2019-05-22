# -*- coding: utf-8 -*-
"""
Basic "Hello World" services
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

# Dummy classes, so let's make pylint not too picky
# pylint: disable=missing-docstring
# pylint: disable=no-self-use
# pylint: disable=too-few-public-methods

from pelix.ipopo.decorators import ComponentFactory, Provides, Instantiate, \
    Property


# Define the component factory, with a given name
@ComponentFactory("hello-world-factory")
# Defines the service to provide when the component is active
@Provides("hello.world")
@Property("Prop1", None, 1)
@Property("Prop2", None, "Says.Hello")
@Property("Instantiated", None, True)
# A component must be instantiated as soon as the bundle is active
@Instantiate("provider")
class Greetings1:
    def hello(self, name="World"):
        return "Hello, {0}!".format(name)


# Another instance for the same service
@ComponentFactory("hello-world-factory2")
@Provides("hello.world")
@Property("Prop1", None, 2)
@Property("Prop2", None, "Says.Hi")
@Property("Instantiated", None, True)
@Instantiate("provider2")
class Greetings2:
    def hello(self, name="World"):
        return "Hi, {0}!".format(name)


@ComponentFactory("another-hello-world-factory")
@Provides("hello.world.no.instance")
@Property("Prop1", None, 3)
@Property("Prop2", None, "Says.Hello")
@Property("Instantiated", None, False)
# Not instantiating this one for testing the case
class OtherGreetings:
    def hello(self, name="World"):
        return "Hello again, {0}!".format(name)
