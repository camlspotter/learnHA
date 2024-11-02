# Hybrid Learner with Breach

## Summary

1. Get the initial learning trajectory set $T_0$ from the original model $O$.
2. Learn a hybrid automaton $A_i$ from the learning set $T_i$.
3. Combined SLX model $M_i$ of the original model $O$ and $i$-th learned model $A_i$.
4. Run Breach falsification over $M_i$ and get the counter examples $C_i$.
5. If $C_i = \emptyset$, exit the loop.
6. $T_{i+1}  = T_i \cup C_i$
7. Loop back to 2. 

## Issue 1: STL is not enough to express trajectory distances with time robustness

Current implementation of trajectory distance:

$$\mathrm{alw} (\bigwedge_i \mathrm{abs}(\mathrm{out\_a}_i[t] - \mathrm{out\_b}_i[t]) < \mathrm{threshold}_i)$$

It is not time-robust: only 1 frame with a large signal value difference could falsify the above STL.

I am afraid STL(Signal Temporal Logic) is not enough powerful to express the DTW distances between signals.

After some amount of research, I conclude that we can write MATLAB expressions in Breach STL, but they do not seem to access simulated trajectories easily. At least it is clear that such uses are not expected.

### Possible workaround: Trajectories of differences with time-robustness

In Simulink level, we can build signals of difference of the original and the learned signals with some time-robustness, though the DTW distance may not be implementable.



## Issue 2: The same inputs are chosen for each generation of the falsification

The same inputs are chosen repeatedly at the falsifications of different learning generations.  They must be skipped for performance.

### Workaround: fill the set of already tried

`pb.X_log` is a matrix carrying the input parameters already tried.  If we fill it with the `pb.X_log` of the falsification result for the previous generation, they may be skipped in the next falsification.  Nice thing of this method is that `pb` is accessible from the falsification script easily. The problem is that we are not sure this really works or not.
