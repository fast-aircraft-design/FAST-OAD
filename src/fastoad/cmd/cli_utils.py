"""Utility functions for CLI interface."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2021 ONERA & ISAE-SUPAERO
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

from distutils.util import strtobool
from typing import Callable

import click

from fastoad.cmd.exceptions import FastFileExistsError


def overwrite_option(func):
    """
    Decorator for adding the option for overwriting existing file.

    Use `force` as argument of the function.
    """
    return click.option(
        "-f",
        "--force",
        is_flag=True,
        help="Do not ask before overwriting files.",
    )(func)


def out_file_option(func):
    """
    Decorator for writing command output in a file.

    Use `out_file` and `force` as argument of the function.
    """
    return click.option(
        "-o",
        "--out_file",
        help="If provided, command output will be written in indicated file instead of "
        "being printed in terminal.",
    )(overwrite_option(func))


def _query_yes_no(question):
    """
    Ask a yes/no question via input() and return its answer as boolean.

    Keeps asking while answer is not similar to "yes" or "no"
    The returned value is True for "yes" or False for "no".
    """
    answer = None
    while answer is None:
        raw_answer = input(question + "\n")
        try:
            answer = strtobool(raw_answer)
        except ValueError:
            pass

    return answer == 1


def manage_overwrite(func: Callable, filename_func: Callable = None, **kwargs):
    """
    Runs `func`, that is expected to write a file, with provided keyword arguments `args`.

    If the run throws FastFileExistsError, a question is displayed and user is
    asked for a yes/no answer. If `yes` is given, arg["overwrite"] is set to True
    and `func` is run again.

    :param func: callable that will do the operation
    :param filename_func: a function that provides the name of written file, given the
                          value returned by func
    :param kwargs: keyword arguments for func
    :return: True if the file has been written,
    """
    written = False
    result = None
    try:
        result = func(**kwargs)
        written = True

    except FastFileExistsError as exc:
        if _query_yes_no(f'File "{exc.args[1]}" already exists. Do you want to overwrite it?'):
            kwargs["overwrite"] = True
            result = func(**kwargs)
            written = True

    if written:
        if filename_func:
            result = filename_func(result)
        if result:
            print(f'File "{result}" has been written.')
    else:
        print("No file written.")

    return written
