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
import os.path as pth
import tracemalloc
from os import makedirs
from shutil import rmtree
from typing import List, Tuple

import openmdao.api as om
import pytest

import fastoad.api as oad

DATA_FOLDER_PATH = pth.join(pth.dirname(__file__), "data")
RESULTS_FOLDER_PATH = pth.join(
    pth.dirname(__file__), "results", pth.splitext(pth.basename(__file__))[0]
)

# Memory leak threshold in MiB
MEMORY_DIFF_THRESHOLD = 20.0
MEMORY_DIFF_THRESHOLD_AVG = 10.0
FINAL_MEMORY_THRESHOLD = 20.0


@pytest.fixture(scope="module")
def cleanup():
    rmtree(RESULTS_FOLDER_PATH, ignore_errors=True)
    makedirs(RESULTS_FOLDER_PATH)


def print_memory_state(tag: str) -> float:
    """Print current memory usage and return it in MiB"""
    current, peak = tracemalloc.get_traced_memory()
    # Subtract tracemalloc overhead
    memory = om.convert_units(current - tracemalloc.get_tracemalloc_memory(), "byte", "Mibyte")
    print(f"{tag:50}: {memory:.3f} MiB (peak: {om.convert_units(peak, 'byte', 'Mibyte'):.3f} MiB)")
    return memory


def get_top_memory_stats(
    snapshot1: tracemalloc.Snapshot, snapshot2: tracemalloc.Snapshot, limit: int = 5
):
    """Get top memory consuming lines between two snapshots"""
    stats = snapshot2.compare_to(snapshot1, "lineno")
    print(f"\nTop {limit} memory consuming lines:")
    for i, stat in enumerate(stats[:limit]):
        print(f"  {i + 1}. {stat}")


def run_problem() -> None:
    """Run a single FASTOAD problem instance"""
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
    print_memory_state("After problem outputs")

    # Explicit cleanup attempts
    try:
        problem.cleanup()  # If available in OpenMDAO
    except AttributeError:
        pass

    # Delete references
    del problem
    del configurator


def test_memory_leak_between_runs(cleanup):
    """Test that memory usage between runs doesn't exceed threshold"""
    tracemalloc.start(5)

    try:
        snapshot_start = tracemalloc.take_snapshot()
        print()
        baseline_memory = print_memory_state("Baseline")

        memory_measurements: List[Tuple[int, float]] = []
        run_snapshots = []

        run_count = 10

        for i in range(run_count):
            print(f"\n{'=' * 60}")
            print(f"RUN {i + 1}/{run_count}")
            print(f"{'=' * 60}")

            pre_run_memory = print_memory_state(f"Before run {i + 1}")

            # Take snapshot before run
            pre_snapshot = tracemalloc.take_snapshot()

            # Run the problem
            run_problem()

            post_run_memory = print_memory_state(f"After run {i + 1}")

            # Take snapshot after run
            post_snapshot = tracemalloc.take_snapshot()
            run_snapshots.append((pre_snapshot, post_snapshot))

            # Calculate memory difference for this run
            run_memory_diff = post_run_memory - pre_run_memory
            memory_measurements.append((i + 1, run_memory_diff))

            print(f"Memory difference for run {i + 1}: {run_memory_diff:.3f} MiB")

            # Analyze memory changes for this specific run
            print(f"\nTop memory changes during run {i + 1}:")
            top_stats = post_snapshot.compare_to(pre_snapshot, "lineno")
            for j, stat in enumerate(top_stats[:5]):  # Show top 5 changes
                size_diff = stat.size_diff / 1024 / 1024  # Convert to MiB
                print(f"  {j + 1}. {size_diff:+.3f} MiB | {stat.traceback.format()[-1].strip()}")
                if j == 0 and abs(size_diff) > 1.0:  # Show full traceback for largest change
                    print("     Full traceback:")
                    for line in stat.traceback.format():
                        print(f"       {line.strip()}")

            # Check if this run exceeded positive threshold
            if run_memory_diff > MEMORY_DIFF_THRESHOLD:
                print(
                    f"\nWARNING: Run {i + 1} memory difference ({run_memory_diff:.3f} MiB) "
                    f"exceeds threshold ({MEMORY_DIFF_THRESHOLD} MiB)"
                )
        # Final analysis
        print(f"\n{'=' * 60}")
        print("MEMORY ANALYSIS SUMMARY")
        print(f"{'=' * 60}")

        gc.collect()

        final_memory = print_memory_state("Final state (after garbage collection)")
        final_diff = final_memory - baseline_memory

        print("\nMemory measurements per run:")
        for run_num, diff in memory_measurements:
            status = "PASS" if abs(diff) <= MEMORY_DIFF_THRESHOLD else "FAIL"
            print(f"  Run {run_num}: {diff:+.3f} MiB [{status}]")

        print(f"\nOverall memory increase (after garbage collection): {final_diff:.3f} MiB")

        # Overall memory analysis from start to finish
        print("\nOverall top memory changes (start to finish):")
        final_snapshot = tracemalloc.take_snapshot()
        overall_stats = final_snapshot.compare_to(snapshot_start, "lineno")
        for i, stat in enumerate(overall_stats[:8]):
            size_diff = stat.size_diff / 1024 / 1024
            count_diff = stat.count_diff
            print(
                f"  {i + 1}. {size_diff:+.3f} MiB ({count_diff:+d} blocks) | "
                f"{stat.traceback.format()[-1].strip()}"
            )

        # Cross-run memory leak detection
        if len(memory_measurements) >= 2:
            print("\nMemory leak analysis:")
            positive_diffs = [
                diff for _, diff in memory_measurements if diff > 0.1
            ]  # Only significant positive diffs
            if len(positive_diffs) >= 2:
                avg_increase = sum(positive_diffs) / len(positive_diffs)
                print(f"  Average memory increase per run: {avg_increase:.3f} MiB")
                if avg_increase > MEMORY_DIFF_THRESHOLD * 0.5:
                    print("  WARNING: Potential memory leak detected - consistent growth pattern")

        max_diff = max([mem for _, mem in memory_measurements])

        # Assert that no single run exceeds the threshold
        assert max_diff <= MEMORY_DIFF_THRESHOLD, (
            f"Memory difference between runs exceeded threshold: "
            f"{max_diff:.3f} MiB > {MEMORY_DIFF_THRESHOLD} MiB"
        )

        # Assert that the average doesn't exceeds the threshold
        assert avg_increase <= MEMORY_DIFF_THRESHOLD_AVG, (
            f"Average memory increase between runs exceeded threshold: "
            f"{avg_increase:.3f} MiB > {MEMORY_DIFF_THRESHOLD_AVG} MiB"
        )

        # Assert that final memory is reasonable
        assert (
            final_memory < FINAL_MEMORY_THRESHOLD
        ), f"Final memory usage too high: {final_memory:.3f} MiB > {FINAL_MEMORY_THRESHOLD} MiB"

    finally:
        tracemalloc.stop()


