.. _calc-runner:

##########
CalcRunner
##########

The :class:`~fastoad.api.CalcRunner` class enables running multiple FAST-OAD
computations (MDA or MDO) in parallel. It is designed for parameter sweeps
and batch evaluations where the same configuration is run with different
input values.

.. note::

    We are actively developing a Design of Experiments (DOE) functionality
    that uses ``CalcRunner`` as its backbone. Stay tuned for updates in
    upcoming releases (see `issue #583
    <https://github.com/fast-aircraft-design/FAST-OAD/issues/583>`_).

.. contents::

*********************
Purpose of CalcRunner
*********************

When designing an aircraft, it is often necessary to evaluate how a change in
one or more input variables affects the overall design. For example, you may
want to sweep the wing aspect ratio over a range of values to understand its
impact on fuel consumption.

``CalcRunner`` provides a convenient way to:

- Run a single computation with on-the-fly input overrides.
- Run many computations concurrently, each with different input values, using
  multiprocessing or MPI.
- Isolate the data of each computation in its own subfolder for easy
  post-processing.


*************************
Step-by-step instructions
*************************

Setting up CalcRunner
=====================

``CalcRunner`` is available in the public API:

.. code:: python

    import fastoad.api as oad

To create a ``CalcRunner`` instance, provide the path to a FAST-OAD
configuration file:

.. code:: python

    runner = oad.CalcRunner(configuration_file_path="my_conf.yml")

You may also specify an alternative input file (overrides the one defined in
the configuration) and choose between MDA (analysis, the default) or MDO
(optimization):

.. code:: python

    runner = oad.CalcRunner(
        configuration_file_path="my_conf.yml",
        input_file_path="my_custom_inputs.xml",
        optimize=False,  # Set to True for MDO
    )


Running a single computation
============================

Use the :meth:`~fastoad.api.CalcRunner.run` method to execute one computation.
You can override specific input values on-the-fly and isolate the data in a
dedicated folder:

.. code:: python

    output_data = runner.run(
        input_values=oad.VariableList(
            [oad.Variable("data:geometry:wing:aspect_ratio", val=12.0)]
        ),
        calculation_folder="./results/ar_12",
    )

The method returns a :class:`~fastoad.api.DataFile` containing the outputs of
the computation.


Running multiple computations in parallel
=========================================

The :meth:`~fastoad.api.CalcRunner.run_cases` method runs several computations
concurrently. You provide a list of :class:`~fastoad.api.VariableList` objects
(one per case) and a destination folder. Each case is stored in a numbered
subfolder (:code:`calc_0`, :code:`calc_1`, …). The subfolder names are
zero-padded based on the total number of cases (e.g. :code:`calc_00` …
:code:`calc_99` when there are more than 9 cases).

.. code:: python

    import fastoad.api as oad

    runner = oad.CalcRunner(configuration_file_path="my_conf.yml")

    # Define the cases to run
    cases = [
        oad.VariableList([oad.Variable("data:geometry:wing:aspect_ratio", val=ar)])
        for ar in [9.0, 10.0, 11.0, 12.0, 13.0]
    ]

    runner.run_cases(
        input_list=cases,
        destination_folder="./results/ar_sweep",
    )

After execution, the results folder will look like::

    results/ar_sweep/
    ├── calc_0/
    │   ├── my_conf.yml
    │   ├── problem_inputs.xml
    │   └── problem_outputs.xml
    ├── calc_1/
    │   ├── ...
    ...

Controlling the number of workers
----------------------------------

By default, all available processors are used. You can limit the number of
parallel workers:

.. code:: python

    # Use exactly 4 workers
    runner.run_cases(
        input_list=cases,
        destination_folder="./results/ar_sweep",
        max_workers=4,
    )

    # Use all available processors except one (useful for keeping your
    # machine responsive)
    runner.run_cases(
        input_list=cases,
        destination_folder="./results/ar_sweep",
        max_workers=-1,
    )


Choosing between multiprocessing and MPI
----------------------------------------

``CalcRunner`` supports both Python multiprocessing and MPI
(via `mpi4py <https://mpi4py.readthedocs.io/>`_). By default, MPI is used
when available. To force the use of multiprocessing:

.. code:: python

    runner.run_cases(
        input_list=cases,
        destination_folder="./results/ar_sweep",
        use_MPI_if_available=False,
    )


Resuming an interrupted batch
-----------------------------

If a batch run is interrupted, you can resume it without recomputing the cases
that already completed. By default, existing subfolders are skipped:

.. code:: python

    # Only cases without an existing subfolder will be computed
    runner.run_cases(
        input_list=cases,
        destination_folder="./results/ar_sweep",
    )

To force re-computation of all cases, set :code:`overwrite_subfolders=True`:

.. code:: python

    runner.run_cases(
        input_list=cases,
        destination_folder="./results/ar_sweep",
        overwrite_subfolders=True,
    )


.. _calc-runner-example:

*************************************
Example: wing aspect ratio sweep
*************************************

The following complete example sweeps the wing aspect ratio from 9 to 18 and
collects the resulting block fuel for each case.

.. code:: python

    import fastoad.api as oad

    # 1. Create the runner
    runner = oad.CalcRunner(configuration_file_path="my_conf.yml")

    # 2. Build the list of cases
    aspect_ratios = [9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0]
    cases = [
        oad.VariableList(
            [oad.Variable("data:geometry:wing:aspect_ratio", val=ar)]
        )
        for ar in aspect_ratios
    ]

    # 3. Run all cases in parallel (using 4 workers)
    runner.run_cases(
        input_list=cases,
        destination_folder="./results/ar_sweep",
        max_workers=4,
    )

    # 4. Collect the results
    results = []
    for i, ar in enumerate(aspect_ratios):
        output = oad.DataFile(f"./results/ar_sweep/calc_{i}/problem_outputs.xml")
        fuel = output["data:mission:sizing:needed_block_fuel"].value[0]
        results.append((ar, fuel))

    for ar, fuel in results:
        print(f"AR = {ar:.1f}  ->  Block fuel = {fuel:.1f} kg")

.. note::

    The variable names used above (e.g. :code:`data:geometry:wing:aspect_ratio`,
    :code:`data:mission:sizing:needed_block_fuel`) depend on the modules
    declared in your configuration file. Use the :code:`fastoad list_variables`
    command to discover the available variables (see :ref:`get-variable-list`).
