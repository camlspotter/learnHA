set -e

rm -rf _out/session

pipenv run python generate_simulation_inputs.py --num-inputs 100 --time-horizon 13.0 --input-variables 'u' --output-variables 'x,v' --invariant 'u:(-9.9, -9.5), x:(10.2, 10.5), v:(15,15)' --number-of-cps 'u:4' --signal-types 'u:linear' -o _out/session/simulation_inputs.json

pipenv run python ./generate_simulation_script.py --script-file _out/session/original_model_simulate.m.bypython --simulink-model-file data/models/ex_sldemo_bounce_Input.slx  --time-horizon 10 --sampling-time 0.01 --fixed-interval-data False --input-variables "u" --output-variables "x,v"

VARIABLE_OPTS="--input-variables 'u' --output-variables 'x,v'"
SIMULATION_OPTS="--time-horizon 13.0 --sampling-time 0.001 --fixed-interval-data False --invariant 'u:(-9.9, -9.5), x:(10.2, 10.5), v:(15,15)' --number-of-cps 'u:4' --signal-types 'u:linear'"

eval "pipenv run python simulate.py $VARIABLE_OPTS $SIMULATION_OPTS --simulink-model-file data/models/ex_sldemo_bounce_Input.slx -o _out/session/bball.txt -n 4"

eval "pipenv run python inference.py $VARIABLE_OPTS -i _out/session/bball.txt --output-directory _out -c dtw -d 1 -m 1 -b 1 --segmentation-error-tol 0.1 --segmentation-fine-error-tol 0.9 --threshold-distance 9.0 --threshold-correlation 0.8 --dbscan-eps-dist 0.01 --dbscan-min-samples 2 --lmm-step-size 5 --is-invariant False --filter-last-segment True --annotations 'u:continuous,x:constant(0)'"

pipenv run python compile_ha.py --ode-solver-type fixed --ode-solver FixedStepAuto --invariant-mode 2 _out/session/learned_HA.json

eval "pipenv run python simulate.py $VARIABLE_OPTS $SIMULATION_OPTS --simulink-model-file data/models/ex_sldemo_bounce_Input.slx -o _out/session/bball0.txt -S 0 -n 4"


eval "pipenv run python simulate.py $VARIABLE_OPTS $SIMULATION_OPTS --simulink-model-file _out/session/learned_HA.slx -o _out/session/learned0.txt -S 0 -n 4"

eval "pipenv run python distance.py $VARIABLE_OPTS _out/session/bball0.txt _out/session/learned0.txt"
