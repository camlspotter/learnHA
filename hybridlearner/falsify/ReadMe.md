This falsify directory contains falsifications by comparing the trajectories of the original and the learned models for the same inputs.

2 versions of falsifications are available:

- falsify.Falsifier: classic version, comparing trajectories using the DTW distance
- breach.Falsifier: Breach version, comparing trajectories using the integrals of the absolute values of trajectory differences

The both interfaces have the same types.
