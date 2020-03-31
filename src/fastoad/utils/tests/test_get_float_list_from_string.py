#  This file is part of FAST : A framework for rapid Overall Aircraft Design
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

from ..strings import get_float_list_from_string


def test_get_float_list_from_string():
    assert [1.0, 2.0, 3.0] == get_float_list_from_string("[ 1, 2., 3]")
    assert [[1.0, 2.0], [3.0, 4.0]] == get_float_list_from_string("[[ 1, 2.],[  3, 4]]")
    assert [[1.0, 2.0], [3.0, 4.0]] == get_float_list_from_string("[[ 1,\n 2.],\n[  3, 4]]\n")
    assert [1.0, 2.0, 3.0] == get_float_list_from_string(" 1, 2., 3")
    assert [1.0, 2.0] == get_float_list_from_string(" 1 2 ")
    assert [1.0] == get_float_list_from_string(" 1 dummy 2 ")
    assert [1.0] == get_float_list_from_string(" 1     ")
    assert get_float_list_from_string(" dummy ") is None
    assert get_float_list_from_string("") is None
