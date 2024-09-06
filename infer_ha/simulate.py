from os import path
import matlab
from infer_ha.matlab_engine import matlab_engine

def simulate(script_file : str,
             output_file : str,
             input_variables : list[str],
             output_variables : list[str],
             input_value_ts : dict[str, list[tuple[float, float]]],
             initial_output_values : dict[str, float]) -> None:

    assert path.isabs(output_file), \
        "simulate: output_file cannot be relative: " \
        + output_file

    variable_index : dict[str,int] = { v : i for (i, v) in enumerate(input_variables + output_variables) }

    matlab_engine.setvar("result_filename", output_file)

    for (var, v) in initial_output_values.items():
        matlab_engine.setvar(f"a{variable_index[var]}", v)
        
    for (var, ts) in input_value_ts.items():
        vs = matlab.double([v for (_, v) in ts])
        matlab_engine.setvar(f"{var}_input", vs)

        ts = matlab.double([t for (t, _) in ts])
        matlab_engine.setvar(f"{var}_time", ts)

    matlab_engine.run(script_file)
