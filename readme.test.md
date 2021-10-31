# Run tests

python -m unittest -v -b --locals

# Run tests with coverages

coverage run --source=pdip -m unittest discover -v coverage run --source=pdip -m unittest discover -v -b

## coverage with append

coverage run -a --concurrency=thread --source=pdip -m unittest -v -b 'tests.api'

## test coverage report

coverage report -m --omit="*/tests/*,*/site-packages/*"

## test coverage html

coverage html --omit="*/tests/*,*/site-packages/*"

## run tests for test modules with append
coverage run -a --source=pdip run_tests.py

# run all tests and generate coverage informations

coverage run -a --source=pdip run_tests.py
<!-- coverage run -a --source=pdip -m unittest discover -v -b -s 'tests.processing' -t '.' -->
<!-- coverage run -a --source=pdip -m unittest discover -v -b -s 'tests' -t '.' -->
coverage report -m --omit="*/tests/*,*/site-packages/*"
coverage html --omit="*/tests/*,*/site-packages/*"
