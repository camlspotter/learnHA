## Learning models by an STL spec

This experiment is to learn hybrid automata by giving a specification.
We find counter examples of learned models which violate the specification
then add the trajectories of the original models of the same inputs.
Finding the counter examples are done by Breach falsification.

### Command

`loop_by_spec.py`

### Test

`tests/test_bball_by_spec.sh`

Its STL specification is:

```
not (ev_[0,7.9] (alw_[0,2] (x[t] < 0.01)))
```

It asserts that the ball keeps bouncing:
the ball never keeps on the ground (or under the ground) more than 2 seconds.

The time constraint `[0,7.9]` for `ev` is required since 



