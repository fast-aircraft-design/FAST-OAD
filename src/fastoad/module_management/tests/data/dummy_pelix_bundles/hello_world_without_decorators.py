# This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
# Copyright (c) 2025 ONERA & ISAE-SUPAERO
# FAST-OAD is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Basic "Hello World" services without using iPOPO decorators
"""

# Define the component factory, with a given name
from fastoad.module_management._bundle_loader import BundleLoader


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
