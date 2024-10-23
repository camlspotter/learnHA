#!/bin/bash

set -e

# Engine Timing System

output_directory=_out/engine
rm -rf $output_directory
mkdir -p $output_directory || true

# engine_64.slx seems to be built from sldemo_engine*.slx.
#
# Simulations of sldemo_engine*.slx produce trajectories with non unique times-steps,
# which are not supported by the current inference algorithm.

pipenv run python loop.py \
     \
     --input-variables 'throttle,torque' --output-variables 'engineSpeed' \
     \
     --simulink-model-file data/models/engine_64.slx \
     --time-horizon 10 --sampling-time 0.01 \
     --fixed-interval-data False \
     --invariant 'throttle:(2,9),torque:(24,25),engineSpeed:(2000,2000)' \
     --number-of-cps 'throttle:3,torque:3' --signal-types 'throttle:fixed-step,torque:fixed-step' \
     \
     --output-directory $output_directory \
     -c dtw -d 1 -m 20 -b 1 \
     --segmentation-error-tol 0.99 \
     --threshold-distance 1000 --threshold-correlation 0.9 \
     --lmm-step-size 5 --is-invariant False --filter-last-segment False \
     \
     --ode-solver-type variable --ode-solver ode45 --invariant-mode 2 \
     --ode-speedup 100 \
     \
     -n 5 \
     --counter-example-threshold 10.0 \
     --max-nloops 5 \
     --annotations 'engineSpeed:continuous'
