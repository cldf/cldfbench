'''
Downloads {and packs} (filtered) media files {and prepare release on Zenodo}
'''

import collections
import html
import mimetypes
import os
import pathlib
import subprocess
import threading
import time
import tqdm
import zipfile


from urllib.request import urlretrieve
from csvw.dsv import UnicodeWriter

from cldfbench.cli_util import add_dataset_spec, get_dataset
from cldfbench.datadir import DataDir
from cldfbench.metadata import get_creators_and_contributors
from clldutils import jsonlib
from clldutils.clilib import PathType
from clldutils.misc import format_size, nfilter
from clldutils.path import md5, git_describe


MEDIA = 'media'
ZENODO_FILE_NAME = 'zenodo.json'
COMMUNITIES = ['lexibank']
LISENCE = "This dataset is licensed under {0}."

README = """## {title}

This dataset contains the {media} files{formats} of the project [{ds_title}]({git_url})
as compressed folder *{media}.zip*.

The {media} files are structured into separate folders named by the first two characters of the file name.
Each individual {media} file is named according to the ID specified in the file
[media.csv]({git_url}/blob/master/cldf/media.csv) whose (filtered) version is part of this ZIP archive
containing the additional column *local_path*.

{license}
"""

DESCRIPTION = "{title}{formats}{supplement_to}"\
    + "{descr}"\
    + "<br /><br />Available online at: <a href='{url}'>{url}</a>"\
    + "<br />GitHub repository: <a href='{git_url}'>{git_url}/tree/{version}</a>"


def register(parser):
    add_dataset_spec(parser, multiple=True)
    parser.add_argument(
        '-m', '--mimetype',
        help='Comma-separated list of desired mimetypes/extensions/classes; default {all}',
        default=None,
    )
    parser.add_argument(
        '-l', '--list',
        help='List available mimetypes and file number and size',
        action='store_true',
        default=False,
    )
    parser.add_argument(
        '-o', '--out',
        help='Directory to which to download the media files.',
        type=PathType(type='dir'),
        default=pathlib.Path('.')
    )
    parser.add_argument(
        '-c', '--communities',
        default='',
        help='Comma-separated list of communities to which the dataset should be submitted',
    )
    parser.add_argument(
        '-p', '--parent-doi',
        default='',
        help='DOI to which this release refers - format 10.5281/zenodo.4309141',
    )
    parser.add_argument(
        '--create-release',
        help="Switch to create ID_{0} directory containing {0}.zip, README.md and zenodo.json for releasing on zenodo.".format(MEDIA),
        action='store_true',
        default=False,
    )
    parser.add_argument(
        '--update-zenodo',
        help="Deposit ID to update metadata by using ID_{0}/zendo.json.".format(MEDIA),
        required=False,
        default=None,
    )


def _create_download_thread(url, target):
    global download_threads
    download_threads = []

    def _download(url, target):
        assert not target.exists()
        urlretrieve(url, str(target))

    while threading.active_count() > 7:
        time.sleep(0.1)

    download_thread = threading.Thread(target=_download, args=(url, target))
    download_thread.start()
    download_threads.append(download_thread)


def _git_repo_url(dir_, git_command='git'):
    dir_ = pathlib.Path(dir_)
    if not dir_.exists():
        raise ValueError('cannot get repo data of non-existent directory')
    dir_ = dir_.resolve()
    cmd = [git_command, '--git-dir=%s' % dir_.joinpath('.git'), 'config', '--get', 'remote.origin.url']
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if p.returncode == 0:
            res = stdout.strip()  # pragma: no cover
        else:
            raise ValueError(stderr)
    except (ValueError, FileNotFoundError):
        res = dir_.name
    if not isinstance(res, str):
        res = res.decode('utf8')
    return res.replace('.git', '')


