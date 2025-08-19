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
