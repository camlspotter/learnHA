set -e
rm -rf _out

pipenv run python loop.py \
     \
     --input-variables 'u' --output-variables 'x,v' \
     \
     --simulink-model-file data/models/ex_sldemo_bounce_Input.slx \
     --time-horizon 13.0 --sampling-time 0.01 \
     --fixed-interval-data False \
     --invariant '-9.9 <= u && u <= -9.5 && 5 <= x && x <= 10 && 3 <= v && v <= 16' \
     --number-of-cps 'u:4' --signal-types 'u:linear' \
     \
     --output-directory _out \
     -c dtw -d 1 -m 1 -b 1 \
     --segmentation-error-tol 0.1 \
     --threshold-distance 18.0 --threshold-correlation 0.7 \
     --lmm-step-size 5 --is-invariant False --filter-last-segment True \
     --annotations '{u:continuous,x:constant(0)}' \
     \
     --ode-solver-type fixed --ode-solver FixedStepAuto --invariant-mode 2 \
     \
     -n 10 \
     --counter-example-threshold 1.0

# original
# --threshold-distance 9.0 --threshold-correlation 0.8
