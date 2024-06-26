.. _add-modules:

##############################################
How to add custom OpenMDAO modules to FAST-OAD
##############################################

With FAST-OAD, you can register any OpenMDAO system of your own so it can be
used through the configuration file.

It is therefore strongly advised to have at least a basic knowledge of
:doc:`OpenMDAO <openmdao:main>` to develop a module for FAST-OAD.

To have your OpenMDAO system available as a FAST-OAD module, you should follow these steps:

.. contents::
   :local:
   :depth: 1

***************************
Create your OpenMDAO system
***************************

It can be a :doc:`Group  <openmdao:features/core_features/working_with_groups/main>`
or a :doc:`Component  <openmdao:features/building_blocks/components/components>`-like class
(generally an :doc:`ExplicitComponent <openmdao:features/core_features/working_with_components/explicit_component>`).

You can create the Python file at the location of your choice. You will just have to provide later the folder path in
FAST-OAD configuration file (see :ref:`add-modules-set-configuration-files`).

Variable naming
===============
You have to pay attention to the naming of your input and output variables.
As FAST-OAD uses the :doc:`promotion system of OpenMDAO <openmdao:basic_user_guide/multidisciplinary_optimization/linking_vars>`,
which means that variables you want to link to the rest of the process must have
the name that is given in the global process.

Nevertheless, you can create new variables for your system:

- Outputs of your system will be available in output file and will be usable as any other variable.
- Unconnected inputs will simply have to be in the input file of the process. They will be automatically included in the
  input file generated by FAST-OAD (see :ref:`generate-input-file`).
- And if you add more than one system to the FAST-OAD process, outputs created by one of your system can of course be
  used as inputs by other systems.

Also keep in mind that the naming of your variable will decide of its location in the input and output files.
Therefore, the way you name your new variables should be consistent with FAST-OAD convention, as explained in
:ref:`variables`.

Defining options
================
You may use the OpenMDAO way for adding :doc:`options to your system <openmdao:features/core_features/options/options>`.
The options you add will be accessible from the FAST-OAD configuration file (see
:ref:`configuration-file-problem-definition`).

When declaring an option, the usage of the :code:`desc` field if strongly advised, as any description
you provide will be printed along with module information with the
:code:`list_modules` sub-command (see :ref:`get-module-list`).


Definition of partial derivatives
=================================
Your OpenMDAO system is expected to provide partial derivatives for all its outputs in analytic or approximate way.

At the very least, for most Component classes, the :code:`setup()` method of your class should contain:

.. code-block:: python

    self.declare_partials("*", "*", method='fd')

or for a Group class:

.. code-block:: python

    self.approx_totals()

The two lines above are the most generic and the least CPU-efficient ways of declaring partial derivatives. For better
efficiency, see how to :doc:`work with derivatives in OpenMDAO  <openmdao:features/core_features/working_with_derivatives/main>`.

About ImplicitComponent classes
===============================
In some cases, you may have to use :doc:`ImplicitComponent  <openmdao:features/core_features/working_with_components/implicit_component>`
classes.

Just remember, as told in :doc:`this tutorial <openmdao:advanced_user_guide/models_implicit_components/models_with_solvers_implicit>`,
that the loop that will allow to solve it needs usage of the :doc:`Newton solver <features/building_blocks/solvers/newton>`.

A good way to ensure it is to build a Group class that will solve the ImplicitComponent with NewtonSolver. This Group
should be the system you will register in FAST-OAD.

The CycleGroup class
====================
FAST-OAD comes with the :class:`~fastoad.model_base.openmdao.group.CycleGroup` class, a convenience
class that allows to define groups with inner solvers.


This class allows to standardize options that control the usage of solvers, so they can be set easily
in the configuration file using the :ref:`model_options <configuration-model-options>` feature.

Using this class, a group that contains inner solvers can be defined this way:

.. code-block:: python

    import fastoad.api as oad

    class SimpleCycleGroup(
        oad.CycleGroup,
    # A simple subclassing is equivalent to setting these attributes:
    #    use_solvers_by_default = True,
    #    default_linear_solver = "om.DirectSolver",
    #    default_nonlinear_solver = "om.NonlinearBlockGS",
    #    default_linear_options={},
    #    default_nonlinear_options={},
    ):

        def initialize():
            super().initialize() # Mandatory if initialize() is defined
            ...

        def setup():
            super().setup() # Also mandatory

            self.add_subsystem(...)
            ...

It is also possible to further customize class arguments like so:

