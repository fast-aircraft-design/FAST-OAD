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

***************************
FAST-OAD configuration file
***************************
FAST-OAD configuration files are in `YAML <https://yaml.org>`_  format.
A quick tutorial for YAML (among many ones) is available
`here <https://www.cloudbees.com/blog/yaml-tutorial-everything-you-need-get-started/>`_


.. code:: yaml

    title: Sample OAD Process

    # List of folder paths where user added custom registered OpenMDAO components
    module_folders:

    # Input and output files
    input_file: ./problem_inputs.xml
    output_file: ./problem_outputs.xml

    # Definition of problem driver assuming the OpenMDAO convention "import openmdao.api as om"
    driver: om.ScipyOptimizeDriver(tol=1e-2, optimizer='COBYLA')

    # Definition of OpenMDAO model
    # Although "model" is a mandatory name for the top level of the model, its
    # sub-components can be freely named by user
    model:

      #  Solvers are defined assuming the OpenMDAO convention "import openmdao.api as om"
      nonlinear_solver: om.NonlinearBlockGS(maxiter=100, atol=1e-2)
      linear_solver: om.DirectSolver()


      # Components can be put in sub-groups
      subgroup:

        # A group can be set with its own solvers.
        # Uncomment the 2 next lines for using the performance module with "mission_file_path: ::sizing_mission"
        #nonlinear_solver: om.NonlinearBlockGS(maxiter=100, atol=1e-2, iprint=0)
        #linear_solver: om.DirectSolver()

        geometry:
          # An OpenMDAO component is identified by its "id"
          id: fastoad.geometry.legacy
        weight:
          id: fastoad.weight.legacy
        mtow:
          id: fastoad.mass_performances.compute_MTOW
        hq_tail_sizing:
          id: fastoad.handling_qualities.tail_sizing
        hq_static_margin:
          id: fastoad.handling_qualities.static_margin
        wing_position:
          id: fastoad.loop.wing_position
        aerodynamics_highspeed:
          id: fastoad.aerodynamics.highspeed.legacy
        aerodynamics_lowspeed:
          id: fastoad.aerodynamics.lowspeed.legacy
        aerodynamics_takeoff:
          id: fastoad.aerodynamics.takeoff.legacy
        aerodynamics_landing:
          id: fastoad.aerodynamics.landing.legacy
          use_xfoil: false
      performance:
        id: fastoad.performances.mission
        propulsion_id: fastoad.wrapper.propulsion.rubber_engine
        mission_file_path: ::sizing_breguet
        # mission_file_path: ::sizing_mission  # Activate solvers in "subgroup" if you use this line.
        out_file: ./flight_points.csv
        adjust_fuel: true
        is_sizing: true
      wing_area:
        id: fastoad.loop.wing_area

    optimization: # This section is needed only if optimization process is run
      design_variables:
        - name: data:geometry:wing:aspect_ratio
          lower: 9.0
          upper: 18.0
      constraints:
        - name: data:geometry:wing:span
          upper: 60.0
      objective:
        - name: data:mission:sizing:needed_block_fuel
          scaler: 1.e-4



Now in details:

Custom module path
==================

.. code:: yaml

    module_folders:

Provides the path where user can have his custom OpenMDAO modules. See section :ref:`add-modules`.

Input and output files
======================

.. code:: yaml

    input_file: ./problem_inputs.xml
    output_file: ./problem_outputs.xml

Specifies the input and output files of the problem. They are defined in the configuration file
and DO NOT APPEAR in the command line interface.

Problem driver
==============

.. code:: yaml

    driver: om.ScipyOptimizeDriver(tol=1e-2, optimizer='COBYLA')

This belongs the domain of the OpenMDAO framework and its utilization. This setting is needed for
optimization problems. It is defined as in Python when assuming the OpenMDAO convention
:code:`import openmdao.api as om`.

For more details, please see the OpenMDAO documentation on `drivers <http://openmdao.org/twodocs/versions/latest/features/building_blocks/drivers/index.html>`_.

