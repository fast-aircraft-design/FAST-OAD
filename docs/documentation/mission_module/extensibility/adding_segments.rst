.. _adding-segments:

########################
Adding segment types
########################

In FAST-OAD mission module, :ref:`segments<flight-segments>` are the base building blocks used
in the :ref:`mission definition file<mission-definition>`. They are implemented in Python and
FAST-OAD offers a set of segment types that allows defining typical aircraft mission profiles.

Yet, the need for some other segment types may occur. This is why FAST-OAD mission module is
designed so that any user can develop new segment types and use them in a custom mission
file.


First of all, be aware that segment implementation relies on Python
`dataclasses <https://docs.python.org/3/library/dataclasses.html>`_. This chapter
will assume you already know how it works.


.. contents::
   :local:
   :depth: 2

.. _adding-segments-links-with-mission-file:

Links between Python implementation and mission definition file
###############################################################

Flight segment classes must all derive from
:class:`~fastoad.models.performances.mission.segments.base.AbstractFlightSegment`.


Segment keyword
***************

When subclassing, a keyword is associated to the class::

    import fastoad.api as oad
    from dataclasses import dataclass

    @dataclass
    class NewSegment(oad.AbstractFlightSegment, mission_file_keyword="new_segment"):
        ...

As soon as your code is interpreted, the :code:`mission_file_keyword` will be usable in mission
definition file when specifying segments:

.. code-block:: yaml

    phases:
      some_phase:
        parts:
        - segment: taxi
          ...
        - segment: new_segment
          ...

.. note::

    **Where to put the code for a new segment implementations?**

    Having your class in any imported Python module will do.

    If you use FAST-OAD through Python, you are free to put your new segment classes where it suits
    you.

    Also, know that FAST-OAD will make Python interpret any Python module in the :ref:`module
    folders you declare in the configuration file <add-modules-set-configuration-files>`. This works
    also for :ref:`declared plugins <add-plugin>`. In both cases, it is not mandatory to add custom
    FAST-OAD modules.

Segment parameters
******************

The other strong link between segment implementation and the mission definition file is that
any dataclass field of the defined segment class will be available as parameter in the mission
definition file.

Given this implementation::

    import fastoad.api as oad
    from dataclasses import dataclass, field
    from typing import List

    @dataclass
    class NewSegment(AbstractFlightSegment, mission_file_keyword="new_segment"):
        my_float: float = 0.0
        my_bool: bool = True
        my_array: List[float] = field(default_factory=list)
        ...

... the mission definition file will accept the following implementation:

.. code-block:: yaml

    phases:
      some_phase:
        parts:
        - segment: new_segment
          my_float: 50.0
          my_bool: false
          my_array: [10.0, 20.0, 30.0]
          target:
            ...

.. note::

    **Defining mandatory parameters**

    It is possible to declare a segment parameter as mandatory (i.e. without associated default
    value) by using :code:`fastoad.api.MANDATORY_FIELD`::

        import fastoad.api as oad
        from dataclasses import dataclass

        @dataclass
        class NewSegment(AbstractFlightSegment, mission_file_keyword="new_segment"):
            my_mandatory_float: float = oad.MANDATORY_FIELD
            ...

    This is a way to work around the fact that if a dataclass defines a field with a default value,
    inheritor classes will not be allowed to define fields without default value, because then the
    non-default fields will follow a default field, which is forbidden.

Implementation of a segment class
#################################


The AbstractFlightSegment class
*******************************

As :ref:`previously said <adding-segments-links-with-mission-file>`, a segment class has to
inherit from :class:`~fastoad.models.performances.mission.segments.base.AbstractFlightSegment`
(and specify the `mission_file_keyword` if its usage if intended in mission definition files)
and will be implemented like this::

    import fastoad.api as oad
    from dataclasses import dataclass, field
    from typing import List

    @dataclass
    class NewSegment(AbstractFlightSegment, mission_file_keyword="new_segment"):
        my_float: float = 0.0
        ...

