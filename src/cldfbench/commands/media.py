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
       - it is only necessary to fill in required fields with provisional data - see step (6)
 (6) call cldfbench media --upload-zenodo deposit_ID
       to update the metadata of the previous uploaded reelease
"""
import os
import html
import time
import pathlib
import zipfile
import threading
import collections
from datetime import datetime
from urllib.request import urlretrieve

from cldfbench.cli_util import add_dataset_spec, get_dataset
from cldfbench.datadir import DataDir
from cldfbench.metadata import get_creators_and_contributors
from clldutils import jsonlib
from clldutils.clilib import PathType, ParserError
from clldutils.misc import format_size, nfilter
from clldutils.path import md5, git_describe
from csvw.dsv import UnicodeWriter
from zenodoclient.api import Zenodo, API_URL, API_URL_SANDBOX, ACCESS_TOKEN
from zenodoclient.models import PUBLISHED
import tqdm
import rfc3986


MEDIA = 'media'
ZENODO_FILE_NAME = 'zenodo.json'
COMMUNITIES = ['lexibank']
LICENCE = 'This dataset is licensed under {0}.'
INDEX_CSV = 'index.csv'

README = """## {title}

Supplement to dataset \"{ds_title}\" ({doi}) containing the {media} files{formats}
as compressed folder *{media}.zip*.

The {media} files are structured into separate folders named by the first two characters of the
file name. Each individual {media} file is named according to the ID specified in the file
*cldf/media.csv*.
A (filtered) version of which is included as {index}
in the *{media}.zip* file containing the additional column *local_path*.