.. code-block:: python

    import fastoad.api as oad

    class CustomizedCycleGroup(
        oad.CycleGroup,
        use_solvers_by_default=False,
        # Solvers are defined using the `import openmdao.api as om` convention
        default_linear_solver="om.ScipyKrylov",
        default_nonlinear_solver="om.NewtonSolver",
        default_linear_options={"iprint": 0},
        default_nonlinear_options={"rtol": 1.0e-4},
    ):
        def setup(self):
            super().setup()

            self.add_subsystem(...)
            ...


In the configuration file, the solvers in CycleGroup classes can be controlled with:

.. code-block:: yaml

    model_options:
        "first_loop.*": # a more or less restrictive pattern could be used
            # This line deactivates the solvers for CycleGroup-derived classes.
            # This can be useful to rely only on higher level solver(s).
            use_inner_solvers : False
        "second_loop.*":
            # This line activates the solvers for CycleGroup-derived classes,
            # even for group derived from CycleGroup with 'use_solvers_by_default=False'
            # The default solver classes defined for each group are used.
            use_inner_solvers : True
            # These lines show how to define solver options.
            linear_solver_options:
                iprint:0
                rtol: 1.e-5
            nonlinear_solver_options:
                iprint:0
                rtol: 1.e-5
        "third_loop.some_component.*":
            # These lines show how to activate and choose the solvers for CycleGroup-derived classes.
            use_inner_solvers : True
            linear_solver : "om.LinearBlockGS"
            nonlinear_solver : "om.NonlinearBlockJac"





Checking validity domains
=========================
Generally, models are valid only when variable values are in given ranges.

OpenMDAO provides a way to specify lower and upper bounds of an output variable and to enforce them
when using a Newton solver by using :doc:`backtracking line searches <openmdao:features/building_blocks/solvers/bounds_enforce>`.

FAST-OAD proposes a way to set lower and upper bounds for input and output variables, but only
for checking and giving feedback of variables that would be out of bounds.

If you want your OpenMDAO class to do this checking, simply use the decorator ValidityDomainChecker:

.. code-block:: python

    @ValidityDomainChecker
    class MyComponent(om.ExplicitComponent):
        def setup(self):
            self.add_input("length", 1., units="km" )
            self.add_input("time", 1., units="h" )
            self.add_output("speed", 1., units="km/h", lower=0., upper=130.)

The above code make that FAST-OAD will issue a warning if at the end of the computation,
"speed" variable is not between lower and upper bound.

But it is possible to set your own bounds outside of OpenMDAO by following this example:

.. code-block:: python

    @ValidityDomainChecker(
        {
            "length": (0.1, None),  # Defines only a lower bound
            "time": (0., 1.),  # Defines lower and upper bounds
            "speed": (None, 150.0),  # Ignores original bounds and sets only upper bound
        }
    )
    class MyComponent(om.ExplicitComponent):
        def setup(self):
            self.add_input("length", 1., units="km" )
            self.add_input("time", 1., units="h" )
            # Bounds that are set here will still apply if backtracking line search is used, but
            # will not be used for validity domain checking because it has been replaced above
            self.add_output("speed", 1., units="km/h", lower=0., upper=130.)




.. _add-modules-register-systems:

***********************
Register your system(s)
***********************

Once your OpenMDAO system is ready, you have to register it to make it known as a FAST-OAD module.

To do that, you just have to add the :class:`~fastoad.module_management.service_registry.RegisterOpenMDAOSystem`
decorator to your OpenMDAO class like this:

.. code-block:: python

    import fastoad.api as oad
    import openmdao.api as om

    @oad.RegisterOpenMDAOSystem("my.custom.name")
    class MyOMClass(om.ExplicitComponent):
        [ ... ]

.. note::

    If you work with Jupyter notebook, remember that any change in your Python files
    will require the kernel to be restarted.

.. _add-modules-set-configuration-files:

*****************************
Modify the configuration file
*****************************

The folders that contain your Python files must be listed in :code:`module_folders`
in the :ref:`configuration-file`:

.. code-block:: yaml

    title: OAD Process with custom component

    # List of folder paths where user added custom registered OpenMDAO components
    module_folders:
      - /path/to/my/custom/module/folder
      - /another/path/

    [ ... ]

Once this is done, (assuming your configuration file is named :code:`my_custom_conf.yml`)
your custom, registered, module should appear in the list provided by the command line:

.. code:: shell-session

      $ fastoad list_modules my_custom_conf.yml


Then your component can be used like any other using the id you have given.

.. code-block:: yaml

    # Definition of OpenMDAO model
    model:
      [ ... ]

      my_custom_model:
        id: "my.custom.name"

      [ ... ]

.. Note::

    FAST-OAD will inspect all sub-folders in a specified module folder,
    **as long as they are Python packages**, i.e. if they contain a
    :code:`__init__.py` file.

