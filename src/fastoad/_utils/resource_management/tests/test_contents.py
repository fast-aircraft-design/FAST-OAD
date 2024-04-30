#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2024 ONERA & ISAE-SUPAERO
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

from pathlib import Path

from ..contents import PackageReader


def test_get_package_contents():
    # Normal package
    reader = PackageReader(__package__)
    assert reader.is_package
    assert not reader.is_module
    assert not reader.has_error

    assert Path(__file__).name in reader.contents
    assert "__init__.py" in reader.contents
    assert "resources" in reader.contents

    # File
    reader = PackageReader(__name__)
    assert not reader.is_package
    assert reader.is_module
    assert not reader.has_error
    assert reader.contents == []

    # Bad package name
    reader = PackageReader(__package__ + ".bad")
    assert not reader.is_package
    assert not reader.is_module
    assert not reader.has_error
    assert reader.contents == []

    # Empty name
    reader = PackageReader("")
    assert not reader.is_package
    assert not reader.is_module
    assert not reader.has_error
    assert reader.contents == []

    reader = PackageReader(None)
    assert not reader.is_package
    assert not reader.is_module
    assert not reader.has_error
    assert reader.contents == []
