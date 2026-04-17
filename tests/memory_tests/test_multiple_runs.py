#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2022 ONERA & ISAE-SUPAERO
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

import gc
import tracemalloc
from pathlib import Path
from shutil import rmtree

import openmdao.api as om
import pytest

import fastoad.api as oad

DATA_FOLDER_PATH = Path(__file__).parent / "data"
RESULTS_FOLDER_PATH = Path(__file__).parent / "results" / Path(__file__).stem

MEMORY_GROWTH_THRESHOLD = 30.0  # MiB - This threshold is somewhat arbitrary and may need adjustment


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)
    RESULTS_FOLDER_PATH.mkdir(parents=True, exist_ok=True)


def print_memory_state(tag: str) -> float:
    """Print current memory usage and return it in MiB"""
    current, peak = tracemalloc.get_traced_memory()
    # Subtract tracemalloc overhead
    memory = om.convert_units(current - tracemalloc.get_tracemalloc_memory(), "byte", "Mibyte")
    print(f"{tag:50}: {memory:.3f} MiB (peak: {om.convert_units(peak, 'byte', 'Mibyte'):.3f} MiB)")
    return memory


def run_problem() -> None:
    """Run a single FASTOAD problem instance"""
    configurator = oad.FASTOADProblemConfigurator(DATA_FOLDER_PATH / "oad_process.yml")
    configurator.input_file_path = RESULTS_FOLDER_PATH / "inputs.xml"
    configurator.output_file_path = RESULTS_FOLDER_PATH / "outputs.xml"

    print_memory_state("After reading configuration file")

    ref_inputs = DATA_FOLDER_PATH / "CeRAS01.xml"
    configurator.write_needed_inputs(ref_inputs)
    print_memory_state("After writing input file")

    problem = configurator.get_problem(read_inputs=True)
    print_memory_state("After building problem")

    problem.setup()
    print_memory_state("After problem setup")

    problem.run_model()
    print_memory_state("After problem run")

    problem.write_outputs()
    print_memory_state("After problem outputs")

    # Explicit cleanup attempts
    problem.cleanup()

    # Delete references
    del problem
    del configurator


def test_memory_leak_between_runs(cleanup):
    """Check that repeated runs do not retain large amounts of traced memory."""
    tracemalloc.start()

    try:
        print()
        baseline_memory = print_memory_state("Baseline")
        retained_memories: list[float] = []

        for run_number in range(2):
            print(f"\nRun {run_number + 1}/2")
            run_problem()

            gc.collect()
            retained_memory = print_memory_state(f"After run {run_number + 1}") - baseline_memory
            retained_memories.append(retained_memory)

        memory_growth = retained_memories[-1] - retained_memories[0]

        print(f"Retained traced memory after runs: {retained_memories}")

        assert memory_growth <= MEMORY_GROWTH_THRESHOLD, (
            f"Retained traced memory grew by {memory_growth:.3f} MiB between runs, "
            f"which exceeds {MEMORY_GROWTH_THRESHOLD} MiB"
        )

    finally:
        tracemalloc.stop()
