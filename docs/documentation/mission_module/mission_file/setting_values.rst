.. _setting-values:

##############################
Setting values in mission file
##############################

Any parameter value in the mission file can be provided in several ways:


.. contents::
   :local:
   :depth: 1

.. _`setting-values-value-unit`:

**************************
hard-coded value and unit
**************************

The standard way is to set the parameter as value, with or without unit.

.. note::

    If no unit is provided while parameter needs one, SI units will be assumed.

    Provided units have to match :ref:`OpenMDAO convention<openmdao:feature_units>`.

Examples:

.. code-block:: yaml

    altitude:
        value: 10.
        unit: km
    altitude:
        value: 10000.   # equivalent to previous one (10km), because SI units are assumed
    mach:
        value: 0.8
    engine_setting:
        value: takeoff   # some parameters expect a string value


.. _setting-values-value-only:

*****************************
hard-coded value with no unit
*****************************

When no unit is provided, the value can be set directly. As for :ref:`setting-values-value-unit`,
if the concerned parameter is not dimensionless, SI units will be assumed.

Example:

.. code-block:: yaml

    mach: 0.8                   # no unit
    altitude: 10000.            # == 10 km
    engine_setting: takeoff     # string value


.. _setting-values-variable-name:

*****************
OpenMDAO variable
*****************

It is possible to provide a variable name instead of a hard-coded value. Then the
value and unit will be set by some FAST-OAD module, or by the input file.

Example:

.. code-block:: yaml

    altitude: data:dummy_category:some_altitude


.. _setting-values-contextual-variable-name:

****************************
Contextual OpenMDAO variable
****************************

It is also possible to provide only a suffix for the variable name. Then the
complete variable name will be decided by the hierarchy the defined parameter
belongs to.
The associated variable name will be
:code:`data:mission:<mission_name>:<route_name>:<phase_name>:<suffix>`.

It is useful when defining a route or a phase that will be
used in several missions (see :ref:`mission-definition`).

.. note::

    - :code:`<route_name>` and :code:`<phase_name>` will be used only when applicable
      (see examples below).

    - A contextual variable can be defined in a segment, but the variable will still be
      "associated" only to the phase.


A basic contextual variable is identified by a single tilde (:code:`~`). In such case,
:code:`<suffix>` is the parameter name.

A generic contextual variable is **preceded** by a tilde. In such case,
:code:`<suffix>` is the name provided as value (without the tilde).

Example 1 : generic contextual variable in a route
==================================================

.. code-block:: yaml

    routes:
      route_A:
        range: ~distance   # "distance" will be the used variable name
        parts:
          - ...

    missions:
      mission_1:
        parts:
          - ...
          - route: route_A
          - ...
      mission_2:
        parts:
          - ...
          - route: route_A
          - ...

:code:`route_A` contains the parameter :code:`range` where a contextual variable name is affected.
:code:`route_A` is used as a step by both :code:`mission_1` and :code:`mission_2`.

Then the mission computation has among its inputs:

  - :code:`data:mission:mission_1:route_A:distance`
  - :code:`data:mission:mission_2:route_A:distance`


Example 2 : basic contextual variable in a flight phase
=======================================================

.. code-block:: yaml

    phases:
      phase_a:
        thrust_rate: ~    # "thrust_rate" will be the used variable name

    routes:
      route_A:
        range: ...
        parts:
          - phase_a
          - ...

    missions:
      mission_1:
        parts:
          - ...
          - route: route_A
          - ...
      mission_2:
        parts:
          - ...
          - phase: phase_a
          - ...

:code:`phase_a` contains the parameter :code:`thrust_rate` where a contextual variable name is affected.
:code:`phase_a` is a used as a step by :code:`route_A`, that is used as a step by :code:`mission_1`.
:code:`phase_a` is also used as a step directly by :code:`mission_2`.

Then the mission computation has among its inputs:

  - :code:`data:mission:mission_1:route_A:phase_a:thrust_rate`
  - :code:`data:mission:mission_2:phase_a:thrust_rate`
