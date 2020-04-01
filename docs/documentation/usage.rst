.. _Usage:

Usage
############
FAST-OAD uses a configuration file for defining your OAD problem. You can
interact with this problem using command line or Python directly.

You may also use some lower-level features of FAST-OAD to interact with
OpenMDAO systems. This part is addressed in the
:ref:`full developer documentation<fastoad>`.


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
        nonlinear_solver = "om.NonlinearBlockGS(maxiter=100)"
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

Provides the path where user can have his custom OpenMDAO modules. See section :ref:`Add-modules`.

------

.. code:: toml

    input_file = "./problem_inputs.xml"
    output_file = "./problem_outputs.xml"

Specifies the input and output files of the problem. They are defined in the configuration file and DO NOT APPEAR in the command line interface.

------

.. code:: toml

    # Definition of problem driver assuming the OpenMDAO convention "import openmdao.api as om"
    driver = "om.ScipyOptimizeDriver()"

This belongs the domain of the OpenMDAO framework and its utilization. This setting is needed for optimization problems. It is defined as in Python when assuming the OpenMDAO convention :code:`import openmdao.api as om`.

For more details, please see the OpenMDAO documentation on `drivers <http://openmdao.org/twodocs/versions/latest/tags/Optimizer.html?highlight=optimizer>`_.

------

.. code:: toml

    [model]
        nonlinear_solver = "om.NonlinearBlockGS(maxiter=100)"
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

Here above are defined systems. A system is defined by its "id" key. See :ref:`Get-system-list`.

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

Also, see :ref:`Get-variable-list`.

------

.. code:: toml

    [[objective]]
        name = "weight:aircraft:MTOW"
        ref = 90000
        ref0 = 60000

Here is defined the objective function (relevant only for optimization).
Keys of this section are named after parameters of the OpenMDAO `System.add_objective() method <http://openmdao.org/twodocs/versions/latest/features/core_features/adding_desvars_objs_consts/adding_objectives.html?highlight=add_objective>`_

Also, see :ref:`Get-variable-list`.

------

.. code:: toml

    [[constraint]]
        name = "propulsion:thrust_rate"
        lower = 0
        upper = 1

Here are defined constraint variables (relevant only for optimization).
Keys of this section are named after parameters of the OpenMDAO `System.add_constraint() method <http://openmdao.org/twodocs/versions/latest/features/core_features/adding_desvars_objs_consts/adding_constraints.html?highlight=add_constraint>`_

This section can be repeated several times to add as many constraint variables as necessary.

Also, see :ref:`Get-variable-list`.

-----

Using FAST-OAD through Command line
===================================

FAST-OAD can be used through shell command line or Python. This section deals with the shell command line, but
if you prefer using Python, you can skip this part and go to :ref:`Python-usage`.

The FAST-OAD command is :code:`fastoad`. Inline help is available with:

.. code:: bash

    $ fastoad -h

`fastoad` works through sub-commands. Each sub-command provides its own
inline help using

.. code:: bash

    $ fastoad <sub-command> -h


.. _Generate-conf-file:

How to generate a configuration file
-------------------------------------

FAST-OAD can provide a ready-to use configuration file with:

.. code:: bash

    $ fastoad gen_conf my_conf.toml

This generates the file `my_conf.toml`


.. _Get-system-list:

How to get list of registered systems
-------------------------------------

If you want to change the list of components in the model in the configuration file,
you need the list of available systems.

List of FAST-OAD systems can be obtained with:

.. code:: bash

    $ fastoad list_systems

If you added custom systems in your configuration file `my_conf.toml`
(see `how to add custom OpenMDAO modules to FAST-OAD<Add modules>`),
they can be listed along FAST-OAD systems with:

.. code:: bash

    $ fastoad list_systems my_conf.toml


.. _Get-variable-list:

How to get list of variables
----------------------------

Once your problem is defined in `my_conf.toml`, you can get a list of the variables of
your problem with:

.. code:: bash

    $ fastoad list_variables my_conf.toml


.. _Generate-input-file:

How to generate an input file
-----------------------------

The name of the input file is defined in your configuration file `my_conf.toml`.
This input file can be generated with:

.. code:: bash

    $ fastoad gen_inputs my_conf.toml

The generated file will be an XML file that contains needed inputs for your problem.
Values will be the default values from system definitions, which means several ones
will be "nan". Actual value must be filled before the process is run.

If you already have a file that contains these values, you can use it to populate
your new input files with:

.. code:: bash

    $ fastoad gen_inputs my_conf.toml my_ref_values.xml

If you are using the configuration file provided by the gen_conf sub-command (see :ref`Generate conf file`), you may download our `CeRAS01_baseline.xml <https://github.com/fast-aircraft-design/FAST-OAD/raw/v0.1a/src/fastoad/notebooks/tutorial/data/CeRAS01_baseline.xml>`_ and use it as source for generating your input file.


.. _Run-problem:

How to run the problem
----------------------

Once your problem is defined in `my_conf.toml`, you can simply run it with:

.. code:: bash

    $ fastoad eval my_conf.toml

*Note: this is equivalent to OpenMDAO's run_model()*


You can also run the defined optimization with:

.. code:: bash

    $ fastoad optim my_conf.toml

*Note: this is equivalent to OpenMDAO's run_driver()*


.. _Python-usage:

Using FAST-OAD through Python
===================================
The command line interface can generate Jupyter notebooks that show how to
use the high-level interface of FAST-OAD.

To do so, type this command **in your terminal**:

.. code:: bash

    $ fastoad notebooks

Then run the Jupyter server as indicated in the obtained message.

