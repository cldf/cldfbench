"""
Dataset metadata
"""
import json
import collections

import attr
from clldutils import licenses
from clldutils.misc import nfilter
from clldutils.markup import iter_markdown_tables

__all__ = ['Metadata', 'get_creators_and_contributors']

CONTRIBUTOR_TYPES = {
    'ContactPerson',
    'DataCollector',
    'DataCurator',
    'DataManager',
    'Distributor',
    'Editor',
    'Funder',
    'HostingInstitution',
    'Producer',
    'ProjectLeader',
    'ProjectManager',
    'ProjectMember',
    'RegistrationAgency',
    'RegistrationAuthority',
    'RelatedPerson',
    'Researcher',
    'ResearchGroup',
    'RightsHolder',
    'Supervisor',
    'Sponsor',
    'WorkPackageLeader',
    'Other',
}

LICENSES = {
    "AAL",
    "ADSL",
    "AFL-1.1",
    "AFL-3.0",
    "AGPL-1.0-only",
    "AGPL-3.0",
    "AGPL-3.0-only",
    "AGPL-3.0-or-later",
    "AMDPLPA",
    "AML",
    "AMPAS",
    "ANTLR-PD",
    "APL-1.0",
    "APSL-1.0",
    "APSL-1.1",
    "APSL-1.2",
    "APSL-2.0",
    "Adobe-2006",
    "Against-DRM",
    "Aladdin",
    "Apache-1.0",
    "Apache-1.1",
    "Apache-2.0",
    "Artistic-1.0",
    "Artistic-1.0-Perl",
    "Artistic-1.0-cl8",
    "Artistic-2.0",
    "BSD-1-Clause",
    "BSD-2-Clause",
    "BSD-2-Clause-FreeBSD",
    "BSD-3-Clause",
    "BSD-3-Clause-Clear",
    "BSD-3-Clause-LBNL",
    "BSD-3-Clause-No-Nuclear-License",
    "BSD-3-Clause-No-Nuclear-License-2014",
    "BSD-4-Clause",
    "BSD-4-Clause-UC",
    "BSD-Source-Code",
    "BSL-1.0",
    "Bahyph",
    "Barr",
    "Beerware",
    "BitTorrent-1.0",
    "BitTorrent-1.1",
    "CATOSL-1.1",
    "CC-BY-1.0",
    "CC-BY-3.0",
    "CC-BY-4.0",
    "CC-BY-NC-1.0",
    "CC-BY-NC-2.5",
    "CC-BY-NC-3.0",
    "CC-BY-NC-4.0",
    "CC-BY-NC-ND-1.0",
    "CC-BY-NC-ND-2.0",
    "CC-BY-NC-ND-2.5",
    "CC-BY-NC-ND-3.0",
    "CC-BY-NC-ND-4.0",
    "CC-BY-NC-SA-1.0",
    "CC-BY-NC-SA-3.0",
    "CC-BY-NC-SA-4.0",
    "CC-BY-ND-1.0",
    "CC-BY-ND-2.0",
    "CC-BY-ND-2.5",
    "CC-BY-ND-4.0",
    "CC-BY-SA-2.0",
    "CC-BY-SA-2.5",
    "CC-BY-SA-3.0",
    "CC-BY-SA-4.0",
    "CC0-1.0",
    "CDDL-1.0",
    "CDLA-Permissive-1.0",
    "CDLA-Sharing-1.0",
    "CECILL-1.1",
    "CECILL-2.0",
    "CECILL-2.1",
    "CECILL-B",
    "CECILL-C",
    "CNRI-Jython",
    "CNRI-Python",
    "CNRI-Python-GPL-Compatible",
    "CPAL-1.0",
    "CPOL-1.02",
    "CUA-OPL-1.0",
    "Caldera",
    "ClArtistic",
    "Condor-1.1",
    "CrystalStacker",
    "Cube",
    "D-FSL-1.0",
    "DSDP",
    "DSL",
    "ECL-2.0",
    "EFL-1.0",
    "EFL-2.0",
    "EPL-1.0",
    "EUDatagrid",
    "EUPL-1.0",
    "EUPL-1.1",
    "EUPL-1.2",
    "Entessa",
    "ErlPL-1.1",
    "Eurosym",
    "FAL-1.3",
    "FSFAP",
    "Fair",
    "Frameworx-1.0",
    "GFDL-1.1",
    "GFDL-1.1-only",
    "GFDL-1.2",
    "GFDL-1.2-only",
    "GFDL-1.2-or-later",
    "GFDL-1.3-no-cover-texts-no-invariant-sections",
    "GL2PS",
    "GPL-1.0+",
    "GPL-1.0-or-later",
    "GPL-2.0",
    "GPL-2.0+",
    "GPL-2.0-with-GCC-exception",
    "GPL-2.0-with-bison-exception",
    "GPL-2.0-with-classpath-exception",
    "GPL-3.0",
    "GPL-3.0-only",
    "GPL-3.0-or-later",
    "GPL-3.0-with-GCC-exception",
    "Giftware",
    "Glulxe",
    "HPND",
    "HaskellReport",
    "IBM-pibs",
    "ICU",
    "IJG",
    "IPA",
    "IPL-1.0",
    "ISC",
    "ImageMagick",
    "Imlib2",
    "Intel",
    "Intel-ACPI",
    "JSON",
    "LGPL-2.0",
    "LGPL-2.0-or-later",
    "LGPL-2.1",
    "LGPL-2.1-only",
    "LGPL-3.0",
    "LGPL-3.0-or-later",
    "LGPLLR",
    "LPL-1.0",
    "LPL-1.02",
    "LPPL-1.0",
    "LPPL-1.2",
    "LPPL-1.3c",
    "LiLiQ-R-1.1",
    "LiLiQ-Rplus-1.1",
    "Linux-OpenIB",
    "MIT",
    "MIT-advertising",
    "MIT-enna",
    "MPL-1.0",
    "MPL-1.1",
    "MPL-2.0",
    "MPL-2.0-no-copyleft-exception",
    "MS-PL",
    "MS-RL",
    "MirOS",
    "Motosoto",
    "Multics",
    "Mup",
    "NASA-1.3",
    "NCSA",
    "NGPL",
    "NOSL",
    "NPL-1.1",
    "NPOSL-3.0",
    "NTP",
    "Naumen",
    "Newsletr",
    "Nokia",
    "Noweb",
    "Nunit",
    "OCCT-PL",
    "OCLC-2.0",
    "ODC-By-1.0",
    "ODC-PDDL-1.0",
    "ODbL-1.0",
    "OFL-1.0",
    "OFL-1.1",
    "OGL-Canada-2.0",
    "OGL-UK-1.0",
    "OGL-UK-2.0",
    "OGL-UK-3.0",
    "OGTSL",
    "OLDAP-1.2",
    "OLDAP-1.3",
    "OLDAP-1.4",
    "OLDAP-2.0",
    "OLDAP-2.0.1",
    "OLDAP-2.1",
    "OLDAP-2.2",
    "OLDAP-2.2.1",
    "OLDAP-2.2.2",
    "OLDAP-2.3",
    "OLDAP-2.4",
    "OLDAP-2.6",
    "OLDAP-2.8",
    "OSET-PL-2.1",
    "OSL-1.0",
    "OSL-1.1",
    "OSL-2.0",
    "OSL-2.1",
    "OSL-3.0",
    "OpenSSL",
    "PHP-3.0",
    "PHP-3.01",
    "Plexus",
    "PostgreSQL",
    "Python-2.0",
    "QPL-1.0",
    "Qhull",
    "RHeCos-1.1",
    "RPL-1.1",
    "RPL-1.5",
    "RPSL-1.0",
    "RSA-MD",
    "RSCPL",
    "Ruby",
    "SAX-PD",
    "SCEA",
    "SGI-B-2.0",
    "SISSL",
    "SMLNJ",
    "SPL-1.0",
    "SWL",
    "Sendmail",
    "Sendmail-8.23",
    "SimPL-2.0",
    "Sleepycat",
    "Spencer-94",
    "Spencer-99",
    "SugarCRM-1.1.3",
    "TCL",
    "TCP-wrappers",
    "TOSL",
    "TU-Berlin-2.0",
    "Unicode-DFS-2015",
    "Unicode-TOU",
    "Unlicense",
    "VSL-1.0",
    "Vim",
    "W3C",
    "W3C-20150513",
    "Watcom-1.0",
    "X11",
    "XFree86-1.1",
    "XSkat",
    "Xerox",
    "Xnet",
    "ZPL-1.1",
    "ZPL-2.0",
    "Zed",
    "Zend-2.0",
    "Zimbra-1.3",
    "Zlib",
    "bsd-license",
    "bzip2-1.0.5",
    "canada-crown",
    "cc-nc",
    "curl",
    "diffmark",
    "dli-model-use",
    "dvipdfm",
    "eCos-2.0",
    "eGenix",
    "eurofound",
    "geo-no-fee-unrestricted",
    "geogratis",
    "gnuplot",
    "hesa-withrights",
    "jabber-osl",
    "libtiff",
    "localauth-withrights",
    "lucent-plan9",
    "met-office-cp",
    "mitre",
    "mpich2",
    "notspecified",
    "other-at",
    "other-closed",
    "other-nc",
    "other-open",
    "other-pd",
    "psfrag",
    "psutils",
    "ukclickusepsi",
    "ukcrown",
    "ukcrown-withrights",
    "ukpsi",
    "user-jsim",
    "wxWindows",
    "xpp",
    "zlib-acknowledgement",
}


