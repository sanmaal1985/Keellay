"""Locate the method files (contracts, formats, procedures) that ship with Keellay."""

from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent


def method_dir() -> tuple[Path, bool]:
    """Return the method directory and whether it is the copy bundled in the installed package.

    An installed wheel carries the method inside the package. An editable install or a source checkout reads it
    from the repository root instead.
    """
    bundled = _PACKAGE_DIR / "method"
    if bundled.is_dir():
        return bundled, True
    source = _PACKAGE_DIR.parents[1] / "method"
    if source.is_dir():
        return source, False
    raise FileNotFoundError("Keellay method files not found: neither in the package nor in a source checkout")
