"""
User-facing API for the Feature Factory collaborative platform.
"""

import os
from setuptools import setup, find_packages

name = "featurefactory"
pkg_name = name       

with open(os.path.join(pkg_name, '__init__.py')) as f:
    for line in f:
        if line.startswith('__version__'):
            __version__ = eval(line.split('=', 1)[1])
            break

setup(
    name             = name,
    author           = 'Micah Smith',
    author_email     = 'micahs@mit.edu',
    version          = __version__,
    description      = 'Feature Factory',
    long_description = '',
    url              = 'https://github.com/HDI-Project/FeatureFactory',
    packages         = find_packages(exclude=["tests", "__pycache__"]),
    install_requires = [
        'dill',
        'flask',
        'jupyter',
        'jupyterhub',
        'matplotlib',
        'numpy',
        'mysqlclient',
        'mysql-connector-python-rf',
        'pandas',
        'scikit-learn',
        'scipy',
        'sqlalchemy',
        'sqlalchemy_utils',
    ],
 )
