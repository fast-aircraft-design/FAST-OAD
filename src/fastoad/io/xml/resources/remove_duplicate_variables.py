"""
Enables to remove duplicate variables from text file
"""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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
from os import remove


def remove_duplicate(input_file_name: str):
    """
    Removes duplicate lines in a text file

    """
    input_file = open(input_file_name, "r")

    # Store all the variables
    stored_lines = []
    for line in input_file:
        if line not in stored_lines:
            stored_lines.append(line)
    # Delete the file
    input_file.close()
    remove(input_file_name)

    # Create new file
    input_file = open(input_file_name, "w")

    # Write non duplicate lines
    for line in stored_lines:
        input_file.write(str(line))

    input_file.close()


if __name__ == "__main__":

    remove_duplicate("legacy1.txt")
