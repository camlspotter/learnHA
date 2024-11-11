# Falsification by Breach
import os
import random
import numpy as np
import textwrap
from typing import Protocol
from pydantic.dataclasses import dataclass
from hybridlearner.types import Invariant
from hybridlearner.utils import io as utils_io
from hybridlearner import matlab
from hybridlearner.matlab import engine
from hybridlearner.trajectory import Trajectories, Trajectory
from hybridlearner.types import Range, MATRIX
from hybridlearner.simulation import simulate_protocol
from hybridlearner.simulation.input import SignalType
from hybridlearner.slx.embed import embed


# Protocol for subtyping!
# Unfortunately I cannot inherit dataclasses and have to list all the fields here.
class find_counter_examples_protocol(Protocol):
    time_horizon: float  # total time of simulation
    sampling_time: float  # simulation frame time
    invariant: Invariant
    number_of_cps: dict[str, int]
    signal_types: dict[str, SignalType]
    input_variables: list[str]
    output_variables: list[str]
    output_directory: str
    nsimulations: int

    # Hack to skip already tried parameters.
    skip_already_tried_parameters: bool

    # STL formula for falsification
    stl_spec: str


@dataclass
class find_counter_examples_options:
    time_horizon: float
    sampling_time: float
    invariant: Invariant
    number_of_cps: dict[str, int]
    signal_types: dict[str, SignalType]
    input_variables: list[str]
    output_variables: list[str]
    output_directory: str
    nsimulations: int
    skip_already_tried_parameters: bool
    stl_spec: str


class Falsifier:
    tried_parameters: matlab.double = matlab.double([])
    tried_obj_log: matlab.double = matlab.double([])

    def find_counter_examples(
        self,
        _rng: random.Random,
        opts: find_counter_examples_protocol,
        learned_model_file: str,
        _i: int,
    ) -> tuple[
        # counter examples
        list[
            tuple[
                Trajectory,
                MATRIX,  # parameters
                float,  # distance
            ]
        ],
        # all trajectories
        list[
            tuple[
                Trajectory, MATRIX  # parameters
            ]
        ],
    ]:
        (counter_examples, all, tried_parameters, tried_obj_log) = (
            find_counter_examples_aux(
                opts, learned_model_file, self.tried_parameters, self.tried_obj_log
            )
        )
        if opts.skip_already_tried_parameters:
            self.tried_parameters = tried_parameters
            self.tried_obj_log = tried_obj_log
        return (counter_examples, all)


def find_counter_examples_aux(
    opts: find_counter_examples_protocol,
    learned_model_file: str,
    tried_parameters: matlab.double,
    tried_obj_log: matlab.double,
) -> tuple[
    # counter examples
    list[
        tuple[
            Trajectory,
            MATRIX,  # parameters
            float,  # distance
        ]
    ],
    # all trajectories
    list[
        tuple[
            Trajectory, MATRIX  # parameters
        ]
    ],
    matlab.double,  # new_tried_parameters
    matlab.double,  # new_tried_obj_log
]:
    script_fn = os.path.join(opts.output_directory, 'falsify_by_spec.m')
    learned_model_file = os.path.abspath(learned_model_file)

    engine.eval('bdclose all;', nargout=0)
    engine.eval('clear;', nargout=0)

    engine.setvar('tried_parameters', tried_parameters)
    engine.setvar('tried_obj_log', tried_obj_log)

    parameters = build_script(opts, script_fn, learned_model_file, tried_parameters)
    parameter_list = "{" + ",".join([f"'{p}'" for p in parameters]) + "}"

    engine.run(script_fn)

    time = np.array(engine.getvar('time'))

    # F**king handling of corner cases of a Python library 😡😡😡!!
    if time.size == 0:
        print('No counter examples found')
        time = matlab.double([])
        signals = matlab.double([])
        scores = np.array([])
    else:
        time = np.array(engine.getvar('time'))[0]
        signals = np.array(engine.getvar('signals'))
        scores = np.array(engine.getvar('scores'))
        print(
            'Counter example sizes:',
            'time:',
            np.shape(time),
            'signals:',
            np.shape(signals),
            'scores:',
            np.shape(scores),
        )

        # Usually, if multiple ncounter examples found, np.shape(signals_matlab) = (n, 3, 1001)
        # (1001 is the number of the frames)
        #
        # However, if only 1 counter example found, np.shape(signals_matlab) = (3, 1001)
        match np.shape(signals):
            case (_, _, _):
                pass
            case (_, _):
                print('Fixing the dimension of singals')
                signals = signals[np.newaxis, :]
            case _:
                assert False

        # scores can be empty! when only 1 counter example is found
        scores = np.array(engine.eval('pb.obj_false', 1))
        print('scores:', scores)
        if scores.size == 0:
            print('Fixing the dimension of scores')
            scores = np.array([0] * len(time))
        else:
            scores = scores[0]

    print(
        'time', np.shape(time), 'signals', np.shape(signals), 'scores', np.shape(scores)
    )

    trs = list(map(lambda sig: (time, np.transpose(np.array(sig))), signals))

    tried_parameters = engine.getvar('tried_parameters')
    tried_obj_log = engine.getvar('tried_obj_log')

    tried_parameters2: MATRIX = np.transpose(np.array(tried_parameters))
    print('tried_parameters', tried_parameters2)

    all_signals = np.array(engine.getvar('all_signals'))
    all_trs = list(map(lambda sig: (time, np.transpose(np.array(sig))), all_signals))

    all_parameters = np.transpose(
        np.array(engine.eval(f'pb.BrSet_Logged.GetParam({parameter_list})', 1))
    )
    print('all_parameters', np.shape(all_parameters))
    print('all_trs', len(all_trs))
    assert np.shape(all_parameters)[0] == len(all_trs)

    # pb.X_false can be empty when only 1 counter example is found
    # buggy: false_parameters = np.transpose(np.array(engine.eval('pb.X_false', 1)))
    false_parameters = np.transpose(
        np.array(engine.eval(f'falses.GetParam({parameter_list})', 1))
    )
    print("false_parameters", np.shape(false_parameters))
    print('trs', len(trs))
    assert np.shape(false_parameters)[0] == len(trs)

    return (
        [
            (t, params, -score)
            for (t, score, params) in zip(trs, scores, false_parameters)
        ],
        [(t, params) for (t, params) in zip(all_trs, all_parameters)],
        tried_parameters,
        tried_obj_log,
    )