@attr.s
class Metadata(object):
    """
    Dataset metadata is used as follows:

    - it is (partly) elicited when creating a new dataset directory ...
    - ... and subsequently written to the directory ...
    - ... where it may be edited ("by hand") ...
    - ... and from where it is read when initializing a `Dataset` object.

    To add custom metadata fields for a dataset,

    - inherit from `Metadata`,
    - add more `attr.ib` s,
    - register the subclass with the dataset by assigning it to `cldfbench.Dataset.metadata_cls`.
    """
    id = attr.ib(
        default=None,
        metadata=dict(elicit=True, required=True))
    title = attr.ib(
        default=None,
        metadata=dict(elicit=True, required=True))
    description = attr.ib(
        default=None)
    license = attr.ib(
        default=None,
        metadata=dict(elicit=True, required=True))
    url = attr.ib(
        default=None,
        metadata=dict(elicit=True))
    citation = attr.ib(
        default=None,
        metadata=dict(elicit=True, required=True))

    @classmethod
    def elicit(cls):
        """
        Factory method, called when creating a new dataset directory.
        """
        kw = {}
        for field in attr.fields(cls):
            if field.metadata.get('elicit', False):
                res = input('{0}: '.format(field.name))
                if (not res) and field.default is not attr.NOTHING:
                    res = field.default
                kw[field.name] = res
        return cls(**kw)

    @classmethod
    def from_file(cls, fname):
        """
        Factory method, called when instantiating a `Dataset` object.
        """
        with fname.open('r', encoding='utf-8') as fp:
            try:
                return cls(**json.load(fp))
            except json.decoder.JSONDecodeError as e:  # pragma: no cover
                raise ValueError('Invalid JSON file: {}\n{}'.format(fname.resolve(), e))

    def write(self, fname):
        with fname.open('w', encoding='utf-8') as fp:
            return json.dump(attr.asdict(self), fp, indent=4)

    @property
    def known_license(self):
        if self.license:
            return licenses.find(self.license)

    @property
    def zenodo_license(self):
        if self.known_license and self.known_license.id in LICENSES:
            return self.known_license.id

    def common_props(self):
        """
        The metadata as JSON-LD object suitable for inclusion in CLDF metadata.
        """
        res = collections.OrderedDict()
        if self.title:
            res["dc:title"] = self.title
        if self.description:
            res["dc:description"] = self.description
        if self.citation:
            res["dc:bibliographicCitation"] = self.citation
        if self.url:
            res["dc:identifier"] = self.url
        if self.known_license:
            res['dc:license'] = self.known_license.url
        elif self.license:
            res['dc:license'] = self.license
        return res

    def markdown(self):
        lines = [
            '# {0}\n'.format(self.title or 'Dataset {0}'.format(self.id)),
            '## How to cite\n\nIf you use these data please cite',
        ]
        if self.citation:
            lines.extend([
                "- the original source",
                "  > {}".format(self.citation),
                "- the derived dataset using the DOI of the "
                "[particular released version](../../releases/) you were using"
            ])
        else:  # pragma: no cover
            lines.extend([
                "this dataset using the DOI of the "
                "[particular released version](../../releases/) you were using"
            ])

        lines.append('\n## Description\n\n')

        if self.description:
            lines.append('{0}\n'.format(self.description))

        if self.license:
            lines.append('This dataset is licensed under a %s license\n' % self.license)

        if self.url:
            lines.append('Available online at %s\n' % self.url)

        return '\n'.join(lines)


def get_creators_and_contributors(text, strict=True):
    ctypes = {c.lower(): c for c in CONTRIBUTOR_TYPES}
    creators, contributors = [], []
    # Read first table in CONTRIBUTORS.md
    try:
        header, rows = next(iter_markdown_tables(text))
    except StopIteration:  # pragma: no cover
        return creators, contributors
    for row in rows:
        row = {k.lower(): v for k, v in zip(header, row)}
        for role in nfilter([r.strip().lower() for r in row.get('role', '').split(',')]):
            c = {k: v for k, v in row.items() if k != 'role'}
            if role in {'author', 'creator', 'maintainer'}:
                if c not in creators:
                    creators.append(c)
            else:
                if strict:
                    c['type'] = ctypes[role]
                else:
                    c['type'] = ctypes.get(role, 'Other')
                if c not in contributors:
                    contributors.append(c)
    return creators, contributors