{license}
"""

DESCRIPTION = "{title}{formats}{supplement_to} {descr} {online}"


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
        '--update-zenodo',
        help="Deposit ID (number after DOI's last slash) to update metadata by using ID_{0}/{1}. "
             "Cannot be used with --create-release.".format(
            MEDIA, ZENODO_FILE_NAME),  # noqa: E122
        default=None,
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
        time.sleep(0.1)

    download_thread = threading.Thread(target=_download, args=(url, target))
    download_thread.start()
    download_threads.append(download_thread)


def run(args):

    ds = get_dataset(args)
    ds_cldf = ds.cldf_reader()
    release_dir = args.out / '{0}_{1}'.format(ds.id, MEDIA)

    if ds_cldf.get('media.csv', None) is None:  # pragma: no cover
        args.log.error('Dataset has no media.csv')
        raise ParserError
    if args.parent_doi and not Zenodo.DOI_PATTERN.match(args.parent_doi):
        args.log.error('Invalid passed DOI')
        raise ParserError
    if args.update_zenodo:
        if not release_dir.exists():
            args.log.error('"{0}" not found -- run --create-release first?'.format(
                release_dir))
            raise ParserError
        if not (release_dir / ZENODO_FILE_NAME).exists():
            args.log.error('"{0}" not found -- run --create-release first?'.format(
                release_dir / ZENODO_FILE_NAME))
            raise ParserError
        if args.create_release:
            args.log.error('You cannot create the release and update zenodo at the same time.')
            raise ParserError
    if args.create_release:
        if not args.parent_doi:
            args.log.error('The corresponding DOI is required (via --parent-doi).')
            raise ParserError

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

    if not args.update_zenodo:
        used_file_extensions = set()
        with UnicodeWriter(media_dir / INDEX_CSV if not args.list else None) as w:
            for i, row in enumerate(tqdm.tqdm(
                    [r for r in ds_cldf['media.csv']], desc='Getting {0} items'.format(MEDIA))):
                url = ds_cldf.get_row_url('media.csv', row)
                if isinstance(url, rfc3986.URIReference):
                    url = url.normalize().unsplit()
                    row['URL'] = url
                f_ext = url.split('.')[-1].lower()
                if args.debug and i > 500:
                    break
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
                        row['local_path'] = pathlib.Path(row['ID'][:2]) / fn
                        if i == 0:
                            w.writerow(row)
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

    if args.create_release:
        assert media_dir.exists(), 'No folder "{0}" found in {1}'.format(MEDIA, media_dir.resolve())

        release_dir.mkdir(exist_ok=True)

        media.append(media_dir / INDEX_CSV)

        try:
            zipf = zipfile.ZipFile(
                str(release_dir / '{0}.zip'.format(MEDIA)), 'w', zipfile.ZIP_DEFLATED)
            fp = args.out
            for f in tqdm.tqdm(media, desc='Creating {0}.zip'.format(MEDIA)):
                zipf.write(str(f), str(os.path.relpath(str(f), str(fp))))
            zipf.close()
        except Exception as e:
            args.log.error(e)
            raise

        def _contrib(d):
            return {k: v for k, v in d.items() if k in {'name', 'affiliation', 'orcid', 'type'}}

        version_v = git_describe('.').split('-')[0]
        version = version_v.replace('v', '')
        git_url = [r for r in ds.repo.repo.remotes if r.name == 'origin'][0].url.replace('.git', '')
        with jsonlib.update(
                release_dir / ZENODO_FILE_NAME, indent=4, default=collections.OrderedDict()) as md:
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
            if communities and not args.debug:
                md['communities'] = [
                    {"identifier": community_id} for community_id in sorted(set(communities))]
            md.update(
                {
                    'title': '{0} {1} Files'.format(ds.metadata.title, MEDIA.title()),
                    'access_right': 'open',
                    'keywords': sorted(set(md.get('keywords', []) + ['linguistics'])),
                    'upload_type': 'dataset',
                    'publication_date': datetime.today().strftime('%Y-%m-%d'),
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
                supplement_to = " - Supplement to dataset " \
                                "<a href='https://doi.org/{0}'>{1}</a> ".format(
                    args.parent_doi, ds.metadata.title)  # noqa: E122
            if ds.metadata.url:
                md['related_identifiers'].append({
                    'scheme': 'url',
                    'identifier': ds.metadata.url,
                    'relation': 'isAlternateIdentifier'})

            formats = ', '.join(sorted(used_file_extensions))
            descr = '<br /><br />' + ds.metadata.description if ds.metadata.description else ''
            online_url, online = '', ''
            if ds.metadata.url:
                online_url = ds.metadata.url
                online = "<br /><br />Available online at: <a href='{0}'>{0}</a>".format(online_url)
            md['description'] = html.escape(DESCRIPTION.format(
                url=online_url,
                formats=' ({0})'.format(formats) if formats else '',
                title=md['title'],
                supplement_to=supplement_to,
                descr=descr,
                online=online))

            license_md = ''
            if ds.metadata.zenodo_license:
                md['license'] = {'id': ds.metadata.zenodo_license}
                license_md = LICENCE.format(ds.metadata.zenodo_license)

            DataDir(release_dir).write('README.md', README.format(
                title=md['title'],
                doi='https://doi.org/{0}'.format(args.parent_doi),
                ds_title=ds.metadata.title,
                license=license_md,
                formats=' ({0})'.format(formats) if formats else '',
                media=MEDIA,
                index=INDEX_CSV))

    if args.update_zenodo:

        md = {}
        md.update(jsonlib.load(release_dir / ZENODO_FILE_NAME))

        if args.debug:
            api_url = API_URL_SANDBOX
            access_token = os.environ.get('ZENODO_SANDBOX_ACCESS_TOKEN')
        else:
            api_url = API_URL
            access_token = ACCESS_TOKEN
        zenodo_url = api_url.replace('api/', '')

        args.log.info('Updating Deposit ID {0} on {1} with:'.format(args.update_zenodo, zenodo_url))
        api = Zenodo(api_url=api_url, access_token=access_token)
        try:
            rec = api.record_from_id('{0}record/{1}'.format(zenodo_url, args.update_zenodo))
        except Exception as e:
            args.log.error('Check connection and credentials for accessing Zenodo.\n{0}'.format(e))
            return
        latest_version = rec.links['latest'].split('/')[-1]
        if latest_version != args.update_zenodo:
            args.log.warn('Passed deposit ID does not refer to latest version {0}!'.format(
                latest_version))
        args.log.info('  DOI:     ' + rec.metadata.doi)
        args.log.info('  Title:   ' + rec.metadata.title)
        args.log.info('  Version: ' + rec.metadata.version)
        args.log.info('  Date:    ' + rec.metadata.publication_date)
        args.log.info('  Files:   ' + ', '.join([f.key for f in rec.files]))
        p = input("Proceed? [y/N]: ")
        if p.lower() == 'y':
            dep = api.update_deposit(args.update_zenodo, **md)
            if dep.state != PUBLISHED:
                api.publish_deposit(dep)
            args.log.info('Updated successfully')
