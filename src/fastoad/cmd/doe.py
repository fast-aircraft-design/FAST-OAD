"""
Python module containing the tools for generating and postprocessing Design of
Experiments (DOEs) in FAST-OAD.
"""
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
from smt.sampling_methods.sampling_method import ScaledSamplingMethod

import fastoad.api as oad
from fastoad._utils.files import as_path
from fastoad.openmdao.variables import VariableList


@dataclass
class DoeVariable:
    """
    Represents a Design of Experiments (DOE) variable defined by its unique `id`.

    :param name: The name of the FAST-OAD OpenMDAO variable used for the DOE.
    :param bind_variable_to: Another DoeVariable instance to bind this variable to. When bound,
                            this variable inherits the bounds of the bound variable, and no new
                            ID is assigned. Once the DOE is sampled, the variables will share
                            the same dimension and same values. Defaults to None.
    :param lower_bound: The lower bound of the variable. Defaults to None.
    :param upper_bound: The upper bound of the variable. Defaults to None.
    :param units: Units of measure used for the DoeVariable
    :param reference_value: A reference value used to adjust bounds as percentages. If given,
                    `lower_bound` and `upper_bound` are considered as percentages, following
                    this formula:
                    [ref_value - ref_value * lower_bound, ref_value + ref_value * upper_bound].
                    Defaults to None.
    :param name_alias: An optional alias for the variable. If not provided, it defaults to the
                       value of `name`.
    """

    name: str
    bind_variable_to: Optional["DoeVariable"] = None
    lower_bound: Optional[float] = None
    _lower_bound: Optional[float] = field(
        init=False, repr=False
    )  # This is needed to permit the use of Dataclasses with Properties
    upper_bound: Optional[float] = None
    _upper_bound: Optional[float] = field(
        init=False, repr=False
    )  # https://florimond.dev/en/posts/2018/10/reconciling-dataclasses-and-properties-in-python
    units: Optional[str] = None
    reference_value: Optional[float] = None
    name_alias: Optional[str] = None

    # Class-level counter using itertools to handle unique IDs. If two variables are binded
    # they share the same id.
    _id_counter: ClassVar[itertools.count] = itertools.count()

    def __post_init__(self) -> None:
        self._validate_variable()
        if self.name_alias is None:
            self.name_alias = self.name
        if self.bind_variable_to is not None:
            self.id = self.bind_variable_to.id
        else:
            self.id = self._generate_id()
            self._validate_bounds()

    @classmethod
    def _generate_id(cls) -> int:
        """Generates a unique id for each instance."""
        return next(cls._id_counter)

    @property
    def lower_bound(self) -> float:  # noqa: F811
        """The lower bound of the DOE variable."""
        if self.bind_variable_to is not None:
            return self.bind_variable_to.lower_bound
        return self._lower_bound

    @lower_bound.setter
    def lower_bound(self, value: float) -> None:
        if self.bind_variable_to is not None and not isinstance(value, property):
            # If not initialized, value default to being property object
            warnings.warn(
                f"Cannot set lower_bound directly for variable '{self.name}' because it is bound to"
                f" '{self.bind_variable_to.name}'. The bound variable's bounds take precedence.",
                UserWarning,
                stacklevel=2,
            )
        else:
            self._lower_bound = value

    @property
    def upper_bound(self) -> float:  # noqa: F811
        """The upper bound of the DOE variable."""
        if self.bind_variable_to is not None:
            return self.bind_variable_to.upper_bound
        return self._upper_bound

    @upper_bound.setter
    def upper_bound(self, value: float) -> None:
        if self.bind_variable_to is not None and not isinstance(value, property):
            # If not initialized, value default to being property object
            warnings.warn(
                f"Cannot set upper_bound directly for variable '{self.name}' because it is bound to"
                f" '{self.bind_variable_to.name}'. The bound variable's bounds take precedence.",
                UserWarning,
                stacklevel=2,
            )
        else:
            self._upper_bound = value

    def _validate_bounds(self) -> None:
        if self.reference_value is not None:
            if (self.lower_bound < 0) or (self.upper_bound < 0):
                raise ValueError(
                    f"Invalid DOE bounds for variable {self.name}: ({self.lower_bound}) and "
                    f"({self.upper_bound}) should be greater than zero when a reference value "
                    f"is given."
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
                    f"Invalid DOE bounds for variable {self.name}: ({self.lower_bound}) should "
                    f"not be greater than ({self.upper_bound})"
                )

    def _validate_variable(self) -> None:
        """Ensures that the variable is either:
        1. Bound to another variable (`bind_variable_to` is set), or
        2. Has both `lower_bound` and `upper_bound` set.
        """
        if self.bind_variable_to is None:
            if isinstance(self.lower_bound, property) or isinstance(self.upper_bound, property):
                # If not initialized, upper and lower bounds default to being properties objects
                raise ValueError(
                    f"DoeVariable '{self.name}' must either be bound to another variable "
                    "(via 'bind_variable_to') or have both 'lower_bound' and 'upper_bound' defined."
                )


