.. _usage:

######
Usage
######
FAST-OAD uses a configuration file for defining your OAD problem. You can
interact with this problem using command line or Python directly.

You may also use some lower-level features of FAST-OAD to interact with
OpenMDAO systems. This part is addressed in the :ref:`API documentation<fastoad>`.

.. contents::

.. _configuration-file:

*******************************
The FAST-OAD configuration file
*******************************
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

        # Although "model" is a mandatory name for the top level of the model, its sub-components can be freely named by user
        [model.geometry]
            # An OpenMDAO component is identified by its "id"
            id = "fastoad.geometry.legacy"
        [model.weight]
            id = "fastoad.weight.legacy"
        [model.aerodynamics.highspeed]
            id = "fastoad.aerodynamics.highspeed.legacy"
        [model.aerodynamics.landing]
            id = "fastoad.aerodynamics.landing.legacy"
            use_xfoil = false
        [model.performance]
            id = "fastoad.performances.breguet"
        [model.propulsion]
            id = "fastoad.propulsion.rubber_engine"
        [model.hq.tail_sizing]
            id = "fastoad.handling_qualities.tail_sizing"
        [model.hq.static_margin]
            id = "fastoad.handling_qualities.static_margin"
            target = 0.05
        [model.loop]
            id = "fastoad.loop.wing_area"

    [optimization]
        [[optimization.design_var]]
            name = "data:geometry:wing:MAC:at25percent:x"
            lower = 10.0
            upper = 25.0
            ref = 15.0

        [[optimization.design_var]]
            name = "data:geometry:wing:aspect_ratio"
            lower = 6.0
            upper = 12.0

        [[optimization.constraint]]
            name = "data:geometry:wing:span"
            upper = 35.0

        [[optimization.objective]]
            name = "data:handling_qualities:static_margin:to_target"

Now in details:

Custom module path
==================

.. code:: toml

    module_folders = []

Provides the path where user can have his custom OpenMDAO modules. See section :ref:`add-modules`.

Input and output files
======================

.. code:: toml

    input_file = "./problem_inputs.xml"
    output_file = "./problem_outputs.xml"

Specifies the input and output files of the problem. They are defined in the configuration file and DO NOT APPEAR in the command line interface.

Problem driver
==============

.. code:: toml

    # Definition of problem driver assuming the OpenMDAO convention "import openmdao.api as om"
    driver = "om.ScipyOptimizeDriver()"

This belongs the domain of the OpenMDAO framework and its utilization. This setting is needed for optimization problems. It is defined as in Python when assuming the OpenMDAO convention :code:`import openmdao.api as om`.

For more details, please see the OpenMDAO documentation on `drivers <http://openmdao.org/twodocs/versions/latest/features/building_blocks/drivers/index.html>`_.

Solvers
=======

.. code:: toml

    [model]
        nonlinear_solver = "om.NonlinearBlockGS(maxiter=100)"
        linear_solver = "om.DirectSolver()"

This is the starting point for defining the model of the problem. The model is a group of components.
If the model involves cycles, which happens for instance when some outputs of A are inputs of B, and vice-versa, it is necessary to specify solvers as done above.

For more details, please see the OpenMDAO documentation on `nonlinear solvers <http://openmdao.org/twodocs/versions/latest/features/building_blocks/solvers/nonlinear/index.html>`_ and `linear solvers <http://openmdao.org/twodocs/versions/latest/features/building_blocks/solvers/linear/index.html>`_.


Problem definition
==================

.. code:: toml

        [model.geometry]
            # An OpenMDAO component is identified by its "id"
            id = "fastoad.geometry.legacy"
        [model.weight]
            id = "fastoad.weight.legacy"
        [model.aerodynamics.highspeed]
            id = "fastoad.aerodynamics.highspeed.legacy"
        [model.aerodynamics.landing]
            id = "fastoad.aerodynamics.landing.legacy"
            use_xfoil = false
        [model.performance]
            id = "fastoad.performances.breguet"
        [model.propulsion]
            id = "fastoad.propulsion.rubber_engine"
        [model.hq.tail_sizing]
            id = "fastoad.handling_qualities.tail_sizing"
        [model.hq.static_margin]
            id = "fastoad.handling_qualities.static_margin"
            target = 0.05
        [model.loop]
            id = "fastoad.loop.wing_area"

Components of the model can be systems, or sub-groups. They are defined with a
section key like :code:`[model.<some_name>]`. Unlike "model", which is the root
element, the name of sub-components can be defined freely by user.

Here above are defined systems. A system is defined by its "id" key. See
:ref:`get-system-list`.

Optimization settings
=====================
This settings are used only when using optimization (see :ref:`run-problem-optim`). They are ignored when doing
analysis (see :ref:`run-problem-eval`)

Design variables
----------------

