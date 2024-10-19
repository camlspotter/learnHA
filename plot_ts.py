#!/usr/bin/env pipenv-shebang

import csv
import argparse
import os
import numpy as np
from hybridlearner.plot import plot_timeseries_multi
from hybridlearner.trajectory import load_trajectories

parser = argparse.ArgumentParser(description="TSV timeseries plotter to SVG")
parser.add_argument('tsv', metavar='tsv', type=str, help='Timeseries TSV file')
parser.add_argument(
    '--output', '-o', help='Output file', type=str, default=None, required=False
)
args = vars(parser.parse_args())

if args['output'] is None:
    fn = os.path.splitext(args['tsv'])
    output = fn[0] + ".svg"
else:
    output = args['output']

header, trajectories = load_trajectories(args['tsv'])

# Drop 'time' header
plot_timeseries_multi(output, output, header[1:], trajectories)
