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

"""Sellar functions"""

from math import exp

import numpy as np
import openmdao.api as om

from fastoad.module_management.service_registry import RegisterOpenMDAOSystem, RegisterSubmodel

SERVICE_FUNCTION_F = "service.function.f"
SERVICE_FUNCTION_G1 = "service.function.g1"
SERVICE_FUNCTION_G2 = "service.function.g2"


@RegisterOpenMDAOSystem("configuration_test.sellar.functions")
class Functions(om.Group):
    def initialize(self):
        # Defined the default "f" function. This choice can be overridden in
        # configuration file
        RegisterSubmodel.active_models[SERVICE_FUNCTION_F] = "function.f.default"
        self.options.declare("input_path", types=str, default="")

    def setup(self):
        self.add_subsystem("f", RegisterSubmodel.get_submodel(SERVICE_FUNCTION_F), promotes=["*"])
        self.add_subsystem("g1", RegisterSubmodel.get_submodel(SERVICE_FUNCTION_G1), promotes=["*"])
        self.add_subsystem("g2", RegisterSubmodel.get_submodel(SERVICE_FUNCTION_G2), promotes=["*"])


@RegisterSubmodel(SERVICE_FUNCTION_F, "function.f.default")
class FunctionF(om.ExplicitComponent):
    """An OpenMDAO component to encapsulate Functions discipline"""

    def initialize(self):
        # These options have no effect and are used for checks
        self.options.declare("dummy_f_option", types=int, default=0)
        self.options.declare("dummy_generic_option", types=str, default="")

    def setup(self):
        self.add_input("x", val=2, desc="")
        self.add_input(
            "z", val=[np.nan, np.nan], desc="", units="m**2"
        )  # NaN as default for testing connection check
        self.add_input("yy1", val=1.0, desc="")
        self.add_input("yy2", val=1.0, desc="")

        self.add_output("f", val=1.0, desc="")

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        """Functions computation"""

        z2 = inputs["z"][1]
        x1 = inputs["x"].item()
        y1 = inputs["yy1"].item()
        y2 = inputs["yy2"].item()

        outputs["f"] = x1**2 + z2 + y1 + exp(-y2)


@RegisterSubmodel(SERVICE_FUNCTION_F, "function.f.alternate")
class FunctionFAlt(FunctionF):
    """An OpenMDAO component to encapsulate Functions discipline"""

    def initialize(self):
        # This option has no effect and is used for checks
        self.options.declare("dummy_generic_option", types=str, default="")

        # This one adds a variable to check if it affects correctly input variables
        self.options.declare("add_input_var", types=bool, default=False)

    def setup(self):
        super().setup()
        if self.options["add_input_var"]:
            self.add_input("bar", val=1.0, desc="")

        self.add_output("baz", val=1.0)

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        """Functions computation"""

        z2 = inputs["z"][1]
        x1 = inputs["x"].item()
        y1 = inputs["yy1"].item()
        y2 = inputs["yy2"].item()

        outputs["f"] = x1**2 + z2 + y1 + exp(-y2) - 28.0

        if "bar" in inputs:
            outputs["baz"] = inputs["bar"]


@RegisterSubmodel(SERVICE_FUNCTION_G1, "function.g1.default")
class FunctionG1(om.ExplicitComponent):
    """An OpenMDAO component to encapsulate Functions discipline"""

    def setup(self):
        self.add_input("yy1", val=1.0, desc="")

        self.add_output("g1", val=1.0, desc="")

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        """Functions computation"""

        y1 = inputs["yy1"]

        outputs["g1"] = 3.16 - y1


@RegisterSubmodel(SERVICE_FUNCTION_G2, "function.g2.default")
class FunctionG2(om.ExplicitComponent):
    """An OpenMDAO component to encapsulate Functions discipline"""

    def setup(self):
        self.add_input("yy2", val=1.0, desc="")

        self.add_output("g2", val=1.0, desc="")

        self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        """Functions computation"""

        y2 = inputs["yy2"]

        outputs["g2"] = y2 - 24.0
