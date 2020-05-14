from clld.interfaces import IMapMarker
from clld.web.icon import ICON_MAP, SHAPES
from pyramid.config import Configurator

# Has to be imported, even if it is seemingly unused:
# we must make sure custom models are known at database initialization!
from tuled import models
from tuled.models import Doculect
import os, sys

if sys.version_info < (3, 6, 0):
    sys.stderr.write('Python 3.6 or above is required.')
    exit(1)

# Renaming 'parameter(s)' to 'concept(s)' (cf. NorthEuraLex)
_ = lambda x: x
_('Parameter')
_('Parameters')


def read_families(families_file):
    FAMILIES = []
    if not os.path.exists(families_file):
        with open(families_file, 'w', encoding='utf8'):
            pass
    with open(families_file, 'r', encoding='utf8') as f:
        for family in f.readlines():
            FAMILIES.append(family.strip())
    return FAMILIES


def update_families(families_file, new_family):
    with open(families_file, 'a+', encoding='utf8') as f:
        f.write(new_family+'\n')
    return read_families(families_file)


# could add more colors
COLORS = ['0000dd', '009900', '990099', 'dd0000', 'ffff00', 'ffffff', '00ff00', 'ff6600', '00ffff']


def get_map_marker(item, req):
    """
    Hook called for each marker on each map. Determines the map marker for the
    given item (the latter would be an instance of a different class depending
    on the map). Returns the URL of the selected map marker.
    In other words, makes sure that each marker on a map would consistently use
    the same icon depending on the language family.
    Automatically generate different markers for different language families.
    New family will be write to the families file.
    """
    FAMILIES = read_families('families.txt')
    family = None

    if isinstance(item, models.Doculect):
        family = item.subfamily
    elif isinstance(item, models.Synset):
        family = item.language.subfamily

    # method to generate different marker for each family
    # new family will be assigned a different marker on the fly, and write to the families text file.
    if family not in FAMILIES:
        FAMILIES = update_families('families.txt', family)  # update the families file

    index = FAMILIES.index(family)
    shape = SHAPES[index % 5]
    color = COLORS[index % 9]

    return ICON_MAP[shape + color].url(req)


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('clld.web.app')
    config.registry.registerUtility(get_map_marker, IMapMarker)

    return config.make_wsgi_app()