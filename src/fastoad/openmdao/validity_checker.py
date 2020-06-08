"""For checking validity domain of OpenMDAO variables."""
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

import inspect
import logging
import uuid
from collections import namedtuple
from copy import deepcopy
from enum import IntEnum
from typing import Dict, List
from uuid import UUID

import numpy as np
import openmdao.api as om
from fastoad.openmdao.variables import VariableList
from openmdao.utils.units import convert_units

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


class _LimitDefinitions(dict):
    """
    Definition of validity check for one variable
    """

    def __init__(self, source_file, logger_name):
        super().__init__()
        # Where the limit definition has been set
        self.source_file = source_file

        # The chosen logger name
        self.logger_name = logger_name


class _LimitDefinition:
    """
    Definition of validity check for one variable
    """

    # namedtuple would not work, as we need the possibility to set values (especially
    # units) after instantiation.
    # TODO: If we drop Python3.6 support, use a dataclass
    def __init__(self, lower, upper, units=None):
        self.lower = lower
        self.upper = upper
        self.units = units


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
        class MyComponent(om.explicitComponent):
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
        class MyComponent(om.explicitComponent):
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

    _limit_definitions: Dict[UUID, _LimitDefinitions] = {}

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

        self.__class__._limit_definitions[self._uuid] = limit_definitions

    def __call__(self, om_class: type):

        # update logger name if needed: if it was not given, module name of
        # decorated class is used.
        if not self._limit_definitions[self._uuid].logger_name:
            self._limit_definitions[self._uuid].logger_name = om_class.__module__

        # "Ok kid, this is were it gets complicated"
        # We need to do things when setup() is called. Inheritance or decorator
        # pattern would do maybe, but it is safer to return the original (modified)
        # input class (at least for interactions with iPOPO).
        # Therefore, original setup() is renamed and another setup() method is
        # added, that will call the original setup() and do what we need.

        # original setup will be renamed with a name that will be unique
        setup_new_name = "__setup_before_validity_domain_checker_%i" % int(self._uuid)

        # Copy the original method "setup" to "__setup_before_option_decorator_<uuid>"
        setattr(om_class, setup_new_name, om_class.setup)

        # Set the new "setup" method
        checker_id = self._uuid

        def setup(self):
            """Will replace the original setup method."""
            # Ok kid, this is where it gets maybe too complicated...
            # We need to get variables of the current OpenMDAO instance.
            # This is done with VariableList.from_system() which we know does
            # setup() on a copy of given instance (not much choice to be sure
            # from_system() will work also for Group instances)
            # But by doing this, it will call this setup() and be stuck in an
            # infinite recursion.
            # So we create a copy of current instance where we put back the
            # original setup so we can safely use VariableList.from_system()
            original_self = deepcopy(self)
            setattr(original_self, "setup", getattr(original_self, setup_new_name))
            variables = VariableList.from_system(original_self)

            # Now update limit definition
            limit_definitions = ValidityDomainChecker._limit_definitions[checker_id]
            for var in variables:
                if var.name in limit_definitions:
                    # Get units for already defined limits
                    limit_def = limit_definitions[var.name]
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
                        limit_definitions[var.name] = _LimitDefinition(lower, upper, units)

            # Now run original setup that has been moved to setup_new_name
            getattr(self, setup_new_name)()

        om_class.setup = setup

        return om_class

    @classmethod
    def check_problem_variables(cls, problem: om.Problem):
        """
        Checks variable values in provided problem and logs warnings for each variable
        that is out of registered limits.

        :param problem:
        :return:
        """
        variables = VariableList.from_problem(problem)
        records = cls.check_variables(variables)
        cls.log_records(records)

    @classmethod
    def check_variables(cls, variables: VariableList) -> List[CheckRecord]:
        """
        Check values of provided variables against registered limits.

        :param variables:
        :return: a list of CheckRecord instances
        """
        records: List[CheckRecord] = []

        for var in variables:
            for limit_definitions in cls._limit_definitions.values():
                if var.name in limit_definitions:
                    limit_def = limit_definitions[var.name]
                    value = convert_units(var.value, var.units, limit_def.units)
                    if value < limit_def.lower:
                        status = ValidityStatus.TOO_LOW
                        limit = limit_def.lower
                    elif value > limit_def.upper:
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
                limit_text = "under lower" if record.value < record.limit_value else "over upper"
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
