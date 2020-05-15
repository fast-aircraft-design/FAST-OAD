.. _usage:

#################
FAST-OAD overview
#################

FAST-OAD is a framework for performing rapid Overall Aircraft Design.

It proposes multi-disciplinary analysis and optimisation by relying on the
`OpenMDAO framework <https://openmdao.org/>`_.

FAST-OAD allows easy switching between models for a same discipline, and also adding/removing
disciplines to match the need of your study.

Currently, FAST-OAD is bundled with models for commercial transport aircraft of years 1990-2000.
Other models will come and you may create your own models and use them instead of bundled ones.

************
How it works
************

A FAST-OAD run wraps up an OpenMDAO problem, which is, in a nutshell, the assembly of components
that each have input and output variables. Of course, the outputs of some component can be the
inputs of some other ones, so that the whole system can be solved.

FAST-OAD allows to define the problem to solve (or to optimize) through a configuration file that
makes easy to add/remove/replace any component. By doing that, the input data of the problem can
be very different from one problem to the other, but FAST-OAD comes with facilities to build the
needed input data files.

A FAST-OAD problem can be fully run from :ref:`command line interface<usage-cli>`
or from the Python API.

Usage of Python API, including pre-processing and post-processing utilities are
currently provided through :ref:`Python notebooks<python-usage>`.

**************************
Overview of FAST-OAD files
**************************
A typical run of FAST-OAD uses two types of user files:

configuration file (**.toml**)
==============================

This file defines the OpenMDAO problem by defining :

    - what components will be in the problem
    - the files for input and output data
    - the problem settings
    - the definition of the optimization problem if needed

A detailed description of this file can be found :ref:`here<configuration-file>`.


The input and output data files (**.xml**)
==========================================

These files contain the information of the variables involved in the
system model:

#. The input file contains the global inputs values
   required to run all the model. The user is free to modify the values
   of the variables in order that these new values are considered during
   a model run.
#. The output file contains all the variables (inputs +
   outputs) values obtained after a model run.

The content of these files and the way variables are named and serialized is
described :ref:`here<variables>`.
