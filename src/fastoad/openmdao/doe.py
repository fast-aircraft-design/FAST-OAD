import contextlib
import os
import os.path as pth
import fastoad.api as oad
import openmdao.api as om
import pandas as pd


def run_doe(
    doe_driver,
    x_dict: dict,
    configuration_file: str,
    run_on_optimization: bool = False,
    doe_file_path: str = None
) -> pd.DataFrame:
    """
    Function for running Designs of Experiments (DoE) on FAST-OAD problems.

    :param doe_driver: driver to be used for running the DoE
    :param x_dict: inputs dictionary {name: {'lower': lower_bound, 'upper': upper_bound}}
    :param configuration_file: configuration file for the problem
    :param run_on_optimization: flag to run DoE on top of the optimization problem declared in the configuration file.
                                If False, the DoE is run on the model only.
    :param doe_file_path: path for saving the results
    :return: dataframe of the design of experiments results

    A classical usage of this method will be::

        driver = om.DOEDriver(om.UniformGenerator(num_samples=100))  # define the driver for the DoE
        x_dict = {"doe_variable_1": {"lower": 2000.0, "upper": 3000.0},  # define the inputs of the DoE and their bounds
                  "doe_variable_2": {"lower": 0.0, "upper": 1.0},
                  }
        df = run_doe(driver, x_dict, CONFIGURATION_FILE_NAME)  # run DoE on the model defined in the configuration file
        df.describe()  # display statistics of the results
    """

    class SubProbComp(om.ExplicitComponent):
        """
        Sub-problem component for nested optimization.
        Inspired from https://github.com/OpenMDAO/RevHack2020/blob/master/solution_approaches/sub_problems.md
        """

        def initialize(self):
            self.options.declare("conf")
            self.options.declare("x_list")
            self.options.declare("y_list")

        def setup(self):
            # create a sub-problem to use later in the compute
            conf = self.options["conf"]
            prob = conf.get_problem(read_inputs=True)  # get conf file (design variables, objective, driver...)
            p = self._prob = prob
            p.setup()

            # define the i/o of the component
            x_list = self._x_list = self.options["x_list"]
            y_list = self._y_list = self.options["y_list"]

            for x in x_list:
                self.add_input(x)

            for y in y_list:
                self.add_output(y)

            # set counter and output variable for recording optimization failure or success
            self._fail_count = 0
            self.add_output('success')

            self.declare_partials("*", "*", method="fd")

        def compute(self, inputs, outputs):
            p = self._prob
            x_list = self._x_list
            y_list = self._y_list

            for x in x_list:
                p[x] = inputs[x]

            with open(os.devnull, "w") as f, contextlib.redirect_stdout(
                f
            ):  # turn off convergence messages
                fail = p.run_driver()

            for y in y_list:
                outputs[y] = p[y]

            if fail:
                self._fail_count += 1
            outputs['success'] = not fail

    # Get problem definition
    conf = oad.FASTOADProblemConfigurator(configuration_file)

    # Get inputs and outputs names
    x_list = list(x_dict.keys())
    prob = conf.get_problem(read_inputs=True)
    prob.setup()
    prob.final_setup()
    outputs = prob.model.get_io_metadata(
            "output", excludes="_auto_ivc.*"
        )
    indep_outputs = prob.model.get_io_metadata(
            "output",
            tags=["indep_var", "openmdao:indep_var"],
            excludes="_auto_ivc.*",
        )
    for abs_name, metadata in indep_outputs.items():
        del outputs[abs_name]
    y_list = [y['prom_name'] for y in outputs.values()]

    # Declare nested optimization if DoE must be run on top of the optimization problem
    if run_on_optimization and conf.get_optimization_definition():
        prob = om.Problem()  # redefine DoE problem with optimization as a sub-problem
        prob.model.add_subsystem(
            "sub_prob",
            SubProbComp(
                conf=conf,
                x_list=x_list,
                y_list=y_list,
            ),
            promotes=["*"],
        )
        prob.setup()

    # Add input parameters for DoE
    for name, parameters in x_dict.items():
        prob.model.add_design_var(
            name, lower=parameters["lower"], upper=parameters["upper"]
        )

    # Setup driver
    prob.driver = doe_driver

    # Attach recorder to the driver
    if os.path.exists("cases.sql"):
        os.remove("cases.sql")
    prob.driver.add_recorder(om.SqliteRecorder("cases.sql"))
    prob.driver.recording_options["includes"] = ["*"]

    # Run problem
    prob.setup()
    with open(os.devnull, "w") as f, contextlib.redirect_stdout(
            f
    ):  # turn off convergence messages
        prob.run_driver()
    prob.cleanup()

    # Get results from recorded cases
    df = pd.DataFrame()
    cr = om.CaseReader("cases.sql")
    cases = cr.list_cases("driver", out_stream=None)
    for case in cases:
        df_case = pd.DataFrame(cr.get_case(case).outputs)  # variables values for the case
        if not run_on_optimization:
            df_case["success"] = cr.get_case(case).success  # success flag for the case
            # (for optimization problems, flag is already defined as an output variable of SubProbComp)
        df = pd.concat([df, df_case], ignore_index=True)
    os.remove("cases.sql")

    # Print number of failures
    fail_count = df["success"][df["success"] == 0].count()
    if fail_count > 0:
        print("%d out of %d cases failed. Check 'success' flag in DataFrame." % (fail_count, len(cases)))

    # save to .csv
    if not doe_file_path:
        doe_file_path = pth.join(pth.dirname(configuration_file), "doe.csv")
    doe_file_path = pth.abspath(doe_file_path)
    df.to_csv(doe_file_path)

    return df
