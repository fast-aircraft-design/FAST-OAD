"""Tools for generating and postprocess Design of Experiments (DOEs) in FAST-OAD"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2025 ONERA & ISAE-SUPAERO
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

from dataclasses import dataclass, field
from os import PathLike
from typing import ClassVar, Dict, List, Optional, Union

import numpy as np
import pandas as pd
import smt.sampling_methods as samp
from smt.applications.mfk import NestedLHS

import fastoad.api as oad
from fastoad._utils.files import as_path
from fastoad.openmdao.variables import VariableList


@dataclass
class DOEVariable:
    """
    Represents a Design of Experiments (DOE) variable defined by its unique `id_variable`.

    :param name: The name of the FAST-OAD DOE variable.
    :param bound_lower: The lower bound of the variable. Defaults to None.
    :param bound_upper: The upper bound of the variable. Defaults to None.
    :param reference_value: A reference value used to adjust bounds as percentages. If given, `bound_lower` and
                            `bound_upper` are considered percentages. Defaults to None.
    :param bind_variable_to: Another DOEVariable instance to bind this variable to. When bound, this variable
                             inherits the bounds of the bound variable, and no new ID is assigned.
    :param name_pseudo: An optional alias for the variable. If not provided, it defaults to the value of `name`.
    """

    name: str
    bound_lower: Optional[float] = None
    bound_upper: Optional[float] = None
    reference_value: Optional[float] = None
    bind_variable_to: Optional["DOEVariable"] = None
    name_pseudo: Optional[str] = None

    # Class-level counters
    _instance_counter: ClassVar[int] = 0
    _next_instance: ClassVar[int] = -1  # The ID of the first var is 0

    def __post_init__(self):
        type(self)._instance_counter += 1
        type(self)._next_instance += 1
        if not self.name_pseudo:  # if no pseudo is given, pseudo=name
            self.name_pseudo = self.name
        if self.bind_variable_to:
            self.id_variable = (
                self.bind_variable_to.id_variable
            )  # ID of the variable bounds, useful when variable binding is used
            type(self)._next_instance -= 1  # No new ID is assigned
            self.bound_lower = self.bind_variable_to.bound_lower
            self.bound_upper = self.bind_variable_to.bound_upper
        else:
            self.id_variable = type(self)._next_instance
            if self.reference_value:
                if (self.bound_lower < 0) | (self.bound_upper < 0):
                    raise ValueError(
                        f"Invalid DOE bounds for variable {self.name}: ({self.bound_lower}) and ({self.bound_upper}) should be greater than zero when a reference value is given."
                    )
                self.bound_lower = self.reference_value - (
                    self.reference_value * self.bound_lower / 100
                )
                self.bound_upper = self.reference_value + (
                    self.reference_value * self.bound_upper / 100
                )
            else:
                if self.bound_lower > self.bound_upper:
                    raise ValueError(
                        f"Invalid DOE bounds for variable {self.name}: ({self.bound_lower}) should not be greater than({self.bound_upper})"
                    )


@dataclass
class DOEConfig:
    """
    Configuration and management of Design of Experiments (DOE) processes.

    This class serves as a central entity for configuring and generating sampling points
    for experiments using various DOE sampling methods using the SMT package. It manages the
    input variables, their bounds, and the relationships between variables (e.g., binding one
    variable to another). The class also supports reproducibility through random seeding. The
    sampling obtained by running :meth:`sampling_doe` is formatted as `VariableList` instances,
    making them directly usable by the `CalcRunner` class for computation.

    :param sampling_method: The method used for sampling (e.g., LHS, Full Factorial, Random).
                            This determines how sampling points are generated.
    :param variables: A list of DOEVariable instances that represent the variables to be
                    included in the experiment. Each variable defines its bounds,
                    reference value, and optional bindings.
    :param destination_folder: The folder where the generated DOE data will be saved. This
                            ensures results are organized and easily accessible.
    :param seed_value: A seed value for random number generation to ensure reproducibility
                    of sampling. Defaults to 0.
    :param sampling_options: An optional dictionary that stores additional parameters or
                            options specific to the chosen sampling method. Defaults to empty dict.
    """

    sampling_method: str
    variables: List[DOEVariable]
    destination_folder: Union[str, PathLike]
    seed_value: int = 0
    sampling_options: Optional[Dict] = field(
        default=None
    )  # This dict stores the eventual additional options for the chosen sampling method

    def __post_init__(self):
        self.destination_folder = as_path(self.destination_folder).resolve()
        # Extract the necessary data to congigurate the DOE
        self.variables_binding = [var.id_variable for var in self.variables]
        self.var_names = [var.name for var in self.variables]
        self.var_names_pseudo = [var.name_pseudo for var in self.variables]
        self.var_names_pseudo_mapping = dict(zip(self.var_names, self.var_names_pseudo))
        # Exctarct bounds taking into account binding
        seen = set()
        self.bounds = []
        for var in self.variables:
            if var.id_variable not in seen:
                seen.add(var.id_variable)
                self.bounds.append([var.bound_lower, var.bound_upper])
        self.bounds = np.asarray(self.bounds)

        self.is_sampled = False
        self.doe_points_multilevel = None

    def _handle_lhs(self, level_count=None):
        if level_count:
            return NestedLHS(nlevel=level_count, xlimits=self.bounds, random_state=self.seed_value)
        else:
            return samp.LHS(criterion="ese", xlimits=self.bounds, random_state=self.seed_value)

    def _handle_full_factorial(self):
        return samp.FullFactorial(xlimits=self.bounds)

    def _write_doe_inputs(self):
        if self.is_sampled:
            file_name = "DOE_inputs"
            if self.doe_points_multilevel:
                level_count = len(self.doe_points_multilevel)
                for i, point_list in enumerate(self.doe_points_multilevel):
                    # Rearrange columns based on the variables_binding variable
                    doe_points_upd = point_list[:, self.variables_binding]
                    doe_points_df_nest = pd.DataFrame(doe_points_upd, columns=self.var_names_pseudo)
                    doe_points_df_nest.to_csv(
                        self.destination_folder
                        / (file_name + f"_{level_count}D_level{i}" + ".csv"),
                        index_label="ID",
                        sep=";",
                        quotechar="|",
                    )
            else:
                doe_points = self.doe_points_df.rename(
                    columns=self.var_names_pseudo_mapping
                )  # Use pseudos for outputs
                doe_points.to_csv(
                    self.destination_folder / (file_name + ".csv"),
                    index_label="ID",
                    sep=";",
                    quotechar="|",
                )
        else:
            raise RuntimeError(
                "You cannot call _write_doe_inputs without having performed the sampling."
            )

    def sampling_doe(self, sample_count) -> List[VariableList]:
        """
        Generates sampling points for a Design of Experiments (DOE) using the SMT library.

        :param sample_count: The number of samples to generate.

        :return: A list of `oad.VariableList` objects containing the generated sampling points.
        """
        method = self.sampling_method
        level_count = None
        use_level = None
        if self.sampling_options:
            if self.sampling_options.get("level_count"):
                level_count = self.sampling_options.get("level_count")
                use_level = self.sampling_options.get("use_level")

        method_dispatch = {
            "LHS": lambda: self._handle_lhs(level_count),
            "Full Factorial": self._handle_full_factorial,
        }
        handler = method_dispatch.get(method)
        if handler is None:
            raise ValueError(
                f"Unknown sampling method. Please use one of the following implemented method:\n{method_dispatch.keys()}"
            )
        sample_method = handler()
        doe_points = sample_method(sample_count)

        column_names = (
            self.var_names
        )  # Use name to create the table, the pseudo is used only if the user want a print
        if level_count:
            self.doe_points_multilevel = doe_points.copy()  # Used for writing
            doe_points = doe_points[use_level]
        doe_points_upd = doe_points[
            :, self.variables_binding
        ]  # Rearrange columns based on the variables_binding variable
        self.doe_points_df = pd.DataFrame(doe_points_upd, columns=column_names)
        doe_points_dict = self.doe_points_df.to_dict(orient="records")

        self.is_sampled = True

        return [  # Good format for CalcRunner
            oad.VariableList(
                [oad.Variable(var_name, val=var_value) for var_name, var_value in doe_point.items()]
            )
            for doe_point in doe_points_dict
        ]
