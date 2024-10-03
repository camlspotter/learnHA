#!/bin/sh
set -e

OUTDIR=tests/2inputs/_out

rm -rf $OUTDIR

pipenv run python compile_ha.py --ode-solver-type fixed --ode-solver FixedStepAuto --invariant-mode 2 tests/2inputs/test.json --output-file $OUTDIR/test.slx

pipenv run python loop.py \
     \
     --input-variables 'y,x' --output-variables 'h,g' \
     \
     --simulink-model-file $OUTDIR/test.slx \
     --time-horizon 10.0 --sampling-time 0.1 \
     --fixed-interval-data False \
     --invariant 'y:(-10, 10), x:(-10, 10), h:(-10, 10), g:(-10,10)' \
     --number-of-cps 'y:5,x:5' --signal-types 'y:linear,x:linear' \
     \
     --output-directory $OUTDIR \
     -c dtw -d 1 -m 1 -b 1 \
     --segmentation-error-tol 0.01 \
     --threshold-distance 100.0 --threshold-correlation 0.01 \
     --lmm-step-size 5 --is-invariant False --filter-last-segment True \
     \
     --ode-solver-type fixed --ode-solver FixedStepAuto --invariant-mode 2 \
     \
     -n 10 \
     --counter-example-threshold 1.0 \
     --max-nloops 2

# original
# --threshold-distance 9.0 --threshold-correlation 0.8
