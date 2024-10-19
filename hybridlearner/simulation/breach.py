# Simluation by Breach
import os
import numpy as np
import textwrap
from .input import SignalType
from hybridlearner.utils import io as utils_io
from hybridlearner.matlab import engine
from hybridlearner.trajectory import Trajectories, write_trajectories
from hybridlearner.types import Range
from hybridlearner.simulation import simulate_protocol


def simulate(
    opts: simulate_protocol,
    simulink_model_file: str,
    output_file: str,
    nsimulations: int,
) -> Trajectories:
    script_fn = os.path.join(opts.output_directory, "simulate_model.m")

    build_script(opts, script_fn, simulink_model_file, nsimulations)

    engine.run(script_fn)
    time = np.array(engine.getvar('time'))[0]

    signals = engine.getvar('signals')
    trajectory_list = list(
        map(lambda sig: (time, np.transpose(np.array(sig))), signals)
    )

    with utils_io.open_for_write(output_file) as out:
        write_trajectories(out, trajectory_list)

    return trajectory_list


def build_script(
    opts: simulate_protocol, script_fn: str, simulink_model_file: str, nsimulations: int
) -> None:
    variable_index: dict[str, int] = {
        v: i for (i, v) in enumerate(opts.input_variables + opts.output_variables)
    }

    with utils_io.open_for_write(script_fn) as out:
        out.write("% MATLABPATH must contain Breach\n")
        out.write("InitBreach;\n\n")

        # Fill variables to load the model
        out.write(
            "% Free variables must be assigned with dummy values for BreachSimulinkSystem\n"
        )
        for ov in opts.output_variables:
            idx = variable_index[ov]
            out.write(f"a{idx} = 42; % for output variable {ov}\n")

        out.write(
            textwrap.dedent(
                f"""\
                timeStepMax = 42; % time horizon
                timeFinal = 42; % samplinig time

                mdl = load_system('{simulink_model_file}');
                Bsim = BreachSimulinkSystem(get_param(mdl, 'Name'));

                """
            )
        )

        # Range of the initial output variables
        for ov in opts.output_variables:
            idx = variable_index[ov]
            r: Range = opts.invariant[ov]
            out.write(f"% Range of the initial value of output variable {ov}\n")
            out.write(f"Bsim.SetParamRanges({{'a{idx}'}}, [{r.min} {r.max}]);\n\n")

        # Generators of the input variables
        for iv in opts.input_variables:
            ncps = opts.number_of_cps[iv]
            signal_type = opts.signal_types[iv]
            r = opts.invariant[iv]
            out.write(f"% Input signal {iv}In for input variable {iv}\n")
            match signal_type:
                case SignalType.FIXED_STEP:
                    out.write(f"Bsim.SetInputGen('UniStep{ncps}');\n")
                    for i in range(0, ncps):
                        out.write(
                            f"Bsim.SetParamRanges({{'{iv}In_u{i}'}}, [{r.min} {r.max}]);\n"
                        )

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
                            f"Bsim.SetParamRanges({{'{iv}In_u{i}'}}, [{r.min} {r.max}]);\n"
                        )

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
        signal_comments = "\n".join(
            [
                f'% Input variable {v} at signal #{signal_positions[v]+1}'
                for v in opts.input_variables
            ]
            + [
                f'% Output variable {v} at signal #{signal_positions[v]+1}'
                for v in opts.output_variables
            ]
        )

        out.write(
            textwrap.dedent(
                f"""\

                Bsim.SetParam('timeStepMax', {opts.sampling_time}); % sampling time
                Bsim.QuasiRandomSample({nsimulations}); % number of simulations
                    
                % Simulation!
                Bsim.Sim({opts.time_horizon}); % time horizon
                    
                % Bsim.PlotSignals(); % visualization
                    
                % Timestamps
                % time = Bsim.GetTime()  % GetTime() seems broken
                time = Bsim.P.traj{{1}}.time;
                    
                % Bulid signals for Trajectories:
                all_signal_names = Bsim.GetSignalList();
                """
            )
        )
        out.write(f"{signal_comments}\n")
        out.write(
            textwrap.dedent(
                f"""\
                signal_names = {signal_names};
                signals = Bsim.GetSignalValues(signal_names);

                % Get values of time and signals from Python!
                """
            )
        )
