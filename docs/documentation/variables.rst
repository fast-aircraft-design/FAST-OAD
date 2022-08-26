.. _variables:

#################
Problem variables
#################

FAST-OAD process relies on `OpenMDAO <https://openmdao.org/>`_, and process variables are OpenMDAO variables.

For any component, variables are declared as inputs or outputs as described
`here <http://openmdao.org/twodocs/versions/latest/features/core_features/defining_components/declaring_variables.html>`_.

FAST-OAD uses the
`promotion system of OpenMDAO <http://openmdao.org/twodocs/versions/latest/basic_guide/promote_vs_connect.html>`_,
which means that all variables that are exchanged between FAST-OAD registered systems [#]_ have a unique name and are
available for the whole process.

The list of variable names and descriptions for a given problem can be obtained from command line (see
:ref:`get-variable-list`).

.. contents::
   :local:


***************
Variable naming
***************

Variables are named with a path-like pattern where path separator is :code:`:`, e.g.:

- :code:`data:geometry:wing:area`
- :code:`data:weight:airframe:fuselage:mass`
- :code:`data:weight:airframe:fuselage:CG:x`

The first path element distributes variables among three categories:

- :code:`data`: variables that define the aircraft and its behaviour. This is the main category
- :code:`settings`: model settings. Generally coefficients for advanced users
- :code:`tuning`: coefficients that allow to do some assumptions (e.g.: "what if wing mass could be reduced of 20%?")

The second path element tells about the nature of the variable (geometry, aerodynamics, weight, ...).

The other path elements depend of the variable. The number of path elements is not fixed.

***************
Serialization
***************

File format
***********

For writing input and output files, FAST-OAD relies on the path in the variable names.

For instance, the variable name :code:`data:geometry:wing:area` will be split according
to colons :code:`:` and each part of the name will become a level in the XML hierarchy:

.. code-block:: xml

        <data>
            <geometry>
                <wing>
                    <area units="m**2">
                        150.0
                    </area>
                </wing>
            </geometry>
        </data>


A complete file that would contain the three above-mentioned variables will be as following:


.. code-block:: xml

    <FASTOAD_model>
        <data>
            <geometry>
                <wing>
                    <area units="m**2">150.0</area>
                </wing>
            </geometry>
            <weight>
                <fuselage>
                    <mass units="kg">10000.0</mass>
                    <CG>
                        <x units="m">20.0</x>
                    </CG>
                </fuselage>
            </weight>
        </data>
    </FASTOAD_model>

.. note::

    Units are given as a string according to
    `OpenMDAO units definitions <http://openmdao.org/twodocs/versions/latest/features/units.html>`_

.. note::

    XML requires a unique root element for containing all other ones. Its name can be
    freely chose, but it is `FASTOAD_model` in files written by FAST-OAD


FAST-OAD API
************

FAST-OAD proposes a convenient way to read/write such files in Python, through the
:class:`~fastoad.io.variable_io.DataFile` class.

Provided that above file is named :code:`data.xml`, following commands apply:

.. doctest::

    >>> import fastoad.api as oad
    >>> # ---------------------------------
    >>> datafile = oad.DataFile("./data.xml")
    >>> # Getting information
    >>> datafile.names()
    ['data:geometry:wing:area', 'data:weight:fuselage:mass', 'data:weight:fuselage:CG:x']
    >>> len(datafile)
    3
    >>> datafile["data:geometry:wing:area"].value
    [150.0]
    >>> datafile["data:geometry:wing:area"].units
    'm**2'
    >>> # ---------------------------------
    >>> # Writing data
    >>> datafile.save()
    >>> # ---------------------------------
    >>> # Modifying data
    >>> datafile["data:geometry:wing:area"].value = 120.0  # no need to provide list or numpy array for scalar values.
    >>> datafile["data:geometry:wing:area"].value
    120.0
    >>> # ---------------------------------
    >>> # Adding data
    >>> fuselage_length = oad.Variable("data:geometry:fuselage:length", val=35.0, units="m")
    >>> datafile.append(fuselage_length)
    >>> # or ...
    >>> datafile["data:geometry:wing:mass"] = dict(val=10500.0, units="kg") # will replace previous definition
    >>> datafile.names()
    ['data:geometry:wing:area', 'data:weight:fuselage:mass', 'data:weight:fuselage:CG:x', 'data:geometry:fuselage:length', 'data:geometry:wing:mass']
    >>> # ---------------------------------
    >>> # Removing data
    >>> del datafile["data:weight:fuselage:CG:x"]
    >>> datafile.names()
    ['data:geometry:wing:area', 'data:weight:fuselage:mass', 'data:geometry:fuselage:length', 'data:geometry:wing:mass']
    >>> # ---------------------------------
    >>> # Writing to another file
    >>> datafile.save_as("./new_data.xml", overwrite=True)
    >>> datafile.file_path  # The object is now associated to the new path
    './new_data.xml'

After running these lines of code, the generated file :code:`new_data.xml` contains:

.. code-block:: xml

    <FASTOAD_model>
        <data>
            <geometry>
                <fuselage>
                    <length units="m">35.0</length>
                </fuselage>
                <wing>
                    <area units="m**2">120.0</area>
                    <mass units="kg">10500.0</mass>
                </wing>
            </geometry>
            <weight>
                <fuselage>
                    <mass units="kg">10000.0</mass>
                </fuselage>
            </weight>
        </data>
    </FASTOAD_model>




.. [#] see :ref:`add-modules-register-systems`
