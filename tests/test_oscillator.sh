#!/bin/bash

set -e

# Switched Oscillator

output_directory=_out/oscillator
rm -rf $output_directory
mkdir -p $output_directory || true

pipenv run python loop.py \
     \
     --input-variables '' --output-variables 'x,y' \
     \
     --simulink-model-file data/models/oscillator.slx \
     --time-horizon 10 --sampling-time 0.01 \
     --fixed-interval-data False \
     --invariant 'x:(0.01, 0.09), y:(0.01, 0.09)' \
     --number-of-cps '' --signal-types '' \
     \
     --output-directory $output_directory \
     -c dtw -d 1 -m 4 -b 1 \
     --segmentation-error-tol 0.1 \
     --threshold-distance 1.0 --threshold-correlation 0.80 \
     --lmm-step-size 5 --is-invariant False --filter-last-segment True \
     \
     --ode-solver-type fixed --ode-solver FixedStepAuto --invariant-mode 2 \
     \
     -n 5 \
     --max-nloops 5 \
     --counter-example-threshold 0.5 \
     --annotations 'x:continuous,y:continuous'
