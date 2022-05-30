.. include:: .special.rst

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

When no unit is provided, the value can be "inlined". As for :ref:`setting-values-value-unit`,
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

It is possible to provide a variable name instead of a hard-coded value. This variable will be
declared as input of the OpenMDAO component.

Unit can be specified. In that case, it will be the unit for OpenMDAO declaration and usage. In any
case, the unit for computation will be the internal unit of the segments (SI units). Conversion
will be done when needed.

Also, a default value can be specified, which will be the declared default value for OpenMDAO. It
has to be consistent with declared unit. If no default value is specified, numpy.nan will be
used in OpenMDAO declaration.


Example:

.. code-block:: yaml

    altitude:
        value: data:dummy_category:some_altitude
        unit: ft
        default: 35000.0

As for numeric values, the definition can be inlined if no unit or default value has to be declared:

.. code-block:: yaml

    altitude: data:dummy_category:some_altitude


Using opposite value
*********************

Sometimes, it can be convenient to use the opposite value of a variable. It can be done by simply
putting the minus sign "-" just before the variable:

.. code-block:: yaml

    delta_mass:
        value: -data:dummy_category:consumed_fuel
        unit: kg
        default: 125.0

.. important::

    The specified default value is for the declared variable, even when the minus sign is used.
    Therefore, if default value is set as negative and the variable is preceded by a minus sign,
    the actually used value (if the default value is kept) will be positive.


.. _setting-values-contextual-variable-name:

****************************
Contextual OpenMDAO variable
****************************

By using the tilda (:code:`~`) in the variable name, it is also possible to make the variable name contextual according to the hierarchy the defined
parameter belongs to.

When a parameter value is defined as :code:`prefix~suffix`, the actual variable name will be
:code:`prefix:<mission_name>:<route_name>:<phase_name>:suffix`.

It is useful when defining a route or a phase that will be
used in several missions (see :ref:`mission-definition`).

.. note::

    - :code:`<route_name>` and :code:`<phase_name>` will be used only when applicable
      (see examples below).

    - A contextual variable can be defined in a segment, but the variable will still be
      "associated" only to the phase.

If no prefix is provided (:code:`~suffix`), the default prefix will be :code:`data:mission:`.

If no suffix is provided (:code:`prefix~`), the default suffix will be the parameter name.

It is also possible to have no prefix nor suffix (:code:`~`). Then the 2 rules above apply.

Example
*******

.. code-block:: yaml

    routes:
      route_A:
        range: ~distance                # Example #1: here the suffix is customized.
        parts:
          - phase_a
          - ...

    phases:
      phase_a:
        thrust_rate: ~                  # Example #2: default prefix and suffix will be used
        time_step: settings:mission~    # Example #3: Here the prefix is customized

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

**Example 1**

:code:`route_A` contains the parameter :code:`range` where a contextual variable name is affected,
that will used the default prefix (:code:`data:mission:`) and the customized suffix
(:code:`distance`).

:code:`route_A` is used as a step by both :code:`mission_1` and :code:`mission_2`.

Then the mission computation has among its inputs:

.. list-table:: Variable names
    :width: 100%
    :header-rows: 1

    * - #
      - Prefix
      - Hierarchy
      - Suffix
      - Full name
    * - 1
      - \data:mission
      - mission_1:route_A
      - distance
      - \data:mission:mission_1:route_A:distance
    * - 1
      - \data:mission
      - mission_2:route_A
      - distance
      - \data:mission:mission_1:route_A:distance


**Examples 2 & 3**

:code:`phase_a` contains the parameters :code:`thrust_rate` and :code:`time_step` where contextual
variable names are affected.
For :code:`thrust_rate`, default prefix (:code:`data:mission:`) and suffix (:code:`thrust_rate`)
will be used.
For :code:`time_step`, prefix is customized (:code:`settings:mission`) and default prefix
(:code:`time_step`) will be used.


:code:`phase_a` is used as a step by :code:`route_A`, that is used as a step by :code:`mission_1`.
:code:`phase_a` is also used as a step directly by :code:`mission_2`.

Then the mission computation has among its inputs:

.. list-table:: Variable names
    :width: 100%
    :header-rows: 1

    * - #
      - Prefix
      - Hierarchy
      - Suffix
      - Full name
    * - 2
      - \data:mission
      - mission_1:route_A:phase_a
      - thrust_rate
      - \data:mission:mission_1:route_A:phase_a:thrust_rate
    * - 2
      - \data:mission
      - mission_2:phase_a
      - thrust_rate
      - \data:mission:mission_2:phase_a:thrust_rate
    * - 3
      - \data:settings
      - mission_1:route_A:phase_a
      - time_step
      - \data:settings:mission_1:route_A:phase_a:time_step
    * - 3
      - \data:settings
      - mission_2:phase_a
      - time_step
      - \data:settings:mission_2:phase_a:time_step
