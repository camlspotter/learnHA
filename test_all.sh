#!/bin/sh
set -e

./run_tests

pipenv run python generate_simulation_inputs.py --num-inputs 100 --time-horizon 13.0 --input-variables 'u' --output-variables 'x,v' --invariant 'u:(-9.9, -9.5), x:(10.2, 10.5), v:(15,15)' --number-of-cps 'u:4' --signal-types 'u:linear' -o _out/simulation_inputs.json

pipenv run python ./generate_simulation_script.py --script-file _out/original_model_simulate.m.bypython --simulink-model-file data/models/ex_sldemo_bounce_Input.slx  --time-horizon 10 --sampling-time 0.01 --fixed-interval-data False --input-variables "u" --output-variables "x,v"

./test_session.sh
