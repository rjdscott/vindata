"""VinData REST API."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("vindata-api")
except PackageNotFoundError:
    __version__ = "0.0.0"
