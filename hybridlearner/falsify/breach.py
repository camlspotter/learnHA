# Falsification by Breach
import os
import random
import numpy as np
import textwrap
from io import TextIOWrapper
from typing import Protocol
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass
from hybridlearner.types import Invariant
from hybridlearner.utils import io as utils_io
from hybridlearner import matlab
from hybridlearner.matlab import engine, breach, expr_matlab_double
from hybridlearner.trajectory import Trajectories, Trajectory
from hybridlearner.types import Range, MATRIX
from hybridlearner.simulation import simulate_protocol, check_variables
from hybridlearner.simulation.input import SignalType
from hybridlearner.slx.merger import merge, merge_without_save


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
    simulink_model_file: str
    nsimulations: int
    counter_example_threshold: float

    # Hack to skip already tried parameters.
    skip_already_tried_parameters: bool


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
    simulink_model_file: str
    nsimulations: int
    counter_example_threshold: float
    skip_already_tried_parameters: bool


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class Falsification_result:
    counter_examples: list[
        tuple[
            Trajectory,  # original
            Trajectory,  # learned
            MATRIX,  # parameters
            float,  # distance
        ]
    ]

    passed_examples: list[
        tuple[
            Trajectory,  # original
            Trajectory,  # learned
            MATRIX,  # parameters
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
        check_variables(opts)
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
    script_fn = os.path.join(opts.output_directory, 'falsify.m')
    with utils_io.open_for_write(script_fn) as out:
        w = out.write

        def wd(s: str) -> None:
            w(textwrap.dedent(s))

        wd(f"""\
        bdclose all;
        clear;
    
        tried_parameters = {expr_matlab_double(tried_parameters)}
        tried_obj_log = {expr_matlab_double(tried_obj_log)}

        """)

        parameters = build_script(opts, out, learned_model_file, tried_parameters)

    engine.run(script_fn)

    time = breach.get_time('time')

    false_original_signals = breach.get_signals('original_signals')
    false_learned_signals = breach.get_signals('learned_signals')
    false_original_trs = breach.signals_to_trajectories(time, false_original_signals)
    false_learned_trs = breach.signals_to_trajectories(time, false_learned_signals)
    scores = breach.get_obj_false('pb', false_original_signals)

    false_parameters: MATRIX

    if false_original_trs == []:
        false_parameters = np.array([])
        false_parameter_set = set([])
    else:
        # Matlab R2404b fails if falses is empty
        false_parameters = breach.get_parameters('falses', parameters)
        false_parameter_set = set([tuple(param) for param in false_parameters])

    falses = [
        (ot, lt, params, -score)
        for (ot, lt, params, score) in zip(
            false_original_trs, false_learned_trs, false_parameters, scores
        )
    ]

    print(
        'time:',
        np.shape(time),
        'false_original_signals:',
        np.shape(false_original_signals),
        'false_learned_signals:',
        np.shape(false_learned_signals),
        'scores:',
        np.shape(scores),
        'false_parameters:',
        np.shape(false_parameters),
    )

    # Check shapes
    assert np.shape(time)[0] == np.shape(false_original_signals)[2]
    assert np.shape(time)[0] == np.shape(false_learned_signals)[2]
    assert np.shape(scores)[0] == np.shape(false_original_signals)[0]
    assert np.shape(scores)[0] == np.shape(false_learned_signals)[0]
    assert np.shape(scores)[0] == np.shape(false_parameters)[0]
    assert len(parameters) == np.shape(false_parameters)[1]

    all_original_signals = breach.get_signals('all_original_signals')
    all_learned_signals = breach.get_signals('all_learned_signals')
    all_parameters = breach.get_parameters('pb.BrSet_Logged', parameters)
    all_original_trs = breach.signals_to_trajectories(time, all_original_signals)
    all_learned_trs = breach.signals_to_trajectories(time, all_learned_signals)

    print(
        'time:',
        np.shape(time),
        'all_original_signals:',
        np.shape(all_original_signals),
        'all_learned_signals:',
        np.shape(all_learned_signals),
        'scores:',
        np.shape(scores),
        'all_parameters:',
        np.shape(all_parameters),
    )

    # Check shapes
    assert np.shape(time)[0] == np.shape(all_original_signals)[2]
    assert np.shape(time)[0] == np.shape(all_learned_signals)[2]
    assert len(parameters) == np.shape(all_parameters)[1]

    print(
        'all_original_signals',
        np.shape(all_original_signals),
        'all_parameters',
        np.shape(all_parameters),
    )
    assert np.shape(all_parameters)[0] == len(
        all_original_trs
    ), f"Oops {np.shape(all_parameters)[0]} {len(all_original_trs)}"

    passed = [
        (ot, lt, params)
        for (ot, lt, params) in zip(all_original_trs, all_learned_trs, all_parameters)
        if tuple(params) not in false_parameter_set
    ]
    print('falses', len(falses), 'passed', len(passed))

    tried_parameters = engine.getvar('tried_parameters')
    tried_obj_log = engine.getvar('tried_obj_log')

    return (
        Falsification_result(counter_examples=falses, passed_examples=passed),
        tried_parameters,
        tried_obj_log,
    )


def build_script(
    opts: find_counter_examples_protocol,
    out: TextIOWrapper,
    learned_model_file: str,
    tried_parameters: matlab.double,
) -> list[str]:  # parameters
    original_model_file = opts.simulink_model_file

    variable_index: dict[str, int] = {
        v: i for (i, v) in enumerate(opts.input_variables + opts.output_variables)
    }

    w = out.write

    def wd(s: str) -> None:
        w(textwrap.dedent(s))

    merged = merge(
        out,
        original_model_file,
        learned_model_file,
        'merged.slx',
        opts.input_variables,
        opts.output_variables,
    )

    wd(f"""\
    % MATLABPATH must contain Breach
    InitBreach;

    % Free variables must be assigned with dummy values for BreachSimulinkSystem
    """)

    # Fill variables to load the model
    for ov in opts.output_variables:
        idx = variable_index[ov]
        w(f"a{idx} = 42; % for output variable {ov}\n")

    w(f"\nBsim = BreachSimulinkSystem('{merged}');\n\n")

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

    original_signal_names = (
        "{"
        + ",".join(
            [f"{{'{iv}'}}" for iv in opts.input_variables]
            + [f"{{'a_{ov}'}}" for ov in opts.output_variables]
        )
        + "}"
    )
    original_signal_comments = "\n".join(
        [f'% Input variable {iv} at signal {iv}' for iv in opts.input_variables]
        + [
            f'% Original output variable {ov} at signal a_{ov}'
            for ov in opts.output_variables
        ]
    )

    #        shift = len(opts.output_variables) * 2
    learned_signal_names = (
        "{"
        + ",".join(
            [f"{{'{iv}'}}" for iv in opts.input_variables]
            + [f"{{'b_{ov}'}}" for ov in opts.output_variables]
        )
        + "}"
    )
    learned_signal_comments = "\n".join(
        [f'% Input variable {iv} at signal {iv}' for iv in opts.input_variables]
        + [
            f'% Learned output variable {ov} at signal b_{ov}'
            for ov in opts.output_variables
        ]
    )

    max_obj_eval = opts.nsimulations + np.array(tried_parameters).shape[1]
    print('Set max_obj_eval:', max_obj_eval)

    stl_components = [
        f'diff_{ov}[t] < {opts.counter_example_threshold}'
        for ov in opts.output_variables
    ]
    stl_formula = f"alw ({' and '.join(stl_components)})"

    wd(f"""\
    Bsim.SetParam('timeStepMax', {opts.sampling_time}); % Probably the next line is enough.
    Bsim.Sys.tspan = 0:{opts.sampling_time}:{opts.time_horizon};  % See the head comment in Core/Falsify.m
    
    % Falsification
    phi = STL_Formula('phi', '{stl_formula}');
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
        disp('tried_obj_log is not defined. Use the default []')
        tried_obj_log = []
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

    """)

    w(f"{original_signal_comments}\n")
    w(f"{learned_signal_comments}\n")

    wd(f"""\
    original_signal_names = {original_signal_names};
    learned_signal_names = {learned_signal_names};

    all_original_signals = pb.BrSet_Logged.GetSignalValues(original_signal_names);
    all_learned_signals = pb.BrSet_Logged.GetSignalValues(learned_signal_names);

    if isempty(falses)
        disp('No counter example found!');
        original_signals = [];
        learned_signals = [];
        scores = [];
    else
        original_signals = falses.GetSignalValues(original_signal_names);
        learned_signals = falses.GetSignalValues(learned_signal_names);
        scores = pb.obj_false;
        % Visualize the counter examples
        % falses.BrSet.PlotSignals();
    end
    """)

    return parameters
