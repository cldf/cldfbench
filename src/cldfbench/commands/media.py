"""
Download {and pack} (filtered) media files {and prepare release on Zenodo}

General workflow:
 (1) call cldfbench media -l
       to get an overview of all media files incl. mimetypes and sizes
 (2) call cldfbench media
       to download all media files
     or
     call cldfbench media --mimetype foo,bar
       to download only those media files which matches mimetypes
       - possible filter(s) could be:
         -- file extentions like wav,mp3,pdf, ...
         -- mimetypes like audio/ogg,audio/x-wav,application/pdf, ...
         -- mimetype classes like audio/,video/, ...
 (3) call cldfbench media --create-release --parent-doi {--mimetype foo,bar}
       {to download and} create the release directory with the zipped media files,
       a README.md and zenodo.json
       - step (2) and (3) can be combined
       - a --parent-doi is required
 (4) check README.md and zenodo.json and modify if necessary
 (5) upload the files media.zip and README.md to Zenodo and remember the deposit ID (number after
     last slash)
       - it is necessary to log in via correct zenodo user and to have the corresponding access
         token in your environment
"""
import dataclasses
import os
import re
import html
import time
import pathlib
import zipfile
import itertools
import threading
import collections
from datetime import datetime
from urllib.request import urlretrieve

from clldutils import jsonlib
from clldutils.clilib import PathType, ParserError
from clldutils.misc import format_size, nfilter
from clldutils.path import md5, git_describe
from csvw.dsv import UnicodeWriter
from csvw.datatypes import anyURI
import tqdm

from cldfbench.cli_util import add_dataset_spec, get_dataset
from cldfbench.datadir import DataDir
from cldfbench.metadata import get_creators_and_contributors

ZENODO_DOI_PATTERN = re.compile(r'10\.5281/zenodo\.(?P<id>[0-9]+)$')
MEDIA = 'media'
ZENODO_FILE_NAME = 'zenodo.json'
COMMUNITIES = ['lexibank']
LICENCE = 'This dataset is licensed under {0}.'
INDEX_CSV = 'index.csv'

README = """## {title}

Supplement to dataset \"{ds_title}\" ({doi}) containing the {media} files{formats}
as compressed folder *{media}.zip*.

The {media} files are structured into separate folders named by the first two characters of the
file name. Each individual {media} file is named according to the ID specified in MediaTable.
A (filtered) version of which is included as {index}
in the *{media}.zip* file containing the additional column *local_path*.

{license}
"""

DESCRIPTION = "{title}{formats}{supplement_to} {descr} {online}"


def register(parser):  # pylint: disable=C0116
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
        help='Directory to which to download the media files and to create the to be released '
             'data.',
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
        help='DOI to which this release refers (format 10.5281/zenodo.1234567). It is required '
             'for --create-release.',
    )
    parser.add_argument(
        '--create-release',
        help='Switch to create ID_{0} directory containing {0}.zip, README.md and {1} for '
             'releasing on zenodo. Cannot be used with --update-zenodo.'.format(
            MEDIA, ZENODO_FILE_NAME),  # noqa: E122
        action='store_true',
        default=False,
    )
    parser.add_argument(
        '--debug',
        help='Switch to work with max. 500 media files and with sandbox.zenodo for testing ONLY',
        action='store_true',
        default=False,
    )


def _create_download_thread(url, target):
    global download_threads
    download_threads = []

    def _download(url, target):
        assert not target.exists()
        urlretrieve(url, str(target))

    while threading.active_count() > 7:
        time.sleep(0.1)  # pragma: no cover

    download_thread = threading.Thread(target=_download, args=(url, target))
    download_thread.start()
    download_threads.append(download_thread)


def _valid_input(media_table, args) -> bool:
    if media_table is None:  # pragma: no cover
        args.log.error('Dataset has no MediaTable or media.csv')
        return False
    if args.parent_doi and not ZENODO_DOI_PATTERN.match(args.parent_doi):
        args.log.error('Invalid passed DOI')
        return False
    if args.create_release:
        if not args.parent_doi:
            args.log.error('The corresponding DOI is required (via --parent-doi).')
            return False
    return True


@dataclasses.dataclass
class FileStats:
    size: dict[str, int] = dataclasses.field(default_factory=collections.Counter)
    number: dict[str, int] = dataclasses.field(default_factory=collections.Counter)
    extensions: set = dataclasses.field(default_factory=set)
    paths: list[pathlib.Path] = dataclasses.field(default_factory=list)

    def update(self, row, f_ext):
        m = f"{row['mimetype']} ({f_ext})"
        self.size[m] += int(row['size'])
        self.number.update([m])
        self.extensions.add(f_ext.lower())

    def print(self):
        for k, v in self.size.most_common():
            print('\t'.join([k.ljust(20), str(self.number[k]), format_size(v)]))


