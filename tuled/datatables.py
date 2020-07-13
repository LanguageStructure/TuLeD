from clld.db.meta import DBSession
from clld.web.datatables.base import Col, IntegerIdCol, LinkToMapCol, LinkCol
from clld.web.util.helpers import external_link, link, map_marker_img
from clld.web.util.htmllib import HTML
from clld.web import datatables

from tuled.models import Concept, Doculect, Word

"""
Columns
"""


class EnglishCol(Col):
    """
    Copied from IsoCodeCol
    """
    __kw__ = {'sTitle': 'English'}


class EolCol(Col):
    """
    Copied from IsoCodeCol
    """
    __kw__ = {'sTitle': 'Eol'}

    def format(self, concept):
         if concept.eol:
             href = 'https://eol.org/pages/{}'.format(concept.eol)
             return external_link(href, concept.eol)
         else:
             return ''


class PortugueseCol(Col):
    """
    Copied from IsoCodeCol
    """
    __kw__ = {'sTitle': 'Portuguese'}


class IsoCodeCol(Col):
    """
    Custom column to set a proper title for the iso_code column of the
    languages table.
    """

    __kw__ = {'sTitle': 'ISO_Code'}


class GlottoCodeCol(Col):
    """
    Custom column to present the glotto_code column of the languages table as a
    link to the respective languoid in Glottolog.
    """

    __kw__ = {'sTitle': 'Glottocode'}

    def format(self, doculect):
        href = 'http://glottolog.org/resource/languoid/id/{}'.format(doculect.glotto_code)
        return external_link(href, doculect.glotto_code)


# class FamilyCol(Col):
#     """
#     Custom column to replace the search with a drop-down and to add icons for
#     the family column of the languages table.
#     Unlike in, e.g., NextStepCol, the choices have to be set in the constructor
#     because otherwise the unit tests do not work.
#     The icons are handled in the format method, the code being stolen from the
#     datatable module of the clld-glottologfamily-plugin repo.
#     """
#
#     def __init__(self, *args, **kwargs):
#         kwargs['choices'] = sorted([
#             x[0] for x in DBSession.query(Doculect.family).distinct()])
#
#         super().__init__(*args, **kwargs)
#
#     def format(self, doculect):
#         return HTML.div(map_marker_img(self.dt.req, doculect), ' ', doculect.family)


class SubfamilyCol(Col):
    """
    Custom column to replace the search with a drop-down for the subfamily
    column of the languages table.
    Unlike in, e.g., NextStepCol, the choices have to be set in the constructor
    because otherwise the unit tests do not work.
    """

    def __init__(self, *args, **kwargs):
        kwargs['choices'] = sorted([
            x[0] for x in DBSession.query(Doculect.subfamily).distinct()])

        super().__init__(*args, **kwargs)

    def format(self, doculect):
        return HTML.div(map_marker_img(self.dt.req, doculect), ' ', doculect.subfamily)


class SemanticClassCol(Col):
    """
    Copied from SubfamilyCol
    """

    def __init__(self, *args, **kwargs):
        kwargs['choices'] = sorted([
            x[0] for x in DBSession.query(Concept.semantic_class).distinct()])

        super().__init__(*args, **kwargs)


class ConcepticonCol(Col):
     """
     Custom column to present the concepticon_name column of the concepts table
     as a link to the respective concept in the Concepticon.
     """

     __kw__ = {'sTitle': 'Concepticon'}

     def format(self, concept):
         if concept.concepticon_class:
             href = 'http://concepticon.clld.org/parameters/{}'.format(concept.concepticon_class)
             return external_link(href, concept.concepticon_class)
         else:
             return ''


class ConceptLinkCol(LinkCol):
    """
    Custom column to present the concept column of the words table as a link
    with a title attribute containing the concept's English name.
    """

    def format(self, item):
        concept = self.get_obj(item)
        if concept:
            return link(self.dt.req, concept, **{'title': concept.name})
        else:
            return ''


class DoculectLinkCol(LinkCol):
    """
    Custom column to present the doculect column of the words table as a link
    with a title attribute containing the doculect's family and subfamily.
    """

    def format(self, item):
        doculect = self.get_obj(item)
        if doculect:
            title = '{}'.format(doculect.name)#,
                        # doculect.family, doculect.subfamily)
            return link(self.dt.req, doculect, **{'title': title})
        else:
            return ''


"""
Tables
"""


class LanguagesDataTable(datatables.Languages):

    def col_defs(self):
        return [
            LinkToMapCol(self, 'm'),
            LinkCol(self, 'name'),
            SubfamilyCol(self, 'subfamily', model_col=Doculect.subfamily),
            GlottoCodeCol(self, 'glotto_code', model_col=Doculect.glotto_code),
            IsoCodeCol(self, 'iso_code', model_col=Doculect.iso_code),
            Col(self, 'latitude'),
            Col(self, 'longitude')]


class ConceptsDataTable(datatables.Parameters):

    def col_defs(self):
        return [
            IntegerIdCol(self, 'id'),
            LinkCol(self, 'name'),
            PortugueseCol(self, 'portuguese', model_col=Concept.portuguese),
            SemanticClassCol(self, 'semantic_class', model_col=Concept.semantic_class),
            ConcepticonCol(self, 'concepticon_class', model_col=Concept.concepticon_class),
            EolCol(self, 'eol', model_col=Concept.eol)]


class WordsDataTable(datatables.Values):

    def col_defs(self):
        res = []

        if self.language:
            res.extend([
                IntegerIdCol(self, 'id', model_col=Concept.id,
                    get_object=lambda x: x.valueset.parameter),
                ConceptLinkCol(self, 'concept', model_col=Concept.name,
                    get_object=lambda x: x.valueset.parameter) ])

        elif self.parameter:
            res.extend([
                DoculectLinkCol(self, 'language', model_col=Doculect.name,
                    get_object=lambda x: x.valueset.language) ])

        res.extend([
            Col(self, 'form', model_col=Word.name, sTitle='Orthographic form'),
            Col(self, 'cognate', model_col=Word.cognate_class, sTitle='Cognate Class'),
            Col(self, 'notes', model_col= Word.notes, sTitle='Notes')])

        return res


class SourcesDataTable(datatables.Sources):

    def col_defs(self):
        return super().col_defs()[:-1]


"""
Hooks
"""

def includeme(config):
    """
    Magical (not in the good sense) hook that replaces the default data tables
    with the custom ones defined in this module.
    """
    config.register_datatable('languages', LanguagesDataTable)
    config.register_datatable('parameters', ConceptsDataTable)
    config.register_datatable('values', WordsDataTable)
    config.register_datatable('sources', SourcesDataTable)
