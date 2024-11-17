set -e
OUTDIR=_out/slexEntityTransportDelay
MODEL=data/models/slexEntityTransportDelay_fixed.slx
rm -rf $OUTDIR
mkdir -p $OUTDIR || true

# slexEntityTransportDelay.slx

# inports ['slexEntityTransportDelay/Dynamics of conveyor belt/n']
# outports ['slexEntityTransportDelay/Dynamics of conveyor belt/Ti', 'slexEntityTransportDelay/Dynamics of conveyor belt/v', 'slexEntityTransportDelay/Dynamics of conveyor belt/P', 'slexEntityTransportDelay/Dynamics of conveyor belt/mode']

# 上のポート情報は slx を開いた Dynamics of converyor belt の図のポート。
# そのうち、 n はポワソン分布に従う入力が回路上では生成されているように見える。
# [0,100]
# input_variables からは除外すべき

# allParams = get_param(mdl, 'ObjectParameters') で double になっている mdl のパラメータを列挙できる
# StopTime : 'timeFinal'
# SolverName : 'FixedStepAuto'
# FixedStep: 'timeStepMax'

pipenv run python loop.py \
     \
     --input-variables 'n' --output-variables 'Ti,v,P,mode' \
     \
     --simulink-model-file $MODEL \
     --time-horizon 900.0 --sampling-time 0.1 \
     --fixed-interval-data False \
     --invariant 'Ti:(0,0), v:(0,0), P:(0,0), mode:(0,0), n:(0,100)' \
     --number-of-cps 'n:10' --signal-types 'n:linear' \
     \
     --output-directory $OUTDIR \
     -c dtw -d 1 -m 1 -b 1 \
     --segmentation-error-tol 0.01 \
     --threshold-distance 100.0 --threshold-correlation 0.01 \
     --lmm-step-size 5 --is-invariant False --filter-last-segment True \
     \
     --ode-solver-type fixed --ode-solver FixedStepAuto --invariant-mode 2 \
     \
     -n 10 \
     --counter-example-threshold 1.0 \
     --max-nloops 5
