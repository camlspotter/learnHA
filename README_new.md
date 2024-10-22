# HybridLearner in Python

## Preparation

- Install MATLAB R2022b at /usr/local/MATLAB/R2022b
- Install pipenv: `pip install pipenv`
- Install pipenv-shebang: `pip install pipenv-shebang`
- `pipenv --python 3.10`
- `pipenv install --dev`
- `export LANG=C` for correct printing of MATLAB warning and error messages
- [Breach](https://github.com/decyphir/breach) must be in MATLABPATH

Note:

Later versions of MATLAB likely work too by fixing the following fields in `Pipfile`:

- The version constraint of `matlabengine` to the one supported by your MATLAB version.
  Check https://pypi.org/project/matlabengine/#history
- `python_version`, to match with one of `matlabengine` supports.

### Cleaning

To start over the preparation:

- `pipenv --rm`

## Programs

At the toplevel directory, there are several application scripts:

`comple_ha.py`
:  Hybrid Automaton in JSON to MATLAB SLX model compiler

`simulate.py`
:  Simulator of modles in SLX

`inference.py` (or `run.py`)
:  Hybrid Automaton inference

`loop.py`
:  Inference loop

`plot_ts.py`
:  Timeseries plotter to SVG

`generate_simulation_script.py`
:  Simulation script generator. Deprecated. Now use `simulate.py`.

`generate_simulation_inputs.py`
:  Simulation input generator.  Deprecated. Now use `simulate.py`.

## Workflow example

### Step by step execution

#### Output directory

Dig a directory for the workflow:

```
$ mkdir _out
```

#### Run the original SLX model

```
$ pipenv run python simulate.py \
    --simulink-model-file data/models/ex_sldemo_bounce_Input.slx \
    --time-horizon 13.0 --sampling-time 0.001 \
    --fixed-interval-data False \
    --input-variables 'u' --output-variables 'x,v' \
    --invariant 'u:(-9.9, -9.5), x:(10.2, 10.5), v:(15,15)' \
    --number-of-cps 'u:4' --signal-types 'u:linear' \
    -o _out/bball.txt \
    -n 8
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
...
```

#### Inference

```
$ pipenv run python inference.py \
    -i _out/bball.txt \
    --output-directory _out \
    -c dtw -d 1 -m 1 -b 1 \
    --segmentation-error-tol 0.1 --segmentation-fine-error-tol 0.9 \
    --threshold-distance 9.0 --threshold-correlation 0.8 \
    --dbscan-eps-dist 0.01 --dbscan-min-samples 2 --lmm-step-size 5 \
    --input-variables u --output-variables x,v \
    --annotations 'u:continuous, x:constant(0)' \
    --is-invariant False --filter-last-segment True
```

It outputs `_out/learned_HA.json` (and `_out/learned_HA.txt` in the old format):

```
$ head _out/learned_HA.json 
{
  "init_mode": 0,
  "modes": [
    {
      "id": 0,
      "invariant": {},
      "flow": {
        "x": {
          "string": "u * 1.0598359126681102e-12 + x * -2.525757381022231e-15 + v * 1.0000000000000033 + 1.0315161919072224e-11"
        },
...
```

#### Compile the learned model to SLX

```
$ pipenv run python compile_ha.py \
    --ode-solver-type fixed \
    --ode-solver FixedStepAuto \
    --invariant-mode 2 \
    _out/learned_HA.json
```

It compiles the model to `_out/learned_HA.slx`.


#### Run the both original and learned models

Use the same parameters including the seed:

To run the original model with a fixed seed and save the result to `_out/bball0.txt`:
```
$ pipenv run python simulate.py \
    --simulink-model-file data/models/ex_sldemo_bounce_Input.slx \
    --time-horizon 13.0 --sampling-time 0.001 \
    --fixed-interval-data False \
    --input-variables 'u' --output-variables 'x,v' \
    --invariant 'u:(-9.9, -9.5), x:(10.2, 10.5), v:(15, 15)' \
    --number-of-cps 'u:4' --signal-types 'u:linear' \
    -o _out/bball0.txt \
    -S 0 -n 64
```

To run the learned model with the same seed and save the result to `_out/learned0.txt`:
```
$ pipenv run python simulate.py \
    --simulink-model-file _out/learned_HA.slx \
    --time-horizon 13.0 --sampling-time 0.001 \
    --fixed-interval-data False \
    --input-variables 'u' --output-variables 'x,v' \
    --invariant 'u:(-9.9, -9.5), x:(10.2, 10.5), v:(15, 15)' \
    --number-of-cps 'u:4' --signal-types 'u:linear' \
    -o _out/learned0.txt \
    -S 0 -n 64
```

#### Distance calculation

```
$ pipenv run python distance.py \
    --input-variables 'u' --output-variables 'x,v' \
    _out/bball0.txt _out/learned0.txt
```

To improve the inference, you can restart from the inference by giving counterexample
trajectories as the input.  It requires manual edition of trajectory files.

### Automatic execution of inference loop

`loop.py` automates the above manual step by step execution:

```
$ pipenv run python loop.py \
     \
     --input-variables 'u' --output-variables 'x,v' \
     \
     --simulink-model-file data/models/ex_sldemo_bounce_Input.slx \
     --time-horizon 13.0 --sampling-time 0.001 \
     --fixed-interval-data False \
     --invariant 'u:(-9.9, -9.5), x:(10.2, 10.5), v:(15, 15)' \
     --number-of-cps 'u:4' --signal-types 'u:linear' \
     \
     --output-directory _out \
     -c dtw -d 1 -m 1 -b 1 \
     --segmentation-error-tol 0.1 --segmentation-fine-error-tol 0.9 \
     --threshold-distance 9.0 --threshold-correlation 0.8 \
     --dbscan-eps-dist 0.01 --dbscan-min-samples 2 \
     --lmm-step-size 5 --is-invariant False --filter-last-segment True \
     --annotations 'u:continuous, x:constant(0)' \
     \
     --ode-solver-type fixed --ode-solver FixedStepAuto --invariant-mode 2 \
     \
     -n 10 \
     --counter-example-threshold 1.0
```

It iterates the following inference loop:

- Execute the original model to generate the initial trajectories
- Infer a hybrid automaton from the original model trajectories
- Compile the automaton to MATLAB slx model
- Execute the original and compiled models in the same parameters
- Compare the trajectories and extract counter examples
- Strengthen the original model trajectories with the counter examples and start over from the inference.

