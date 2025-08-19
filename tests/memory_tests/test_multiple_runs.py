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

import gc
import os.path as pth
import tracemalloc
from os import makedirs
from shutil import rmtree

import openmdao.api as om
import pytest

import fastoad.api as oad

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(
    pth.dirname(__file__), "results", pth.splitext(pth.basename(__file__))[0]
)


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)
    makedirs(RESULTS_FOLDER_PATH)


def print_stat_diffs(snapshot1, snapshot2):
    stats = snapshot2.compare_to(snapshot1, "lineno")
    for stat in stats:
        if "options_dictionary" in stat.traceback._frames[0][0]:
            break


def print_memory_state(tag):
    memory = om.convert_units(
        tracemalloc.get_traced_memory()[0] - tracemalloc.get_tracemalloc_memory(), "byte", "Mibyte"
    )
    print(f"{tag:50}:", f"{memory:.3f}MiB")
    return memory


def run_problem():
    configurator = oad.FASTOADProblemConfigurator(pth.join(DATA_FOLDER_PATH, "oad_process.yml"))
    configurator.input_file_path = pth.join(RESULTS_FOLDER_PATH, "inputs.xml")
    configurator.output_file_path = pth.join(RESULTS_FOLDER_PATH, "outputs.xml")
    print_memory_state("After reading configuration file")

    ref_inputs = pth.join(DATA_FOLDER_PATH, "CeRAS01.xml")
    configurator.write_needed_inputs(ref_inputs)
    print_memory_state("After writing input file")

    problem = configurator.get_problem(read_inputs=True)
    print_memory_state("After building problem")

    problem.setup()
    print_memory_state("After problem setup")

    problem.run_model()
    print_memory_state("After problem run")

    problem.write_outputs()


def test_runs(cleanup):
    tracemalloc.start()

    snapshot0 = tracemalloc.take_snapshot()
    print()
    print_memory_state("start")

    count = 2
    for i in range(count):
        print(f"RUN {i + 1}/{count}")
        run_problem()

    print_memory_state("Before garbage collector")
    gc.collect()
    final_memory = print_memory_state("Final state")

    snapshot1 = tracemalloc.take_snapshot()
    stats = snapshot1.compare_to(snapshot0, "lineno")
    for stat in stats[:10]:
        print(stat)

    assert final_memory < 5
    tracemalloc.stop()