@dataclass
class DoeSampling:
    """Configuration and management of Design of Experiments (DOE) processes.

    This class serves as a central entity for configuring and generating sampling points
    for experiments using various DOE sampling methods using the SMT package. It manages the
    input variables, their bounds, and the relationships between variables (e.g., binding one
    variable to another). The class also supports reproducibility through random seeding. The
    sampling obtained by running :meth:`sampling_doe` is formatted as `VariableList` instances,
    making them directly usable by the `CalcRunner` class for computation.

    :param sampling_method: The method used for sampling (e.g., LHS, Full Factorial, Random).
                            This determines how sampling points are generated.
    :param variables: A list of DoeVariable instances that represent the variables to be
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
    variables: List[DoeVariable]
    destination_folder: Union[str, PathLike]
    seed_value: int = 0
    sampling_options: Optional[dict] = field(
        default=None
    )  # This dict stores the eventual additional options for the chosen sampling method
    _is_sampled: bool = field(
        default=False, init=False, repr=False
    )  # Internal flag, default to False

    @property
    def variables_binding_list(self):  # noqa: F811
        """List of the id of the binded variables."""
        return [var.id for var in self.variables]

    @property
    def var_names(self):  # noqa: F811
        """List of the names of the DoeVariables."""
        return [var.name for var in self.variables]

    @property
    def var_units(self):  # noqa: F811
        """List of the units of the DoeVariables."""
        return [var.units for var in self.variables]

    @property
    def var_names_pseudo(self):  # noqa: F811
        """List of the pseudo names of the DoeVariables."""
        return [var.name_alias for var in self.variables]

    @property
    def _var_names_pseudo_mapping(self):
        return dict(zip(self.var_names, self.var_names_pseudo))

    @property
    def bounds(self):  # noqa: F811
        """List of the absolute bounds value of the DoeVariables."""
        seen = set()
        seen_names = set()
        bounds_list = []

        for var in self.variables:
            if var.id not in seen:  # Do not add multiple times binded variables
                if var.name not in seen_names:
                    seen.add(var.id)
                    seen_names.add(var.name)
                    bounds_list.append([var.lower_bound, var.upper_bound])
                else:
                    warnings.warn(
                        f"Variable '{var.name}' set multiple times. Please check the DOE variable "
                        f"definition. The bounds defined first take precedence. "
                        f"({var.lower_bound, var.upper_bound}) will be ignored.",
                        UserWarning,
                        stacklevel=2,
                    )
                    self.variables.remove(var)

        return np.asarray(bounds_list)

    def __post_init__(self) -> None:
        self.destination_folder = as_path(self.destination_folder).resolve()
        self.doe_points_multilevel = None
        self._bounds = (
            self.bounds
        )  # we use it to trigger the check for same name in variables defined in the bounds setter

    def _handle_lhs(self, level_count: Optional[int] = None) -> ScaledSamplingMethod:
        if level_count is not None:
            return NestedLHS(nlevel=level_count, xlimits=self.bounds, random_state=self.seed_value)
        return samp.LHS(criterion="ese", xlimits=self.bounds, random_state=self.seed_value)

    def _handle_full_factorial(self) -> ScaledSamplingMethod:
        return samp.FullFactorial(xlimits=self.bounds)

    def _handle_random(self) -> ScaledSamplingMethod:
        return samp.Random(xlimits=self.bounds, random_state=self.seed_value)

    def _write_doe_inputs(self) -> None:
        if self._is_sampled:
            file_name = "DOE_inputs"
            if self.doe_points_multilevel is not None:
                level_count = len(self.doe_points_multilevel)
                for i, point_list in enumerate(self.doe_points_multilevel):
                    # Rearrange columns based on the variables_binding variable
                    doe_points_updated = point_list[:, self.variables_binding_list]
                    doe_points_df_nest = pd.DataFrame(
                        doe_points_updated, columns=self.var_names_pseudo
                    )
                    doe_points_df_nest.to_csv(
                        self.destination_folder
                        / (
                            file_name + f"_{level_count}D_level{i + 1}" + ".csv"
                        ),  # Leveles start at 1
                        index_label="ID",
                    )
            else:
                doe_points = self.doe_points_df.rename(
                    columns=self._var_names_pseudo_mapping
                )  # Use pseudos for outputs
                doe_points.to_csv(
                    self.destination_folder / (file_name + ".csv"),
                    index_label="ID",
                )
        else:
            raise RuntimeError(
                "You cannot call '_write_doe_inputs' without having performed the sampling."
                "Please use the 'sample_doe' method before."
            )

    def sample_doe(self, sample_count: int) -> List[VariableList]:
        """Generates sampling points for a Design of Experiments (DOE) using the SMT library.

        :param sample_count: The number of samples to generate.

        :return: A list of `oad.VariableList` objects containing the generated sampling points.
        """
        method = self.sampling_method
        level_count = None
        use_level = None
        if self.sampling_options and self.sampling_options.get("level_count") is not None:
            level_count = self.sampling_options.get("level_count")
            if self.sampling_options.get("use_level") is not None:
                if self.sampling_options.get("use_level") < 1 or self.sampling_options.get(
                    "use_level"
                ) > self.sampling_options.get("level_count"):
                    raise ValueError(
                        f"'use_level' parameter should be between 1 and 'level_count' "
                        f"= {self.sampling_options.get('level_count')}."
                    )

            use_level = self.sampling_options.get("use_level") - 1

        method_dispatch = {
            "LHS": lambda: self._handle_lhs(level_count),
            "Full Factorial": self._handle_full_factorial,
            "Random": self._handle_random,
        }
        handler = method_dispatch.get(method)
        if handler is None:
            raise ValueError(
                f"Unknown sampling method. Please use one of the following implemented "
                f"method:\n{method_dispatch.keys()}"
            )
        sample_method = handler()
        doe_points = sample_method(sample_count)

        column_names = (
            self.var_names
        )  # Use name to create the table, the alias is used only if the user want a print
        if level_count is not None:
            self.doe_points_multilevel = doe_points.copy()  # Used for writing
            doe_points = doe_points[use_level]
        doe_points_updated = doe_points[
            :, self.variables_binding_list
        ]  # Rearrange columns based on the variables_binding variable
        self.doe_points_df = pd.DataFrame(doe_points_updated, columns=column_names)
        doe_points_dict = self.doe_points_df.to_dict(orient="records")

        self._is_sampled = True
        self._write_doe_inputs()

        return [  # Good format for CalcRunner
            oad.VariableList(
                [
                    oad.Variable(var_name, val=var_value["val"], units=var_value["units"])
                    for var_name, var_value in doe_point.items()
                ]
            )
            for doe_point in doe_points_dict
        ]

    @staticmethod
    def doe_from_sampled_csv(
        file_path: Union[str, PathLike],
        var_names_pseudo_mapping: Optional[Dict] = None,
    ) -> list[VariableList]:
        """Generates the DOE points directly from a pre-sampled CSV file.

        :param file_path: The path of the input CSV file.
        :param var_names_pseudo_mapping: A dict containing var_name:var_name_pseudo used
                                        for reading the CSV file.

        :return: A list of `oad.VariableList` objects containing the generated sampling points.
        """
        doe_points_df = pd.read_csv(file_path)
        # Ensure "ID" column exists
        if "ID" not in doe_points_df.columns:
            doe_points_df.insert(0, "ID", range(len(doe_points_df)))  # Create ID column

        # Handle column renaming (mapping or default behavior)
        if var_names_pseudo_mapping is None:
            var_names = doe_points_df.drop(columns=["ID"]).columns.tolist()
            var_names_pseudo_mapping = dict(zip(var_names, var_names))

        doe_points_dict = doe_points_df.rename(columns=var_names_pseudo_mapping).to_dict(
            orient="records"
        )

        return [  # Good format for CalcRunner
            oad.VariableList(
                [oad.Variable(var_name, val=var_value) for var_name, var_value in doe_point.items()]
            )
            for doe_point in doe_points_dict
        ]
