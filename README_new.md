# HybridLearner in Python

## Install

- Install pipenv
- pipenv --python 3.10
- pipenv install

## Programs

comple_ha.py
:  Hybrid Automaton to MATLAB SLX model compiler

simulate.py
:  Simulator of modles in SLX

generate_simulation_script.py
:  Simulation script generator. Deprecated. Now use `simulate.py`.

plot_ts.py
:  Timeseries plotter to SVG

run.py
:  Original Hybrid Automaton inference

## Workflow

`mkdir _out`

### Simulation of the original SLX model

`pipenv run python simulate.py --simulink-model-file ../../src/test_cases/engine/learn_ha_loop/ex_sldemo_bounce_Input.slx --time-horizon 13.0 --sampling-time 0.001 --fixed-interval-data False --input-variables 'u' --output-variables 'x,v' --invariant '-9.9 <= u && u <= -9.5 && 10.2 <= x && x <= 10.5 && 15 <= v && v <= 15' --number-of-cps 'u:4' --signal-types 'u:linear' -o _out/bball.txt -S 0 -n 64`

It generates `_out/bball.txt`.

### Run inference

`pipenv run python run.py -i _out/bball.txt --output-directory _out -c dtw -d 1 -m 1 -b 1 --segmentation-error-tol 0.1 --segmentation-fine-error-tol 0.9 --threshold-distance 9.0 --threshold-correlation 0.8 --dbscan-eps-dist 0.01 --dbscan-min-samples 2 --input-variables x0 --output-variables x1,x2 --lmm-step-size 5 --annotations '{x0:continuous,x1:constant(0)}' --is-invariant False --filter-last-segment True`

It outputs `_out/learned_HA.txt` and `_out/learned_HA.json`.

### Compile to SLX model

`pipenv run python compile_ha.py --ode-solver-type fixed --ode-solver FixedStepAuto --invariant-mode 2 _out/learned_HA.json`

It compiles the model to `_out/learned_HA.slx`.

