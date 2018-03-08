python setup.py extract_messages --input-dirs=. --output-file locale/Funduck.pot
python setup.py update_catalog -d locale --domain Funduck -i locale/Funduck.pot