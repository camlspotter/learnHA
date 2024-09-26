#!/bin/sh

set -e

rm -rf vandel/_out
mkdir vandel/_out

pipenv run python compile_ha.py --ode-solver-type fixed --ode-solver FixedStepAuto --invariant-mode 2 vandel/van_del_pol_oscillator.json --output-file vandel/_out/van_del_pol_oscillator.slx

pipenv run python loop.py \
     \
     --input-variables '' --output-variables 'x,y' \
     \
     --simulink-model-file vandel/_out/van_del_pol_oscillator.slx \
     --time-horizon 10.0 --sampling-time 0.001 \
     --fixed-interval-data False \
     --invariant '-5 <= x && x <= 5 && -5 <= y && y <= 5' \
     --number-of-cps '' --signal-types '' \
     \
     --output-directory vandel/_out \
     -c dtw -d 3 -m 1 -b 1 \
     --segmentation-error-tol 0.1 --segmentation-fine-error-tol 0.9 \
     --threshold-distance 9.0 --threshold-correlation 0.8 \
     --dbscan-eps-dist 0.01 --dbscan-min-samples 2 \
     --lmm-step-size 5 --is-invariant False --filter-last-segment True \
     --annotations '' \
     \
     --ode-solver-type fixed --ode-solver FixedStepAuto --invariant-mode 2 \
     \
     -n 10 \
     --counter-example-threshold 1.0
