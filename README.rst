FAST-OAD: Future Aircraft Sizing Tool - Overall Aircraft Design
###############################################################

FAST-OAD is a framework for performing rapid Overall Aircraft Design. The computational core of FAST-OAD is based on the  [OpenMDAO framework](https://openmdao.org/).

.. contents::

Install
############
**Prerequisite**:FAST-OAD needs Python 3.6 or 3.7.

Since FAST-OAD is not officially released, you can install the latest version with this command:

.. code:: bash

    $ pip install git+https://github.com/fast-aircraft-design/FAST-OAD.git@latest

At the prompt, enter your Github credentials.




Usage
############
FAST-OAD uses a configuration file for defining your OAD problem. You can
interact with this problem using command line or Python directly.

You may also use some lower-level features of FAST-OAD to interact with
OpenMDAO systems. This part is addressed in the full developer documentation
(link to dev doc)


The FAST-OAD configuration file
===============================
FAST-OAD configuration files are in `TOML format <https://github.com/toml-lang/toml#toml>`_.

.. code:: toml

    title = "Sample OAD Process"

    # List of folder paths where user added custom registered OpenMDAO components
    module_folders = []

    # Input and output files
    input_file = "./problem_inputs.xml"
    output_file = "./problem_outputs.xml"

    # Definition of problem driver assuming the OpenMDAO convention "import openmdao.api as om"
    driver = "om.ScipyOptimizeDriver(optimizer='SLSQP', tol=1e-8)"

    # Definition of OpenMDAO model
    [model]
        # Solvers are defined assuming the OpenMDAO convention "import openmdao.api as om"
        nonlinear_solver = "om.NonlinearBlockGS(iprint=1, maxiter=100)"
        linear_solver = "om.DirectSolver()"

        # Though "model" is a mandatory name for the top level of the model, sublevels can be freely named by user
        [model.geometry]
            # An OpenMDAO component is identified by its "id"
            id = "fastoad.geometry.legacy"
        [model.weights]
            id = "fastoad.weights.legacy"
        [model.aerodynamics]
            id = "fastoad.aerodynamics.highspeed.legacy"

        # subgroups are defined by added a hierarchy level
        [model.perfo_loop]
            # Solvers for the subgroup are defined the same way as the main group
            nonlinear_solver = "om.NonlinearBlockGS(iprint=1)"
            linear_solver = "om.DirectSolver()"
            [model.perfo_loop.performance]
                id = "fastoad.performances.breguet.from_owe"
            [model.propulsion]
                id = "fastoad.propulsion.rubber_engine"


Using FAST-OAD through Command line
===================================
The FAST-OAD command is :code:`fastoad`.

    $ fastoad -h

FAST-OAD can provide a ready-to use configuration file with:

    $ fastoad gen_conf_file

toto


Using FAST-OAD through Python
===================================
See Jupyter notebooks




Note
####

This project has been set up using PyScaffold 3.1. For details and usage
information on PyScaffold see https://pyscaffold.org/.
