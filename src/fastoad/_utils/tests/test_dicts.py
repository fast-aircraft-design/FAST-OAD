#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2023 ONERA & ISAE-SUPAERO
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

from ..dicts import AbstractNormalizedDict


class DictWithLowerCaseKeys(AbstractNormalizedDict):
    @staticmethod
    def normalize(key):
        return key.lower()


def test_normalized_dict():
    for d in [
        DictWithLowerCaseKeys({"Aa": "Aa", "bB": "bB"}),
        DictWithLowerCaseKeys(Aa="Aa", bB="bB"),
        DictWithLowerCaseKeys([("Aa", "Aa"), ("bB", "bB")]),
        DictWithLowerCaseKeys([("Aa", "Aa")], bB="bB"),
    ]:
        print(d)

        assert list(d.keys()) == ["aa", "bb"]
        assert list(d.values()) == ["Aa", "bB"]

        d["cC"] = "cC"
        assert list(d.keys()) == ["aa", "bb", "cc"]
        assert list(d.values()) == ["Aa", "bB", "cC"]

        del d["bb"]
        assert list(d.keys()) == ["aa", "cc"]
        assert list(d.values()) == ["Aa", "cC"]

        assert "aa" in d
        assert "Aa" in d
