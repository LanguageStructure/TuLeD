import sys
import itertools

from clldutils.misc import slug
from clld.cliutil import Data, bibtex2source
from clld.db.meta import DBSession
from clld.db.models import common
from clld.db.util import compute_language_sources
from clld.lib import bibtex
import tuled

from tuled.models import Doculect, Word, Concept


if sys.version_info < (3, 6, 0):
    sys.stderr.write('Python 3.6 or above is required.')
    exit(1)


def add_meta_data(session):
    """
    Creates and adds to the given SQLAlchemy session the common.Dataset and
    related model instances that comprise the project's meta info.
    Helper for the main function that keeps the meta data in one place for
    easier reference and editing.
    """

    dataset = common.Dataset(
        id=tuled.__name__,
        domain="tuled.org",
        name="TuLeD",
        description="Tupían Lexical Database",
        publisher_name="Seminar für Sprachwissenschaft at the University of Tübingen",
        publisher_place="Tübingen",
        license='https://creativecommons.org/licenses/by-sa/4.0/',
        contact="team@tuled.org",
        jsondata={
            'license_icon': 'cc-by-sa.png',
            'license_name': 'Creative Commons Attribution-ShareAlike 4.0 International License'},
    )

    dataset.editors.append(common.Editor(
        contributor=common.Contributor(id='fgerardi', name='Fabrício Ferraz Gerardi')))
    dataset.editors.append(common.Editor(
        contributor=common.Contributor(id='sreichert', name='Stanislav Reichert')))

    session.add(dataset)


def add_sources(sources_file_path, session):
    """
    Creates and adds to the given SQLAlchemy session the common.Source model
    instances that comprise the project's references. Expects the path to a
    bibtex file as its first argument.
    Returns a dict containing the added model instances with the bibtex IDs
    being the keys.
    Helper for the main function.
    """
    bibtex_db = bibtex.Database.from_file(sources_file_path, encoding='utf-8')
    for record in bibtex_db:
        session.add(bibtex2source(record))
    session.flush()


def main(args):
    colors = [
        '0000dd', '009900', '990099', 'dd0000', 'ffff00', 'ffffff', '00ff00', 'ff6600', '00ffff']
    icons = [s + c for s in ['c', 'd'] for c in colors]
    data = Data()
    add_meta_data(DBSession)
    contrib = data.add(common.Contribution, 'tuled', id='tuled', name='tuled')
    add_sources(args.cldf.bibpath, DBSession)
    sources = {s.id: s.pk for s in DBSession.query(common.Source)}
    subgroups = []
    for row in args.cldf['LanguageTable']:
        if row['SubGroup'] not in subgroups:
            subgroups.append(row['SubGroup'])
        data.add(
            Doculect,
            row['ID'],
            id=row['ID'],
            name=row['Name'].replace('_', ' '),
            subfamily=row['SubGroup'],
            iso_code=row['ISO639P3code'],
            glotto_code=row['Glottocode'],
            longitude=row['Longitude'],
            latitude=row['Latitude'],
            jsondata=dict(icon=icons[len(subgroups) - 1])
        )
    for row in args.cldf['ParameterTable']:
        data.add(
            Concept,
            row['ID'],
            id=row['ID'].split('_')[0],
            name=row['Name'],
            portuguese=row['Portuguese_Gloss'],
            semantic_field=row['Semantic_Field'],
            concepticon_class=row['Concepticon_ID'],
            eol=row['EOL_ID'],
        )
    for (lid, pid), rows in itertools.groupby(
        sorted(args.cldf['FormTable'], key=lambda r: (r['Language_ID'], r['Parameter_ID'])),
        lambda r: (r['Language_ID'], r['Parameter_ID']),
    ):
        vsid = '{}-{}'.format(lid, pid)
        vs = data.add(
            common.ValueSet, vsid,
            id=vsid,
            language=data['Doculect'][lid],
            parameter=data['Concept'][pid],
            contribution=contrib,
        )
        refs = set()
        for row in rows:
            DBSession.add(Word(
                id=row['ID'],
                valueset=vs,
                name=row['Form'],
                tokens=' '.join(row['Segments']),
                simple_cognate=int(row['SimpleCognate']),
                notes=row['Comment'],
                morphemes=' '.join(row['Morphemes']),
                partial_cognate=int(row['PartialCognates'][0]) if row['PartialCognates'] else None,
            ))
            refs = refs.union(row['Source'])

        for ref in refs:
            DBSession.add(common.ValueSetReference(valueset=vs, source_pk=sources[slug(ref, lowercase=False)]))


def prime_cache(args):
    """If data needs to be denormalized for lookup, do that here.
    This procedure should be separate from the db initialization, because
    it will have to be run periodically whenever data has been updated.
    """
    compute_language_sources()
