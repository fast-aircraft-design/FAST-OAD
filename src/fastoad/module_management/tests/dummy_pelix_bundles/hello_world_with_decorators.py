"""
Basic "Hello World" services using iPOPO decorators
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
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

# Dummy classes, so let's make pylint not too picky
# pylint: disable=missing-docstring
# pylint: disable=no-self-use
# pylint: disable=too-few-public-methods

from pelix.ipopo.decorators import ComponentFactory, Provides, Instantiate, Property

# Define the component factory, with a given name


# First, let's register 2 factories the iPOPO way
@ComponentFactory("hello-world-factory")
@Provides("hello.world")
@Property("_Prop1", "Prop1", 1)
@Property("_Prop_2", "Prop 2", "Says.Hello")
@Property("Instantiated", None, True)
@Instantiate("provider")
class Greetings1:
    def hello(self, name="World"):
        return "Hello, {0}!".format(name)


@ComponentFactory("hello-world-factory2")
@Provides("hello.world")
@Property("_Prop1", "Prop1", 2)
@Property("_Prop_2", "Prop 2", "Says.Hi")
@Property("Instantiated", None, True)
@Instantiate("provider2")
class Greetings2:
    def hello(self, name="World"):
        return "Hi, {0}!".format(name)
