import sys
import csv
import itertools
import collections
import pathlib
from pycldf import Sources
from clldutils.misc import nfilter
from clldutils.color import qualitative_colors
from clld.cliutil import Data, bibtex2source
from clld.db.meta import DBSession
from clld.db.models import common
from clld.lib import bibtex
import tuled
from tuled import models
from tuled.models import Doculect, Synset, Word, Concept

if sys.version_info < (3, 6, 0):
    sys.stderr.write('Python 3.6 or above is required.')
    exit(1)


"""
Dataset classes
"""


class LangDataset:
    """
    Handles reading the TuLeD language data dataset.
    """

    class LangDatasetDialect(csv.Dialect):
        """
        Describes the tsv dialect used for the language data file.
        """
        delimiter = '\t'
        lineterminator = '\r\n'
        quoting = csv.QUOTE_NONE
        strict = True

    Language = collections.namedtuple('Language', ['name', 'subfamily',
                                                   'iso_code', 'id',
                                                   'glotto_code',
                                                   'longitude', 'latitude'])

    def __init__(self, dataset_fp):
        """
        Constructor.
        """
        self.dataset_fp = dataset_fp

    def gen_langs(self):
        """
        Yields a Language named tuple at a time.
        """
        with open(self.dataset_fp, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, dialect=self.LangDatasetDialect)
            for row in reader:
                yield self.Language(row['Language'], row['Sub-Family'],
                                    row['ISO_Code'], row['Language_ID'],
                                    row['Glottolog'], row['Longitude'],
                                    row['Latitude'])


class ConceptDataset:
    """
    Handles reading the TuLeD concept dataset.
    """

    class ConceptDatasetDialect(csv.Dialect):
        """
        Describes the tsv dialect used for the concepts data file.
        """
        delimiter = '\t'
        lineterminator = '\r\n'
        quoting = csv.QUOTE_NONE
        strict = True

    Concept = collections.namedtuple('Concept', ['id', 'name', 'portuguese',
                                                 'semantic_class', 'concepticon', 'eol'])

    def __init__(self, dataset_fp):
        """
        Constructor.
        """
        self.dataset_fp = dataset_fp

    def gen_concepts(self):
        """
        Yields a Concept named tuple at a time.
        """
        with open(self.dataset_fp, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, dialect=self.ConceptDatasetDialect)
            for line in reader:
                yield self.Concept('', line['Name'],
                                   line['Portuguese'], line['Semantic'], line['Concepticon'], line['Eol'])


class MainDataset:
    """
    Handles reading the main TuLeD dataset.
    """

    class MainDatasetDialect(csv.Dialect):
        """
        Describes the tsv dialect used for the dataset file.
        """
        delimiter = '\t'
        lineterminator = '\r\n'
        quoting = csv.QUOTE_NONE
        strict = True

    Word = collections.namedtuple('Word', ['language', 'concept', 'form',
                                           'portuguese', 'semantic',
                                           'simple_cognate', 'partial_cognate', 'tokens', 'morphemes', 'notes'])

    def __init__(self, dataset_fp):
        """
        Constructor.
        """
        self.dataset_fp = dataset_fp

    def gen_words(self):
        """
        Yields a Word named tuple at a time.
        """
        with open(self.dataset_fp, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, dialect=self.MainDatasetDialect)
            for line in reader:
                yield self.Word(line['Language'], line['Concept'],
                                line['Form'], line['Portuguese'],
                                line['Semantic'], line['SimpleCognate'],
                                line['PartialCognate'], line['Tokens'],
                                line['Morphemes'], line['Notes'])


"""
Database-populating functions
"""


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


def iteritems(cldf, t, *cols):
    cmap = {cldf[t, col].name: col for col in cols}
    for item in cldf[t]:
        for k, v in cmap.items():
            item[v] = item[k]
        yield item

def add_sources(sources_file_path, session):
    """
    Creates and adds to the given SQLAlchemy session the common.Source model
    instances that comprise the project's references. Expects the path to a
    bibtex file as its first argument.
    Returns a dict containing the added model instances with the bibtex IDs
    being the keys.
    Helper for the main function.
    """
    d = {}

    bibtex_db = bibtex.Database.from_file(sources_file_path, encoding='utf-8')
    seen = set()

    for record in bibtex_db:

        if record.id in seen:
            continue

        d[record.id] = bibtex2source(record)
        session.add(d[record.id])
        seen.add(record.id)

    session.flush()

    return d


