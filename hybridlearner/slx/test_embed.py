import os
from hybridlearner.utils import io
from hybridlearner.slx.embed import *
from hybridlearner.matlab import engine

script = '_out/embed_model.m'

with io.open_for_write(script) as oc:
    embed(
        oc, 'data/models/ex_sldemo_bounce_Input.slx', 'embeded.slx', ['u'], ['x', 'v']
    )

# It builds _out/embeded.slx
try:
    os.remove('_out/embeded.slx')
except OSError:
    pass

engine.run(script)
