#!/bin/bash

args=("$@")

mkdir -p data
source venv/bin/activate
python3 tuled/scripts/process_excel_sheet.py ${args[@]} data/languages.tsv data/concepts.tsv data/main.tsv
python3 tuled/scripts/initializedb.py development.ini data/main.tsv data/languages.tsv data/concepts.tsv data/sources.bib
deactivate
