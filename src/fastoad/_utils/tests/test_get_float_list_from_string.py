from ..strings import get_float_list_from_string


def test_get_float_list_from_string():
    assert [1.0, 2.0, 3.0] == get_float_list_from_string("[ 1, 2., 3]")
    assert [[1.0, 2.0], [3.0, 4.0]] == get_float_list_from_string("[[ 1, 2.],[  3, 4]]")
    assert [[1.0, 2.0], [3.0, 4.0]] == get_float_list_from_string("[[ 1,\n 2.],\n[  3, 4]]\n")
    assert [1.0, 2.0, 3.0] == get_float_list_from_string(" 1, 2., 3")
    assert [1.0, 2.0] == get_float_list_from_string(" 1 2 ")
    assert [1.0] == get_float_list_from_string(" 1     ")
    assert get_float_list_from_string(" dummy ") is None
    assert get_float_list_from_string("") is None
