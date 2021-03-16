.. _add-propulsion-module:

#################################################
How to add a custom propulsion model to FAST-OAD
#################################################

Propulsion models have a specific status because they are directly called by
the performance models, so the connection is not done through OpenMDAO.

By following instructions in this page, you should ensure your propulsion model
will run smoothly with the existing performance models. You will also be able
to access your engine parameters through FAST-OAD process.

*********************
The FlightPoint class
*********************

The :class:`~fastoad.base.flight_point.FlightPoint` class is designed to store
flight parameters for one flight point.

It is meant to be the class that performance modules will work with, and that
will be exchanged with propulsion models.

FlightPoint class is meant for:

    - storing all needed parameters that are needed for performance modelling,
      including propulsion parameters.
    - easily exchanging data with pandas DataFrame.
    - being extensible for new parameters.

.. note::

    All parameters in FlightPoint instances are expected to be in SI units.

Available flight parameters
===========================
The documentation of :class:`~fastoad.base.flight_point.FlightPoint` provides
the list of available flight parameters, available as attributes.
As FlightPoint is a dataclass, this list is available through Python using::

    >>> from fastoad.base.flight_point import FlightPoint
    >>> from dataclasses import fields

    >>> [f.name for f in fields(FlightPoint)]

Exchanges with pandas DataFrame
===============================
A pandas DataFrame can be generated from a list of FlightPoint instances::

    >>> import pandas as pd
    >>> from fastoad.base.flight_point import FlightPoint

    >>> fp1 = FlightPoint(mass=70000., altitude=0.)
    >>> fp2 = FlightPoint(mass=60000., altitude=10000.)
    >>> df = pd.DataFrame([fp1, fp2])

And FlightPoint instances can be created from DataFrame rows::

    # Get one FlightPoint instance from a DataFrame row
    >>> fp1bis = FlightPoint.create(df.iloc[0])

    # Get a list of FlightPoint instances from the whole DataFrame
    >>> flight_points = FlightPoint.create_list(df)


.. _flight_point_extensibility:

Extensibility
=============
FlightPoint class is bundled with several fields that are commonly used in trajectory
assessment, but one might need additional fields.

Python allows to add attributes to any instance at runtime, but for FlightPoint to run
smoothly, especially when exchanging data with pandas, you have to work at class level.
This can be done using :meth:`add_field`, preferably outside of any class or function::

    # Adds a float field with None as default value
    >>> FlightPoint.add_field("ion_drive_power")

    # Adds a field and define its type and default value
    >>> FlightPoint.add_field("warp", annotation_type=int, default_value=9)

    # Now these fields can be used at instantiation
    >>> fp = FlightPoint(ion_drive_power=110.0, warp=12)

    # Removes a field, even an original one (useful only to avoid having it in outputs)
    >>> FlightPoint.remove_field("sfc")

*************************
The IPropulsion interface
*************************

When developing your propulsion model, to ensure that it will work smoothly
with current performances models, you have to do it in a class that
implements the :class:`~fastoad.models.propulsion.propulsion.IPropulsion`
interface, meaning your class must have at least the 2 methods
:meth:`~fastoad.models.propulsion.propulsion.IPropulsion.compute_flight_points`
and :meth:`~fastoad.models.propulsion.propulsion.IPropulsion.get_consumed_mass`.

Computation of propulsion data
==============================
:meth:`~fastoad.models.propulsion.propulsion.IPropulsion.compute_flight_points`
will modify the provided flight point(s) by adding propulsion-related parameters.
A conventional fuel engine will rely on parameters like :code:`mach`,
:code:`altitude` and will provide parameters like :code:`sfc` (Specific Fuel
Consumption).

Propulsion model inputs
-----------------------

For your model to work with current performance models, your model is expected
to rely on known flight parameters, i.e. the original parameters of
:class:`~fastoad.base.flight_point.FlightPoint`.

