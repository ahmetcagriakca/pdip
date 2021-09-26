# Install package

pip install .

# setup create dist
set version of package with PYPI_PACKAGE_VERSION environment value
python setup.py sdist bdist_wheel

# twine check and upload

## twine  check 
python -m twine check dist/*

## twine  upload  test
python -m twine upload -r pdip --repository-url https://upload.pypi.org/legacy/. dist/* --verbose

## twine  upload  test
python -m twine upload -r pdip --repository-url https://test.pypi.org/legacy/ dist/* --verbose

# Uninstall package

pip uninstall pdip