def run(args):  # pylint: disable=C0116
    ds = get_dataset(args)
    ds_cldf = ds.cldf_reader()

    media_table = ds_cldf.get('MediaTable', ds_cldf.get('media.csv', None))
    if not _valid_input(media_table, args):
        raise ParserError

    mime_types = [m.strip() for m in nfilter(args.mimetype.split(','))] if args.mimetype else []

    media_dir = args.out / MEDIA
    media_dir.mkdir(exist_ok=True)
    stats = FileStats()

    with UnicodeWriter(media_dir / INDEX_CSV if not args.list else None) as w:
        for i, row in enumerate(tqdm.tqdm(media_table, desc='Getting media items')):
            if args.debug and i > 500:
                break  # pragma: no cover
            row['URL'] = anyURI.to_string(ds_cldf.get_row_url(media_table, row))
            #
            # FIXME: Don't assume URLs without query!
            #
            f_ext = row['URL'].split('.')[-1].lower()
            if any((not mime_types,
                    f_ext in mime_types,
                    any(row['mimetype'].startswith(x) for x in mime_types))):
                stats.update(row, f_ext)
                if not args.list:
                    d = media_dir / row['ID'][:2]
                    d.mkdir(exist_ok=True)
                    target = d / '.'.join([row['ID'], f_ext])
                    row['local_path'] = pathlib.Path(row['ID'][:2]) / target.name
                    if i == 0:
                        w.writerow(row)
                    w.writerow(row.values())
                    stats.paths.append(target)
                    if (not target.exists()) or md5(target) != row['ID']:
                        _create_download_thread(row['URL'], target)

    stats.paths.append(media_dir / INDEX_CSV)

    if args.list:
        stats.print()
        return

    # Waiting for the download threads to finish
    if 'download_threads' in globals():
        for t in download_threads:
            t.join()

    if args.create_release:
        release_dir = args.out / f'{ds.id}_{MEDIA}'
        release_dir.mkdir(exist_ok=True)
        _zip_media(release_dir, stats.paths, args)
        _release_metadata(release_dir, ds, args, stats.extensions)


def _zip_media(release_dir, media, args):
    try:
        with zipfile.ZipFile(release_dir / f'{MEDIA}.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in tqdm.tqdm(media, desc=f'Creating {MEDIA}.zip'):
                zf.write(f, str(os.path.relpath(str(f), str(args.out))))
    except Exception as e:  # pragma: no cover
        args.log.error(e)
        raise


def _release_metadata(release_dir, ds, args, used_file_extensions):
    version_v = git_describe('.').split('-')[0]
    git_url = [r for r in ds.repo.repo.remotes if r.name == 'origin'][0].url.replace('.git', '')
    with (jsonlib.update(
            release_dir / ZENODO_FILE_NAME, indent=4, default=collections.OrderedDict()) as md):
        contribs = ds.dir / 'CONTRIBUTORS.md'
        creators, contributors = get_creators_and_contributors(
            contribs.read_text(encoding='utf8') if contribs.exists() else '', strict=False)
        if creators:
            md['creators'] = [_contrib(p) for p in creators]
        if contributors:
            md['contributors'] = [_contrib(p) for p in contributors]
        communities = list(itertools.chain(
            [r["identifier"] for r in md.get("communities", [])],
            [c.strip() for c in nfilter(args.communities.split(','))],
            COMMUNITIES))
        if communities and not args.debug:
            md['communities'] = [
                {"identifier": community_id} for community_id in sorted(set(communities))]
        md.update(
            {
                'title': f'{ds.metadata.title} {MEDIA.title()} Files',
                'access_right': 'open',
                'keywords': sorted(set(md.get('keywords', []) + ['linguistics'])),
                'upload_type': 'dataset',
                'publication_date': datetime.today().strftime('%Y-%m-%d'),
                'version': version_v.replace('v', ''),
                'related_identifiers': [],
            }
        )
        _add_rel_id(md, 'url', f'{git_url}/tree/{version_v}', 'isSupplementTo')

        supplement_to = ''
        if args.parent_doi:
            _add_rel_id(md, 'doi', args.parent_doi, 'isPartOf')
            supplement_to = f" - Supplement to dataset " \
                            f"<a href='https://doi.org/{args.parent_doi}'>{ds.metadata.title}</a> "
        if ds.metadata.url:
            _add_rel_id(md, 'url', ds.metadata.url, 'isAlternateIdentifier')

        formats = ', '.join(sorted(used_file_extensions))
        md['description'] = html.escape(DESCRIPTION.format(
            url=ds.metadata.url or '',
            formats=' ({formats})' if formats else '',
            title=md['title'],
            supplement_to=supplement_to,
            descr='<br /><br />' + ds.metadata.description if ds.metadata.description else '',
            online=f"<br /><br />Available online at: "
                   f"<a href='{ds.metadata.url}'>{ds.metadata.url}</a>" if ds.metadata.url else ''))

        if ds.metadata.zenodo_license:
            md['license'] = {'id': ds.metadata.zenodo_license}

        DataDir(release_dir).write('README.md', README.format(
            title=md['title'],
            doi=f'https://doi.org/{args.parent_doi}',
            ds_title=ds.metadata.title,
            license=LICENCE.format(
                ds.metadata.zenodo_license) if ds.metadata.zenodo_license else '',
            formats=f' ({formats})' if formats else '',
            media=MEDIA,
            index=INDEX_CSV))


def _contrib(d):
    return {k: v for k, v in d.items() if k in {'name', 'affiliation', 'orcid', 'type'}}


def _add_rel_id(md, scheme, identifier, relation):
    md['related_identifiers'].append(
        {'scheme': scheme, 'identifier': identifier, 'relation': relation})
