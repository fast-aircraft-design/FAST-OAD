=========
Changelog
=========

Version 1.9.0
=============

- Added
    - Add maximum cl and maximum altitude constraints in cruise, optimal_cruise, and altitude_change segments. (https://github.com/fast-aircraft-design/FAST-OAD/pull/666)
    - Start to use Ruff for linting. (https://github.com/fast-aircraft-design/FAST-OAD/pull/634)
    - Add linting rules in CI using Ruff. (https://github.com/fast-aircraft-design/FAST-OAD/pull/657)
    - Add new rules in Ruff (UP RET FBT FA PTH). (https://github.com/fast-aircraft-design/FAST-OAD/pull/609)
    - Migrate to poetry 2.x. (https://github.com/fast-aircraft-design/FAST-OAD/pull/646)
    - Added plugin description, guidelines for contributors and ✨. (https://github.com/fast-aircraft-design/FAST-OAD/pull/651)
    - Added compatibility with Python 3.13 (with poetry 2.x). (https://github.com/fast-aircraft-design/FAST-OAD/pull/649)
    - Deprecate Python 3.9. (https://github.com/fast-aircraft-design/FAST-OAD/pull/658)
    - Added compatibility with Python 3.14. (https://github.com/fast-aircraft-design/FAST-OAD/pull/661)

- Modified
    - Enhanced Variable Metadata Handling. (https://github.com/fast-aircraft-design/FAST-OAD/pull/622)
    - Simplify dependencies of the project: Pandas. (https://github.com/fast-aircraft-design/FAST-OAD/pull/660)
    - Update CI to use the organization variable POETRY_VERSION. (https://github.com/fast-aircraft-design/FAST-OAD/pull/662)
    - Update minimum OpenMDAO version to version 3.40. (https://github.com/fast-aircraft-design/FAST-OAD/pull/659)

- Fixed
    - Fix watchman test, preparing to update the OpenMDAO bounds in master branch. (https://github.com/fast-aircraft-design/FAST-OAD/pull/656

Version 1.8.4
=============

- Added:
    - Deactivate OpenMDAO automatic reporting. (https://github.com/fast-aircraft-design/FAST-OAD/pull/627)
    - Add loads as a valid FAST-OAD discipline. (https://github.com/fast-aircraft-design/FAST-OAD/pull/629)
    - Add CAS in the mission log. (in https://github.com/fast-aircraft-design/FAST-OAD/pull/633 by @dimitris-glenis)
    - Added more verbose logging for failed module import. (https://github.com/fast-aircraft-design/FAST-OAD/pull/639)
    - Better handling of failed module logging. (https://github.com/fast-aircraft-design/FAST-OAD/pull/641)
    - Better handling of optional module. (https://github.com/fast-aircraft-design/FAST-OAD/pull/642)
    - Update plotly to v6. (https://github.com/fast-aircraft-design/FAST-OAD/pull/643)
- Fixed:
    - Add RunOnce solver as default for `run_system`. (https://github.com/fast-aircraft-design/FAST-OAD/pull/625)
    - Fix inconsistent behaviour of the get_val method when not providing units of measure. (https://github.com/fast-aircraft-design/FAST-OAD/pull/616)
    - Fix OpenMDAO incompatibility. (https://github.com/fast-aircraft-design/FAST-OAD/pull/619)
    - Fix mission target calculation. (https://github.com/fast-aircraft-design/FAST-OAD/pull/628)

Version 1.8.3
=============

- Added:
    - New github Pull Request template. (https://github.com/fast-aircraft-design/FAST-OAD/pull/585)
    - Add sorting capability to imports using ruff. (https://github.com/fast-aircraft-design/FAST-OAD/pull/587)
    - Allow non pickable object as propulsion component. (https://github.com/fast-aircraft-design/FAST-OAD/pull/588)
    - Enhanced documentation for mission segment parameters. (https://github.com/fast-aircraft-design/FAST-OAD/pull/582)
- Fixed:
    - Remove Codecov plain text token in Github Action. (https://github.com/fast-aircraft-design/FAST-OAD/pull/591)
    - Upgrade Github actions test to ubuntu-latest. (https://github.com/fast-aircraft-design/FAST-OAD/pull/602)
    - Set a timeout limit on GitHub Action's pipeline. (https://github.com/fast-aircraft-design/FAST-OAD/pull/605)
- Temporary fix:
    - Freeze OpenMDAO version to <3.38. (https://github.com/fast-aircraft-design/FAST-OAD/pull/613)

Version 1.8.2
=============
- Modified:
    - Mission module:
        - Automated addition of taxi-out and takeoff phases is now deprecated. (https://github.com/fast-aircraft-design/FAST-OAD/pull/574)
        - `load_factor` parameter has been added to mission segments with weight-driven lift (https://github.com/fast-aircraft-design/FAST-OAD/pull/579).
        - transition segment can now handle a payload change (https://github.com/fast-aircraft-design/FAST-OAD/pull/580).
- Fixed:
    - Minor fixes in mission module (https://github.com/fast-aircraft-design/FAST-OAD/pull/579):
        - Lift value was generally not computed (knowing CL can be enough), though the column is always in csv files.
        - In ClimbAndCruise segment, the target of inner climb segment could be set without guarantee the climb segment was not None.

Version 1.8.1
=============
- Modified:
    - Python 3.12 is now supported. (https://github.com/fast-aircraft-design/FAST-OAD/pull/555)
    - Python 3.8, that reached end of life, is no longer supported. (https://github.com/fast-aircraft-design/FAST-OAD/pull/555)

Version 1.8.0
=============
- Added:
    - Custom imports handling in configuration file. (https://github.com/fast-aircraft-design/FAST-OAD/pull/559)
    - Initializing output values from input file. (https://github.com/fast-aircraft-design/FAST-OAD/pull/551)
    - Layout of mission viewer can now be controlled by user. (https://github.com/fast-aircraft-design/FAST-OAD/pull/549 by @Mokyoslurp)
    - Added sunburst mass breakdown for missions other than the sizing one. (https://github.com/fast-aircraft-design/FAST-OAD/pull/547)
    - In mission computation, added CL as possible target for altitude change. (https://github.com/fast-aircraft-design/FAST-OAD/pull/563)
    - New method get_val() in Variable class to get values in different units. (https://github.com/fast-aircraft-design/FAST-OAD/pull/570)
    - Plots now handle horizontal_tail:center new naming. (https://github.com/fast-aircraft-design/FAST-OAD/pull/546)

- Fixed:
    - Better NaN detection in inputs. (https://github.com/fast-aircraft-design/FAST-OAD/pull/532)
    - Deactivation of dataset is now effective for both plots in mass breakdown bar plot. (https://github.com/fast-aircraft-design/FAST-OAD/pull/545 by @aeomath)
    - Payload range module can now handle mission files with several missions. (https://github.com/fast-aircraft-design/FAST-OAD/pull/562)

Version 1.7.4
=============
- Fixed:
    - Fixed compatibility of ValidityDomainChecker class with OpenMDAO 3.34. (https://github.com/fast-aircraft-design/FAST-OAD/pull/553)

Version 1.7.3
=============
- Added:
    - Compatibility with Python 3.11. (https://github.com/fast-aircraft-design/FAST-OAD/pull/538)
    - Aircraft plot: minor change in naming of geometry variable for horizontal tail (old name still accepted). (https://github.com/fast-aircraft-design/FAST-OAD/pull/546)

- Fixed:
    - Fixed validity checker for array variables. (https://github.com/fast-aircraft-design/FAST-OAD/pull/537)
    - In mass breakdown bar plot, legend was controlling visibility only for the right-handed plot. (https://github.com/fast-aircraft-design/FAST-OAD/pull/545 by @aeomath)

Version 1.7.2
=============
- Added:
    - A `fastoad.testing.run_system()` function is now available in public API for component unit test. (https://github.com/fast-aircraft-design/FAST-OAD/pull/533)

- Modified:
    - `pathlib.Path` objects are now accepted whenever a file or folder path is expected. (https://github.com/fast-aircraft-design/FAST-OAD/pull/521, https://github.com/fast-aircraft-design/FAST-OAD/pull/522, https://github.com/fast-aircraft-design/FAST-OAD/pull/525)
    - Enhanced and documented the `CycleGroup` class. (https://github.com/fast-aircraft-design/FAST-OAD/pull/528)

- Fixed:
    - Climb was not stopping when start was already over the asked optimal altitude/flight level. (https://github.com/fast-aircraft-design/FAST-OAD/pull/526)
    - Fixed links to OpenMDAO doc. (https://github.com/fast-aircraft-design/FAST-OAD/pull/527)
    - Fixed behavior when input variables could be added using `model_options`. (https://github.com/fast-aircraft-design/FAST-OAD/pull/530)
    - Fixed the variables displayed by default in MissionViewer. (https://github.com/fast-aircraft-design/FAST-OAD/pull/535)

Version 1.7.1
=============
- Added:
    - The base class `CycleGroup` is now proposed to standardize options for groups that contain a loop. (https://github.com/fast-aircraft-design/FAST-OAD/pull/516)

- Fixed:
    - Missions can now be defined without route. (https://github.com/fast-aircraft-design/FAST-OAD/pull/515)

Version 1.7.0
=============
- Added:
    - Centralized way to set options from configuration file. (https://github.com/fast-aircraft-design/FAST-OAD/pull/510)

- Fixed:
    - Fix for validity domain checker. (https://github.com/fast-aircraft-design/FAST-OAD/pull/511)

Version 1.6.0
=============
- Added:
    - FAST-OAD is now officially compatible with Python 3.10. Support of Python 3.7 has been abandoned. (https://github.com/fast-aircraft-design/FAST-OAD/pull/496)
    - OpenMDAO group options can now be set from configuration file. (https://github.com/fast-aircraft-design/FAST-OAD/pull/502)
    - Mission computation:
        - A value for maximum lift coefficient can now be set for climb and cruise segments. (https://github.com/fast-aircraft-design/FAST-OAD/pull/504)
        - Added the field consumed_fuel, computed for each time step and present in CSV output file. (https://github.com/fast-aircraft-design/FAST-OAD/pull/505)

- Fixed:
    - Decreased execution time by avoiding unnecessary setup operations. (https://github.com/fast-aircraft-design/FAST-OAD/pull/503)

Version 1.5.2
=============
- Added:
    - Added sphinx documentation for source data file generation. (https://github.com/fast-aircraft-design/FAST-OAD/pull/500)

- Fixed:
    - Fix for climb segment going far too high when asked for optimal altitude in some cases. (https://github.com/fast-aircraft-design/FAST-OAD/pull/497 and https://github.com/fast-aircraft-design/FAST-OAD/pull/498)
    - Now accepting upper case distribution names for FAST-OAD plugins. (https://github.com/fast-aircraft-design/FAST-OAD/pull/499)
    - Now DataFile.from_problem() returns a DataFile instance, and not a VariableList instance. (https://github.com/fast-aircraft-design/FAST-OAD/pull/494)

Version 1.5.1
=============
- Fixed:
    - Some warning were issued by pandas when using mission module. (https://github.com/fast-aircraft-design/FAST-OAD/pull/492)

Version 1.5.0
=============
- Added:
    - Computation of payload-range data. (https://github.com/fast-aircraft-design/FAST-OAD/pull/471 and https://github.com/fast-aircraft-design/FAST-OAD/pull/482)
    - Payload-range plot. (https://github.com/fast-aircraft-design/FAST-OAD/pull/480)
    - Time-step simulation of takeoff in mission module (https://github.com/fast-aircraft-design/FAST-OAD/pull/481, https://github.com/fast-aircraft-design/FAST-OAD/pull/484, https://github.com/fast-aircraft-design/FAST-OAD/pull/487, https://github.com/fast-aircraft-design/FAST-OAD/pull/490)
    - Introduced concept of macro-segment, for proposing assembly of several segments as one usable segment. (https://github.com/fast-aircraft-design/FAST-OAD/pull/488)
    - Segment implementations can now be registered using decorators. (https://github.com/fast-aircraft-design/FAST-OAD/pull/485)
    - Mission definition can now define a global target fuel consumption. (https://github.com/fast-aircraft-design/FAST-OAD/pull/467)
    - A FAST-OAD plugin can now come with its own source data files, obtainable using `fastoad gen_source_data_file` command. (https://github.com/fast-aircraft-design/FAST-OAD/pull/477)

- Changed:
    - fast-oad (not fast-oad-core) now requires at least fast-oad-cs25 0.1.4. (https://github.com/fast-aircraft-design/FAST-OAD/pull/475)
    - fast-oad (and fast-oad-core) now requires at least OpenMDAO 3.18. (https://github.com/fast-aircraft-design/FAST-OAD/pull/483)
    - Variable viewer can now display discrete outputs of type string. (https://github.com/fast-aircraft-design/FAST-OAD/pull/479)

- Fixed:
    - MissionViewer was not able to show several missions. (https://github.com/fast-aircraft-design/FAST-OAD/pull/477)
    - Fixed compatibility with OpenMDAO 3.26 (https://github.com/fast-aircraft-design/FAST-OAD/pull/486)

Version 1.4.2
=============
- Fixed:
    - Fixed compatibility with Openmdao 3.22. (https://github.com/fast-aircraft-design/FAST-OAD/pull/464)
    - Now a warning is issued when a nan value is in generated input file from a given data source. (https://github.com/fast-aircraft-design/FAST-OAD/pull/468)
    - Now FAST-OAD_CS25 0.1.4 is explicitly required. (https://github.com/fast-aircraft-design/FAST-OAD/pull/475)

Version 1.4.1
=============
- Fixed:
    - Fixed backward compatibility of bundled missions. (https://github.com/fast-aircraft-design/FAST-OAD/pull/466)

Version 1.4.0
=============

- Changed:
    - Added a new series of tutorials. (https://github.com/fast-aircraft-design/FAST-OAD/pull/426)
    - Enhancements in mission module (https://github.com/fast-aircraft-design/FAST-OAD/pull/430 and https://github.com/fast-aircraft-design/FAST-OAD/pull/462), mainly:
        - a parameter with a variable as value can now be associated to a unit and a default value that will be used in the OpenMDAO input declaration (and be in generated input data file).
        - a target parameter can be declared as relative to the start point of the segment by prefixing the parameter name with "delta_"
          when setting a parameter, a minus sign can be put before a variable name to get the opposite value (can be useful with relative values)
        - a parameter can now be set at route or mission level.
        - dISA can now be set in mission definition file with isa_offset.
        - a mission phase can now contain other phases.
        - if a segment parameter (dataclass field) is an array or a list, the associated variable in mission file will be declared with shape_by_conn=True.
        - taxi-out and takeoff are no more automatically set outside of the mission definition file:
            - mission starting point (altitude, speed, mass) can now be set using the "start" segment.
            - the mass input of the mission can be set using the "mass_input" segment. This segment can be anywhere in the mission, though it is expected that fuel consumption in previous segments is mass-independent.
            - if none of the two above solution is used to define a mass input variable, the mission module falls back to behaviour of earlier releases, i.e. the automatic addition of taxi-out and takeoff at beginning of the mission.
    - Upgrade to wop 2.x API. (https://github.com/fast-aircraft-design/FAST-OAD/pull/453)

- Fixed:
    - Variable viewer was showing only one variable at a time if variable names contained no colon. (https://github.com/fast-aircraft-design/FAST-OAD/pull/456)
    - Optimization viewer was handling incorrectly bounds with value 0. (https://github.com/fast-aircraft-design/FAST-OAD/pull/461)

Version 1.3.5
=============
- Fixed:
    - Deactivated automatic reports from OpenMDAO 3.17+ (can still be driven by environment variable OPENMDAO_REPORTS). (https://github.com/fast-aircraft-design/FAST-OAD/pull/449)
    - Mass breakdown bar plot now accepts more than 5 datasets. The used color map is now consistent with othe FAST-OAD plots. (https://github.com/fast-aircraft-design/FAST-OAD/pull/451)

Version 1.3.4
=============
- Fixed:
    - FAST-OAD was quickly crashing in multiprocessing environment. (https://github.com/fast-aircraft-design/FAST-OAD/pull/442)
    - Memory consumption could increase considerably when numerous computations were done in the same Python session. (https://github.com/fast-aircraft-design/FAST-OAD/pull/443)
    - Deactivated sub-models kept being deactivated in following computations done in the same Python session. (https://github.com/fast-aircraft-design/FAST-OAD/pull/444)

Version 1.3.3
=============
- Fixed:
    - Fixed crash when using Newton solver or case recorders. (https://github.com/fast-aircraft-design/FAST-OAD/pull/434)
    -  DataFile class enhancement (https://github.com/fast-aircraft-design/FAST-OAD/pull/435) :
        - Instantiating DataFile with an non-existent file now triggers an error.
        - DataClass.from_*() methods now return a DataClass instance instead of VariableList.
        - A dedicated section has been added in Sphinx documentation (General Documentation > Process variables > Serialization > FAST-OAD API).
    - A component input could be in FAST-OAD-generated input file though it was explicitly connected to an IndepVarComp output in configuration  file. (https://github.com/fast-aircraft-design/FAST-OAD/pull/437)

Version 1.3.2
=============
- Fixed:
    - Compatibility with OpenMDAO 3.17.0. (https://github.com/fast-aircraft-design/FAST-OAD/pull/428)

Version 1.3.1
=============
- Fixed:
    - Version requirements for StdAtm and FAST-OAD-CS25 were unwillingly pinned to 0.1.x. (https://github.com/fast-aircraft-design/FAST-OAD/pull/422)
    - `fastoad -v` was producing `unknown` when only FAST-OAD-core was installed. (https://github.com/fast-aircraft-design/FAST-OAD/pull/422)
    - Fixed some deprecation warnings. (https://github.com/fast-aircraft-design/FAST-OAD/pull/423)

Version 1.3.0.post0
===================
- Modified package organization. (https://github.com/fast-aircraft-design/FAST-OAD/pull/420)

Version 1.3.0
=============
- Changes:
    - Rework of plugin system. (https://github.com/fast-aircraft-design/FAST-OAD/pull/409 - https://github.com/fast-aircraft-design/FAST-OAD/pull/417)
        - Plugin group identifier is now `fastoad.plugins` (usage of `fastoad_model` is deprecated)
        - A plugin can now provide, besides models, notebooks and sample configuration files.
        - CLI and API have been updated to allow choosing the source when generating a configuration file, and to provide the needed information about installed plugin (`fastoad plugin_info`)
        - Models are loaded only when needed (speeds up some basic operations like `fastoad -h`)
    - CS25-related models are now in separate package [FAST-OAD-CS25](https://pypi.org/project/fast-oad-cs25/). This package is still installed along with FAST-OAD to preserve backward-compatibility. Also, package [FAST-OAD-core](https://pypi.org/project/fast-oad-core/) is now available, which does NOT install FAST-OAD-CS25 (thus contains only the mission model). (https://github.com/fast-aircraft-design/FAST-OAD/pull/414)
    - IndepVarComp variables in FAST-OAD models are now correctly handled and included in input data file. (https://github.com/fast-aircraft-design/FAST-OAD/pull/408)
    - Changes in mission module. Most noticeable change is that the number of engines is no more an input of the mission module, but should be handled by the propulsion model. No impact when using the base CS-25 process, since the variable name has not changed.(https://github.com/fast-aircraft-design/FAST-OAD/pull/411)

- Bug fixes:
    - FAST-OAD is now able to manage dynamically shaped problem inputs. (https://github.com/fast-aircraft-design/FAST-OAD/pull/416 - https://github.com/fast-aircraft-design/FAST-OAD/pull/418)


Version 1.2.1
=============
- Changes:
  - Updated dependency requirements. All used libraries are now compatible with Jupyter lab 3 without need for building extensions. (https://github.com/fast-aircraft-design/FAST-OAD/pull/392)
  - Now Atmosphere class is part of the [stdatm](https://pypi.org/project/stdatm/) package (https://github.com/fast-aircraft-design/FAST-OAD/pull/398)
  - For `list_variables` command, the output format can now be chosen, with the addition of the format of variables_description.txt (for custom modules now generate a variable descriptions. (https://github.com/fast-aircraft-design/FAST-OAD/pull/399)

- Bug fixes:
  - Minor fixes in Atmosphere class. (https://github.com/fast-aircraft-design/FAST-OAD/pull/386)


Version 1.1.2
=============
- Bug fixes:
    - Engine setting could be ignored for cruise segments. (https://github.com/fast-aircraft-design/FAST-OAD/pull/397)

Version 1.1.1
=============
- Bug fixes:
    - Fixed usage of list_modules with CLI. (https://github.com/fast-aircraft-design/FAST-OAD/pull/395)

Version 1.1.0
=============
- Changes:
    - Added new submodel feature to enable a more modular approach. (https://github.com/fast-aircraft-design/FAST-OAD/pull/379)
    - Implemented the submodel feature in the aerodynamic module. (https://github.com/fast-aircraft-design/FAST-OAD/pull/388)
    - Implemented the submodel feature in the geometry module. (https://github.com/fast-aircraft-design/FAST-OAD/pull/387)
    - Implemented the submodel feature in the weight module. (https://github.com/fast-aircraft-design/FAST-OAD/pull/385)
    - Added the possibility to list custom modules. (https://github.com/fast-aircraft-design/FAST-OAD/pull/369)
    - Updated high lift aerodynamics and rubber engine models. (https://github.com/fast-aircraft-design/FAST-OAD/pull/352)
    - Added custom modules tutorial notebook. (https://github.com/fast-aircraft-design/FAST-OAD/pull/317)
- Bug fixes:
    - Fixed incompatible versions of jupyter-client. (https://github.com/fast-aircraft-design/FAST-OAD/pull/390)
    - Fixed the naming and description of the virtual taper ratio used in the wing geometry. (https://github.com/fast-aircraft-design/FAST-OAD/pull/383)
    - Fixed some wrong file links and typos in CeRAS notebook. (https://github.com/fast-aircraft-design/FAST-OAD/pull/380)
    - Fixed issues with variable descriptions in xml file. (https://github.com/fast-aircraft-design/FAST-OAD/pull/364)

Version 1.0.5
=============
- Changes:
    - Now using the new WhatsOpt feature that allows to generate XDSM files without being registered on server. (https://github.com/fast-aircraft-design/FAST-OAD/pull/361)
    - Optimization viewer does no allow anymore to modify output values. (https://github.com/fast-aircraft-design/FAST-OAD/pull/372)
- Bug fixes:
    - Compatibility with OpenMDAO 3.10 (which becomes the minimal required version). (https://github.com/fast-aircraft-design/FAST-OAD/pull/375)
    - Variable descriptions can now be read from comment of XML data files, which fixes the missing descriptions in variable viewer. (https://github.com/fast-aircraft-design/FAST-OAD/pull/359)
    - Performance model: the computed taxi-in distance was irrelevant. (https://github.com/fast-aircraft-design/FAST-OAD/pull/368)

Version 1.0.4
=============
- Changes:
    - Enum classes in FAST-OAD models are now extensible by using `aenum` instead of `enum`. (https://github.com/fast-aircraft-design/FAST-OAD/pull/345)
- Bug fixes:
    - Incompatibility with `ruamel.yaml` 0.17.5 and above has been fixed. (https://github.com/fast-aircraft-design/FAST-OAD/pull/344)
    - Computation of partial derivatives for OpenMDAO was incorrectly declared in some components.
      MDA, or MDO with COBYLA solver, were not affected. (https://github.com/fast-aircraft-design/FAST-OAD/pull/347)
    - Errors in custom modules are no more hidden. (https://github.com/fast-aircraft-design/FAST-OAD/pull/348)

Version 1.0.3
=============
- Changes:
    - Configuration files can now contain unknown sections (at root level) to allow these files to be used by other tools. (https://github.com/fast-aircraft-design/FAST-OAD/pull/333)
- Bug fixes:
    - Importing, in a `__init__.py`, some classes that were registered as FAST-OAD modules could make that the register process fails. (https://github.com/fast-aircraft-design/FAST-OAD/pull/331)
    - When generating an input file using a data source, the whole data source was copied instead of just keeping the needed variables. (https://github.com/fast-aircraft-design/FAST-OAD/pull/332)
    - Instead of overwriting an existing input files, variables of previous file were kept. (https://github.com/fast-aircraft-design/FAST-OAD/pull/330)
    - A variable that was connected to an output could be incorrectly labelled as input when listing problem variables. (https://github.com/fast-aircraft-design/FAST-OAD/pull/341)
    - Fixed broken links in Sphinx documentation, including docstrings. (https://github.com/fast-aircraft-design/FAST-OAD/pull/315)

Version 1.0.2
=============
- FAST-OAD now requires a lower version of `ruamel.yaml`. It should prevent Anaconda to try and fail to update its
  "clone" of `ruamel.yaml`. (https://github.com/fast-aircraft-design/FAST-OAD/pull/308)

Version 1.0.1
=============
- Bug fixes:
    - In a jupyter notebook, each use of a filter in variable viewer caused the display of a new variable viewer. (https://github.com/fast-aircraft-design/FAST-OAD/pull/301)
    - Wrong warning message was displayed when an incorrect path was provided for `module_folders` in the configuration file. (https://github.com/fast-aircraft-design/FAST-OAD/pull/303)

Version 1.0.0
=============
- Core software:
    - Changes:
        - FAST-OAD configuration file is now in YAML format. (https://github.com/fast-aircraft-design/FAST-OAD/pull/277)
        - Module declaration are now done using Python decorators directly on registered classes. (https://github.com/fast-aircraft-design/FAST-OAD/pull/259)
        - FAST-OAD now supports custom modules as plugins. (https://github.com/fast-aircraft-design/FAST-OAD/pull/266)
        - Added "fastoad.loop.wing_position" module for computing wing position from target static margin in MDA. (https://github.com/fast-aircraft-design/FAST-OAD/pull/268)
        - NaN values in input data are now detected at computation start. (https://github.com/fast-aircraft-design/FAST-OAD/pull/273)
        - Now api.generate_inputs() returns the path of generated file. (https://github.com/fast-aircraft-design/FAST-OAD/pull/254)
        - `fastoad list_systems` is now `fastoad list_modules` and shows documentation for OpenMDAO options. (https://github.com/fast-aircraft-design/FAST-OAD/pull/287)
        - Connection of OpenMDAO variables can now be done in configuration file. (https://github.com/fast-aircraft-design/FAST-OAD/pull/263)
        - More generic code for mass breakdown plots to ease usage for custom weight models. (https://github.com/fast-aircraft-design/FAST-OAD/pull/250)
        - DataFile class has been added for convenient interaction with FAST-OAD data files. (https://github.com/fast-aircraft-design/FAST-OAD/pull/293)
        - Moved some part of code to private API. What is still public will be kept and maintained. (https://github.com/fast-aircraft-design/FAST-OAD/pull/295)
    - Bug fixes:
        - FAST-OAD was crashing when mpi4py was installed. (https://github.com/fast-aircraft-design/FAST-OAD/pull/272)
        - Output of `fastoad list_variables` can now be redirected in a file. (https://github.com/fast-aircraft-design/FAST-OAD/pull/284)
        - Activation of time-step mission computation in tutorial notebook is now functional. (https://github.com/fast-aircraft-design/FAST-OAD/pull/285)
        - Variable viewer toolbar now works correctly in JupyterLab. (https://github.com/fast-aircraft-design/FAST-OAD/pull/288)
        - N2 diagrams caused a 404 error in notebooks since OpenMDAO 3.7. (https://github.com/fast-aircraft-design/FAST-OAD/pull/289)
- Models:
    - Changes:
        - A notebook has been added that shows how to compute CeRAS-01 aircraft. (https://github.com/fast-aircraft-design/FAST-OAD/pull/275)
        - Unification of performance module. (https://github.com/fast-aircraft-design/FAST-OAD/pull/251)
            - Breguet computations are now defined using the mission input file.
            - A computed mission can now be integrated or not to the sizing process.
        - Better management of speed parameters in Atmosphere class. (https://github.com/fast-aircraft-design/FAST-OAD/pull/281)
        - More robust airfoil profile processing. (https://github.com/fast-aircraft-design/FAST-OAD/pull/256)
        - Added tuner parameter in computation of compressibility. (https://github.com/fast-aircraft-design/FAST-OAD/pull/258)

Version 0.5.4-beta
==================

- Bug fix: An infinite loop could occur if custom modules were declaring the same variable
  several times with different units or default values.


Version 0.5.3-beta
==================

- Added compatibility with OpenMDAO 3.4, which is now the minimum required
  version of OpenMDAO. (https://github.com/fast-aircraft-design/FAST-OAD/pull/231)
- Simplified call to VariableViewer. (https://github.com/fast-aircraft-design/FAST-OAD/pull/221)
- Bug fix: model for compressibility drag now takes into account sweep angle
  and thickness ratio. (https://github.com/fast-aircraft-design/FAST-OAD/pull/237)
- Bug fix: at installation, minimum version of Scipy is forced to 1.2. (https://github.com/fast-aircraft-design/FAST-OAD/pull/219)
- Bug fix: SpeedChangeSegment class now accepts Mach number as possible target. (https://github.com/fast-aircraft-design/FAST-OAD/pull/234)
- Bug fix: variable "data:weight:aircraft_empty:mass has now "kg" as unit. (https://github.com/fast-aircraft-design/FAST-OAD/pull/236)


Version 0.5.2-beta
==================

- Added compatibility with OpenMDAO 3.3. (https://github.com/fast-aircraft-design/FAST-OAD/pull/210)
- Added computation time in log info. (https://github.com/fast-aircraft-design/FAST-OAD/pull/211)
- Fixed bug in XFOIL input file. (https://github.com/fast-aircraft-design/FAST-OAD/pull/208)
- Fixed bug in copy_resource_folder(). (https://github.com/fast-aircraft-design/FAST-OAD/pull/212)

Version 0.5.1-beta
==================

- Now avoids apparition of numerous deprecation warnings from OpenMDAO.

Version 0.5.0-beta
==================

- Added compatibility with OpenMDAO 3.2.
- Added the mission performance module (currently computes a fixed standard mission).
- Propulsion models are now declared in a specific way so that another
  module can do a direct call to the needed propulsion model.

Version 0.4.2-beta
==================

- Prevents installation of OpenMDAO 3.2 and above for incompatibility reasons.
- In Breguet module, output values for climb and descent distances were 1000 times
  too large (computation was correct, though).

Version 0.4.0-beta
==================

Some changes in mass and performances components:
    - The Breguet performance model can now be adjusted through input variables
      in the "settings" section.
    - The mass-performance loop is now done through the "fastoad.loop.mtow"
      component.

Version 0.3.1-beta
==================

- Adapted the FAST-OAD code to handle OpenMDAO version 3.1.1.

Version 0.3.0-beta
==================

- In Jupyter notebooks, VariableViewer now has a column for input/output type.
- Changed base OAD process so that propulsion model can now be directly called
  by the performance module instead of being a separate OpenMDAO component (which
  is still possible, though). It prepares the import of FAST legacy
  mission-based performance model.

Version 0.2.2-beta
==================

- Changed dependency requirement to have OpenMDAO version at most 3.1.0
  (FAST-OAD is not yet compatible with 3.1.1)

Version 0.2.1-beta
==================

- Fixed compatibility with wop 1.9 for XDSM generation


Version 0.2.0b
==============

- First beta release


Version 0.1.0a
==============

- First alpha release
