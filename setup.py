#!/usr/bin/env python

from distutils.core import setup
import os.path

setup(name='gator',
      version='1.0',
      description='Hydra ISF and QuakeML AggreGator',
      author='Mike Hearne',
      author_email='mhearne@usgs.gov',
      url='https://github.com/mhearne-usgs/gator',
      scripts=['aggregate.py'],
      data_files=(os.path.expanduser('~'),['gator.ini'])
     )
