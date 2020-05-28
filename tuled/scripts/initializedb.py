from __future__ import unicode_literals
import sys, os, csv, collections

from clld.scripts.util import initializedb, Data, bibtex2source
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
                                                 'semantic_class'])

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
                                   line['Portuguese'], line['Semantic'])


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
                                           'cognate', 'notes'])

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
                                line['Semantic'], line['Cognate'], line['Notes'])


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
    dataset = common.Dataset(id='tuled', name='TuLeD',
                             description='Tupían Lexical Database',
                             publisher_name='Seminar für Sprachwissenschaft at the University of Tübingen',
                             publisher_place='Tübingen',
                             license='https://creativecommons.org/licenses/by-sa/4.0/',
                             jsondata={
                                 'license_icon': 'cc-by-sa.png',
                                 'license_name': 'Creative Commons Attribution-ShareAlike 4.0 International License'},
                             contact='team@tuled.org',
                             domain='xyz.org')
    session.add(dataset)

    dataset.editors.append(common.Editor(
        contributor=common.Contributor(id='fgerardi', name='Fabrício Ferraz Gerardi')))
    dataset.editors.append(common.Editor(
        contributor=common.Contributor(id='sreichert', name='Stanislav Reichert')))


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
                                  semantic_class=concept.semantic_class)
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
    """
    Populates the database. Expects: (1) the db to be empty; (2) the main_data,
    lang_data, concept_data, and sources_data args to be present in the given
    argparse.Namespace instance.
    This function is called within a db transaction, the latter being handled
    by initializedb.
    """
    main_dataset = MainDataset(args.main_data)

    add_meta_data(DBSession)

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
            last_synset = Synset(id=f'{word.language}-{word.concept}',
                                 language=doculects[word.language],
                                 parameter=concepts[word.concept])
            DBSession.add(last_synset)

        if not (word.form or word.cognate):  # empty notes?
            continue

        DBSession.add(Word(id=f'{word.language}-{word.concept}-{word.form}-{word.portuguese}',
                           valueset=last_synset,
                           name=word.form,
                           cognate_class=word.cognate,
                           notes = word.notes))


"""
The clld.scripts.util.initializedb func is a wrapper around the main func, but
it uses its own argparse.ArgumentParser instance. Thus, there are two ways to
avoid hardcoding the paths to the datasets: (1) init an
ArgumentParser instance here and fake some sys.argv input to the initializedb's
instance so that initializedb does not break; (2) add new arguments to
initializedb's instance in the undocumented and weird way that seems to have
been provided for such cases. The latter option is implemented.
"""
if __name__ == '__main__':

    if os.path.exists('db.sqlite'):
        os.remove('db.sqlite')

    main_data_arg = [('main_data',), {
        'help': 'path to the tsv file that contains the TuLeD data'}]
    lang_data_arg = [('lang_data',), {
        'help': 'path to the tsv file that contains the language data'}]
    concept_data_arg = [('concept_data',), {
        'help': 'path to the tsv file that contains the concept data'}]
    sources_data_arg = [('sources_data',), {
        'help': 'path to the bibtex file that contains the references'}]

    initializedb(main_data_arg, lang_data_arg, concept_data_arg, sources_data_arg, create=main)
