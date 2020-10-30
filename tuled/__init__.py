from clld.db.models import common
from pyramid.config import Configurator

from clld.interfaces import IMapMarker
from clldutils.svg import icon, data_url

# we must make sure custom models are known at database initialization!
from tuled import models
from tuled.models import Doculect, Word
import sys

if sys.version_info < (3, 6, 0):
    sys.stderr.write('Python 3.6 or above is required.')
    exit(1)

# Renaming 'parameter(s)' to 'concept(s)' (cf. NorthEuraLex)
_ = lambda x: x
_('Parameter')
_('Parameters')


def get_map_marker(item, req):
    if isinstance(item, models.Doculect):
        return data_url(icon(item.jsondata['icon']))

    if isinstance(item, common.ValueSet):
        return data_url(icon(item.language.jsondata['icon']))

    if isinstance(item, Word):
        return data_url(icon(item.valueset.language.jsondata['icon']))


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('clld.web.app')
    config.registry.registerUtility(get_map_marker, IMapMarker)
    config.include('clldmpg')

    return config.make_wsgi_app()
