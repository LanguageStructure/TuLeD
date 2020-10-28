#!/bin/bash

python3.8 data/TuledParse.py
rm 'preprocessed_data.tsc'
python3.8 tuled/scripts/initializedb.py development.ini