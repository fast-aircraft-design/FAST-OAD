.. _add-propulsion-module:

#################################################
How to add a custom propulsion model to FAST-OAD
#################################################

Propulsion models have a specific status because they are directly called by
the performance models, so the connection is not done through OpenMDAO.

Nevertheless, FAST-OAD allows propulsion parameters to be accessible through OpenMDAO
variables, hence through FAST-OAD data files.


