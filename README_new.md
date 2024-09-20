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

## Workflow example

### Output directory

Dig a directory for the workflow:

```
$ mkdir _out
```

### Run the original SLX model

```
$ pipenv run python simulate.py --simulink-model-file ../../src/test_cases/engine/learn_ha_loop/ex_sldemo_bounce_Input.slx --time-horizon 13.0 --sampling-time 0.001 --fixed-interval-data False --input-variables 'u' --output-variables 'x,v' --invariant '-9.9 <= u && u <= -9.5 && 10.2 <= x && x <= 10.5 && 15 <= v && v <= 15' --number-of-cps 'u:4' --signal-types 'u:linear' -o _out/bball.txt -S 0 -n 8
```

It generates `_out/bball.txt`:

```
$ head _out/bball.txt
0	-9.56223125938998	10.3533824164106	15
0.001	-9.56223924100062	10.3683776352936	14.9904377647498
0.002	-9.56224722261126	10.3833632919374	14.980875521518
0.003	-9.5622552042219	10.398339386334	14.9713132703046
0.004	-9.56226318583253	10.4133059184754	14.9617510111096
0.005	-9.56227116744317	10.4282628883536	14.9521887439329
0.006	-9.56227914905381	10.4432102959606	14.9426264687747
0.007	-9.56228713066445	10.4581481412884	14.9330641856348
0.008	-9.56229511227509	10.4730764243292	14.9235018945133
0.009	-9.56230309388573	10.4879951450748	14.9139395954103
```

### Run inference

```
$ pipenv run python run.py -i _out/bball.txt --output-directory _out -c dtw -d 1 -m 1 -b 1 --segmentation-error-tol 0.1 --segmentation-fine-error-tol 0.9 --threshold-distance 9.0 --threshold-correlation 0.8 --dbscan-eps-dist 0.01 --dbscan-min-samples 2 --input-variables x0 --output-variables x1,x2 --lmm-step-size 5 --annotations '{x0:continuous,x1:constant(0)}' --is-invariant False --filter-last-segment True
```

It outputs `_out/learned_HA.txt` and `_out/learned_HA.json`:

```
$ head _out/learned_HA.json 
{
  "init_mode": 0,
  "modes": [
    {
      "id": 0,
      "invariant": {},
      "flow": {
        "x1": {
          "x0": 1.0598359126681102e-12,
          "x1": -2.525757381022231e-15,
```

### Compile the learned model to SLX

```
$ pipenv run python compile_ha.py --ode-solver-type fixed --ode-solver FixedStepAuto --invariant-mode 2 _out/learned_HA.json
```

It compiles the model to `_out/learned_HA.slx`.


### Run the both original and learned models

To run the original model with a fixed seed and save the result to `_out/bball0.txt`:
```
$ pipenv run python simulate.py -S 0 --simulink-model-file ../../src/test_cases/engine/learn_ha_loop/ex_sldemo_bounce_Input.slx --time-horizon 13.0 --sampling-time 0.001 --fixed-interval-data False --input-variables 'u' --output-variables 'x,v' --invariant '-9.9 <= u && u <= -9.5 && 10.2 <= x && x <= 10.5 && 15 <= v && v <= 15' --number-of-cps 'u:4' --signal-types 'u:linear' -o _out/bball0.txt -S 0 -n 64
```

To run the learned model with the same seed and save the result to `_out/learned0.txt`:
```
$ pipenv run python simulate.py -S 0 --simulink-model-file _out/learned_HA.slx --time-horizon 13.0 --sampling-time 0.001 --fixed-interval-data False --input-variables 'u' --output-variables 'x,v' --invariant '-9.9 <= u && u <= -9.5 && 10.2 <= x && x <= 10.5 && 15 <= v && v <= 15' --number-of-cps 'u:4' --signal-types 'u:linear' -o _out/learned0.txt -S 0 -n 64
```

### Distance

pipenv run python distance.py --output-variables xy _out/bball0.txt _out/learned0.txt