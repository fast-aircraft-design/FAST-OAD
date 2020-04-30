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

import openmdao.api as om
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


def test_register_checks_instantiation(cleanup):
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
            Variable("var_with_upper_and_lower", value=-2.0, units="m"),  # too low for logger1
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


def test_register_checks_as_decorator(cleanup):
    log_file_path = pth.join(RESULTS_FOLDER_PATH, "log4.txt")
    set_logger_file(log_file_path)

    @ValidityDomainChecker({"input1": (1.0, 5.0), "output2": (300.0, 500.0)}, "main.dec")
    class Comp1(om.ExplicitComponent):
        def setup(self):
            self.add_input("input1", 0.5, units="km")
            self.add_output("output1", 150.0, units="km/h", upper=130.0)
            self.add_output("output2", 200.0, units="K", lower=0.0)
            self.add_output("output3", 1000.0, units="kg", lower=0.0, upper=5000.0)

    comp = Comp1()

    # Just checking there is no side effect. VariableList.from_system() uses
    # setup(), even if it is made to have no effect, and ValidityDomainChecker
    # modifies setup(), so is is worth checking.
    variables = VariableList.from_system(comp)
    assert len(variables) == 4

    # Now for the real test
    # We test that upper and lower bounds are retrieved from OpenMDAO component,
    # overwritten when required and that units are correctly taken into account.
    comp.setup()

    variables = VariableList(
        [
            Variable("input1", value=3.0, units="m"),
            Variable("output1", value=40.0, units="m/s"),
            Variable("output2", value=310.0, units="degC"),
            Variable("output3", value=6.0, units="t"),
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
        ("input1", ValidityStatus.TOO_LOW, 1.0, 3.0, __file__, "main.dec"),
        ("output1", ValidityStatus.TOO_HIGH, 130.0, 40.0, __file__, "main.dec"),
        ("output2", ValidityStatus.TOO_HIGH, 500.0, 310.0, __file__, "main.dec"),
        ("output3", ValidityStatus.TOO_HIGH, 5000.0, 6.0, __file__, "main.dec"),
    ]

    ValidityDomainChecker.log_records(records)
    with open(log_file_path) as log_file:
        assert len(log_file.readlines()) == 4