Solvers
=======

.. code:: yaml

    model:
      nonlinear_solver: om.NonlinearBlockGS(maxiter=100, atol=1e-2)
      linear_solver: om.DirectSolver()

This is the starting point for defining the model of the problem. The model is a group of
components. If the model involves cycles, which happens for instance when some outputs of A are
inputs of B, and vice-versa, it is necessary to specify solvers as done above.

For more details, please see the OpenMDAO documentation on
`nonlinear solvers <http://openmdao.org/twodocs/versions/latest/features/building_blocks/solvers/nonlinear/index.html>`_
and `linear solvers <http://openmdao.org/twodocs/versions/latest/features/building_blocks/solvers/linear/index.html>`_.


.. _configuration-file-problem-definition:

Problem definition
==================

.. code:: yaml

      # Components can be put in sub-groups
      subgroup:

        # A group can be set with its own solvers.
        # Uncomment the 2 next lines for using the performance module with "mission_file_path: ::sizing_mission"
        #nonlinear_solver: om.NonlinearBlockGS(maxiter=100, atol=1e-2, iprint=0)
        #linear_solver: om.DirectSolver()

        geometry:
          # An OpenMDAO component is identified by its "id"
          id: fastoad.geometry.legacy
        weight:
          id: fastoad.weight.legacy
        mtow:
          id: fastoad.mass_performances.compute_MTOW
        hq_tail_sizing:
          id: fastoad.handling_qualities.tail_sizing
        hq_static_margin:
          id: fastoad.handling_qualities.static_margin
        wing_position:
          id: fastoad.loop.wing_position
        aerodynamics_highspeed:
          id: fastoad.aerodynamics.highspeed.legacy
        aerodynamics_lowspeed:
          id: fastoad.aerodynamics.lowspeed.legacy
        aerodynamics_takeoff:
          id: fastoad.aerodynamics.takeoff.legacy
        aerodynamics_landing:
          id: fastoad.aerodynamics.landing.legacy
          use_xfoil: false
      performance:
        id: fastoad.performances.mission
        propulsion_id: fastoad.wrapper.propulsion.rubber_engine
        mission_file_path: ::sizing_breguet
        # mission_file_path: ::sizing_mission  # Activate solvers in "subgroup" if you use this line.
        out_file: ./flight_points.csv
        adjust_fuel: true
        is_sizing: true
      wing_area:
        id: fastoad.loop.wing_area

Components of the model can be modules, or sub-groups. They are defined as a sub-section of
:code:`model:`. Sub-sections and sub-components can be freely named by user.

A module is defined by its :code:`id:` key, but additional keys can be
used, depending on the options of the module. The list of available options of a module is
available through the :code:`list_modules` sub-command (see :ref:`get-module-list`).

A sub-group can be set with its own solvers to resolve cycles it may contains.

Here above, a sub-group with geometric, weight, handling-qualities and aerodynamic modules is defined.
Performance and wing area computation modules are set apart.


Optimization settings
=====================
This settings are used only when using optimization (see :ref:`run-problem-optim`). They are
ignored when doing analysis (see :ref:`run-problem-eval`).

The section is identified by:

.. code:: yaml

    optimization:


Design variables
----------------

.. code:: yaml

      design_var:
        - name: data:geometry:wing:MAC:at25percent:x
          lower: 16.0
          upper: 18.0

Here are defined design variables (relevant only for optimization).
Keys of this section are named after parameters of the OpenMDAO
`System.add_design_var() method <http://openmdao.org/twodocs/versions/latest/features/core_features/adding_desvars_objs_consts/adding_desvars.html?highlight=add_design_var>`_

Several design variables can be defined.

Also, see :ref:`get-variable-list`.

Objective function
------------------

.. code:: yaml

      objective:
        - name: data:mission:sizing:fuel

Here is defined the objective function (relevant only for optimization).
Keys of this section are named after parameters of the OpenMDAO
`System.add_objective() method <http://openmdao.org/twodocs/versions/latest/features/core_features/adding_desvars_objs_consts/adding_objectives.html?highlight=add_objective>`_

