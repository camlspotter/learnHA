import os
from hybridlearner.utils import io
from hybridlearner.slx.merger import *
from hybridlearner.matlab import engine

script = '_out/merge_models.m'

with io.open_for_write(script) as oc:
    # It builds _out/merged.slx
    try:
        os.remove('_out/merged.slx')
    except OSError:
        pass

    merge(
        oc,
        'data/models/ex_sldemo_bounce_Input.slx',
        'data/models/bball_learned_HA0.slx',
        'merged.slx',
    )

engine.run(script)