def build_script(
    opts: find_counter_examples_protocol,
    script_fn: str,
    learned_model_file: str,
    tried_parameters: matlab.double,
) -> list[str]:  # parameters
    variable_index: dict[str, int] = {
        v: i for (i, v) in enumerate(opts.input_variables + opts.output_variables)
    }

    with utils_io.open_for_write(script_fn) as out:
        embeded = embed(
            out,
            learned_model_file,
            'embeded.slx',
            opts.input_variables,
            opts.output_variables,
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

        out.write(f"\nBsim = BreachSimulinkSystem('{embeded}');\n\n")

        parameters = []

        # Range of the initial output variables
        for ov in opts.output_variables:
            idx = variable_index[ov]
            r: Range = opts.invariant[ov]
            out.write(f"% Range of the initial value of output variable {ov}\n")
            out.write(f"Bsim.SetParamRanges({{'a{idx}'}}, [{r.min} {r.max}]);\n\n")
            parameters.append(f'a{idx}')

        # Generators of the input variables
        for iv in opts.input_variables:
            idx = variable_index[iv] + 1  # need +1
            ncps = opts.number_of_cps[iv]
            signal_type = opts.signal_types[iv]
            r = opts.invariant[iv]
            out.write(f"% Input signal {iv} for input variable {iv}\n")
            match signal_type:
                case SignalType.FIXED_STEP:
                    out.write(f"Bsim.SetInputGen('UniStep{ncps}');\n")
                    for i in range(0, ncps):
                        out.write(
                            f"Bsim.SetParamRanges({{'{iv}_u{i}'}}, [{r.min} {r.max}]);\n"
                        )
                        parameters.append(f'{iv}_u{i}')
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
                            f"Bsim.SetParamRanges({{'{iv}_u{i}'}}, [{r.min} {r.max}]);\n"
                        )
                        parameters.append(f'{iv}_u{i}')

        signal_names = (
            "{"
            + ",".join(
                [f"{{'{iv}'}}" for iv in opts.input_variables]
                + [f"{{'{ov}'}}" for ov in opts.output_variables]
            )
            + "}"
        )
        signal_comments = "\n".join(
            [f'% Input variable {iv} at signal {iv}' for iv in opts.input_variables]
            + [f'% Output variable {ov} at signal {ov}' for ov in opts.output_variables]
        )

        max_obj_eval = opts.nsimulations + np.array(tried_parameters).shape[1]
        print('Set max_obj_eval:', max_obj_eval)

        out.write(
            textwrap.dedent(
                f"""\
                Bsim.SetParam('timeStepMax', {opts.sampling_time}); % Probably the next line is enough.
                Bsim.Sys.tspan = 0:{opts.sampling_time}:{opts.time_horizon};  % See the head comment in Core/Falsify.m

                % Falsification
                phi = STL_Formula('phi', '{opts.stl_spec}');
                R = BreachRequirement(phi);
                pb = FalsificationProblem(Bsim,R);
                pb.X_log = tried_parameters;
                pb.obj_log = tried_obj_log;
                pb.StopAtFalse=0 % more than 1 counter examples if found
                pb.max_obj_eval = {max_obj_eval};
                pb.solve();
                falses = pb.GetFalse();

                % Get values of time, original_signals and learned_signalsfrom Python!
                tried_parameters = pb.X_log;
                tried_obj_log = pb.obj_log;

                if isempty(falses)
                    time = [];
                    signals = [];
                    scores = [];
                    return;
                end

                % Visualize the counter examples
                % falses.BrSet.PlotSignals();

                % Times
                % time = falses.GetTime() % GetTime() seems broken.
                time = falses.P.traj{{1}}.time;
                """
            )
        )

        out.write(f'{signal_comments}\n')

        out.write(
            textwrap.dedent(
                f"""\
                signal_names = {signal_names};
                signals = falses.GetSignalValues(signal_names);

                all_signals = pb.BrSet_Logged.GetSignalValues(signal_names);

                scores = pb.obj_false;
                """
            )
        )

    return parameters
