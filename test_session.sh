VARIABLE_OPTS="--input-variables 'u' --output-variables 'x,v'"
SIMULATION_OPTS="--time-horizon 13.0 --sampling-time 0.001 --fixed-interval-data False --invariant '-9.9 <= u && u <= -9.5 && 10.2 <= x && x <= 10.5 && 15 <= v && v <= 15' --number-of-cps 'u:4' --signal-types 'u:linear'"

rm -rf _out

eval "pipenv run python simulate.py $VARIABLE_OPTS $SIMULATION_OPTS --simulink-model-file ../../src/test_cases/engine/learn_ha_loop/ex_sldemo_bounce_Input.slx -o _out/bball.txt -n 8"

eval "pipenv run python inference.py $VARIABLE_OPTS -i _out/bball.txt --output-directory _out -c dtw -d 1 -m 1 -b 1 --segmentation-error-tol 0.1 --segmentation-fine-error-tol 0.9 --threshold-distance 9.0 --threshold-correlation 0.8 --dbscan-eps-dist 0.01 --dbscan-min-samples 2 --lmm-step-size 5 --is-invariant False --filter-last-segment True --annotations '{u:continuous,v:constant(0)}' "

pipenv run python compile_ha.py --ode-solver-type fixed --ode-solver FixedStepAuto --invariant-mode 2 _out/learned_HA.json

eval "pipenv run python simulate.py $VARIABLE_OPTS $SIMULATION_OPTS --simulink-model-file ../../src/test_cases/engine/learn_ha_loop/ex_sldemo_bounce_Input.slx -o _out/bball0.txt -S 0 -n 64"


eval "pipenv run python simulate.py $VARIABLE_OPTS $SIMULATION_OPTS --simulink-model-file _out/learned_HA.slx -o _out/learned0.txt -S 0 -n 64"

pipenv run python distance.py --output-variables 'x,y' _out/bball0.txt _out/learned0.txt
