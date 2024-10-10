# `hybridlearner` code structure

## `trajectory`

- Definition of simulation timeseries.
- `distance`: distance between timeserieses

## `simulation`

SLX model simulator

- `input`: Simulation initial data types and builder
- `script`: MATLAB simulation script

## `segmentation`

Trajectory segmentation

- `derivatives`: Compute differencials

## `inference`

Hybrid automaton inference

- `clustering`: Segment clustering
- `invariant`: Invariant inference
- `annotation`: Variable type annotation to optimize assignments
- `transition`: Transition inference (guards and assignments)

## `automaton`

Data type of hybrid automaton.

Conversion from `inference.Raw` (old type) to `HybridAutomaton`.

## `obsolete`

Printer of old type of hybrid automaton `inference.Raw`.

## `slx`

- `compiler`: compiler of hybrid automaton to MATLAB SLX model

## Other modules

- `polynomial`: Polynomials
- `astdsl`: Python expressions for small DSL
- `common`: Common options, i.e. input and output variables
