"""
Backwards compatibility with supported python versions.
"""
import sys
import datetime
import functools


if (sys.version_info.major, sys.version_info.minor) >= (3, 10):  # pragma: no cover
    def entry_points_select(eps, group):
        """
        Staring with Python 3.10, `importlib.metadata.entry_points` returns `EntryPoints`."""
        return eps.select(group=group)
else:
    def entry_points_select(eps, group):  # pragma: no cover
        """In Python 3.9, `importlib.metadata.entry_points` returns a `dict`."""
        return eps.get(group, [])


if (sys.version_info.major, sys.version_info.minor) >= (3, 11):  # pragma: no cover
    # datetime.UTC was added in py3.11.
    utcnow = functools.partial(datetime.datetime.now, datetime.UTC)
else:  # pragma: no cover
    utcnow = datetime.datetime.utcnow
