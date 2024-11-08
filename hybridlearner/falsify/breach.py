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


@dataclass
class find_counter_examples_options:
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


class Falsifier:
    tried_parameters: matlab.double = matlab.double([])
    tried_obj_log: matlab.double = matlab.double([])

    def find_counter_examples(
        self,
        _rng: random.Random,
        opts: find_counter_examples_protocol,
        learned_model_file: str,
        _i: int,
    ) -> list[
        tuple[
            Trajectory,  # original
            Trajectory,  # learned
            float,  # distance
        ]
    ]:
        (counter_examples, tried_parameters, tried_obj_log) = find_counter_examples_aux(
            opts, learned_model_file, self.tried_parameters, self.tried_obj_log
        )
        self.tried_parameters = tried_parameters
        self.tried_obj_log = tried_obj_log
        return counter_examples


def find_counter_examples_aux(
    opts: find_counter_examples_protocol,
    learned_model_file: str,
    tried_parameters: matlab.double,
    tried_obj_log: matlab.double,
) -> tuple[
    list[
        tuple[
            Trajectory,  # original
            Trajectory,  # learned
            float,  # distance
        ]
    ],
    matlab.double,  # new_tried_parameters
    matlab.double,  # new_tried_obj_log
]:
    script_fn = os.path.join(opts.output_directory, 'falsify.m')

    engine.eval('bdclose all;', nargout=0)
    engine.eval('clear;', nargout=0)

    engine.setvar('tried_parameters', tried_parameters)
    engine.setvar('tried_obj_log', tried_obj_log)

    build_script(opts, script_fn, learned_model_file, tried_parameters)

    engine.run(script_fn)

    time = np.array(engine.getvar('time'))
    if time.size == 0:
        time = matlab.double([])
        original_signals = matlab.double([])
        learned_signals = matlab.double([])
        maybe_scores = np.array([])
    else:
        time = np.array(engine.getvar('time'))[0]
        original_signals = engine.getvar('original_signals')
        learned_signals = engine.getvar('learned_signals')
        maybe_scores = np.array(engine.getvar('maybe_scores'))[0]

    original_trs = list(
        map(lambda sig: (time, np.transpose(np.array(sig))), original_signals)
    )

    learned_trs = list(
        map(lambda sig: (time, np.transpose(np.array(sig))), learned_signals)
    )

    tried_parameters = engine.getvar('tried_parameters')
    tried_obj_log = engine.getvar('tried_obj_log')

    tried_parameters2: MATRIX = np.transpose(np.array(tried_parameters))
    print('tried_parameters', tried_parameters2)

    # XXX No distance for now
    return (
        [
            (ot, lt, -score)
            for (ot, lt, score) in zip(original_trs, learned_trs, maybe_scores)
        ],
        tried_parameters,
        tried_obj_log,
    )


def build_script(
    opts: find_counter_examples_protocol,
    script_fn: str,
    learned_model_file: str,
    tried_parameters: matlab.double,
) -> None:
    original_model_file = opts.simulink_model_file

    variable_index: dict[str, int] = {
        v: i for (i, v) in enumerate(opts.input_variables + opts.output_variables)
    }

    with utils_io.open_for_write(script_fn) as out:
        merged = merge(out, original_model_file, learned_model_file, 'merged.slx')

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

        original_signal_names = (
            "{"
            + ",".join(
                [f"{{'in_{i+1}'}}" for (i, _) in enumerate(opts.input_variables)]
                + [f"{{'out_a{i+1}'}}" for (i, _) in enumerate(opts.output_variables)]
            )
            + "}"
        )
        original_signal_comments = '%hahaha'
        original_signal_comments = "\n".join(
            [
                f'% Input variable {v} at signal in_{i+1}'
                for (i, v) in enumerate(opts.input_variables)
            ]
            + [
                f'% Original output variable {v} at signal out_a{i+1}'
                for (i, v) in enumerate(opts.output_variables)
            ]
        )

        #        shift = len(opts.output_variables) * 2
        learned_signal_names = (
            "{"
            + ",".join(
                [f"{{'in_{i+1}'}}" for (i, _) in enumerate(opts.input_variables)]
                + [f"{{'out_b{i+1}'}}" for (i, _) in enumerate(opts.output_variables)]
            )
            + "}"
        )
        learned_signal_comments = "\n".join(
            [
                f'% Input variable {v} at signal in_{i+1}'
                for (i, v) in enumerate(opts.input_variables)
            ]
            + [
                f'% Learned output variable {v} at signal out_b{i+1}'
                for (i, v) in enumerate(opts.output_variables)
            ]
        )

        max_obj_eval = opts.nsimulations + np.array(tried_parameters).shape[1]
        print('Set max_obj_eval:', max_obj_eval)

        stl_components = [
            f'diff{i+1}[t] < {opts.counter_example_threshold}'
            for (i, _) in enumerate(opts.output_variables)
        ]
        stl_formula = f"alw ({' and '.join(stl_components)})"

        out.write(
            textwrap.dedent(
                f"""\
                Bsim.SetParam('timeStepMax', {opts.sampling_time}); % Probably the next line is enough.
                Bsim.Sys.tspan = 0:{opts.sampling_time}:{opts.time_horizon};  % See the head comment in Core/Falsify.m

                % Falsification
                phi = STL_Formula('phi', '{stl_formula}');
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
                    original_signals = [];
                    learned_signals = [];
                    return;
                end

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

                maybe_scores = pb.obj_false;
                """
            )
        )
