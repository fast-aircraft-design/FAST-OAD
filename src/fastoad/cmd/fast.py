"""
main
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2019  ONERA/ISAE
#  FAST is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse

from fastoad.io.configuration import ConfiguredProblem


def main():
    parser = argparse.ArgumentParser(description='FAST main program')
    parser.add_argument('conf_file', type=str, help='the file for configuring the problem')
    parser.add_argument('--gen_inputs', action='store_true',
                        help='generates a template file that contains needed inputs')
    parser.add_argument('--optim', action='store_true',
                        help='runs the optimization of the problem with provided input file')
    parser.add_argument('--eval', action='store_true',
                        help='simply evaluates the problem with provided input file')

    args = parser.parse_args()

    if args.conf_file:
        problem = ConfiguredProblem()
        problem.configure(args.conf_file)

        problem.model.approx_totals()

        if args.gen_inputs:
            problem.write_needed_inputs()
        elif args.optim:
            problem.read_inputs()
            problem.run_driver()
            problem.write_outputs()
        elif args.eval:
            problem.read_inputs()
            problem.run_model()
            problem.write_outputs()


if __name__ == '__main__':
    main()
