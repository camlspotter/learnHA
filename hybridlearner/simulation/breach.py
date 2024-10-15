# Simluation by Breach
import numpy as np
import textwrap
from .input import SignalType
from hybridlearner.utils import io as utils_io
from hybridlearner.matlab import engine
from hybridlearner.trajectory import Trajectories
from hybridlearner.types import Range
from hybridlearner.simulation import simulate_options


def simulate(
    opts: simulate_options, script_fn: str, model_fn: str, nsimulations: int
) -> Trajectories:
    build_script(opts, script_fn, model_fn, nsimulations)

    engine.run(script_fn)
    time = np.array(engine.getvar('time'))[0]

    signals = engine.getvar('signals')
    trajectories = list(map(lambda sig: (time, np.transpose(np.array(sig))), signals))

    return Trajectories(trajectories=trajectories, stepsize=opts.sampling_time)


def build_script(
    opts: simulate_options, script_fn: str, model_fn: str, nsimulations: int
) -> None:
    variable_index: dict[str, int] = {
        v: i for (i, v) in enumerate(opts.input_variables + opts.output_variables)
    }

    with utils_io.open_for_write(script_fn) as out:
        out.write("InitBreach;\n")

        # Fill variables to load the model
        for ov in opts.output_variables:
            idx = variable_index[ov]
            out.write(f"a{idx} = 42; % dummy\n")

        out.write(
            textwrap.dedent(
                f"""\
                timeStepMax = 42; %dummy
                timeFinal = 42; %dummy

                mdl = load_system('{model_fn}');
                Bsim = BreachSimulinkSystem(get_param(mdl, 'Name'));
                """
            )
        )

        # Range of the initial output variables
        for ov in opts.output_variables:
            idx = variable_index[ov]
            r: Range = opts.invariant[ov]
            out.write(f"Bsim.SetParamRanges({{'a{idx}'}}, [{r.min} {r.max}]);\n")

        # Generators of the input variables
        for iv in opts.input_variables:
            ncps = opts.number_of_cps[iv]
            signal_type = opts.signal_types[iv]
            r = opts.invariant[iv]
            match signal_type:
                case SignalType.FIXED_STEP:
                    out.write(f"Bsim.SetInputGen('UniStep{ncps}');\n")
                    for i in range(0, ncps):
                        out.write(
                            f"Bsim.SetParamRanges({{'{iv}In_u{i}'}}, [{r.min} {r.max}]);\n"
                        )

                case SignalType.LINEAR:
                    assert False, "LINEAR is not supported yet"

        out.write(
            textwrap.dedent(
                f"""\
                Bsim.SetParam('timeStepMax', {opts.sampling_time});

                Bsim.QuasiRandomSample({nsimulations});
                Bsim.Sim({opts.time_horizon}); % time up to {opts.time_horizon}
                % Bsim.PlotSignals();

                signals = Bsim.GetSignalList();
                output_signals = signals(1:{len(opts.input_variables + opts.output_variables)});
                traces = Bsim.GetTraces();
                
                % GetTime() seems broken.
                % time = Bsim.GetTime()
                time = Bsim.P.traj{{1}}.time

                signals = Bsim.GetSignalValues(output_signals);
                """
            )
        )
