FAST-OAD: Future Aircraft Sizing Tool - Overall Aircraft Design
###############################################################

FAST-OAD is a framework for performing rapid Overall Aircraft Design. The computational core of FAST-OAD is based on the
`OpenMDAO framework <https://openmdao.org/>`_.

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
OpenMDAO systems. This part is addressed in the
`full developer documentation <https://fast-aircraft-design.github.io/FAST-OAD-doc/>`_.


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
    driver = "om.ScipyOptimizeDriver()"

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
        [model.performance]
            id = "fastoad.performances.breguet.from_owe"
        [model.propulsion]
            id = "fastoad.propulsion.rubber_engine"

    [[design_var]]
        name = "propulsion:MTO_thrust"
        lower = 0
        ref = 1.5e5
        ref0 = 50000

    [[objective]]
        name = "weight:aircraft:MTOW"
        ref = 90000
        ref0 = 60000

    [[constraint]]
        name = "propulsion:thrust_rate"
        lower = 0
        upper = 1

Now in details:

------

.. code:: toml

    module_folders = []

Provides the path where user can have his custom OpenMDAO modules. See section `How to add custom OpenMDAO modules to FAST-OAD`_.

------

.. code:: toml

    input_file = "./problem_inputs.xml"
    output_file = "./problem_outputs.xml"

Specifies the input and output files of the problem. They are defined in the configuration file and DO NOT APPEAR in the command line interface.

------

.. code:: toml

    # Definition of problem driver assuming the OpenMDAO convention "import openmdao.api as om"
    driver = "om.ScipyOptimizeDriver()"

Here we enter in the domain of OpenMDAO. This setting is needed for optimization problems. It is defined as in Python when assuming the OpenMDAO convention "import openmdao.api as om".

For more details, please see the OpenMDAO documentation on `drivers <http://openmdao.org/twodocs/versions/latest/tags/Optimizer.html?highlight=optimizer>`_.

------

.. code:: toml

    [model]
        nonlinear_solver = "om.NonlinearBlockGS(iprint=1, maxiter=100)"
        linear_solver = "om.DirectSolver()"

This is the starting point for defining the model of the problem. The model is a group of components.
If the model involves cycles, which happens for instance when some outputs of A are inputs of B, and vice-versa, it is necessary to specify solvers as done above.

For more details, please see the OpenMDAO documentation on `nonlinear solvers <http://openmdao.org/twodocs/versions/latest/features/building_blocks/solvers/nonlinear/index.html?highlight=solvers>`_ and `linear solvers <http://openmdao.org/twodocs/versions/latest/features/building_blocks/solvers/linear/index.html?highlight=solvers>`_.


------

.. code:: toml

        [model.geometry]
            # An OpenMDAO component is identified by its "id"
            id = "fastoad.geometry.legacy"
        [model.weights]
            id = "fastoad.weights.legacy"
        [model.aerodynamics]
            id = "fastoad.aerodynamics.highspeed.legacy"
        [model.performance]
            id = "fastoad.performances.breguet.from_owe"
        [model.propulsion]
            id = "fastoad.propulsion.rubber_engine"

Components of the model can be systems, or sub-groups. They are defined with a section key like :code:`[model.<some_name>]`. Unlike "model", which is the root element, the name of sub-components can be defined freely by user.

Here above are defined systems. A system is defined by its "id" key. See `How to get list of registered systems`_.

------

.. code:: toml

    [[design_var]]
        name = "propulsion:MTO_thrust"
        lower = 0
        ref = 1.5e5
        ref0 = 50000

Here are defined design variables (relevant only for optimization).
Keys of this section are named after parameters of the OpenMDAO `System.add_design_var() method <http://openmdao.org/twodocs/versions/latest/features/core_features/adding_desvars_objs_consts/adding_desvars.html?highlight=add_design_var>`_

This section can be repeated several times to add as many design variables as necessary.

Also, see `How to get list of variables`_.

------

.. code:: toml

    [[objective]]
        name = "weight:aircraft:MTOW"
        ref = 90000
        ref0 = 60000

Here is defined the objective function (relevant only for optimization).
Keys of this section are named after parameters of the OpenMDAO `System.add_objective() method <http://openmdao.org/twodocs/versions/latest/features/core_features/adding_desvars_objs_consts/adding_objectives.html?highlight=add_objective>`_

Also, see `How to get list of variables`_.

------

.. code:: toml

    [[constraint]]
        name = "propulsion:thrust_rate"
        lower = 0
        upper = 1

Here are defined constraint variables (relevant only for optimization).
Keys of this section are named after parameters of the OpenMDAO `System.add_constraint() method <http://openmdao.org/twodocs/versions/latest/features/core_features/adding_desvars_objs_consts/adding_constraints.html?highlight=add_constraint>`_

This section can be repeated several times to add as many constraint variables as necessary.

Also, see `How to get list of variables`_.

-----

Using FAST-OAD through Command line
===================================
UNDER CONSTRUCTION

The FAST-OAD command is :code:`fastoad`.

    $ fastoad -h

FAST-OAD can provide a ready-to use configuration file with:

    $ fastoad gen_conf_file


How to get list of registered systems
-------------------------------------


    $ fastoad list_systems


How to get list of variables
----------------------------

    $ fastoad list_outputs


Using FAST-OAD through Python
===================================
See Jupyter notebooks

How to add custom OpenMDAO modules to FAST-OAD
==============================================


Note
####

This project has been set up using PyScaffold 3.1. For details and usage
information on PyScaffold see https://pyscaffold.org/.
