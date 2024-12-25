# Breach internals (sofar what I found)

https://github.com/decyphir/breach

First, read the tutorial.

## Breach path

```sh
export MATLABPATH=:$WHERE_YOU_PUT_BREACH
```

## Initialization

```
InitBreach;
```

## Load a model

```
Bsim = BreachSimulinkSystem('modelname');
```

Before it, if `modelname` contains free variables (such as `a1`, `a2`, etc for HybridLearner case), they must be assigned with dummy values:

```
a1 = 42;
a2 = 42;
Bsim = BreachSimulinkSystem('modelname');
```

## Simulation time span

```
Bsim.Sys.tspan = 0:0.01:100.0;  % See the head comment in Core/Falsify.m
```

## Initial parameter ranges

```
% Range of the initial value of output variable a1
Bsim.SetParamRanges({a1}, [0 100])
```

Breach will choose random values in these ranges.

## Input signal setting

```
% Input signal in_1 for input variable x0

% 3 control points uniformly distributed in the simulation time span,
% i.e, at 0%, 50% and 100%
Bsim.SetInputGen('UniStep3');

% Value ranges at the control points
Bsim.SetParamRanges({'in_1_u0'}, [2.0 9.0]);
Bsim.SetParamRanges({'in_1_u1'}, [2.0 9.0]);
Bsim.SetParamRanges({'in_1_u2'}, [2.0 9.0]);     
```

## Falsification

Follow what the tutorial says:

```
% Falsification
phi = STL_Formula('phi', 'alw (diff1[t] < 10.0)');
R = BreachRequirement(phi);
pb = FalsificationProblem(Bsim,R);               
```

If we want multiple counter examples:

```
% More than 1 counter examples if found
pb.StopAtFalse= 0
```

```
% How many cases to be checked
pb.max_obj_eval = 25; 
```

```
% Falsification and counter examples
pb.solve();
falses = pb.GetFalse();
```

```
% If no counter example is found, falses is empty
if isempty(falses)
    ....
end    
```

### Get times

```
% time = falses.GetTime() did not work for me
time = pb.BrSet_Logged.GetTime()
```


### Parameters tried

Tried parameters and their robustnesses:

- `pb.X_log`: tried parameters
- `pb.obj_log`: the robustnesses (probably)

## Parameter history hack

Note: **This is a hack.**

We can skip these parameters in future falisification by caching them:

```
cached_X_log = pb.X_log;
cached_obj_log = pb.obj_log;

...
% New problem
pb = FalsificationProblem(Bsim,R); 
% With cached history of the past:
pb.X_log = cached_X_log;
pb.obj_log = cached_obj_log;
pb.solve() # It does not use those already in `pb.X_log`.
```


### Getting signals:

Note😡😡😡: **The dimentions of these signals may be different when only 1 counter example is found.**  See `fix_signals` function to mend this issue.

Those of counter examples:

```
signals = falses.GetSignalValues({{'u'}, {'x'}, {'v'}});
```

Those of all the trials:

```
all_signals = pb.BrSet_Logged.GetSignalValues(signal_names);
```

### BreachSimulinkSystem

BreachSimulinkSystem('xxx') builds `xxx_breach.slx` at `$BREACH_DIR/Ext/ModelsData/xxx_breach.slx`.

If MATLAB annoys 'Parsing failed for machine: <a href="matlab:sf('Open', 87)">'xxx_breach'</a>`, you should check this model and simulate it by hand.

