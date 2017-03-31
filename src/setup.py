"""
User-facing API for the Feature Factory collaborative platform.
"""

from setuptools import setup, find_packages

setup(
    name='featurefactory',
    version='0.2.0',
    description='Feature Factory',
    url='https://github.com/HDI-Project/FeatureFactory',
    packages=find_packages(exclude=["tests"]),
    install_requires=[
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
