set -e
OUTDIR=_out/cars1_with_v
MODEL=data/models/cars1_with_v.slx
rm -rf $OUTDIR
mkdir -p $OUTDIR || true

# input ports:  Car 1/Throttle, Car 1/Brake
# output ports: cars/Out1, cars/Out2, cars/Out3, cars/Out4, cars/Out5
# output port initial values:
#  - cars/Out1: 0
#  - cars/Out2: 10
#  - cars/Out3: 20
#  - cars/Out4: 30
#  - cars/Out5: 40

pipenv run python loop.py \
     \
     --input-variables 'Throttle, Brake' --output-variables 'y1, v1' \
     \
     --simulink-model-file $MODEL \
     --time-horizon 80.0 --sampling-time 0.01 \
     --fixed-interval-data False \
     --invariant 'Throttle:(0,1), Brake:(0,1), y1:(0,0), v1:(0,0)' \
     --number-of-cps 'Throttle:11, Brake:11' --signal-types 'Throttle:linear, Brake:linear' \
     --annotations 'y1:continuous, v1:continuous' \
     \
     --output-directory $OUTDIR \
     -c dtw -d 2 -m 1 -b 1 \
     --segmentation-error-tol 0.01 \
     --threshold-distance 100.0 --threshold-correlation 0.01 \
     --lmm-step-size 5 --is-invariant False --filter-last-segment True \
     \
     --ode-solver-type fixed --ode-solver FixedStepAuto --invariant-mode 2 \
     \
     -n 30 \
     --counter-example-threshold 1.0 \
     --max-nloops 5
