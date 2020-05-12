.. _usage:

################
Process overview
################


The FAST-OAD environment mainly uses two types of user files:

-  Configuration files (**.toml**):

   FASTOADProblem instances require a configuration file at
   initialization. The usage of this type of file is described in the
   `README <https://github.com/fast-aircraft-design/FAST-OAD>`__ of the
   repository.

-  System variables files (**.xml**):

   These files regroup the information of the variables involved in the
   system model. There are two types of system variables files:

       1. INPUT_FILE: The input file contains the global inputs values
       required to run all the model. The user is free to modify the values
       of the variables in order that these new values are considered during
       a model run.

       2. ,OUTPUT_FILE: The output file contains all the variables (inputs +
       outputs) values obtained after a model run.

The following figure shows an overview of the user files: |User Files|

The user defines the CONFIGURATION_FILE that the FASTOADProblem instance
will read. The user can read and write this file, and thus modify the
problem, the input and output file names etc. The FASTOADProblem then
knows which is the structure of the model and what are the modules used.
Thus, it is capable of determining which are the global inputs required
for running the model.

Executing the ``generate_inputs()`` function with the
``configuration_file_path`` as the first argument will generate the
INPUT_FILE.xml file that contains all the global inputs. If a second
argument ``source_path`` (SOURCE_PATH.xml) is provided then the instance
will use the values found in this file for the same variables of the
INPUT_FILE. If the SOURCE_PATh file uses a different schema, a
translation file ``source_path_schema`` can be provided as a third
argument to the function.

Once the variables of the INPUT_FILE have a correct value (by default
values are NaN) the problem can be executed. For that the user can
perform either a Multidisciplinary Design Analysis (MDA) using
``evaluate_problem()`` or a Multidisciplinary Design Optimization (MDO)
using ``optimize_problem()``. Both of these function generate the
OUTPUT_FILE.xml containing all the variables of the system and their
values resulting from the computation.

.. |User Files| image:: ../img/user_files_arch.svg
