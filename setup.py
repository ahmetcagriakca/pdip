from setuptools import setup, find_packages

setup(
    name='pdi',
    version='0.1.0',
    description='Python Data Integrator infrastructures',
    url='https://github.com/ahmetcagriakca/pdi',
    author='Ahmet Çağrı AKCA',
    author_email='ahmetcagriakca@gmail.com',
    license='MIT',
    packages=find_packages(),
    zip_safe=False,
    keywords=['PDI', 'API', 'ETL','PROCESS','MULTIPROCESS','IO','CQRS','MSSQL','ORACLE','POSTGRES','MYSQL','CSV'],
    install_requires=[
            'injector',
            'jsonpickle',
            'PyYAML',
            'Fernet',
            'cryptography',
            'SQLAlchemy',
            'Flask',
            'Flask_Cors',
            'Flask-Injector',
            'flask-restx',
            'Werkzeug',
            'dataclasses',
            'requests'
    ],
    classifiers=[
        # Define that your audience are developers
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',   # Again, pick a license
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