Only one objective variable can be defined.

Also, see :ref:`get-variable-list`.

Constraints
-----------

.. code:: yaml

      constraint:
        - name: data:handling_qualities:static_margin
          lower: 0.05
          upper: 0.1

Here are defined constraint variables (relevant only for optimization).
Keys of this section are named after parameters of the OpenMDAO `System.add_constraint() method <http://openmdao.org/twodocs/versions/latest/features/core_features/adding_desvars_objs_consts/adding_constraints.html?highlight=add_constraint>`_

Several constraint variables can be defined.

Also, see :ref:`get-variable-list`.


.. _usage-cli:

***********************************
Using FAST-OAD through Command line
***********************************

FAST-OAD can be used through shell command line or Python. This section deals with the shell command line, but
if you prefer using Python, you can skip this part and go to :ref:`python-usage`.

The FAST-OAD command is :code:`fastoad`. Inline help is available with:

.. code:: shell-session

    $ fastoad -h

`fastoad` works through sub-commands. Each sub-command provides its own
inline help using

.. code:: shell-session

    $ fastoad <sub-command> -h


.. _generate-conf-file:

How to generate a configuration file
====================================

FAST-OAD can provide a ready-to use configuration file with:

.. code:: shell-session

    $ fastoad gen_conf my_conf.yml

This generates the file `my_conf.yml`


.. _get-module-list:

How to get list of registered modules
=====================================

If you want to change the list of components in the model in the configuration file,
you need the list of available modules.

List of FAST-OAD modules can be obtained with:

.. code:: shell-session

    $ fastoad list_modules

If you added custom modules in your configuration file :code:`my_conf.yml`
(see :ref:`how to add custom OpenMDAO modules to FAST-OAD<add-modules>`),
they can be listed along FAST-OAD modules with:

.. code:: shell-session

    $ fastoad list_modules my_conf.yml

You may also use the :code:`--verbose` option to get detailed information on each module, including
the available options, if any.

.. _get-variable-list:

How to get list of variables
============================

Once your problem is defined in `my_conf.yml`, you can get a list of the variables of
your problem with:

.. code:: shell-session

    $ fastoad list_variables my_conf.yml


.. _generate-input-file:

How to generate an input file
=============================

The name of the input file is defined in your configuration file `my_conf.yml`.
This input file can be generated with:

.. code:: shell-session

    $ fastoad gen_inputs my_conf.yml

The generated file will be an XML file that contains needed inputs for your problem.
Values will be the default values from module definitions, which means several ones
will be "nan". Actual value must be filled before the process is run.

If you already have a file that contains these values, you can use it to populate
your new input files with:

.. code:: shell-session

    $ fastoad gen_inputs my_conf.yml my_ref_values.xml

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

.. code:: shell-session

    $ fastoad n2 my_conf.yml

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

.. code:: shell-session

    $ fastoad xdsm my_conf.yml

*Note: it may take a couple of minutes*

.. _run-problem:

How to run the problem
======================

.. _run-problem-eval:

Run Multi-Disciplinary Analysis
-------------------------------

Once your problem is defined in `my_conf.yml`, you can simply run it with:

.. code:: shell-session

    $ fastoad eval my_conf.yml

*Note: this is equivalent to OpenMDAO's run_model()*


.. _run-problem-optim:

Run Multi-Disciplinary Optimization
-----------------------------------

You can also run the defined optimization with:

.. code:: shell-session

    $ fastoad optim my_conf.yml

*Note: this is equivalent to OpenMDAO's run_driver()*


.. _python-usage:

*****************************
Using FAST-OAD through Python
*****************************
The command line interface can generate Jupyter notebooks that show how to
use the high-level interface of FAST-OAD.

To do so, type this command **in your terminal**:

.. code:: shell-session

    $ fastoad notebooks

Then run the Jupyter server as indicated in the obtained message.

