#!/bin/bash

set -e

# Cell model

output_directory=_out/cell
rm -rf $output_directory
mkdir -p $output_directory || true

pipenv run python loop.py \
     \
     --input-variables '' --output-variables 'x' \
     \
     --simulink-model-file data/models/excitable_cell.slx \
     --time-horizon 500 --sampling-time 0.01 \
     --fixed-interval-data False \
     --invariant 'x:(-76,-74)' \
     --number-of-cps '' --signal-types '' \
     \
     --output-directory $output_directory \
     -c dtw -d 1 -m 4 -b 1 \
     --segmentation-error-tol 0.01 \
     --threshold-distance 1.0 --threshold-correlation 0.92 \
     --lmm-step-size 5 --is-invariant False --filter-last-segment True \
     \
     --ode-solver-type fixed --ode-solver FixedStepAuto --invariant-mode 2 \
     --ode-speedup 3 \
     \
     -n 10 \
     --counter-example-threshold 10.0 \
     --max-nloops 5 \
     --annotations 'x:continuous'
