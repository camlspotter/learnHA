set -e
OUTDIR=_out/bball_by_spec
rm -rf $OUTDIR

pipenv run python loop_by_spec.py \
     \
     --input-variables 'u' --output-variables 'x,v' \
     \
     --simulink-model-file data/models/ex_sldemo_bounce_Input.slx \
     --time-horizon 10.0 --sampling-time 0.01 \
     --fixed-interval-data False \
     --invariant 'u:(-15.0, -5.0), x:(5, 10), v:(-10, 16)' \
     --number-of-cps 'u:4' --signal-types 'u:linear' \
     \
     --output-directory $OUTDIR \
     -c dtw -d 1 -m 1 -b 1 \
     --segmentation-error-tol 0.01 \
     --threshold-distance 100.0 --threshold-correlation 0.01 \
     --lmm-step-size 5 --is-invariant False --filter-last-segment True \
     --annotations 'u:continuous, x:constant(0)' \
     \
     --ode-solver-type fixed --ode-solver FixedStepAuto --invariant-mode 2 \
     \
     -n 30 \
     --max-nloops 5 \
     \
     --stl-spec 'not (ev_[0,7.9] (alw_[0,2] (x[t] < 0.01)))'
