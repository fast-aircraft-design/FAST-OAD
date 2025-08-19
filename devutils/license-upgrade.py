# This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
# Copyright (c) 2025 ONERA & ISAE-SUPAERO
# FAST-OAD is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")  # Check or fix flag
    parser.add_argument("files", nargs="*")  # Files to check

    args = parser.parse_args()

    cmd = [
        "insert_license",
        "--license-filepath",
        "license-header.txt",
        "--use-current-year",
    ] + args.files

    if args.check:
        # In check mode, capture output and fail if changes needed
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 or result.stdout.strip():
            print(
                "Some files have incorrect license header.\nRun locally 'pre-commit run license-headers-fix --all-files' to fix automatically"
            )
            return 1
        print("All license headers are up to date")
        return 0
    else:
        # In fix mode, run normally
        return subprocess.run(cmd).returncode


if __name__ == "__main__":
    sys.exit(main())
