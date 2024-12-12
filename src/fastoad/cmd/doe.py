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

import os
from dataclasses import dataclass, field
from os import PathLike
from typing import ClassVar, Dict, List, Optional, Union

import numpy as np
import pandas as pd
import smt.sampling_methods as samp
from smt.applications.mfk import NestedLHS

import fastoad.api as oad
from fastoad.openmdao.variables import VariableList


@dataclass
class DOEVariable:
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
    sampling_method: str
    variables: List[DOEVariable]
    destination_folder: Union[str, PathLike]
    seed_value: int = 0
    sampling_options: Optional[Dict] = field(
        default=None
    )  # This dict stores the eventual additional options for the chosen sampling method

    def __post_init__(self):
        # Extract the necessary data to congigurate the DOE
        self.variables_binding = [var.id_variable for var in self.variables]
        self.var_names = [var.name for var in self.variables]
        self.var_names_pseudo = [var.name_pseudo for var in self.variables]
        # Exctarct bounds taking into account binding
        seen = set()
        self.bounds = []
        for var in self.variables:
            if var.id_variable not in seen:
                seen.add(var.id_variable)
                self.bounds.append([var.bound_lower, var.bound_upper])
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

    def _print_sampling_info(self):
        pass

    def _write_doe_inputs(self):
        file_name = "DOE_inputs"
        column_names = self.var_names_pseudo
        if self.doe_points_multilevel:
            level_count = len(self.doe_points_multilevel) + 1
            for i, point_list in enumerate(self.doe_points_multilevel):
                # Rearrange columns based on the bounds_binding variable
                doe_points_upd = point_list[:, self.bounds_binding]
                doe_points_df_nest = pd.DataFrame(doe_points_upd, columns=column_names)
                doe_points_df_nest.to_csv(
                    os.path.join(
                        self.destination_folder, file_name + f"_{level_count}D_level{i}" + ".csv"
                    ),
                    index_label="ID",
                    sep=";",
                    quotechar="|",
                )
        else:
            self.doe_points_df.to_csv(
                os.path.join(self.destination_folder, file_name + ".csv"),
                index_label="ID",
                sep=";",
                quotechar="|",
            )

    def generate_doe(self, sample_count, **kwargs) -> List[VariableList]:
        """
        Generates a DOE input using the SMT library for sampling.

        See SMT documentation for DOE options:
        https://smt.readthedocs.io/en/latest/index.html

        :param

        :return: TODO.
        """
        method = self.sampling_method
        level_count = None
        use_level = None
        if kwargs.get("level_count"):
            level_count = kwargs.get("level_count")
            use_level = kwargs.get("use_level")

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
        )  # Use name to create the table, the pseudo is used only if the user want a print
        if level_count:
            self.doe_points_multilevel = doe_points.copy()  # Used for writing
            doe_points = doe_points[use_level]
        doe_points_upd = doe_points[
            :, self.variables_binding
        ]  # Rearrange columns based on the bounds_binding variable
        self.doe_points_df = pd.DataFrame(doe_points_upd, columns=column_names)
        doe_points_dict = self.doe_points_df.to_dict(orient="records")

        return [  # Good format for calc-runner
            oad.VariableList(
                [oad.Variable(var_name, val=var_value) for var_name, var_value in doe_point.items()]
            )
            for doe_point in doe_points_dict
        ]

    def write_output(self):
        pass


# def gen_doe(
#     var_names: list,
#     var_bounds: list,
#     n_samples: int,
#     var_names_pseudo: dict = None,
#     var_bounds_percentage_mode: bool = True,
#     bounds_binding: Optional[list] = None,
#     sampling_method: str = "LHS",
#     level_count: Optional[int] = None,
#     use_level: Optional[int] = None,
#     seed_value: int = 12,
#     folder_path: str = None,
# ) -> list[oad.Variable]:
#     """
#     Generates a DOE input using the SMT library for sampling.

#     See SMT documentation for DOE options:
#     https://smt.readthedocs.io/en/latest/index.html

#     :param var_name: list, names of the input variables used to create the DOE
#     :param var_bounds: list, upper and lower bounds for the DOE in the same order of var_names.
#     If var_bounds_percentage_mode = True, then the format is [mean, percentageDifference]; else is [lowerBound, upperBound]
#     :param n_samples: int, number of sampes generated by the DOE.
#     If sampling_method = "FullFactorial", then n_samples represent the number of samples per input, so that the total number of sampling is n_samples**n_var
#     :param var_names_pseudo: dict, TODO
#     :param folder_path: Path, path in which the DOE .csv is saved
#     :param file_name: str, custom name of the DOE .csv
#     :param var_bounds_percentage_mode: bool, if true the function evaluates the bounds of the variables as a percentage of the given value
#     :param sampling_method: str, "LHS", "FullFactorial", or "Random". SMT sampling method for the DOE generation
#     :param random_state: int, seed number to control random draws for sampling method (set by default to get reproductibility)

