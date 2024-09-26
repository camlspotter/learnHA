#!/bin/sh

set -e

pipenv run python compile_ha.py --ode-solver-type fixed --ode-solver FixedStepAuto --invariant-mode 2 vandel/van_del_pol_oscillator.json

# Bug: number-of-cps and signal-types cannot be empty
pipenv run python simulate.py \
       --input-variables '' --output-variables 'x,y' \
       --time-horizon 20.0 --sampling-time 0.01 \
       --fixed-interval-data False \
       --invariant '0.5 <= x && x <= 1.5 && 0.5 <= y && y <= 1.5' \
       --simulink-model-file vandel/van_del_pol_oscillator.slx \
       -o vandel/simulate.txt \
       --number-of-cps '' --signal-types '' \
       -n 10

pipenv run python inference.py \
       --input-variables '' --output-variables 'x,y' \
       -i vandel/simulate.txt \
       --output-directory vandel \
       -c dtw -d 3 -m 1 -b 1 \
       --segmentation-error-tol 0.1 --segmentation-fine-error-tol 0.9 \
       --threshold-distance 9.0 --threshold-correlation 0.8 \
       --dbscan-eps-dist 0.01 --dbscan-min-samples 2 --lmm-step-size 5 --is-invariant False \
       --filter-last-segment True

