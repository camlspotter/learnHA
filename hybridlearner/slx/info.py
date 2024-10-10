import os
import tempfile
import textwrap
from hybridlearner.matlab import engine


def get_Outports(fn: str) -> list[str]:
    fn = os.path.abspath(fn)
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.m', prefix='get_Outports_'
    ) as oc:
        oc.write(
            textwrap.dedent(
                f"""\
            global res;
            res='hello';
            modelPath = "{fn}";
            mdl = load_system(modelPath);
            modelName = get_param(mdl, 'Name');
            res = getfullname(Simulink.findBlocksOfType(mdl, 'Outport'));
            disp(res);
            """
            )
        )
        oc.flush()
        engine.run(oc.name)
        s = engine.getvar('res')
        print('result:', s)
        return s