#     :return: TODO.
#     """
#     print("\n--------------------")
#     print("-- DOE GENERATION --")
#     print("--------------------\n")

#     if bounds_binding:
#         # Check on the list given
#         max_num = max(bounds_binding)  # Get the maximum number in the list
#         expected_set = set(range(max_num + 1))  # Create set of all numbers from 0 to max_num
#         actual_set = set(bounds_binding)  # Create a set from the list to remove duplicates
#         if not expected_set.issubset(actual_set):
#             raise ValueError(
#                 f"bounds_binding: {bounds_binding} is not a list containing all the int between 0 and n_inputs."
#             )
#         n_inputs = max(bounds_binding) + 1
#         n_var = len(var_names)
#     else:
#         n_inputs = len(var_names)
#         bounds_binding = [i for i in range(n_inputs)]
#         n_var = len(var_names)

#     if var_bounds_percentage_mode:
#         xbounds = []
#         for mean, percentage in var_bounds:
#             reduction = mean - (mean * percentage / 100)  # Reduce mean by percentage
#             increase = mean + (mean * percentage / 100)  # Increase mean by percentage
#             xbounds.append([reduction, increase])
#         xbounds = np.array(xbounds)
#     else:
#         xbounds = []
#         for down, up in var_bounds:
#             if down >= up:
#                 raise ValueError(f"Invalid bounds: ({down}) should not be greater than({up})")
#             xbounds.append([down, up])
#         xbounds = np.array(xbounds)

#     print("--   VARIABLE BOUNDS    --")
#     for i in range(n_var):
#         print(
#             f"Name = {var_names[i]} | Bounds = {xbounds[bounds_binding[i],0]}   {xbounds[bounds_binding[i],1]}"
#         )

#     use_nested = False
#     if sampling_method == "LHS" and level_count:
#         use_nested = True

#     if sampling_method == "LHS":
#         if level_count:
#             sampling = NestedLHS(nlevel=level_count, xlimits=xbounds, random_state=random_state)
#             print("\n-- NESTED LHS SAMPLING --\n")
#         else:
#             sampling = samp.LHS(criterion="ese", random_state=random_state, xlimits=xbounds)
#             print("\n--   LHS SAMPLING   --\n")
#         doe_points = sampling(n_samples)  # do the sampling
#     elif sampling_method == "FullFactorial":
#         n_samples = n_samples**n_inputs
#         sampling = samp.FullFactorial(xlimits=xbounds)
#         doe_points = sampling(n_samples)  # do the sampling
#         print("\n-- FULL FACTORIAL SAMPLING --\n")
#     elif sampling_method == "Random":
#         sampling = samp.Random(
#             xlimits=xbounds,
#             random_state=random_state,
#         )
#         doe_points = sampling(n_samples)  # do the sampling
#         print("\n--   RANDOM SAMPLING   --\n")
#     else:
#         raise ValueError(
#             f"The sampling method {sampling_method} is not existent or not yet implemented."
#         )

#     if var_names_pseudo:
#         column_names = [key for key, val in var_names_pseudo.items()]
#     else:
#         column_names = [var_name for var_name in var_names]
#     if not folder_path:
#         folder_path = Path(__file__).parent
#     if not os.path.exists(folder_path):
#         os.makedirs(folder_path)

#     if use_nested:
#         for i, point_list in enumerate(doe_points):
#             # Rearrange columns based on the bounds_binding variable
#             doe_points_upd = point_list[:, bounds_binding]
#             doe_points_df_nest = pd.DataFrame(doe_points_upd, columns=column_names)
#             doe_points_df_nest.to_csv(
#                 os.path.join(folder_path, file_name + f"_{level_count}D_level{i}" + ".csv"),
#                 index_label="ID",
#                 sep=";",
#             )
#             if i == use_level:
#                 doe_points_df = point_list.copy()
#     else:
#         # Rearrange columns based on the bounds_binding variable
#         doe_points_upd = doe_points[:, bounds_binding]
#         doe_points_df = pd.DataFrame(doe_points_upd, columns=column_names)
#         doe_points_df.to_csv(
#             os.path.join(folder_path, file_name + ".csv"), index_label="ID", sep=";", quotechar="|"
#         )

#     doe_points_dict = doe_points_df.to_dict(orient="records")
#     doe_data = [  # good format for calc-runner
#         oad.VariableList(
#             [oad.Variable(var_name, val=var_value) for var_name, var_value in doe_point.items()]
#         )
#         for doe_point in doe_points_dict
#     ]
#     print("--   DOE GENERATED   --")

#     return doe_data
