VARIABLE_OPTS="--input-variables 'u' --output-variables 'x,v'"
SIMULATION_OPTS="--time-horizon 13.0 --sampling-time 0.001 --fixed-interval-data False --invariant '-9.9 <= u && u <= -9.5 && 5 <= x && x <= 10 && 14 <= v && v <= 14' --number-of-cps 'u:4' --signal-types 'u:linear'"

rm -rf _out

eval "pipenv run python loop.py \
     \
     $VARIABLE_OPTS \
     \
     $SIMULATION_OPTS --simulink-model-file data/models/ex_sldemo_bounce_Input.slx -n 10 \
     \
     --output-directory _out -c dtw -d 1 -m 1 -b 1 --segmentation-error-tol 0.1 --segmentation-fine-error-tol 0.9 --threshold-distance 9.0 --threshold-correlation 0.8 --dbscan-eps-dist 0.01 --dbscan-min-samples 2 --lmm-step-size 5 --is-invariant False --filter-last-segment True --annotations '{u:continuous,x:constant(0)}'" \
     \
     --ode-solver-type fixed --ode-solver FixedStepAuto --invariant-mode 2 \
     \
     --counter-example-threshold 1.0