def add_concepts(concepts_dataset, session):
    """
    Creates and adds to the given SQLAlchemy session the Concept instances
    harvested from the given ConceptDataset instance. Returns a dict of the
    added model instances with the concept IDs being the keys.
    Helper for the main function.
    """
    d = {}

    for index, concept in enumerate(concepts_dataset.gen_concepts(), 1):
        d[concept.name] = Concept(id=index, name=concept.name,
                                  portuguese=concept.portuguese,
                                  semantic_field=concept.semantic_class,
                                  concepticon_class=concept.concepticon,
                                  eol=concept.eol)
        session.add(d[concept.name])

    session.flush()

    return d


def add_doculects(lang_dataset, session, sources={}):
    """
    Creates and adds to the given SQLAlchemy session the Doculect instances
    harvested from the given LangDataset instance. Returns a dict of the added
    model instances with the respective ISO codes being the keys.
    The optional arg should contain common.Source instances with the keys being
    strings starting with the ISO code of the language that the source is for.
    Helper for the main function.
    """
    d = {}

    for lang in lang_dataset.gen_langs():

        if not (lang.name and lang.subfamily and lang.iso_code and
                lang.glotto_code and lang.longitude and lang.latitude and
                lang.id):
            print(f'SKIP: Missing data for {lang.name}.', file=sys.stderr)
            continue

        d[lang.name] = Doculect(id=lang.id, name=lang.name, subfamily=lang.subfamily,
                                iso_code=lang.iso_code, glotto_code=lang.glotto_code,
                                longitude=lang.longitude, latitude=lang.latitude)
        session.add(d[lang.name])

    session.flush()

    for key, source in sources.items():
        if key[:3] in d:
            session.add(common.LanguageSource(
                language_pk=d[key[:3]].pk,
                source_pk=source.pk))
    session.flush()

    return d


def main(args):

    data = Data()
    """
    data.add(
        common.Dataset,
        tuled.__name__,
        id=tuled.__name__,
        domain='',

        publisher_name="Tübingen University",
        publisher_place="Tübingen",
        publisher_url="",
        license="http://creativecommons.org/licenses/by/4.0/",
        jsondata={
            'license_icon': 'cc-by.png',
            'license_name': 'Creative Commons Attribution 4.0 International License'},

    )
    """
    add_meta_data(DBSession)

    data_dir = pathlib.Path(tuled.__file__).parent.parent / 'data'
    args.main_data = input('main data [{}]: '.format(data_dir / 'main.tsv')) or str(data_dir / 'main.tsv')
    args.sources_data = input('sources data [{}]: '.format(data_dir / 'sources.bib')) or str(data_dir / 'sources.bib')
    args.concept_data = input('concept data [{}]: '.format(data_dir / 'concepts.tsv')) or str(data_dir / 'concepts.tsv')
    args.lang_data = input('lang data [{}]: '.format(data_dir / 'languages.tsv')) or str(data_dir / 'languages.tsv')

    main_dataset = MainDataset(args.main_data)

    sources = add_sources(args.sources_data, DBSession)
    concepts = add_concepts(ConceptDataset(args.concept_data), DBSession)
    doculects = add_doculects(LangDataset(args.lang_data), DBSession, sources)

    last_synset = None
    for word in main_dataset.gen_words():

        if word.language not in doculects or word.concept not in concepts:
            continue

        # assert word.concept in concepts
        # assert word.language in doculects

        if last_synset is None \
                or last_synset.language != doculects[word.language] \
                or last_synset.parameter != concepts[word.concept]:
            last_synset = Synset(id=f'{word.language}-{word.concept}-{word.form}',
                                 language=doculects[word.language],
                                 parameter=concepts[word.concept])
            DBSession.add(last_synset)

        if not (word.form or word.simple_cognate):  # empty notes?
            continue

        DBSession.add(Word(id=f'{word.language}-{word.concept}-{word.form}-{word.portuguese}',
                           valueset=last_synset,
                           name=word.form,
                           tokens=word.tokens,
                           simple_cognate=word.simple_cognate,
                           notes=word.notes,
                           morphemes=word.morphemes,
                           partial_cognate=word.partial_cognate)
                           )

def prime_cache(args):
    """If data needs to be denormalized for lookup, do that here.
    This procedure should be separate from the db initialization, because
    it will have to be run periodically whenever data has been updated.
    """
