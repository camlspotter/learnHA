set -e
rm -rf _out/bball_breach

pipenv run python loop_breach.py \
     \
     --input-variables 'u' --output-variables 'x,v' \
     \
     --simulink-model-file data/models/ex_sldemo_bounce_Input.slx \
     --time-horizon 13.0 --sampling-time 0.01 \
     --fixed-interval-data False \
     --invariant 'u:(-15.0, -5.0), x:(5, 10), v:(3, 16)' \
     --number-of-cps 'u:4' --signal-types 'u:linear' \
     \
     --output-directory _out/bball_breach \
     -c dtw -d 1 -m 1 -b 1 \
     --segmentation-error-tol 0.01 \
     --threshold-distance 100.0 --threshold-correlation 0.01 \
     --lmm-step-size 5 --is-invariant False --filter-last-segment True \
     --annotations 'u:continuous, x:constant(0)' \
     \
     --ode-solver-type fixed --ode-solver FixedStepAuto --invariant-mode 2 \
     \
     -n 10 \
     --counter-example-threshold 1.0 \
     --max-nloops 3
