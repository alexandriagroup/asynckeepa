"""
Setup for keepa
"""
from setuptools import setup
import os
import sys
from io import open as io_open

package_name = 'asynckeepa'

if sys.version_info < (3, 5, 3):
    raise RuntimeError("asynckeepa 3.x requires Python 3.5.3+")

# Get version from ./_version.py
__version__ = None
version_file = os.path.join(os.path.dirname(__file__), package_name, '_version.py')

with io_open(version_file, mode='r') as fd:
    exec(fd.read())

filepath = os.path.dirname(__file__)
readme_file = os.path.join(filepath, 'README.rst')

setup(
    name=package_name,
    packages=[package_name],
    version=__version__,
    description='Interfaces with keepa.com (async version)',
    long_description=open(readme_file).read(),
    author='Nicolas Baccelli',
    author_email='nicolas.baccelli@gmail.com',
    license='Apache Software License',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Database :: Front-Ends',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    url='https://github.com/alexandriagroup/asynckeepa',
    keywords='keepa',
    install_requires=['numpy>=1.9.3', 'aiohttp>=3.5.4']
)
