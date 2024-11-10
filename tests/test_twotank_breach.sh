# TwoTanks

set -e

output_directory=_out/twoTank_breach
rm -rf $output_directory
mkdir -p $output_directory || true

pipenv run python loop_breach.py \
     \
     --input-variables 'u' --output-variables 'x,y' \
     \
     --simulink-model-file data/models/twoTank.slx \
     --time-horizon 10 --sampling-time 0.001 \
     --fixed-interval-data False \
     --invariant 'u:(-0.1,0.1), x:(1.2,1.2), y:(1,1)' \
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
     -n 5 \
     --counter-example-threshold 10.0 \
     --max-nloops 5 \
     --annotations 'u:continuous,x:continuous,y:continuous'
