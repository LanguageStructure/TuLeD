from pathlib import Path

from clld.web.assets import environment

import tuled


environment.append_path(
    Path(tuled.__file__).parent.joinpath('static').as_posix(),
    url='/tuled:static/')
environment.load_path = list(reversed(environment.load_path))
