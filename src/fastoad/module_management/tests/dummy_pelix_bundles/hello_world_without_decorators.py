"""
Basic "Hello World" services without using iPOPO decorators
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

# Define the component factory, with a given name
from fastoad.module_management import BundleLoader


# Register factories without instantiating with our wrapping of iPOPO
class OtherGreetings:
    def hello(self, name="World"):
        return "Hello again, {0}!".format(name)


BundleLoader().register_factory(
    OtherGreetings,
    factory_name="another-hello-world-factory",
    service_names=["hello.world", "hello.world.no.instance"],
    properties={"Prop1": 3, "Prop 2": "Says.Hello", "Instantiated": False},
)


class OtherGreetings2:
    def hello(self, name="Universe"):
        return "Hello again, {0}!".format(name)


# This one provides a different service and tests registering without properties
BundleLoader().register_factory(
    OtherGreetings2, factory_name="hello-universe-factory", service_names=["hello.universe"]
)
