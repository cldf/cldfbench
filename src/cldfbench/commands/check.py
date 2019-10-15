"""
Run generic CLDF checks
"""
import pytest
from cldfbench.cli_util import get_dataset, add_catalog_spec, add_dataset_spec


def register(parser):
    add_dataset_spec(parser)
    add_catalog_spec(parser, 'glottolog')
    parser.add_argument('--with-tests', action='store_true', default=False)


def run(args):
    ds = get_dataset(args.dataset, ep=args.entry_point)

    # validate
    args.log.info("Validating CLDF...")
    cldf = ds.cldf_reader()
    cldf.validate(log=args.log)

    if args.with_tests:  # pragma: no cover
        testfile = ds.dir / "test.py"
        if testfile.is_file():
            args.log.info("Running tests...")
            pytest.main([
                '--cldf-metadata=%s' % ds.default_cldf_spec.metadata_path,
                testfile
            ])
        else:
            args.log.warning("No tests found")

    gccol = cldf.get(('LanguageTable', 'glottocode'))
    if gccol:
        # Check languages
        args.log.info("Checking Languages...")
        glottocodes = {l.id: l.category for l in args.glottolog.api.languoids()}
        for lang in cldf['LanguageTable']:
            if not lang[gccol.name]:
                args.log.warning("Language '%s' is missing a glottocode" % lang)
            elif lang[gccol.name] not in glottocodes:
                args.log.error("Language '%s' has an INVALID glottocode '%s'" % (
                    lang, lang[gccol.name]))
            elif glottocodes[lang[gccol.name]].lower().startswith('pseudo'):
                args.log.info("Language {0} mapped to family {1}".format(
                    lang, glottocodes[lang[gccol.name]]))
    else:
        args.log.warning('Dataset has no LanguageTable')

    # Check sources
    args.log.info("Checking Sources...")
    #sources_in_forms = check_sources(cldf)
    #sources_in_bib = cldf.sources.keys()
    #for s in sources_in_forms:
    #    if s not in sources_in_bib:
    #        args.log.warning("Source '%s' is not defined in sources.bib" % s)
    #    if s == "":
    #        args.log.warning("%d lexemes have no source defined" % sources_in_forms[s])
