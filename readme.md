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
coverage run --source=pdi -m pytest
python -m unittest -v -b --locals  

coverage run --source=pdi -m unittest -v
coverage run --source=pdi -m unittest -v -b 
# test coverage report
 coverage report -m --omit="*/tests/*,*/site-packages/*"

# test coverage html
coverage html  --omit="*/tests/*,*/site-packages/*"
