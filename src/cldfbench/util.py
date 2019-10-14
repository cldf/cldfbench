import sys
import subprocess


def iter_requirements():
    """
    :return: generator of lines in pip's requirements.txt format, specifying packages which are \
    imported in the current python process.
    """
    imported = set(m.split('.')[0].lower() for m in sys.modules.keys())

    try:
        installed = subprocess.check_output(['pip', 'freeze'])
    except subprocess.CalledProcessError:  # pragma: no cover
        raise ValueError()

    for req in installed.decode('utf-8').split('\n'):
        if '==' in req:
            pkg = req.split('==')[0]
        elif 'egg=' in req:
            pkg = req.split('egg=')[-1]
        else:
            continue  # pragma: no cover
        if pkg.lower() in imported:
            yield req
