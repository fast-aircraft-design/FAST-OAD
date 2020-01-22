###############################################################
FAST-OAD: Future Aircraft Sizing Tool - Overall Aircraft Design
###############################################################

FAST-OAD is a framework for performing rapid Overall Aircraft Design. The computational core of FAST-OAD is based on the
`OpenMDAO framework <https://openmdao.org/>`_.

.. sectnum::

.. contents::

Install
############
**Prerequisite**:FAST-OAD needs at least **Python 3.6** (usage of **Python 3.8.*** is discouraged as Jupyter notebooks are still `not compatible with it <https://github.com/jupyterlab/jupyterlab/issues/6487>`_).

It is recommended (but not required) to install FAST-OAD in a virtual environment (`conda <https://docs.conda.io/en/latest/>`_, `venv <https://docs.python.org/3.7/library/venv.html>`_...)

Once Python is installed, FAST-OAD can be installed using pip.

    **Note**: If your network uses a proxy, you may have to do `some settings <https://pip.pypa.io/en/stable/user_guide/#using-a-proxy-server>`_ for pip to work correctly

Until FAST-OAD is publicly released, the installation process must rely on GitHub
instead of PyPI. Therefore, you have 2 ways to install it:

With Git installed
==================
You can install the latest version with this command:

.. code:: bash

    $ pip install git+https://github.com/fast-aircraft-design/FAST-OAD.git@latest

At the prompt, enter your GitHub credentials.

Without Git installed
=====================
Please download this tarball: `<https://github.com/fast-aircraft-design/FAST-OAD/archive/latest.zip>`_

Unzip it in the location of your choice, then do:

.. code:: bash

   $ pip install -e <location/of/FAST-OAD-latest/>


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

This belongs the domain of the OpenMDAO framework and its utilization. This setting is needed for optimization problems. It is defined as in Python when assuming the OpenMDAO convention "import openmdao.api as om".

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

FAST-OAD can be used through shell command line or Python. This section deals with the shell command line, but
if you prefer using Python, you can skip this part and go to `Using FAST-OAD through Python`_.

The FAST-OAD command is :code:`fastoad`. Inline help is available with:

.. code:: bash

    $ fastoad -h

`fastoad` works through sub-commands. Each sub-command provides its own
inline help using

.. code:: bash

    $ fastoad <sub-command> -h


How to generate a configuration file
-------------------------------------

FAST-OAD can provide a ready-to use configuration file with:

.. code:: bash

    $ fastoad gen_conf my_conf.toml

This generates the file `my_conf.toml`

How to get list of registered systems
-------------------------------------

If you want to change the list of components in the model in the configuration file,
you need the list of available systems.

List of FAST-OAD systems can be obtained with:

.. code:: bash

    $ fastoad list_systems

If you added custom systems in your configuration file `my_conf.toml`
(see `How to add custom OpenMDAO modules to FAST-OAD`_),
they can be listed along FAST-OAD systems with:

.. code:: bash

    $ fastoad list_systems my_conf.toml

How to get list of variables
----------------------------

Once your problem is defined in `my_conf.toml`, you can get a list of the variables of
your problem with:

.. code:: bash

    $ fastoad list_variables my_conf.toml

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
    
If you are using the configuration file provided by the gen_conf sub-command (see `How to generate a configuration file`_), you may dowload our `CeRAS01_baseline.xml <https://github.com/fast-aircraft-design/FAST-OAD/raw/v0.1a/src/fastoad/notebooks/tutorial/data/CeRAS01_baseline.xml>`_ and use it as source for generating your input file.

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

Using FAST-OAD through Python
===================================
The command line interface can generate Jupyter notebooks that show how to
use the high-level interface of FAST-OAD.

To do so, type this command **in your terminal**:

.. code:: bash

    $ fastoad notebooks

Then run the Jupyter server as indicated in the obtained message.


How to add custom OpenMDAO modules to FAST-OAD
==============================================
With FAST-OAD, you can register any OpenMDAO system of your own so it can be
used though the configuration file.

To have your OpenMDAO system available in FAST-OAD, requirements are:

- You have to pay attention to the naming of your input and output variables.
  As FAST-OAD uses the `promotion system of OpenMDAO <http://openmdao.org/twodocs/versions/latest/basic_guide/promote_vs_connect.html?highlight=promote>`_,
  which means that variables you want to link to the rest of the process must have
  the name that is given in the global process. The names of variables are available
  using the command line (see `How to get list of variables`_).
- Your system must be registered. Assuming your OpenMDAO class is named `MyOMClass`
  in `myclass.py`, you can create in the same folder the file `register.py` with following lines:

  .. code-block:: python

    from myclass import MyOMClass
    from fastoad import OpenMDAOSystemFactory

    OpenMDAOSystemFactory.register_system(MyOMClass, 'my.custom.name')

- The folder that contains these Python files must be listed in `module_folders`
  in the configuration file

  .. code-block:: TOML

    title = "OAD Process with custom component"

    # List of folder paths where user added custom registered OpenMDAO components
    module_folders = ["/path/to/my/custom/module/folder"]

  Once this is done, your custom system should appear in the list provided by the
  command:

  .. code:: bash

      $ fastoad list_systems my_custom_conf.toml

  (assuming your configuration file is named `my_custom_conf.toml` )

Then your component can be used like any other using the id you have given.

.. code-block:: TOML

    # Definition of OpenMDAO model
    [model]
        [ ... ]

        [model.my_custom_model]
            id = "my.custom.name"

        [ ... ]


Note
####

This project has been set up using PyScaffold 3.1. For details and usage
information on PyScaffold see https://pyscaffold.org/.
