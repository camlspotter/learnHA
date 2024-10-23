set -e

SIMULATION_OPTS=""

rm -rf _out/vandel_loop
mkdir _out/vandel_loop

pipenv run python compile_ha.py --ode-solver-type fixed --ode-solver FixedStepAuto --invariant-mode 2 tests/vandel/van_del_pol_oscillator.json --output-file _out/vandel_loop/van_del_pol_oscillator.slx

eval "pipenv run python loop.py \
     \
     --input-variables '' --output-variables 'x,y' \
     \
     --time-horizon 20.0 --sampling-time 0.01 \
     --fixed-interval-data False \
     --invariant 'x:(0.5,1.5), y:(0.5,1.5)' \
     --number-of-cps '' --signal-types '' \
     --simulink-model-file _out/vandel_loop/van_del_pol_oscillator.slx -n 10 \
     \
     --output-directory vandel/ -c dtw -d 1 -m 1 -b 1 --segmentation-error-tol 0.1 --segmentation-fine-error-tol 0.9 --threshold-distance 9.0 --threshold-correlation 0.8 --dbscan-eps-dist 0.01 --dbscan-min-samples 2 --lmm-step-size 5 --is-invariant False --filter-last-segment True --annotations '' \
     \
     --ode-solver-type fixed --ode-solver FixedStepAuto --invariant-mode 2 \
     \
     --counter-example-threshold 1.0"
