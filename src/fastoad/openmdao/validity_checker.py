"""For checking validity domain of OpenMDAO variables."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
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

import inspect
import logging
import uuid
from collections import namedtuple
from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, List
from uuid import UUID

import numpy as np
import openmdao.api as om
from openmdao.utils.units import convert_units

from fastoad.openmdao.variables import VariableList

CheckRecord = namedtuple(
    "CheckRecord",
    [
        "variable_name",
        "status",
        "limit_value",
        "limit_units",
        "value",
        "value_units",
        "source_file",
        "logger_name",
    ],
)
"""
A namedtuple that contains result of one variable check
"""


class ValidityStatus(IntEnum):
    """
    Simple enumeration for validity status.
    """

    OK = 0
    TOO_LOW = -1
    TOO_HIGH = 1


class ValidityDomainChecker:
    """
    Decorator class that checks variable values against limit bounds

    This class aims at producing a status of out of limits variables at the end
    of an OpenMDAO computation.

    The point is to allow to define limit bounds when defining an OpenMDAO
    system, but to make the check on the OpenMDAO problem after the run.

    When defining an OpenMDAO system, use this class as Python decorator to
    define validity domains:

    .. code-block::

        @ValidityDomainChecker
        class MyComponent(om.ExplicitComponent):
            ...

    The above code will check values against lower and upper bounds that have
    been defined when adding OpenMDAO outputs.

    Next code shows how to define lower and upper bounds, for inputs and/or
    outputs.

    .. code-block::

        @ValidityDomainChecker(
            {
                "a:variable:with:two:bounds": (-10.0, 1.0),
                "a:variable:with:lower:bound:only": (0.0, None),
                "a:variable:with:upper:bound:only": (None, 4.2),
            },
        )
        class MyComponent(om.ExplicitComponent):
            ...

    The defined domain limits supersedes lower and upper bounds from
    OpenMDAO output definitions, but only in the frame of ValidityDomainChecker.
    In any case, OpenMDAO process is not affected by usage of ValidityDomainChecker.

    Validity status can be obtained through log messages from Python logging module
    after problem has been run with:

    .. code-block::

        ...
        problem.run_model()
        ValidityDomainChecker.check_problem_variables(problem)

    **Warnings**:
    - Units of limit values defined in ValidityDomainChecker are assumed to be the
      same as in add_input() and add_output() statements of decorated class
    - Validity check currently only applies to scalar values
    """

    _limit_definitions: Dict[UUID, "_LimitDefinitions"] = {}

    def __init__(self, limits: Dict[str, tuple] = None, logger_name: str = None):
        """
        :param limits: a dictionary where keys are variable names and values are two-values tuples
                   that give lower and upper bound. One bound can be set to None.
        :param logger_name: The named of the logger that will be used. If not provided, name of
                        current module (i.e. "__name__"") will be used.
        """
        self._uuid = uuid.uuid4()

        # use given logger name for now. If it is None, it will be replaced by
        # calling module name in __call__ (because I could not find a way to get
        # this module name here with inspect, though it is very easy when we
        # have the decorated class)
        limit_definitions = _LimitDefinitions(self._get_caller_filename(), logger_name)
        for var_name, bounds in limits.items():
            lower = bounds[0] if bounds[0] is not None else -np.inf
            upper = bounds[1] if bounds[1] is not None else np.inf
            limit_definitions[var_name] = _LimitDefinition(lower, upper)

        self._limit_definitions[self._uuid] = limit_definitions

    def __call__(self, om_class: type):
        # Update logger name if needed: if it was not given, module name of
        # decorated class is used.
        if not self._limit_definitions[self._uuid].logger_name:
            self._limit_definitions[self._uuid].logger_name = om_class.__module__

        # We add to the OpenMDAO class a reference to self._limit_definitions[self._uuid]
        # to be able to update it with OpenMDAO declarations after problem setup.
        # See _update_problem_limit_definitions()
        om_class._fastoad_limit_definitions = self._limit_definitions[
            self._uuid
        ]  # pylint: disable=protected-access # We create it
        return om_class

    @classmethod
    def check_problem_variables(cls, problem: om.Problem) -> List[CheckRecord]:
        """
        Checks variable values in provided problem.

        Logs warnings for each variable that is out of registered limits.

        problem.setup() must have been run.

        :param problem:
        :return: the list of checks
        """
        for limit_definitions in cls._limit_definitions.values():
            limit_definitions.activated = False

        cls._update_problem_limit_definitions(problem)

        variables = VariableList.from_problem(problem)
        records = cls.check_variables(variables, activated_only=True)
        cls.log_records(records)
        return records

    @classmethod
    def check_variables(
        cls, variables: VariableList, activated_only: bool = True
    ) -> List[CheckRecord]:
        """
        Check values of provided variables against registered limits.

        :param variables:
        :param activated_only: if True, only activated checkers are considered.
        :return: the list of checks
        """
        records: List[CheckRecord] = []

        for var in variables:
            for limit_definitions in cls._limit_definitions.values():
                if (
                    limit_definitions.activated or not activated_only
                ) and var.name in limit_definitions:
                    limit_def = limit_definitions[var.name]
                    value = convert_units(var.value, var.units, limit_def.units)
                    if np.any(value < limit_def.lower):
                        status = ValidityStatus.TOO_LOW
                        limit = limit_def.lower
                    elif np.any(value > limit_def.upper):
                        status = ValidityStatus.TOO_HIGH
                        limit = limit_def.upper
                    else:
                        status = ValidityStatus.OK
                        limit = None

                    records.append(
                        CheckRecord(
                            var.name,
                            status,
                            limit,
                            limit_def.units,
                            var.value,
                            var.units,
                            limit_definitions.source_file,
                            limit_definitions.logger_name,
                        )
                    )
        return records

    @staticmethod
    def log_records(records: List[CheckRecord]):
        """
        Logs warnings through Python logging module for each CheckRecord in provided list if
        it is not OK.

        :param records:
        :return:
        """
        for record in records:
            if record.status != ValidityStatus.OK:
                logger = logging.getLogger(record.logger_name)
                limit_text = (
                    "under lower" if np.any(record.value < record.limit_value) else "over upper"
                )
                logger.warning(
                    'Variable "%s" out of bound: value %s%s is %s limit ( %s%s ) in file %s',
                    record.variable_name,
                    record.value,
                    " " + record.value_units if record.value_units else "",
                    limit_text,
                    record.limit_value,
                    " " + record.limit_units if record.limit_units else "",
                    record.source_file,
                )

    @classmethod
    def _update_problem_limit_definitions(cls, problem: om.Problem):
        """
        Updates limit definitions using variable declarations of provided OpenMDAO problem.

        Ensures limit definitions of encountered components are activated.

        problem.setup() must have been run.

        :param problem:
        """

        variables = VariableList.from_problem(
            problem, get_promoted_names=False, promoted_only=False
        )

        for var in variables:
            system_path = var.name.split(".")
            system = problem.model
            for system_name in system_path[:-1]:
                system = getattr(system, system_name)
            var_name = system_path[-1]

            if hasattr(system, "_fastoad_limit_definitions"):

                limit_definitions = system._fastoad_limit_definitions
                limit_definitions.activated = True

                if var_name in limit_definitions:
                    # Get units for already defined limits
                    limit_def = limit_definitions[var_name]
                    if limit_def.units is None and var.units is not None:
                        limit_def.units = var.units
                elif "lower" in var.metadata or "upper" in var.metadata:
                    # Get bounds if defined in add_output.
                    lower = var.metadata.get("lower")
                    # lower can be None if it is not found OR if it defined and set to None
                    if lower is None:
                        lower = -np.inf
                    upper = var.metadata.get("upper")
                    # upper can be None if it is not found OR if it defined and set to None
                    if upper is None:
                        upper = np.inf
                    units = var.metadata.get("units")
                    if lower > -np.inf or upper < np.inf:
                        limit_definitions[var_name] = _LimitDefinition(lower, upper, units)

    @staticmethod
    def _get_caller_filename():
        current_frame = inspect.currentframe()
        try:
            frame = inspect.getouterframes(current_frame)[2]
            filename = frame[1]
        finally:
            del current_frame
            del frame

        return filename


@dataclass
class _LimitDefinitions(dict):
    """
    Definition of validity check for one variable.
    """

    source_file: str
    logger_name: str
    activated: bool = False


@dataclass
class _LimitDefinition:
    """
    Definition of one validity domain.

    namedtuple would not do, as we need the possibility to set values (especially
    units) after instantiation.
    """

    lower: float
    upper: float
    units: str = None
