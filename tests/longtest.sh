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
     -n 10 \
     --counter-example-threshold 1.0 \
     --max-nloops 2 \
     --annotations 'x:continuous,y:continuous'


# TwoTanks

output_directory=_out/twoTank
rm -rf $output_directory
mkdir -p $output_directory || true

pipenv run python loop.py \
     \
     --input-variables 'u' --output-variables 'x1,x2' \
     \
     --simulink-model-file data/models/twoTank.slx \
     --time-horizon 10 --sampling-time 0.001 \
     --fixed-interval-data False \
     --invariant 'u:(-0.1,0.1), x1:(1.2,1.2), x2:(1,1)' \
     --number-of-cps 'u:2' --signal-types 'u:linear' \
     \
     --output-directory $output_directory \
     -c dtw -d 1 -m 4 -b 1 \
     --segmentation-error-tol 0.01 \
     --threshold-distance 1.5 --threshold-correlation 0.7 \
     --lmm-step-size 5 --is-invariant False --filter-last-segment True \
     \
     --ode-solver-type fixed --ode-solver FixedStepAuto --invariant-mode 2 \
     --ode-speedup 50 \
     \
     -n 10 \
     --counter-example-threshold 10.0 \
     --max-nloops 10 \
     --annotations 'u:continuous,x1:continuous,x2:continuous'


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
     --counter-example-threshold 500.0 \
     --max-nloops 10 \
     --annotations 'x:continuous'


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
     -n 2 \
     --counter-example-threshold 10.0 \
     --max-nloops 10 \
     --annotations 'engineSpeed:continuous'
