# install requirements
pip install -r requirements.txt

# Install package
pip install .

# Uninstall package
pip uninstall pdi

# Run tests
pytest .

# Run tests with coverages
pytest --cov=./ -s 