#!/usr/bin/env python

from setuptools import setup

setup(name='featurefactory',
      version='0.1',
      description='Feature Factory',
      packages=['orm', 'factory', 'problems'],
      install_requires=[
          'jupyter',
          'matplotlib',
          'numpy',
          'mysqlclient',
          'mysql-connector-python-rf',
          'pandas',
          'scikit-learn',
          'scipy',
          'sqlalchemy',
          'sqlalchemy_utils'
      ]
     )
