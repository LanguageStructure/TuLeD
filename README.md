# Tupían Lexical Database
![TuLeD](mapNimu2.png)


## Installation and deployment

### Localhost

```
python3 run.py
```

or

```
pserve --reload development.ini
```

The website location is specified in `development.ini`: http://127.0.0.1:6543 . 

### On a server

- Look up the username ('Primary SSH login'), server address ('FTP server'), port (the 5-digit code at the end of 'SSH access to cluster') and password ('FTP password'). (Most of these values can be found in the `FTP - SSH` tab.)
```
ssh -vvv USER@SERVER -p PORT
```
- Add the contents of this repo to the `www` directory (via git or FTP).
- This should only be necessary once:
```
cd www
pip3 install --upgrade pip setuptools
pip3 install clld==6.0.1
pip3 install -e .
```
- Deploy the website (for the first time or after file updates) via:
```
python3 run.py
```

## File/project updates

### Populating the database

Download the Excel sheet as a tsv, make sure the filename does not contain spaces, and run this bash script from within the tuled home directory.

```bash
./refresh.sh path/to/excel.tsv
```

* TODO: update the `sqlalchemy.url` in `development.ini`! (currently, it's just a default value)

### Overriding CLLD default names

To change the "Parameter(s)" strings to "Concept(s)". These steps **only** need to be performed again if the string translations should be changed or if you want to add more translations.
- If other strings to be changed were added to `tuled/__init__.py` (requires all of the following steps since it rewrites `tuled/locale/en/LC_MESSAGES/clld.po`):
```
pybabel extract tuled -o tuled/locale/tuled.pot
pybabel init -i tuled/locale/tuled.pot -d tuled/locale -D clld -l en
```
- To add or change the string translations, edit the `msgstr` fields in `tuled/locale/en/LC_MESSAGES/clld.po` and run:
```
pybabel compile -d tuled/locale -D clld --statistics
pybabel update -i tuled/locale/tuled.pot -d tuled/locale -D clld --previous
```

## Development

I added comments to the most relevant files in this system:

```
C:\USERS\VBL\DOCUMENTS\TULED
│   .gitignore
│   db.sqlite
│   development.ini
│   MANIFEST.in
│   README.md
│   setup.cfg
│   setup.py
│   tox.ini
│
├───tuled
│   │   __init__.py               # override clld defaults
│   │   adapters.py               # custom CSV/JSON/etc readers
│   │   appconf.ini               # website tabs
│   │   assets.py
│   │   datatables.py             # define columns and tables (cf. models.py)
│   │   interfaces.py
│   │   maps.py
│   │   models.py                 # (complements datatables.py)
│   │   views.py
│   │
│   ├───locale
│   │   │   tuled.pot             # override tab name defaults
│   │   │
│   │   └───en
│   │       └───LC_MESSAGES
│   │               clld.po       # override tab name defaults
│   │
│   ├───scripts
│   │       initializedb.py       # connect databases to the app
│   │       __init__.py
│   │   
│   ├───static
│   │   │   project.css
│   │   │   project.js
│   │   │
│   │   └───download
│   ├───templates
│   │   │   tuled.mako            # layout
│   │   │
│   │   └───dataset
│   │           detail_html.mako  # start page layout/contents
│   │
│   └───tests
│           conftest.py
│           test_functional.py
│           test_scripts.py
│           test_selenium.py
│
└───tuled.egg-info
        dependency_links.txt
        entry_points.txt
        not-zip-safe
        PKG-INFO
        requires.txt
        SOURCES.txt
        top_level.txt
```

Notes:
- `appconf.ini` follows a very strict format, also in terms of permitted values
- [To understand the structure better](https://clld.readthedocs.io/en/latest/tutorial.html)
