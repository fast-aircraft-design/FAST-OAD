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