def run(args):

    ds = get_dataset(args)
    ds_cldf = ds.cldf_reader()

    if ds_cldf.get('media.csv', None) is None:
        args.log.error('Dataset has no media.csv')
        return

    mime_types = None
    if args.mimetype:
        mime_types = [m.strip() for m in nfilter(args.mimetype.split(','))]

    if args.list:
        size = collections.Counter()
        number = collections.Counter()
    else:
        media_dir = args.out / MEDIA
        media_dir.mkdir(exist_ok=True)
        media = []

    used_file_extensions = set()
    with UnicodeWriter(media_dir / 'media.csv') as w:
        for i, row in enumerate(tqdm.tqdm([r for r in ds_cldf['media.csv']], desc='Getting {0} items'.format(MEDIA))):
            url = ds_cldf.get_row_url('media.csv', row)
            f_ext = url.split('.')[-1]
            if (mime_types is None) or f_ext in mime_types\
                    or any(row['mimetype'].startswith(x) for x in mime_types):
                if args.list:
                    m = '{0} ({1})'.format(row['mimetype'], f_ext)
                    size[m] += int(row['size'])
                    number.update([m])
                else:
                    used_file_extensions.add(f_ext.lower())
                    d = media_dir / row['ID'][:2]
                    d.mkdir(exist_ok=True)
                    fn = '.'.join([row['ID'], f_ext])
                    target = d / fn
                    row['local_path'] = str(target)
                    if i == 0:
                        w.writerow(row)
                    else:
                        w.writerow(row.values())
                    media.append(target)
                    if (not target.exists()) or md5(target) != row['ID']:
                        _create_download_thread(url, target)

    if args.list:
        for k, v in size.most_common():
            print('\t'.join([k.ljust(20), str(number[k]), format_size(v)]))
        return

    # Waiting for the download threads to finish
    if 'download_threads' in globals():
        for t in download_threads:
            t.join()

    release_dir = args.out / '{0}_{1}'.format(ds.id, MEDIA)

    if args.create_release:
        assert media_dir.exists(), 'No folder "{0}" found in {1}'.format(MEDIA, media_dir.resolve())

        release_dir.mkdir(exist_ok=True)

        media.append(media_dir / 'media.csv')

        try:
            zipf = zipfile.ZipFile(
                str(release_dir / '{0}.zip'.format(MEDIA)), 'w', zipfile.ZIP_DEFLATED)
            fp = args.out
            for f in tqdm.tqdm(media, desc='Creating {0}.zip'.format(MEDIA)):
                zipf.write(str(f), str(os.path.relpath(f, fp)))
            zipf.close()
        except Exception as e:
            args.log.error(e)
            raise

        def _contrib(d):
            return {k: v for k, v in d.items() if k in {'name', 'affiliation', 'orcid', 'type'}}

        version_v = git_describe('.').split('-')[0]
        version = version_v.replace('v', '')
        git_url = _git_repo_url('.')
        with jsonlib.update(release_dir / ZENODO_FILE_NAME, indent=4, default=collections.OrderedDict()) as md:
            contribs = ds.dir / 'CONTRIBUTORS.md'
            creators, contributors = get_creators_and_contributors(
                contribs.read_text(encoding='utf8') if contribs.exists() else '', strict=False)
            if creators:
                md['creators'] = [_contrib(p) for p in creators]
            if contributors:
                md['contributors'] = [_contrib(p) for p in contributors]
            communities = [r["identifier"] for r in md.get("communities", [])] + \
                [c.strip() for c in nfilter(args.communities.split(','))] + \
                COMMUNITIES
            if communities:
                md['communities'] = [
                    {"identifier": community_id} for community_id in sorted(set(communities))]
            md.update(
                {
                    'title': '{0} {1} Files'.format(ds.metadata.title, MEDIA.title()),
                    'access_right': 'open',
                    'keywords': sorted(set(md.get('keywords', []) + ['linguistics'])),
                    'upload_type': 'dataset',
                    'version': version,
                    'related_identifiers': [
                        {
                            'scheme': 'url',
                            'identifier': '{0}/tree/{1}'.format(git_url, version_v),
                            'relation': 'isSupplementTo'
                        },
                    ],
                }
            )
            if args.parent_doi:
                md['related_identifiers'].append({
                    'scheme': 'doi', 'identifier': args.parent_doi, 'relation': 'isPartOf'})
                supplement_to = " - Supplement to the project <a href='https://doi.org/{0}'>{1}</a> ".format(
                    args.parent_doi, ds.metadata.title)
            else:
                args.log.warn('No parent DOI passed')
                supplement_to = " - Supplement to the project {0} ".format(ds.metadata.title)
            if ds.metadata.url:
                md['related_identifiers'].append({
                    'scheme': 'url', 'identifier': ds.metadata.url, 'relation': 'isAlternateIdentifier'})

            formats = ', '.join(sorted(used_file_extensions))
            descr = '<br />' + ds.metadata.description if ds.metadata.description else ''
            md['description'] = html.escape(DESCRIPTION.format(
                git_url=git_url,
                url=ds.metadata.url if ds.metadata.url else '',
                version=version_v,
                formats=' ({0})'.format(formats) if formats else '',
                title=md['title'],
                supplement_to=supplement_to,
                descr=descr))

            license_md = ''
            if ds.metadata.zenodo_license:
                md['license'] = {'id': ds.metadata.zenodo_license}
                license_md = LISENCE.format(ds.metadata.zenodo_license)

            DataDir(release_dir).write('README.md', README.format(
                title=md['title'],
                git_url=git_url,
                ds_title=ds.metadata.title,
                license=license_md,
                formats=' ({0})'.format(formats) if formats else '',
                media=MEDIA))
