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

import logging
import os.path as pth
from logging import FileHandler
from os import mkdir
from shutil import rmtree

import pytest
from fastoad.openmdao.validity_checker import ValidityDomainChecker, ValidityStatus
from fastoad.openmdao.variables import VariableList, Variable

_LOGGER = logging.getLogger(__name__)  # Logger for this module

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(pth.dirname(__file__), "results")


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)
    mkdir(RESULTS_FOLDER_PATH)


def set_logger_file(log_file_path):
    logger = logging.getLogger("main")
    for hdlr in logger.handlers:
        logger.removeHandler(hdlr)

    formatter = logging.Formatter("%(name)s - %(message)s")
    handler = FileHandler(log_file_path)
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def test_register_checks(cleanup):
    ValidityDomainChecker(
        {
            "var_with_upper_and_lower": (-1.0, 10.0),
            "var_with_lower": (-10.0, None),
            "var_with_upper": (None, 5.0),
        },
        "main.logger1",
    )

    # Now registering is done through instantiation, and with another logger
    ValidityDomainChecker(
        {"var_with_upper_and_lower": (-3.0, 5.0), "var_with_lower": (0.0, None)}, "main.logger2"
    )

    # Third call with same logger as the first one
    ValidityDomainChecker({"other_var": (-10.0, 1.0)}, "main.logger1")

    # Check 1 --------------------------------------------------------------------------------------
    log_file_path = pth.join(RESULTS_FOLDER_PATH, "log1.txt")
    set_logger_file(log_file_path)
    variables = VariableList(
        [
            Variable("var_with_upper_and_lower", value=-2.0),  # too low for logger1
            Variable("var_with_lower", value=-1.0),  # too low for logger2
            Variable("var_with_upper", value=10.0),  # too high, only for logger1
            Variable("other_var", value=1.1),  # too high, only for logger1 (second registering)
            Variable("unbound_var", value=42.0),
        ]
    )

    records = ValidityDomainChecker.check_variables(variables)
    assert [
        (
            rec.variable_name,
            rec.status,
            rec.limit_value,
            rec.value,
            rec.source_file,
            rec.logger_name,
        )
        for rec in records
    ] == [
        ("var_with_upper_and_lower", ValidityStatus.TOO_LOW, -1.0, -2.0, __file__, "main.logger1"),
        ("var_with_upper_and_lower", ValidityStatus.OK, None, -2.0, __file__, "main.logger2"),
        ("var_with_lower", ValidityStatus.OK, None, -1.0, __file__, "main.logger1"),
        ("var_with_lower", ValidityStatus.TOO_LOW, 0.0, -1.0, __file__, "main.logger2"),
        ("var_with_upper", ValidityStatus.TOO_HIGH, 5.0, 10.0, __file__, "main.logger1"),
        ("other_var", ValidityStatus.TOO_HIGH, 1.0, 1.1, __file__, "main.logger1"),
    ]

    ValidityDomainChecker.log_records(records)
    with open(log_file_path) as log_file:
        assert len(log_file.readlines()) == 4

    # Check 2 --------------------------------------------------------------------------------------
    log_file_path = pth.join(RESULTS_FOLDER_PATH, "log2.txt")
    set_logger_file(log_file_path)
    variables = VariableList(
        [
            Variable("other_var", value=-11.0),  # too low, only for logger1 (second registering)
            Variable("var_with_lower", value=-15.0),  # too low for logger1 and logger2
            Variable("var_with_upper", value=0.0),  # Ok
            Variable("unbound_var", value=1e42),
            Variable("var_with_upper_and_lower", value=7.0),  # too high for logger2
        ]
    )

    records = ValidityDomainChecker.check_variables(variables)
    assert [
        (
            rec.variable_name,
            rec.status,
            rec.limit_value,
            rec.value,
            rec.source_file,
            rec.logger_name,
        )
        for rec in records
    ] == [
        ("other_var", ValidityStatus.TOO_LOW, -10.0, -11.0, __file__, "main.logger1"),
        ("var_with_lower", ValidityStatus.TOO_LOW, -10.0, -15.0, __file__, "main.logger1"),
        ("var_with_lower", ValidityStatus.TOO_LOW, 0.0, -15.0, __file__, "main.logger2"),
        ("var_with_upper", ValidityStatus.OK, None, 0.0, __file__, "main.logger1"),
        ("var_with_upper_and_lower", ValidityStatus.OK, None, 7.0, __file__, "main.logger1"),
        ("var_with_upper_and_lower", ValidityStatus.TOO_HIGH, 5.0, 7.0, __file__, "main.logger2"),
    ]

    ValidityDomainChecker.log_records(records)
    with open(log_file_path) as log_file:
        assert len(log_file.readlines()) == 4

    # Check 3 --------------------------------------------------------------------------------------
    log_file_path = pth.join(RESULTS_FOLDER_PATH, "log3.txt")
    set_logger_file(log_file_path)
    variables = VariableList(
        [
            Variable("var_with_upper_and_lower", value=1.0),  # Ok
            Variable("other_var", value=-5.0),  # Ok
            Variable("unbound_var", value=-1e42),
            Variable("var_with_lower", value=1.0),  # Ok
        ]
    )

    records = ValidityDomainChecker.check_variables(variables)
    assert [
        (
            rec.variable_name,
            rec.status,
            rec.limit_value,
            rec.value,
            rec.source_file,
            rec.logger_name,
        )
        for rec in records
    ] == [
        ("var_with_upper_and_lower", ValidityStatus.OK, None, 1.0, __file__, "main.logger1"),
        ("var_with_upper_and_lower", ValidityStatus.OK, None, 1.0, __file__, "main.logger2"),
        ("other_var", ValidityStatus.OK, None, -5.0, __file__, "main.logger1"),
        ("var_with_lower", ValidityStatus.OK, None, 1.0, __file__, "main.logger1"),
        ("var_with_lower", ValidityStatus.OK, None, 1.0, __file__, "main.logger2"),
    ]

    ValidityDomainChecker.log_records(records)
    with open(log_file_path) as log_file:
        assert len(log_file.readlines()) == 0
