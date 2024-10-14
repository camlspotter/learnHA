import os
import tempfile
import textwrap
from typeguard import typechecked
from hybridlearner.matlab import engine


# Force runtime typechecking, since engine is not typed at all
@typechecked
def getvar_list_str(var: str) -> list[str]:
    res = engine.getvar(var)
    # Annoying!  A singleton list is returned as non-list
    # XXX What happens for the empty list?
    if not isinstance(res, list):
        res = [res]
    return res


def get_IOports(fn: str) -> tuple[list[str], list[str]]:
    fn = os.path.abspath(fn)
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.m', prefix='get_IOports_'
    ) as oc:
        oc.write(
            textwrap.dedent(
                f"""\
                global inports;
                global outports;
                inports='dummy';
                outports='dummy';
                modelPath = "{fn}";
                mdl = load_system(modelPath);
                inports = getfullname(Simulink.findBlocksOfType(mdl, 'Inport'));
                outports = getfullname(Simulink.findBlocksOfType(mdl, 'Outport'));
                """
            )
        )
        oc.flush()
        engine.run(oc.name)
        return (getvar_list_str('inports'), getvar_list_str('outports'))
