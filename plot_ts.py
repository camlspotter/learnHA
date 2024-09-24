import csv
import argparse
import os
import numpy as np
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description="TSV timeseries plotter to SVG")
parser.add_argument('tsv', metavar='tsv', type=str, help='Timeseries TSV file')
parser.add_argument(
    '--output-svg', '-o', help='SVG output', type=str, default=None, required=False
)
args = vars(parser.parse_args())

if args['output_svg'] is None:
    fn = os.path.splitext(args['tsv'])
    args['output_svg'] = fn[0] + ".svg"

with open(args['tsv'], 'r') as ic:
    reader = list(csv.reader(ic, delimiter='\t'))
    ts = [float(row[0]) for row in reader]
    vs = np.array([list(map(float, row[1:])) for row in reader])
    plt.plot(ts, vs)

plt.grid()
plt.savefig(args['output_svg'])
