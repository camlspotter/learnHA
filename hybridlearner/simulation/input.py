from enum import Enum
from pydantic.dataclasses import dataclass
from dataclasses import asdict
import random
from hybridlearner.types import Range
from hybridlearner.types import Invariant
import json

class SignalType(Enum):
    FIXED_STEP = "fixed-step"
    # VAR_STEP = "var-step"
    LINEAR = "linear"
    # SPLINE = "spline"
    # SINE_WAVE = "sine-wave"

def parse_signal_types(s : str) -> dict[str,SignalType]:
    def parse_vt(s : str) -> tuple[str,SignalType]:
        match s.split(":"):
            case (var, vt):
                return (var, SignalType(vt))
            case _:
                assert False, "Invalid number of var type: " + s
    return dict([parse_vt(s) for s in s.split(",")])

Signal = list[tuple[float, float]]  # (time, value)

@dataclass
class Simulation_input:
    input_value_ts : dict[str, Signal]
    initial_output_values : dict[str, float]


def linear_signal(time_horizon : float,
                  cps : list[float]) -> Signal:
    """
    Function to generate constant-piecewise-linear signal, where the hold-time is fixed/uniform for each control-points
      [( t_i, p_i )]_{i in [0..n-1]} 
    where
      t_i = timeHorizon * i / (n-1)
    """

    time_step = time_horizon / (len(cps) - 1)
             
    time_vector : list[float] = [ i * time_step for i in range(0, len(cps)) ]

    data_vector : list[float] = cps

    # return Signal(times= time_vector, data= data_vector)
    return list(zip(time_vector, data_vector))


def fixed_step_signal(time_horizon : float,
                      cps : list[float]) -> Signal:
    """
    fixed_step_signal(timeHorizon, control_points, time_vector, data_vector)
       [ (t_i, p_i), (t_{i+1} - epsilon, p_i) ]_{i in [0..n-1]} 
   where
      t_i = timeHorizon * i / n   (not / (n+1) somehow)
    """

    time_step = time_horizon / len(cps)

    time_vectors : list[list[float]] = [ [i * time_step, i * (time_step+1)] for i in range(0, len(cps)) ]

    time_vector : list[float] = [ t for tt in time_vectors for t in tt ]

    data_vectors : list[list[float]] = [ [v, v] for v in cps ]

    data_vector : list[float] = [ v for vv in data_vectors for v in vv ]

    # return Signal(times= time_vector, data= data_vector)
    return list(zip(time_vector, data_vector))

def build_signal(rng : random.Random,
                 time_horizon : float,
                 r : Range,
                 number_of_cps : int,
                 signal_type : SignalType) -> Signal:
    cps = [ r.pick_random_point(rng) for _ in range(0, number_of_cps) ]
    match signal_type:
        case SignalType.FIXED_STEP:
            return fixed_step_signal(time_horizon, cps)
        case SignalType.LINEAR:
            return linear_signal(time_horizon, cps)

def generate_input_value_ts(rng : random.Random,
                                    time_horizon : float,
                                    invariant : Invariant,
                                    number_of_cps : dict[str, int],
                                    signal_types : dict[str, SignalType],
                                    input_variables : list[str]) -> dict[str, Signal]:
    return { v : build_signal(rng,
                              time_horizon,
                              invariant[v],
                              number_of_cps[v],
                              signal_types[v]) for v in input_variables }

def generate_output_values(rng : random.Random,
                           invariant : Invariant,
                           output_variables : list[str]) -> dict[str, float]:
    return { v : invariant[v].pick_random_point(rng) for v in output_variables }

def generate_simulation_input(rng : random.Random,
                              time_horizon : float,
                              invariant : Invariant,
                              number_of_cps : dict[str, int],
                              signal_types : dict[str, SignalType],
                              input_variables : list[str],
                              output_variables : list[str]) -> Simulation_input:
    input_value_ts = generate_input_value_ts(rng, time_horizon, invariant, number_of_cps, signal_types, input_variables)
    initial_output_values = generate_output_values(rng, invariant, output_variables)
    return Simulation_input(input_value_ts= input_value_ts,
                            initial_output_values= initial_output_values)

def test() -> None:
    sis = [ generate_simulation_input(random.Random(),
                                      10.0,
                                      { 'x' : Range(1, 2),
                                        'y' : Range(2, 3) },
                                      { 'x' : 4 },
                                      { 'x' : SignalType.LINEAR },
                                      ['x'],
                                      ['y'])
            for _ in range(0,10) ]
    print(json.dumps(list(map(asdict, sis))))
