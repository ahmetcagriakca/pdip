from os import getenv
from pathlib import Path

from setuptools import setup, find_packages

here = Path(__file__).parent.resolve()
long_description = (here / 'README.md').read_text(encoding='utf-8')

env_version = getenv('PYPI_PACKAGE_VERSION', default='0.6.6')
version = env_version.replace('v', '')
setup(
    name='pdip',
    version=f'{version}',
    description='Python Data Integrator infrastructures package',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/ahmetcagriakca/pdip',
    download_url=f'https://github.com/ahmetcagriakca/pdip/archive/refs/tags/v{version}.tar.gz',
    author='Ahmet Çağrı AKCA',
    author_email='ahmetcagriakca@gmail.com',
    license='MIT',
    packages=find_packages(
        exclude=["tests", "tests*", "test_*", '__pycache__', '*.__pycache__', '__pycache.*', '*.__pycache__.*']),
    zip_safe=False,
    keywords=['PDI', 'API', 'ETL', 'PROCESS', 'MULTIPROCESS', 'IO', 'CQRS', 'MSSQL', 'ORACLE', 'POSTGRES', 'MYSQL',
              'CSV'],
    python_requires='>=3.8',
    install_requires=[
        "dataclasses",
        "injector",
        "PyYAML",
        "SQLAlchemy"
    ],
    extras_require={
        "api": [
            "Flask==2.2.3",
            "Flask_Cors==3.0.10",
            "Flask-Ext==0.1",
            "Flask-Injector==0.14.0",
            "flask-restx==1.1.0",
            "markupsafe==2.1.5",
            "Werkzeug==2.2.3"
        ],
        "cryptography": [
            "cryptography==41.0.7",
            "Fernet==1.0.1"
        ],
        "integrator": [
            "cx_Oracle==8.2.1",
            "dataclasses-json==0.5.6",
            "func-timeout==4.3.5",
            "kafka-python==2.0.2",
            "mysql-connector-python==8.0.26",
            "pandas==2.1.4",
            "psycopg2-binary==2.8.6",
            "pyodbc==4.0.30"
        ],
        "preferred": [
            "dataclasses==0.6",
            "injector==0.21.0",
            "PyYAML==6.0.1",
            "SQLAlchemy==2.0.23"
        ]
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    project_urls={  # Optional
        'Bug Reports': 'https://github.com/ahmetcagriakca/pdip/issues',
        'Source': 'https://github.com/ahmetcagriakca/pdip',
    },
)
