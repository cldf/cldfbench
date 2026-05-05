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
import functools
import os
import re
import html
import shutil
import time
import pathlib
import zipfile
import itertools
import threading
import collections
from collections.abc import Generator
import dataclasses
from typing import Optional, Any
from datetime import datetime
from urllib.request import urlretrieve
from urllib.parse import urlparse

import csvw
from csvw.datatypes import anyURI
from csvw.dsv import UnicodeWriter
from clldutils import jsonlib
from clldutils.clilib import PathType, ParserError
from clldutils.misc import format_size, nfilter
from clldutils.path import md5, git_describe
from pycldf import Dataset as CLDFDataset
import tqdm

from cldfbench.cli_util import add_dataset_spec, get_dataset, set_creators_and_contributors
from cldfbench.datadir import DataDir

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
        '--debug',
        help='Switch to work with max. 500 media files and with sandbox.zenodo for testing ONLY',
        action='store_true',
        default=False,
    )


def _create_download_thread(url, target, download_threads):
    def _download(url, target):
        assert not target.exists()
        urlretrieve(url, str(target))

    while threading.active_count() > 7:
        time.sleep(0.1)  # pragma: no cover

    download_thread = threading.Thread(target=_download, args=(url, target))
    download_thread.start()
    download_threads.append(download_thread)


@dataclasses.dataclass(frozen=True)
class Row:
    """A row in a media table with info about the location of the associated file."""
    id: str
    mimetype: str
    data: dict[str, Any]
    url: Optional[str] = None
    local_path: Optional[pathlib.Path] = None

    @property
    def ext(self) -> str:
        """Filename extension gleaned from the URL"""
        return urlparse(self.data['URL']).path.split('.')[-1].lower()

    def download(self, target: pathlib.Path, download_threads: list):
        """Retrieve the associated media file either by copy or by doanload."""
        if self.local_path:
            shutil.copy(self.local_path, target)
        else:
            _create_download_thread(self.url, target, download_threads)


@dataclasses.dataclass
class MediaTableSpec:
    """A table together with column access info."""
    table: csvw.Table
    id_col: str
    media_type_col: str
    _ds: CLDFDataset

    @classmethod
    def from_dataset(cls, ds_cldf) -> 'MediaTableSpec':
        """
        A dataset may contain a regular MediaTable component, or just a table with url media.csv.
        """
        media_table = ds_cldf.get('MediaTable', ds_cldf.get('media.csv', None))
        if media_table is None:
            raise ValueError()  # pragma: no cover

        col_names = {'Media_Type': 'mimetype', 'id': 'ID'}
        for prop in col_names:
            col = ds_cldf.get(('MediaTable', prop))
            if col:
                col_names[prop] = col.name
        return cls(media_table, col_names['id'], col_names['Media_Type'], _ds=ds_cldf)

    def __iter__(self) -> Generator[Row, None, None]:
        for row in self.table:
            row['URL'] = anyURI.to_string(self._ds.get_row_url(self.table, row))
            url, local_src = row['URL'], None
            if not row['URL'].startswith('http'):
                url = None
                local_src = self._ds.directory / row['URL']
                if not local_src.exists():
                    continue
            yield Row(row[self.id_col], row[self.media_type_col], row, url, local_src)


def _valid_input(args) -> bool:
    if args.parent_doi and not ZENODO_DOI_PATTERN.match(args.parent_doi):
        args.log.error('Invalid passed DOI')
        return False
    if not args.list:
        if not args.parent_doi:
            args.log.error('The corresponding DOI is required (via --parent-doi).')
            return False
    return True


@dataclasses.dataclass(frozen=True)
class File:
    """Metadata about a media file."""
    path: pathlib.Path
    mimetype: Optional[str] = None
    size: Optional[int] = None

    @functools.cached_property
    def ext(self) -> str:
        """Filename extension, aka suffix without the dot."""
        return self.path.suffix.replace('.', '')

    @property
    def key(self) -> str:
        """Filetype formatted as human-readable string."""
        return f"{self.mimetype} ({self.ext})" if self.mimetype else None


@dataclasses.dataclass
class MediaDir:
    """A container for media file metadata."""
    path: pathlib.Path
    files: list[File] = dataclasses.field(default_factory=list)
    rows: list[dict[str, Any]] = dataclasses.field(default_factory=list)

    def __post_init__(self):
        self.path.mkdir(exist_ok=True)

    @property
    def index(self) -> pathlib.Path:
        """The location of the file index."""
        return self.path / INDEX_CSV

    def write_index(self):
        """Write the file metadata to a csv file."""
        with UnicodeWriter(self.index) as w:
            for i, row in enumerate(self.rows):
                if i == 0:
                    w.writerow(row.keys())
                w.writerow(row.values())

    def add(self, row) -> pathlib.Path:
        """Add a file and return its target path in media_dir."""
        size = row.data.get('size')
        d = self.path / row.id[:2]
        f = File(d / '.'.join([row.id, row.ext]), row.mimetype, int(size) if size else None)
        row.data['local_path'] = pathlib.Path(d.name) / f.path.name
        self.rows.append(row.data)
        self.files.append(f)
        return f.path

    @functools.cached_property
    def extensions(self) -> set[str]:
        """The set of filename extensions used for the media files in the dataset."""
        return {f.ext for f in self.files}

    def print_stats(self):
        """Print summary stats about the media files in the dataset."""
        size_by_mimetype = collections.Counter()
        count_by_mimetype = collections.Counter()
        for f in self.files:
            size_by_mimetype[f.key] += f.size or 0
            count_by_mimetype.update([f.key])

        for k, v in size_by_mimetype.most_common():
            print('\t'.join([k.ljust(20), str(count_by_mimetype[k]), format_size(v)]))


def run(args):  # pylint: disable=C0116
    ds = get_dataset(args)
    ds_cldf = ds.cldf_reader()
    download_threads = []

    if not _valid_input(args):
        raise ParserError

    try:
        media_table = MediaTableSpec.from_dataset(ds_cldf)
    except ValueError as e:  # pragma: no cover
        args.log.error('Dataset has no MediaTable or media.csv')
        raise ParserError from e

    mime_types = [m.strip() for m in nfilter(args.mimetype.split(','))] if args.mimetype else []
    media_dir = MediaDir(args.out / MEDIA)

    for i, row in enumerate(tqdm.tqdm(media_table, desc='Getting media items')):
        if args.debug and i > 500:
            break  # pragma: no cover

        if any((not mime_types,
                row.ext in mime_types,
                any(row.mimetype.startswith(x) for x in mime_types))):
            target = media_dir.add(row)
            if not args.list:
                # We do not only list stats about the media files, but retrieve them.
                target.parent.mkdir(exist_ok=True)
                if (not target.exists()) or md5(target) != row.id:
                    row.download(target, download_threads)

    if args.list:
        media_dir.print_stats()
        return

    # Waiting for the download threads to finish
    for t in download_threads:
        t.join()

    media_dir.write_index()
    release_dir = args.out / f'{ds.id}_{MEDIA}'
    release_dir.mkdir(exist_ok=True)
    _zip_media(release_dir, [media_dir.index] + [f.path for f in media_dir.files], args)
    _release_metadata(release_dir, ds, args, media_dir.extensions)


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
        set_creators_and_contributors(ds, md)
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


def _add_rel_id(md, scheme, identifier, relation):
    md['related_identifiers'].append(
        {'scheme': scheme, 'identifier': identifier, 'relation': relation})
