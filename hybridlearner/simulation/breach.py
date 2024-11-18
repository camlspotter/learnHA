# Simluation by Breach
import os
import random
import numpy as np
import textwrap
import re
from .input import SignalType
from hybridlearner.utils import io as utils_io
from hybridlearner.matlab import engine, breach
from hybridlearner.trajectory import Trajectories, save_trajectories
from hybridlearner.types import Range, MATRIX
from hybridlearner.simulation import simulate_protocol, check_variables
from hybridlearner.slx.info import get_IOports


def simulate(
    _rng: random.Random,
    opts: simulate_protocol,
    simulink_model_file: str,
    output_file: str,
    nsimulations: int,
) -> Trajectories:
    check_variables(opts)
    script_fn = os.path.join(opts.output_directory, "simulate_model.m")

    build_script(opts, script_fn, simulink_model_file, nsimulations)

    engine.run(script_fn)

    time = breach.get_time('time')
    signals = breach.get_signals('signals')
    trajectories = breach.signals_to_trajectories(time, signals)

    header = ['time'] + opts.input_variables + opts.output_variables
    save_trajectories(output_file, header, trajectories)

    return trajectories


def build_script(
    opts: simulate_protocol, script_fn: str, simulink_model_file: str, nsimulations: int
) -> None:
    variable_index: dict[str, int] = {
        v: i for (i, v) in enumerate(opts.input_variables + opts.output_variables)
    }

    inport_dict, output_dict = breach.get_port_dicts(
        simulink_model_file, opts.input_variables, opts.output_variables
    )

    with utils_io.open_for_write(script_fn) as out:
        w = out.write

        def wd(s: str) -> None:
            w(textwrap.dedent(s))

        wd(f"""\
        % MATLABPATH must contain Breach
        InitBreach;

        """)

        # Fill variables to load the model
        w(
            "% Free variables must be assigned with dummy values for BreachSimulinkSystem\n"
        )
        for ov in opts.output_variables:
            idx = variable_index[ov]
            out.write(f"a{idx} = 42; % for output variable {ov}\n")

        wd(f"""\
        timeStepMax = 42; % time horizon
        timeFinal = 42; % samplinig time

        mdl = load_system('{simulink_model_file}');
        Bsim = BreachSimulinkSystem(get_param(mdl, 'Name'));

        """)

        # Range of the initial output variables
        for ov in opts.output_variables:
            idx = variable_index[ov]
            r: Range = opts.invariant[ov]
            wd(f"""\
            % Range of the initial value of output variable {ov}
            try
                Bsim.SetParamRanges({{'a{idx}'}}, [{r.min} {r.max}]);
            catch
                % Workaround.
                % Some models do not define a{idx} variables therefore
                % SetParamRanges fails for them.
                warning('Parameter a{idx} does not exist. Skip setting its range [{r.min} {r.max}]');
            end

            """)

        # Generators of the input variables
        for iv in opts.input_variables:
            ip = inport_dict[iv]
            ncps = opts.number_of_cps[iv]
            signal_type = opts.signal_types[iv]
            r = opts.invariant[iv]
            w(f"% Input signal {ip} for input variable {iv}\n")
            match signal_type:
                case SignalType.FIXED_STEP:
                    w(f"Bsim.SetInputGen('UniStep{ncps}');\n")
                    for i in range(0, ncps):
                        w(f"Bsim.SetParamRanges({{'{ip}_u{i}'}}, [{r.min} {r.max}]);\n")

                case SignalType.LINEAR:
                    wd(f"""\
                    input_gen.type = 'UniStep';
                    input_gen.cp = {ncps};
                    input_gen.method = {{'linear'}};
                    Bsim.SetInputGen(input_gen);
                    """)
                    for i in range(0, ncps):
                        w(f"Bsim.SetParamRanges({{'{ip}_u{i}'}}, [{r.min} {r.max}]);\n")

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

        wd(f"""\

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
        """)
        w(f"{signal_comments}\n")
        wd(f"""\
        signal_names = {signal_names};
        signals = Bsim.GetSignalValues(signal_names);

        % Get values of time and signals from Python!
        """)
