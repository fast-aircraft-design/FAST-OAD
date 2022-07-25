##############
Extensibility
##############

In FAST-OAD mission module, :ref:`segments<flight-segments>` are the base building blocks used
in the :ref:`mission definition file<mission-definition>`. They are implemented in Python and
FAST-OAD offers a set of segment types that allows defining typical aircraft mission profiles.

Yet, the need for some other segment types may occur. This is why FAST-OAD mission module is
designed so that any user can develop new segment types and use them in a custom mission
file.

.. toctree::
   :maxdepth: 2

    Adding segment types <adding_segments>
    The FlightPoint class <flight_point>
