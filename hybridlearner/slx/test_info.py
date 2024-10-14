from hybridlearner.slx.info import *

assert get_IOports('data/models/ex_sldemo_bounce_Input.slx') == (
    ['ex_sldemo_bounce_Input/uIn'],
    [
        'ex_sldemo_bounce_Input/Outport',
        'ex_sldemo_bounce_Input/Outport1',
        'ex_sldemo_bounce_Input/Outport2',
    ],
)
