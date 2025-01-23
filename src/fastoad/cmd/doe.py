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

import itertools
import warnings
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
    Represents a Design of Experiments (DOE) variable defined by its unique `variable_id`.

    :param name: The name of the FAST-OAD DOE variable.
    :param lower_bound: The lower bound of the variable. Defaults to None.
    :param upper_bound: The upper bound of the variable. Defaults to None.
    :param reference_value: A reference value used to adjust bounds as percentages. If given, `lower_bound` and
                            `upper_bound` are considered as percentages. Defaults to None.
    :param bind_variable_to: Another DOEVariable instance to bind this variable to. When bound, this variable
                             inherits the bounds of the bound variable, and no new ID is assigned. Once the DOE
                             is sampled, the variables will share the same dimension and same values.
    :param name_alias: An optional alias for the variable. If not provided, it defaults to the value of `name`.
    """

    name: str
    lower_bound: Optional[float] = None
    _lower_bound: Optional[float] = field(
        init=False, repr=False
    )  # This is needed to permit the use of Dataclasses with Properties
    upper_bound: Optional[float] = None
    _upper_bound: Optional[float] = field(
        init=False, repr=False
    )  # More info here: # noqa: F811 # https://florimond.dev/en/posts/2018/10/reconciling-dataclasses-and-properties-in-python
    reference_value: Optional[float] = None
    bind_variable_to: Optional["DOEVariable"] = None
    name_alias: Optional[str] = None

    # Class-level counter using itertools to handle unique IDs. If two variables are binded, they shares the same ID.
    _id_counter: ClassVar[itertools.count] = itertools.count()

    def __post_init__(self):
        self.validate_variable()
        if not self.name_alias:
            self.name_alias = self.name
        if self.bind_variable_to:
            self.variable_id = self.bind_variable_to.variable_id
        else:
            self.variable_id = self._generate_id()
            self.validate_bounds()

    @classmethod
    def _generate_id(cls):
        """Generates a unique ID for each instance."""
        return next(cls._id_counter)

    @property
    def lower_bound(self):  # noqa: F811 # https://florimond.dev/en/posts/2018/10/reconciling-dataclasses-and-properties-in-python
        if self.bind_variable_to:
            return self.bind_variable_to.lower_bound
        return self._lower_bound

    @lower_bound.setter
    def lower_bound(self, value):
        if self.bind_variable_to:
            warnings.warn(
                f"Cannot set lower_bound directly for variable '{self.name}' because it is bound to '{self.bind_variable_to.name}'. "
                f"The bound variable's bounds take precedence.",
                UserWarning,
            )
        else:
            self._lower_bound = value

    @property
    def upper_bound(self):  # noqa: F811 # https://florimond.dev/en/posts/2018/10/reconciling-dataclasses-and-properties-in-python
        if self.bind_variable_to:
            return self.bind_variable_to.upper_bound
        return self._upper_bound

    @upper_bound.setter
    def upper_bound(self, value):
        if self.bind_variable_to:
            warnings.warn(
                f"Cannot set upper_bound directly for variable '{self.name}' because it is bound to '{self.bind_variable_to.name}'. "
                f"The bound variable's bounds take precedence.",
                UserWarning,
            )
        else:
            self._upper_bound = value

    def validate_bounds(self):
        if self.reference_value:
            if (self.lower_bound < 0) or (self.upper_bound < 0):
                raise ValueError(
                    f"Invalid DOE bounds for variable {self.name}: ({self.lower_bound}) and ({self.upper_bound}) should be greater than zero when a reference value is given."
                )
            self._lower_bound = self.reference_value - (
                self.reference_value * self.lower_bound / 100
            )
            self._upper_bound = self.reference_value + (
                self.reference_value * self.upper_bound / 100
            )
        else:
            if self.lower_bound > self.upper_bound:
                raise ValueError(
                    f"Invalid DOE bounds for variable {self.name}: ({self.lower_bound}) should not be greater than ({self.upper_bound})"
                )

    def validate_variable(self):
        """
        Ensures that the variable is either:
        1. Bound to another variable (`bind_variable_to` is set), or
        2. Has both `lower_bound` and `upper_bound` set.
        """
        if self.bind_variable_to:
            if not isinstance(self._lower_bound, property) or not isinstance(
                self._upper_bound, property
            ):
                # If not initialized, upper and lower bounds default to being properties objects
                warnings.warn(
                    f"Variable '{self.name}' is bound to '{self.bind_variable_to.name}'. "
                    f"Bounds ({self._lower_bound}, {self._upper_bound}) will be ignored.",
                    UserWarning,
                )
        else:
            if isinstance(self.lower_bound, property) or isinstance(self.upper_bound, property):
                raise ValueError(
                    f"DOEVariable '{self.name}' must either be bound to another variable (via 'bind_variable_to') "
                    f"or have both 'lower_bound' and 'upper_bound' defined."
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

    # Dataclass features initialized in __post_init__
    variables_binding: List[int] = field(init=False, repr=False)
    var_names: List[str] = field(init=False, repr=False)
    var_names_pseudo: List[str] = field(init=False, repr=False)
    bounds: np.ndarray = field(init=False, repr=False)
    _is_sampled: bool = field(
        default=False, init=False, repr=False
    )  # Internal flag, default to False

    def __post_init__(self):
        self.destination_folder = as_path(self.destination_folder).resolve()
        # Extract the necessary data to configurate the DOE
        self.variables_binding = [var.variable_id for var in self.variables]
        self.var_names = [var.name for var in self.variables]
        self.var_names_pseudo = [var.name_alias for var in self.variables]
        self.var_names_pseudo_mapping = dict(zip(self.var_names, self.var_names_pseudo))
        # Exctract bounds taking into account binding
        seen = set()
        seen_names = set()
        self.bounds = []
        for var in self.variables:
            if var.variable_id not in seen:  # Do not add multiple times binded variables
                if var.name not in seen_names:
                    seen.add(var.variable_id)
                    seen_names.add(var.name)
                    self.bounds.append([var.lower_bound, var.upper_bound])
                else:
                    warnings.warn(
                        f"Variable '{var.name}' set multiple times. Please check the DOE variable definition."
                        f"The bounds defined first take precedence. ({var.lower_bound, var.upper_bound}) will be"
                        f"ignored.",
                        UserWarning,
                    )
        self.bounds = np.asarray(self.bounds)
        self.doe_points_multilevel = None

    def _handle_lhs(self, level_count=None):
        if level_count:
            return NestedLHS(nlevel=level_count, xlimits=self.bounds, random_state=self.seed_value)
        else:
            return samp.LHS(criterion="ese", xlimits=self.bounds, random_state=self.seed_value)

    def _handle_full_factorial(self):
        return samp.FullFactorial(xlimits=self.bounds)

    def _handle_random(self):
        return samp.Random(xlimits=self.bounds, random_state=self.seed_value)

    def _write_doe_inputs(self):
        if self._is_sampled:
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

    def sample_doe(self, sample_count: int) -> List[VariableList]:
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
            "Random": self._handle_random,
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
        )  # Use name to create the table, the alias is used only if the user want a print
        if level_count:
            self.doe_points_multilevel = doe_points.copy()  # Used for writing
            doe_points = doe_points[use_level]
        doe_points_upd = doe_points[
            :, self.variables_binding
        ]  # Rearrange columns based on the variables_binding variable
        self.doe_points_df = pd.DataFrame(doe_points_upd, columns=column_names)
        doe_points_dict = self.doe_points_df.to_dict(orient="records")

        self._is_sampled = True

        return [  # Good format for CalcRunner
            oad.VariableList(
                [oad.Variable(var_name, val=var_value) for var_name, var_value in doe_point.items()]
            )
            for doe_point in doe_points_dict
        ]
