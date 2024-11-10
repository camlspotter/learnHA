## ./tests/test_bball_breach.sh

Working.

## ./tests/test_cell_breach.sh

Working.

## ./tests/test_engine_breach.sh

Working.

## ./tests/test_oscillator_breach.sh

Working.

## ./tests/test_twotank_breach.sh 

```
Error in falsify_learned_model (line 150)
pb.solve();

Error in run (line 91)
evalin('caller', strcat(script, ';'));
Suggested Actions:
      You can suppress the diagnostics and continue simulation without bracketing these zero crossings by switching the  zero crossing detection algorithm to 'Adaptive' and setting the Ignored Zero Crossings diagnostic to 'none'. - Fix
      Disable zero-crossing detection on the blocks listed above that caused the most events.
 - Show complete stack trace

Traceback (most recent call last):
  File "/home/jun/hal/HybridLearner/src/learnHA/loop_breach.py", line 152, in <module>
    result, new_tried_parameters, new_tried_obj_log = find_counter_examples(
  File "/home/jun/hal/HybridLearner/src/learnHA/hybridlearner/falsify/breach.py", line 32, in find_counter_examples
    engine.run(script_fn)
  File "/home/jun/hal/HybridLearner/src/learnHA/hybridlearner/matlab.py", line 24, in run
    _eng.run(fn, nargout=0)  # nargout=0 is required since x.m returns nothing.
  File "/home/jun/.local/share/virtualenvs/learnHA-q5-VROtl/lib/python3.10/site-packages/matlab/engine/matlabengine.py", line 71, in __call__
    _stderr, feval=True).result()
  File "/home/jun/.local/share/virtualenvs/learnHA-q5-VROtl/lib/python3.10/site-packages/matlab/engine/futureresult.py", line 67, in result
    return self.__future.result(timeout)
  File "/home/jun/.local/share/virtualenvs/learnHA-q5-VROtl/lib/python3.10/site-packages/matlab/engine/fevalfuture.py", line 82, in result
    self._result = pythonengine.getFEvalResult(self._future,self._nargout, None, out=self._out, err=self._err)
matlab.engine.MatlabExecutionError: Simulink will stop the simulation of model 'merged_breach' because the 1 zero crossing signal(s) identified below caused 1000 consecutive zero crossing events in time interval between 3.1554436208840472e-30 and 3.1585990645049313e-27.
 --------------------------------------------------------------------------------
Number of consecutive zero-crossings : 1000
           Zero-crossing signal name : Sf0
                          Block type : S-Function
                          Block path : 'merged_breach/twoTank/Chart'
--------------------------------------------------------------------------------
```
