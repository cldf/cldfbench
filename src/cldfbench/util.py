"""
Utilities.
"""
import sys
import pathlib
import platform
import subprocess
import importlib.metadata
from typing import Literal, Union
from collections.abc import Iterable, Generator

import termcolor

from ._compat import entry_points_select


def colored(color: Literal['red', 'blue'], text, **kw):
    """Make termcolor.colored amenable to currying via functools.partial."""
    return termcolor.colored(text, color, **kw)


def get_entrypoints(group: str) -> Iterable[importlib.metadata.EntryPoint]:
    """Get registered entry points for a group."""
    return entry_points_select(importlib.metadata.entry_points(), group)


def iter_aligned(
        pairs: Iterable[Union[tuple[str, str], list[str]]],
        prefix: str = '',
        minspace: int = 1,
) -> Generator[str, None, None]:
    """
    >>> print("\n".join(iter_aligned([('abc', '12'), ('x', '1234')], prefix='+')))
    +abc 12
    +x   1234
    """
    pairs = list(pairs)  # make sure we can iterate twice over `pairs`
    if pairs:
        maxlabel = max(len(p[0]) for p in pairs) + minspace
        for p in pairs:
            yield f"{prefix}{p[0].ljust(maxlabel)}{p[1] or ''}"


def iter_requirements() -> Generator[str, None, None]:
    """
    :return: generator of lines in pip's requirements.txt format, specifying packages which are \
    imported in the current python process.
    """
    imported = set(m.split('.')[0].lower() for m in sys.modules)
    pip = pathlib.Path(sys.executable).parent / 'pip'

    if platform.system() == "Windows":
        pip = pip.with_suffix(".exe")  # pragma: no cover

    if not pip.exists():  # pragma: no cover
        pip = pathlib.Path(sys.executable).parent / 'pip3'

        if platform.system() == "Windows":
            pip = pip.with_suffix(".exe")
    if not pip.exists():  # pragma: no cover
        return

    try:
        installed = subprocess.check_output([str(pip), 'freeze'])
    except subprocess.CalledProcessError as e:  # pragma: no cover
        raise ValueError() from e

    for req in installed.decode('utf-8').split('\n'):
        if '==' in req:
            pkg = req.split('==')[0]
        elif 'egg=' in req:
            pkg = req.split('egg=')[-1]  # pragma: no cover
        else:
            continue  # pragma: no cover
        if (pkg.lower() in imported) or (pkg.lower().replace('python-', '') in imported):
            yield req
