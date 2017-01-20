#!/usr/bin/env python2

from __future__ import print_function, division, absolute_import

# Load config, utils, venv
import os.path
import imp
my_dir = os.path.dirname(os.path.abspath(__file__))
utils = imp.load_source('utils', os.path.join(my_dir, '../utils.py'))
conf = utils.conf
utils.activate_virtualenv()

input_file_parser = imp.load_source('input_file_parser', os.path.join(my_dir, 'input_file_parsers/{}.py'.format(conf.source_file_parser)))

import subprocess
import os
import sys

tabix = utils.get_path('tabix')
bgzip = utils.get_path('bgzip')

matrix_fname = os.path.join(conf.data_dir, 'matrix.tsv')
matrix_gz_fname = os.path.join(conf.data_dir, 'matrix.tsv.gz')

utils.run_script('''
# Tabix expects the header line to start with a '#'
(echo -n '#'; cat '{matrix_fname}') |
'{bgzip}' > '{matrix_gz_fname}'
'''.format(**locals()))

utils.run_cmd([tabix, '-p' ,'vcf', matrix_gz_fname])
