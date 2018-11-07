"""
User-facing API for the FeatureHub collaborative platform.
"""

import os
from setuptools import setup, find_packages

name = "featurehub"
pkg_name = name       

with open('./requirements.txt', 'r') as f:
    requirements = f.readlines()

requirements_autosklearn = ['auto-sklearn==0.2.0']
requirements_xgboost = ['xgboost==0.81']

extras_require = {
    'autosklearn': requirements_autosklearn,
    'xgboost': requirements_xgboost,
    'all': requirements_autosklearn + requirements_xgboost,
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
    setup_requires   = setup_requirements,
    test_suite       = 'tests',
    tests_require    = test_requirements,
    extras_require   = extras_require,
 )
