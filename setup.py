from os import getenv
from pathlib import Path

from setuptools import setup, find_packages

here = Path(__file__).parent.resolve()
long_description = (here / 'README.md').read_text(encoding='utf-8')

env_version = getenv('PYPI_PACKAGE_VERSION', default='0.8.0')
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
        exclude=[
            "tests", "tests*", "test_*",
            "examples", "examples.*", "examples*",
            "__pycache__", "*.__pycache__", "__pycache.*", "*.__pycache__.*",
        ]),
    zip_safe=False,
    keywords=['PDI', 'API', 'ETL', 'PROCESS', 'MULTIPROCESS', 'IO', 'CQRS', 'MSSQL', 'ORACLE', 'POSTGRES', 'MYSQL',
              'CSV'],
    python_requires='>=3.10',
    install_requires=[
        "injector",
        "PyYAML",
        "SQLAlchemy"
    ],
    extras_require={
        "api": [
            "Flask==3.1.3",
            "Flask_Cors==6.0.2",
            "Flask-Injector==0.15.0",
            "flask-restx==1.3.2",
            "markupsafe==3.0.3",
            "Werkzeug==3.1.8"
        ],
        "cryptography": [
            "cryptography==46.0.7"
        ],
        "integrator": [
            "oracledb>=2,<3",
            "confluent-kafka>=2.4,<3",
            "dataclasses-json==0.6.7",
            "func-timeout==4.3.5",
            "mysql-connector-python>=9.1,<10",
            "pandas==2.2.3",
            "psycopg2-binary==2.9.12",
            "pyodbc==5.3.0"
        ],
        "preferred": [
            "injector==0.24.0",
            "PyYAML==6.0.3",
            "SQLAlchemy==2.0.49"
        ]
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
    ],
    project_urls={  # Optional
        'Bug Reports': 'https://github.com/ahmetcagriakca/pdip/issues',
        'Source': 'https://github.com/ahmetcagriakca/pdip',
    },
)
