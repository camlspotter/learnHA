# Old tests

## Bball

- test_bball.sh: working
- test_bball_breach.sh: working
- test_bball_by_spec.sh: working

## Cell

- test_cell.sh: working
- test_cell_breach.sh: working

## Engine

- test_engine.sh: working
- test_engine_breach.sh: working

## Oscillator

- test_oscillator.sh: working
- test_oscillator_breach.sh: working

## Two tanks

- test_twotank.sh: working
- test_twotank_breach.sh: working

## Vandel

Not a hybrid model. A test of higher dimension ODEs.

- vandel/vandel.sh: working
- vandel/vandel_loop.sh: working

## Session

Testing smaller tools

- test_session.sh: working

# Newer tests

## Cars

Car racing with 4, 1, 2 cars

- test_car.sh: working but the result is not good
- test_cars1.sh: working but the result is not good
- test_cars1_breach.sh: working but the result is not good
- test_cars1_with_v.sh: working but the result is not good
- test_cars2.sh: working but the result is not good
- test_cars2_with_v.sh: working but the result is not good

## Chopper

Using ME's model not included in this repository

- test_chopper0_1.sh: fails at simulation

```
    self._result = pythonengine.getFEvalResult(self._future,self._nargout, None, out=self._out, err=self._err)
matlab.engine.MatlabExecutionError: ['chopper0_1/Solver Configuration']: 整合的な状態とモードについて求解する、時間 0.0026 での過渡的な初期化が収束しませんでした。
```

We may fix it with other solvers than auto.

## Transport delay

- test_transport_delay.sh: fails because the model does not follow the requirements for HybridLearner.

```
Error: The first output of Ti 100.0 is different from the one specified 0.0.
       The initial value variable a1 might not be used properly.
```



