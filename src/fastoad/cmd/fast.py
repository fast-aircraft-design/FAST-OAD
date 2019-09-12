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
import os.path as pth

from fastoad.io.configuration import ConfiguredProblem
from fastoad.io.xml import OpenMdaoXmlIO


def main():
    parser = argparse.ArgumentParser(description='FAST main program')
    parser.add_argument('conf_file', type=str, help='the file for configuring the problem')
    parser.add_argument('--gen_input_file',
                        help='generates a template file that contains needed inputs')
    parser.add_argument('--input_file', dest='input_file',
                        help='runs the problem with provided input file')

    args = parser.parse_args()

    if args.conf_file:
        problem = ConfiguredProblem()
        problem.load(args.conf_file)
        problem.setup()

        if args.gen_input_file:
            writer = OpenMdaoXmlIO(pth.abspath(args.gen_input_file))
            writer.write_inputs(problem)


if __name__ == '__main__':
    main()