.. code:: toml

    [[optimization.design_var]]
        name = "propulsion:MTO_thrust"
        lower = 0
        ref = 1.5e5
        ref0 = 50000

Here are defined design variables (relevant only for optimization).
Keys of this section are named after parameters of the OpenMDAO `System.add_design_var() method <http://openmdao.org/twodocs/versions/latest/features/core_features/adding_desvars_objs_consts/adding_desvars.html?highlight=add_design_var>`_

This section can be repeated several times to add as many design variables as necessary.

Also, see :ref:`get-variable-list`.

Objective function
------------------

.. code:: toml

    [[optimization.objective]]
        name = "weight:aircraft:MTOW"
        ref = 90000
        ref0 = 60000

Here is defined the objective function (relevant only for optimization).
Keys of this section are named after parameters of the OpenMDAO `System.add_objective() method <http://openmdao.org/twodocs/versions/latest/features/core_features/adding_desvars_objs_consts/adding_objectives.html?highlight=add_objective>`_

Also, see :ref:`get-variable-list`.

Constraints
-----------

.. code:: toml

    [[optimization.constraint]]
        name = "propulsion:thrust_rate"
        lower = 0
        upper = 1

Here are defined constraint variables (relevant only for optimization).
Keys of this section are named after parameters of the OpenMDAO `System.add_constraint() method <http://openmdao.org/twodocs/versions/latest/features/core_features/adding_desvars_objs_consts/adding_constraints.html?highlight=add_constraint>`_

This section can be repeated several times to add as many constraint variables as necessary.

Also, see :ref:`get-variable-list`.


.. _usage-cli:

***********************************
Using FAST-OAD through Command line
***********************************

FAST-OAD can be used through shell command line or Python. This section deals with the shell command line, but
if you prefer using Python, you can skip this part and go to :ref:`python-usage`.

The FAST-OAD command is :code:`fastoad`. Inline help is available with:

.. code:: bash

    $ fastoad -h

`fastoad` works through sub-commands. Each sub-command provides its own
inline help using

.. code:: bash

    $ fastoad <sub-command> -h


.. _generate-conf-file:

How to generate a configuration file
====================================

FAST-OAD can provide a ready-to use configuration file with:

.. code:: bash

    $ fastoad gen_conf my_conf.toml

This generates the file `my_conf.toml`


.. _get-system-list:

How to get list of registered systems
=====================================

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


.. _get-variable-list:

How to get list of variables
============================

Once your problem is defined in `my_conf.toml`, you can get a list of the variables of
your problem with:

.. code:: bash

    $ fastoad list_variables my_conf.toml


.. _generate-input-file:

How to generate an input file
=============================

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


.. _view-problem:

How to view the problem process
===============================

FAST-OAD proposes two graphical ways to look at the problem defined in configuration
file.
This is especially useful to see how models and variables are connected.

.. _n2_diagram:

N2 diagram
----------

FAST-OAD can use OpenMDAO to create a `N2 diagram <http://openmdao.org/twodocs/versions/latest/features/model_visualization/n2_basics.html>`_.
It provides in-depth information about the whole process.

You can create a :code:`n2.html` file with:

.. code:: bash

    $ fastoad n2 my_conf.toml

.. _xdsm_diagram:

XDSM
----

Using `WhatsOpt <https://github.com/OneraHub/WhatsOpt>`_ as web service, FAST-OAD
can provide a `XDSM <http://mdolab.engin.umich.edu/content/xdsm-overview>`_.

XDSM offers a more synthetic view than N2 diagram.

As it uses a web service, see `WhatsOpt documentation <https://github.com/OneraHub/WhatsOpt-Doc>`_
for how to gain access to the online WhatsOpt server,
or see `WhatsOpt developer documentation <https://whatsopt.readthedocs.io/en/latest/install/>`_ to
run your own server.

You can create a :code:`xdsm.html` file with:

.. code:: bash

    $ fastoad xdsm my_conf.toml

*Note: it may take a couple of minutes*

.. _run-problem:

How to run the problem
======================

.. _run-problem-eval:

Run Multi-Disciplinary Analysis
-------------------------------

Once your problem is defined in `my_conf.toml`, you can simply run it with:

.. code:: bash

    $ fastoad eval my_conf.toml

*Note: this is equivalent to OpenMDAO's run_model()*


.. _run-problem-optim:

Run Multi-Disciplinary Optimization
-----------------------------------

You can also run the defined optimization with:

.. code:: bash

    $ fastoad optim my_conf.toml

*Note: this is equivalent to OpenMDAO's run_driver()*


.. _python-usage:

*****************************
Using FAST-OAD through Python
*****************************
The command line interface can generate Jupyter notebooks that show how to
use the high-level interface of FAST-OAD.

To do so, type this command **in your terminal**:

.. code:: bash

    $ fastoad notebooks

Then run the Jupyter server as indicated in the obtained message.

