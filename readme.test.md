# Run tests
python -m unittest -v -b --locals  

# Run tests with coverages

coverage run --source=pdip -m unittest discover -v
coverage run --source=pdip -m unittest discover -v -b 

## coverage with append
coverage run -a  --concurrency=thread --source=pdip -m unittest -v -b 'tests.api'

## test coverage report
coverage report -m --omit="*/tests/*,*/site-packages/*"

## test coverage html
coverage html  --omit="*/tests/*,*/site-packages/*"

## run tests for test modules with append
coverage run -a --concurrency=thread --source=pdip -m unittest discover -v -b -s 'tests.api' -t '.'
coverage run -a --source=pdip -m unittest discover -v -b -s 'tests.api.basic_app_with_cqrs,tests.api.basic_app_db_model' -t '.'
coverage run -a --source=pdip -m unittest discover -v -b -s 'tests.api'  -t '.'
coverage run -a --source=pdip -m unittest discover -v -b -s 'tests.configuration' -t '.'
coverage run -a --source=pdip -m unittest discover -v -b -s 'tests.connection' -t '.'
coverage run -a --source=pdip -m unittest discover -v -b -s 'tests.cryptography' -t '.'
coverage run -a --source=pdip -m unittest discover -v -b -s 'tests.db' -t '.'
coverage run -a --source=pdip -m unittest discover -v -b -s 'tests.dependency' -t '.'
coverage run -a --source=pdip -m unittest discover -v -b -s 'tests.multi_processing' -t '.'
coverage run -a --source=pdip -m unittest discover -v -b -s 'tests.utils' -t '.'
coverage run -a --source=pdip run_tests.py
python3 -m coverage run -a --source=pdip -m unittest discover -v -b -s 'tests.api' -t '.'
python3 -m coverage run -a --source=pdip -m unittest discover -v -b -s 'tests.api.basic_app_with_cqrs' -t '.'
python3 -m coverage run -a --source=pdip -m unittest discover -v -b -s 'tests.configuration' -t '.'
python3 -m coverage run -a --source=pdip -m unittest discover -v -b -s 'tests.connection' -t '.'
python3 -m coverage run -a --source=pdip -m unittest discover -v -b -s 'tests.cryptography' -t '.'
python3 -m coverage run -a --source=pdip -m unittest discover -v -b -s 'tests.db' -t '.'
python3 -m coverage run -a --source=pdip -m unittest discover -v -b -s 'tests.dependency' -t '.'
python3 -m coverage run -a --source=pdip -m unittest discover -v -b -s 'tests.multi_processing' -t '.'
python3 -m coverage run -a --source=pdip -m unittest discover -v -b -s 'tests.utils' -t '.'

# run all tests and generate coverage informations
coverage run --source=pdip -m unittest discover -v -b 
<!-- coverage run -a --source=pdip -m unittest discover -v -b -s 'tests.multi_processing' -t '.' -->
coverage report -m --omit="*/tests/*,*/site-packages/*"
coverage html  --omit="*/tests/*,*/site-packages/*"