# def test_runs_original(cleanup):
#     """Original test for backward compatibility"""
#     tracemalloc.start()
#     snapshot0 = tracemalloc.take_snapshot()
#     print()
#     print_memory_state("start")

#     count = 2
#     for i in range(count):
#         print(f"RUN {i + 1}/{count}")
#         run_problem()

#     print_memory_state("Before garbage collector")
#     gc.collect()
#     final_memory = print_memory_state("Final state")

#     snapshot1 = tracemalloc.take_snapshot()
#     stats = snapshot1.compare_to(snapshot0, "lineno")
#     for stat in stats[:10]:
#         print(stat)

#     assert final_memory < 5
#     tracemalloc.stop()


# # Additional utility functions for CI/CD integration


# def create_memory_report(
#     memory_measurements: List[Tuple[int, float]], baseline: float, final: float
# ) -> str:
#     """Create a formatted memory report for CI/CD logs"""
#     report = []
#     report.append("MEMORY USAGE REPORT")
#     report.append("=" * 50)
#     report.append(f"Baseline memory: {baseline:.3f} MiB")
#     report.append(f"Final memory: {final:.3f} MiB")
#     report.append(f"Overall change: {final - baseline:+.3f} MiB")
#     report.append("")
#     report.append("Per-run memory changes:")

#     for run_num, diff in memory_measurements:
#         status = "PASS" if abs(diff) <= MEMORY_DIFF_THRESHOLD else "FAIL"
#         report.append(f"  Run {run_num}: {diff:+.3f} MiB [{status}]")

#     return "\n".join(report)


# @pytest.mark.parametrize("run_count", [2, 3, 5])
# def test_memory_scaling(cleanup, run_count):
#     """Test memory usage with different numbers of runs"""
#     tracemalloc.start()

#     try:
#         baseline = print_memory_state("Baseline")
#         memory_diffs = []

#         for i in range(run_count):
#             pre_memory = print_memory_state(f"Pre-run {i+1}")
#             run_problem()
#             gc.collect()
#             post_memory = print_memory_state(f"Post-run {i+1}")
#             memory_diffs.append(post_memory - pre_memory)

#         # Check that memory growth is not accelerating
#         if len(memory_diffs) >= 2:
#             # Memory growth should be relatively stable
#             growth_variance = max(memory_diffs) - min(memory_diffs)
#             assert (
#                 growth_variance < MEMORY_DIFF_THRESHOLD
#             ), f"Memory growth variance too high: {growth_variance:.3f} MiB"

#     finally:
#         tracemalloc.stop()
