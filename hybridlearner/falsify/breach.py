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
) -> tuple[Trajectories, Trajectories]:
    script_fn = os.path.join(opts.output_directory, 'falsify_learned_model.m')

    build_script(opts, script_fn, learned_model_file)

    engine.run(script_fn)

    time = np.array(engine.getvar('time'))[0]

    original_signals = engine.getvar('original_signals')
    original_trajectory_list = list(
        map(lambda sig: (time, np.transpose(np.array(sig))), original_signals)
    )
    original_trs = Trajectories(
        trajectories=original_trajectory_list, stepsize=opts.sampling_time
    )

    learned_signals = engine.getvar('learned_signals')
    learned_trajectory_list = list(
        map(lambda sig: (time, np.transpose(np.array(sig))), learned_signals)
    )
    learned_trs = Trajectories(
        trajectories=learned_trajectory_list, stepsize=opts.sampling_time
    )

    return original_trs, learned_trs


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

        out.write("% MATLABPATH must contain Breach\n")
        out.write("InitBreach;\n\n")

        # Fill variables to load the model
        out.write(
            "% Free variables must be assigned with dummy values for BreachSimulinkSystem\n"
        )
        for ov in opts.output_variables:
            idx = variable_index[ov]
            out.write(f"a{idx} = 42; % for output variable {ov}\n")

        out.write(f"\nBsim = BreachSimulinkSystem('{merged}');\n\n")

        # Range of the initial output variables
        for ov in opts.output_variables:
            idx = variable_index[ov]
            r: Range = opts.invariant[ov]
            out.write(f"% Range of the initial value of output variable {ov}\n")
            out.write(f"Bsim.SetParamRanges({{'a{idx}'}}, [{r.min} {r.max}]);\n\n")

        # Generators of the input variables
        for iv in opts.input_variables:
            idx = variable_index[iv] + 1  # need +1
            ncps = opts.number_of_cps[iv]
            signal_type = opts.signal_types[iv]
            r = opts.invariant[iv]
            out.write(f"% Input signal in_{idx} for input variable {iv}\n")
            match signal_type:
                case SignalType.FIXED_STEP:
                    out.write(f"Bsim.SetInputGen('UniStep{ncps}');\n")
                    for i in range(0, ncps):
                        out.write(
                            f"Bsim.SetParamRanges({{'in_{idx}_u{i}'}}, [{r.min} {r.max}]);\n"
                        )
                    out.write("\n")

                case SignalType.LINEAR:
                    out.write(
                        textwrap.dedent(
                            f"""\
                            input_gen.type = 'UniStep';
                            input_gen.cp = {ncps};
                            input_gen.method = {{'linear'}};
                            Bsim.SetInputGen(input_gen);
                            """
                        )
                    )
                    for i in range(0, ncps):
                        out.write(
                            f"Bsim.SetParamRanges({{'in_{idx}_u{i}'}}, [{r.min} {r.max}]);\n"
                        )

        # The output var signals are followed by the input var signals
        signal_positions = {
            v: i for (i, v) in enumerate(opts.output_variables + opts.input_variables)
        }
        original_signal_names = (
            "{"
            + ",".join(
                [
                    f'all_signal_names{{{signal_positions[v]+1}}}'
                    for v in opts.input_variables + opts.output_variables
                ]
            )
            + "}"
        )
        original_signal_comments = "\n".join(
            [
                f'% Original input variable {v} at signal #{signal_positions[v]+1}'
                for v in opts.input_variables
            ]
            + [
                f'% Original output variable {v} at signal #{signal_positions[v]+1}'
                for v in opts.output_variables
            ]
        )

        shift = len(opts.input_variables) + len(opts.output_variables)
        learned_signal_names = (
            "{"
            + ",".join(
                [
                    f'all_signal_names{{{signal_positions[v]+1+shift}}}'
                    for v in opts.input_variables + opts.output_variables
                ]
            )
            + "}"
        )
        learned_signal_comments = "\n".join(
            [
                f'% Learned input variable {v} at signal #{signal_positions[v]+1+shift}'
                for v in opts.input_variables
            ]
            + [
                f'% Learned output variable {v} at signal #{signal_positions[v]+1+shift}'
                for v in opts.output_variables
            ]
        )

        out.write(
            textwrap.dedent(
                f"""\
                Bsim.SetParam('timeStepMax', {opts.sampling_time}); % Probably the next line is enough.
                Bsim.Sys.tspan = 0:{opts.sampling_time}:{opts.time_horizon};  % See the head comment in Core/Falsify.m

                % Falsification
                phi = STL_Formula('phi', 'alw (abs(out_a1[t] - out_b1[t]) < 0.1)');
                R = BreachRequirement(phi);
                pb = FalsificationProblem(Bsim,R);
                pb.StopAtFalse=0 % more than 1 counter examples if found
                pb.max_obj_eval = {opts.nsimulations};
                pb.solve();
                falses = pb.GetFalse();

                % Visualize the counter examples
                % falses.BrSet.PlotSignals();

                % Times
                % time = falses.GetTime() % GetTime() seems broken.
                time = falses.P.traj{{1}}.time;

                all_signal_names = falses.GetSignalList();
                """
            )
        )
        out.write(f"{original_signal_comments}\n")
        out.write(
            textwrap.dedent(
                f"""\
                original_signal_names = {original_signal_names};
                original_signals = falses.GetSignalValues(original_signal_names);

                """
            )
        )

        out.write(f"{learned_signal_comments}\n")
        out.write(
            textwrap.dedent(
                f"""\
                learned_signal_names = {learned_signal_names};
                learned_signals = falses.GetSignalValues(learned_signal_names);

                % Get values of time, original_signals and learned_signalsfrom Python!
                """
            )
        )