The main field of the class will be
:attr:`~fastoad.models.performances.mission.segments.base.AbstractFlightSegment.target`,
provided as a :ref:`FlightPoint instance <flight-point>`, which
will contain the flight point parameters set as target in the mission definition file.

The instantiation in FAST-OAD will be like this::

    import fastoad.api as oad

    segment = NewSegment( target=oad.FlightPoint(altitude=5000.0, true_airspeed=200.0,
                          my_float=4.2,
                         ...
                        )

.. note::

    Instantiation arguments will always be passed as keyword arguments (this behavior can be
    enforced only for Python 3.10+).

The new class will have to implement the method
:meth:`~fastoad.models.performances.mission.segments.base.AbstractFlightSegment.compute_from_start_to_target`
that will be in charge of computing the flight points between a provided `start`
and a provided `target` (providing the result as a pandas DataFrame)

.. note::

    The mission computation will actually call the method
    :meth:`~fastoad.models.performances.mission.segments.base.AbstractFlightSegment.compute_from`,
    that will do the computation between provided `start` and the target defined at instantiation
    (i.e. in the mission definition file).

    This method does some generic pre-processing of start and target before calling
    :meth:`~fastoad.models.performances.mission.segments.base.AbstractFlightSegment.compute_from_start_to_target`.
    Therefore, in the vast majority of cases, implementing the latter will be the correct thing to do.


The AbstractTimeStepFlightSegment class
***************************************

:class:`~fastoad.models.performances.mission.segments.base.AbstractTimeStepFlightSegment` is a
base class for segments that do time step computations.

This class has 4 main additional fields:

    - :attr:`~fastoad.models.performances.mission.segments.base.AbstractTimeStepFlightSegment.propulsion`,
      that is expected to be an :class:`~fastoad.model_base.propulsion.IPropulsion` instance.
    - :attr:`~fastoad.models.performances.mission.segments.base.AbstractTimeStepFlightSegment.polar`,
      that is expected to be a :class:`~fastoad.models.performances.mission.polar.Polar` instance.
    - :attr:`~fastoad.models.performances.mission.segments.base.AbstractTimeStepFlightSegment.reference_area`,
      that provides the reference surface area consistently with provided aerodynamic polar.
    - :attr:`~fastoad.models.performances.mission.segments.base.AbstractTimeStepFlightSegment.time_step`,
      that sets the time step for resolution. It is set with a low enough default value.

An inheritor class will have to provide the implementations for 3 methods that are used at each
computed time step:
:meth:`~fastoad.models.performances.mission.segments.base.AbstractTimeStepFlightSegment.get_distance_to_target`,
:meth:`~fastoad.models.performances.mission.segments.base.AbstractTimeStepFlightSegment.compute_propulsion` and
:meth:`~fastoad.models.performances.mission.segments.base.AbstractTimeStepFlightSegment.get_gamma_and_acceleration`.
(see each method documentation for more information)

There are some specialized base classes that provide a partial implementation of
:class:`~fastoad.models.performances.mission.segments.base.AbstractTimeStepFlightSegment`:

    - :class:`~fastoad.models.performances.mission.segments.base.AbstractManualThrustSegment`
      implements :meth:`~fastoad.models.performances.mission.segments.base.AbstractTimeStepFlightSegment.compute_propulsion`.
      It has its own field,
      :attr:`~fastoad.models.performances.mission.segments.base.AbstractManualThrustSegment.thrust_rate`,
      that is used to compute thrust.
    - :class:`~fastoad.models.performances.mission.segments.base.AbstractRegulatedThrustSegment` also
      implements :meth:`~fastoad.models.performances.mission.segments.base.AbstractTimeStepFlightSegment.compute_propulsion`,
      but it adjusts the thrust rate to have aircraft thrust equal to its drag.
    - :class:`~fastoad.models.performances.mission.segments.base.AbstractFixedDurationSegment`
      implements :meth:`~fastoad.models.performances.mission.segments.base.AbstractTimeStepFlightSegment.get_distance_to_target`.
      It allows to compute a segment with a time duration set by the target.

