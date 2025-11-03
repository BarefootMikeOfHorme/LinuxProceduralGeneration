from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("vaultmind-forge")
except PackageNotFoundError:
    __version__ = "0.1.0"