# Falsification by Breach
import os
import random
import numpy as np
import textwrap
from typing import Protocol
from pydantic import ConfigDict
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


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class Falsification_result:
    counter_examples: list[
        tuple[
            Trajectory,
            MATRIX,  # parameters
            float,  # distance
        ]
    ]

    passed_examples: list[
        tuple[
            Trajectory, MATRIX  # parameters
        ]
    ]


class Falsifier:
    tried_parameters: matlab.double = matlab.double([])
    tried_obj_log: matlab.double = matlab.double([])

    def find_counter_examples(
        self,
        _rng: random.Random,
        opts: find_counter_examples_protocol,
        learned_model_file: str,
        _i: int,
    ) -> Falsification_result:
        (result, tried_parameters, tried_obj_log) = find_counter_examples_aux(
            opts, learned_model_file, self.tried_parameters, self.tried_obj_log
        )
        if opts.skip_already_tried_parameters:
            self.tried_parameters = tried_parameters
            self.tried_obj_log = tried_obj_log
        return result


def find_counter_examples_aux(
    opts: find_counter_examples_protocol,
    learned_model_file: str,
    tried_parameters: matlab.double,
    tried_obj_log: matlab.double,
) -> tuple[
    Falsification_result,
    matlab.double,  # new_tried_parameters
    matlab.double,  # new_tried_obj_log
]:
    script_fn = os.path.join(opts.output_directory, 'falsify_by_spec.m')
    learned_model_file = os.path.abspath(learned_model_file)

    engine.eval0('bdclose all;')
    engine.eval0('clear;')

    engine.setvar('tried_parameters', tried_parameters)
    engine.setvar('tried_obj_log', tried_obj_log)

    parameters = build_script(opts, script_fn, learned_model_file, tried_parameters)
    parameter_list = "{" + ",".join([f"'{p}'" for p in parameters]) + "}"

    engine.run(script_fn)

    time = np.array(engine.getvar('time'))[0]

    # Usually, if multiple ncounter examples found,
    #   np.shape(signals_matlab) = (n, 3, 1001)
    # (1001 is the number of the frames)
    #
    # However, if only 1 counter example found, np.shape(signals_matlab) = (3, 1001)
    def fix_signals(signals: MATRIX) -> MATRIX:
        match np.shape(signals):
            case (_, _, _):
                return signals
            case (_, _):
                print('Fixing the dimension of singals')
                return signals[np.newaxis, :]
            case _:
                assert False

    # F**king handling of corner cases of a Python library 😡😡😡!!
    false_signals = fix_signals(np.array(engine.getvar('signals')))

    # scores can be empty! when only 1 counter example is found
    scores = np.array(engine.eval1('pb.obj_false'))
    if scores.size == 0:
        print('Strange scores:', scores, 'Fixing its dimension')
        scores = np.array([0])
    else:
        scores = scores[0]

    print(
        'time:',
        np.shape(time),
        'false_signals:',
        np.shape(false_signals),
        'scores:',
        np.shape(scores),
    )
    assert np.shape(false_signals)[0] == np.shape(scores)[0]

    false_trs = list(
        map(lambda sig: (time, np.transpose(np.array(sig))), false_signals)
    )
    false_parameters = np.transpose(
        np.array(engine.eval1(f'falses.GetParam({parameter_list})'))
    )
    assert np.shape(false_parameters)[0] == len(false_trs)
    # Use tuple to put param in a set
    false_parameter_set = set([tuple(param) for param in false_parameters])
    falses = [
        (t, params, -score)
        for (t, params, score) in zip(false_trs, false_parameters, scores)
    ]

    all_signals = fix_signals(np.array(engine.getvar('all_signals')))
    all_trs = list(map(lambda sig: (time, np.transpose(np.array(sig))), all_signals))
    all_parameters = np.transpose(
        np.array(engine.eval1(f'pb.BrSet_Logged.GetParam({parameter_list})'))
    )
    print(
        'all_signals', np.shape(all_signals), 'all_parameters', np.shape(all_parameters)
    )
    assert np.shape(all_parameters)[0] == len(
        all_trs
    ), f"Oops {np.shape(all_parameters)[0]} {len(all_trs)}"

    passed = [
        (t, params)
        for (t, params) in zip(all_trs, all_parameters)
        if tuple(params) not in false_parameter_set
    ]
    print('falses', len(falses), 'passed', len(passed))

    tried_parameters = engine.getvar('tried_parameters')
    tried_obj_log = engine.getvar('tried_obj_log')

    return (Falsification_result(falses, passed), tried_parameters, tried_obj_log)


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
        w = out.write

        def wd(s: str) -> None:
            w(textwrap.dedent(s))

        embeded = embed(
            out,
            learned_model_file,
            'embeded.slx',
            opts.input_variables,
            opts.output_variables,
        )

        wd(f"""\
        % MATLABPATH must contain Breach
        InitBreach;
                
        % Free variables must be assigned with dummy values for BreachSimulinkSystem
        """)
        for ov in opts.output_variables:
            idx = variable_index[ov]
            w(f"a{idx} = 42; % for output variable {ov}\n")

        w(f"\nBsim = BreachSimulinkSystem('{embeded}');\n\n")

        parameters = []

        # Range of the initial output variables
        for ov in opts.output_variables:
            idx = variable_index[ov]
            r: Range = opts.invariant[ov]
            wd(f"""\
            % Range of the initial value of output variable {ov}
            Bsim.SetParamRanges({{'a{idx}'}}, [{r.min} {r.max}]);

            """)
            parameters.append(f'a{idx}')

        # Generators of the input variables
        for iv in opts.input_variables:
            idx = variable_index[iv] + 1  # need +1
            ncps = opts.number_of_cps[iv]
            signal_type = opts.signal_types[iv]
            r = opts.invariant[iv]
            w(f"% Input signal {iv} for input variable {iv}\n")
            match signal_type:
                case SignalType.FIXED_STEP:
                    w(f"Bsim.SetInputGen('UniStep{ncps}');\n")
                    for i in range(0, ncps):
                        w(f"Bsim.SetParamRanges({{'{iv}_u{i}'}}, [{r.min} {r.max}]);\n")
                        parameters.append(f'{iv}_u{i}')
                    w("\n")

                case SignalType.LINEAR:
                    wd(f"""\
                        input_gen.type = 'UniStep';
                        input_gen.cp = {ncps};
                        input_gen.method = {{'linear'}};
                        Bsim.SetInputGen(input_gen);
                        """)
                    for i in range(0, ncps):
                        w(f"Bsim.SetParamRanges({{'{iv}_u{i}'}}, [{r.min} {r.max}]);\n")
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

        wd(f"""\
        Bsim.Sys.tspan = 0:{opts.sampling_time}:{opts.time_horizon};  % See the head comment in Core/Falsify.m
            
        % Falsification
        phi = STL_Formula('phi', '{opts.stl_spec}');
        R = BreachRequirement(phi);
        pb = FalsificationProblem(Bsim,R);
        pb.StopAtFalse=0 % more than 1 counter examples if found
        pb.max_obj_eval = {max_obj_eval};

        % Falsification cache
        if ~exist('tried_parameters', 'var')
            disp('tried_parameters is not defined. Use the default []')
            tried_parameters = []
        end
        if ~exist('tried_obj_log', 'var')
            disp('tried_parameters is not defined. Use the default []')
            tried_parameters = []
        end
        pb.X_log = tried_parameters;
        pb.obj_log = tried_obj_log;

        pb.solve();
        falses = pb.GetFalse();

        % Falsification cache
        tried_parameters = pb.X_log;
        tried_obj_log = pb.obj_log;

        % Times
        % time = falses.GetTime() % GetTime() seems broken.
        time = pb.BrSet_Logged.GetTime();

        if isempty(falses)
            disp('No counter example found!');
            signals = [];
            scores = [];
            return;
        end

        % Visualize the counter examples
        % falses.BrSet.PlotSignals();

        """)

        w(f'{signal_comments}\n')

        wd(f"""\
        signal_names = {signal_names};
        signals = falses.GetSignalValues(signal_names);

        all_signals = pb.BrSet_Logged.GetSignalValues(signal_names);

        scores = pb.obj_false;
        """)

    return parameters
