# install requirements
pip install -r requirements.txt

# Install package
pip install .

# Uninstall package
pip uninstall pdi

# Run tests
python -m unittest -v -b --locals  

# Run tests with coverages

coverage run --source=pdi -m unittest -v
coverage run --source=pdi -m unittest -v -b 

## coverage with append
coverage run -a --source=pdi -m unittest -v -b 

## run tests for test modules with append
coverage run -a --source=pdi -m unittest discover -v -b -s 'tests.api' -t '.'
coverage run -a --source=pdi -m unittest discover -v -b -s 'tests.configuration' -t '.'
coverage run -a --source=pdi -m unittest discover -v -b -s 'tests.cryptography' -t '.'
coverage run -a --source=pdi -m unittest discover -v -b -s 'tests.db' -t '.'
coverage run -a --source=pdi -m unittest discover -v -b -s 'tests.dependency' -t '.'
coverage run -a --source=pdi -m unittest discover -v -b -s 'tests.multi_processing' -t '.'
coverage run -a --source=pdi -m unittest discover -v -b -s 'tests.utils' -t '.'

## test coverage report
coverage report -m --omit="*/tests/*,*/site-packages/*,*/pdi/connection/*"

## test coverage html
coverage html  --omit="*/tests/*,*/site-packages/*,*/pdi/connection/*"
