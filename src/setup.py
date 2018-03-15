"""
User-facing API for the FeatureHub collaborative platform.
"""

import os
from setuptools import setup, find_packages

name = "featurehub"
pkg_name = name       

requirements = ['dill',
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
                'xxhash',
               ]

extras_require = {
    'AutoSklearn': ['auto-sklearn==0.2.0'],
}
  

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', ]

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
    description      = 'FeatureHub',
    long_description = '',
    url              = 'https://github.com/HDI-Project/FeatureHub',
    packages         = find_packages(exclude=["tests", "__pycache__"]),
    install_requires = requirements,
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    extras_require   = extras_require,
 )
