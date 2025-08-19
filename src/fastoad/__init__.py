import sys

if sys.version_info >= (3, 10):
    import importlib.metadata as importlib_metadata
else:
    import importlib_metadata

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = "FAST-OAD-core"
    __version__ = importlib_metadata.distribution(dist_name).version
except importlib_metadata.PackageNotFoundError:
    __version__ = "unknown"
finally:
    del importlib_metadata
