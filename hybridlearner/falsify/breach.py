# Falsification by Breach
import os
import numpy as np
import textwrap
from hybridlearner.utils import io as utils_io
from hybridlearner.matlab import engine
from hybridlearner.trajectory import Trajectories
from hybridlearner.types import Range
from hybridlearner.simulation import simulate_protocol
from hybridlearner.falsify import find_counter_examples_protocol
from hybridlearner.simulation.input import SignalType
from hybridlearner.slx.merger import merge_without_save


def find_counter_examples(
    opts: find_counter_examples_protocol, learned_model_file: str
) -> Trajectories:
    script_fn = os.path.join(opts.output_directory, 'falsify_learned_model.m')

    build_script(opts, script_fn, learned_model_file)

    engine.run(script_fn)

    time = np.array(engine.getvar('time'))[0]
    signals = engine.getvar('signals')
    trajectory_list = list(
        map(lambda sig: (time, np.transpose(np.array(sig))), signals)
    )

    trs = Trajectories(trajectories=trajectory_list, stepsize=opts.sampling_time)

    #    with utils_io.open_for_write(output_file) as out:
    #        trs.output(out)

    return trs


def build_script(
    opts: find_counter_examples_protocol, script_fn: str, learned_model_file: str
) -> None:
    original_model_file = opts.simulink_model_file

    variable_index: dict[str, int] = {
        v: i for (i, v) in enumerate(opts.input_variables + opts.output_variables)
    }

    with utils_io.open_for_write(script_fn) as out:
        merged = merge_without_save(
            out, original_model_file, learned_model_file, 'merged.slx'
        )

        out.write("InitBreach;\n")

        # Fill variables to load the model
        for ov in opts.output_variables:
            idx = variable_index[ov]
            out.write(f"a{idx} = 42; % dummy\n")

        out.write(f"Bsim = BreachSimulinkSystem('{merged}');\n\n")

        # Range of the initial output variables
        for ov in opts.output_variables:
            idx = variable_index[ov]
            r: Range = opts.invariant[ov]
            out.write(f"Bsim.SetParamRanges({{'a{idx}'}}, [{r.min} {r.max}]);\n")

        # Generators of the input variables
        for iv in opts.input_variables:
            idx = variable_index[iv] + 1  # need +1
            ncps = opts.number_of_cps[iv]
            signal_type = opts.signal_types[iv]
            r = opts.invariant[iv]
            match signal_type:
                case SignalType.FIXED_STEP:
                    out.write(f"Bsim.SetInputGen('UniStep{ncps}');\n")
                    for i in range(0, ncps):
                        out.write(
                            f"Bsim.SetParamRanges({{'in_{idx}_u{i}'}}, [{r.min} {r.max}]);\n"
                        )

                case SignalType.LINEAR:
                    assert False, "LINEAR is not supported yet"

        # The output var signals are followed by the input var signals
        signal_positions = {
            v: i for (i, v) in enumerate(opts.output_variables + opts.input_variables)
        }
        signal_names = (
            "{"
            + ",".join(
                [
                    f'all_signal_names{{{signal_positions[v]+1}}}'
                    for v in opts.input_variables + opts.output_variables
                ]
            )
            + "}"
        )

        out.write(
            textwrap.dedent(
                f"""\
                Bsim.SetParam('timeStepMax', {opts.sampling_time}); % Probably the next line is enough.
                Bsim.Sys.tspan = 0:{opts.sampling_time}:{opts.time_horizon};  % See the head comment in Core/Falsify.m

                phi = STL_Formula('phi', 'alw (abs(out_a1[t] - out_b1[t]) < 0.1)');
                R = BreachRequirement(phi);
                pb = FalsificationProblem(Bsim,R);
                pb.StopAtFalse=0 % more than 1 counter examples if found
                pb.max_obj_eval = {opts.nsimulations};
                pb.solve();
                falses = pb.GetFalse();

                % Visualize the counter examples
                % falses.BrSet.PlotSignals();

                % GetTime() seems broken.
                % time = falses.GetTime()
                time = falses.P.traj{{1}}.time;

                all_signal_names = falses.GetSignalList();
                % Input variables must come first in Trajectories
                signal_names = {signal_names};
                signals = falses.GetSignalValues(signal_names);
                """
            )
        )