.. note::

    Special attention has to be paid to the **thrust parameters**. Depending on the
    flight phase, the aircraft can fly in **manual** mode, with an imposed thrust
    rate, or in **regulated** mode, where propulsion has to give an imposed thrust.
    Your model has to provide these two modes, and to use them as intended.

    The :code:`thrust_is_regulated` parameter tells what mode is on. If it is True,
    the model has to rely on the :code:`thrust` parameter. If it False, the model has to
    rely on the :code:`thrust_rate` parameter.


Propulsion model outputs
------------------------

If you work with the Breguet module, your model has to compute the
:code:`sfc` parameter.

But if you use the mission module, you have total freedom about the output of
your model. If you want to use a parameter that is not available, you can add
it to the FlightPoint class as described
:ref:`above <flight_point_extensibility>`.

The only requirement is that you have to implement
:meth:`~fastoad.models.propulsion.propulsion.IPropulsion.get_consumed_mass`
accordingly for the mission module to have a correct assessment of mass
evolution.

Computation of consumed mass
============================
The :meth:`~fastoad.models.propulsion.propulsion.IPropulsion.get_consumed_mass`
simply provides the mass consumption over the provided time.
It is meant to use the parameters computed in
:meth:`~fastoad.models.propulsion.propulsion.IPropulsion.compute_flight_points`.


********************
The OpenMDAO wrapper
********************
Once your propulsion model is ready, you have to make a wrapper around it for:

    - having the possibility to choose it in the FAST-OAD configuration file
    - having its parameters available in FAST-OAD data files

Defining the wrapper
====================
Your wrapper class has to implement the
:class:`~fastoad.models.propulsion.propulsion.IOMPropulsionWrapper` interface,
meaning it should implement the 2 methods :meth:`~fastoad.models.propulsion.propulsion.IOMPropulsionWrapper.get_model`
and :meth:`~fastoad.models.propulsion.propulsion.IOMPropulsionWrapper.setup`.

:meth:`~fastoad.models.propulsion.propulsion.IOMPropulsionWrapper.get_model` has
to provide an instance of your model. If the constructor of your propulsion
model class needs parameters, you may get them from :code:`inputs`, that will
be the :code:`inputs` parameter that OpenMDAO will provide to the performance
module when calling :code:`compute()` method.

Therefore, the performance module will have to define the inputs that your
propulsion model needs in its :code:`setup` method, as required by OpenMDAO.
To do this, the :code:`setup` method ot the performance module calls the
:meth:`~fastoad.models.propulsion.propulsion.IOMPropulsionWrapper.setup` of
your wrapper, that is expected to define the needed input variables.

For an example, please see the source code of
:class:`~fastoad.models.propulsion.fuel_propulsion.rubber_engine.openmdao.OMRubberEngineWrapper`.


Registering the wrapper
=======================

Registering is needed for being able to choose your propulsion wrapper in
FAST-OAD configuration file. Due to the specific status of propulsion models,
the registering process is a bit different that
:ref:`the one for classic OpenMDAO modules<add-modules-register-systems>`.

The registering is done using the
:class:`~fastoad.module_management.service_registry.RegisterPropulsion`
decorator::

    from fastoad.models.propulsion import IOMPropulsionWrapper
    from fastoad.module_management.service_registry import RegisterPropulsion


    @RegisterPropulsion("star.trek.propulsion")
    class WarpDriveWrapper(IOMPropulsionWrapper):

        [ ... ]


Using the wrapper in the configuration file
===========================================

As for :ref:`other custom modules<add-modules-set-configuration-files>`, the
folder that contains your Python module(s) must be listed in the :code:`module_folders`
of the configuration file.

The association of the propulsion model to the performance module is done
with the `propulsion_id` keyword, as in following example:

.. code-block:: yaml


    title: OAD Process with custom propulsion model

    # List of folder paths where user added custom registered OpenMDAO components
    module_folders:
      - /path/to/my/propulsion/wrapper/

    [ ... ]

    # Definition of OpenMDAO model
    model:
      [ ... ]
      performance:
        id: fastoad.performances.mission
        propulsion_id: star.trek.propulsion
