from infer_ha.simulate import simulate
from infer_ha.simulation_input import generate_simulation_input, VarType
from infer_ha.range import Range
from infer_ha.simulation_script import generate_simulation_script
import infer_ha.utils.io as utils_io
import random

# ./HybridLearner --engine learn-ha-loop --output-directory $OUTDIR \
#   --simulink-model-file ../src/test_cases/engine/learn_ha_loop/ex_sldemo_bounce_Input.slx \
#   --variable-category "u:input, x:output, v:output" \
#   --simu-init-size $SIMU_INIT_SIZE \
#   --initial-value "u>=-9.5 & u<=-9.9 & x>=10.2 & x<=10.5 & v>=15 & v<=15" \
#   --input-signal-type "u=linear" \
#   --numberOf-control-points "u=4" \
#   --time-horizon 13 \
#   --sampling-time 0.001 \
#   --modes 1 --degree 1 --boundary-degree 1 \
#   --segment-relative-error 0.1  --segment-relative-fine-error 0.01 \
#   --precision-equivalence 50.0 \
#   --max-traces 1 --max-stoptime 20 \
#   --invariant 2 \
#   --cluster-algo dtw \
#   --correlation-threshold 0.8 --distance-threshold 9.0 \
#   --fixed-interval-data 0 --filter-last-segment 1 \
#   --max-generate-trace-size 1024  --ode-speedup 50 \
#   --solver-type fixed --ode-solver FixedStepAuto

input_variables = ['u']
output_variables = ['x', 'v']
invariant = { 'u': Range(-9.9, -9.5),
              'x': Range(10.2, 10.5),
              'v': Range(15, 15) }
number_of_cps_dict= { 'u': 4 }
var_type_dict= { 'u': VarType.LINEAR }
simulink_model_filename= '../../src/test_cases/engine/learn_ha_loop/ex_sldemo_bounce_Input.slx'
time_horizon= 13.0
sampling_time = 0.001
fixed_interval_data= False

output_filename= "model_simulation.txt"

script_filename= "tmp_model_simulate.m"

with utils_io.open_for_write(script_filename) as out:
    generate_simulation_script(out= out,
                               title= 'Title',
                               simulink_model_filename= simulink_model_filename,
                               output_filename= output_filename,
                               time_horizon= time_horizon,
                               sampling_time= sampling_time,
                               fixed_interval_data= fixed_interval_data,
                               input_variables= input_variables,
                               output_variables = output_variables)

sis = generate_simulation_input(rng= random.Random(),
                                time_horizon= time_horizon,
                                invariant= invariant,
                                number_of_cps_dict= number_of_cps_dict,
                                var_type_dict= var_type_dict,
                                input_variables= input_variables,
                                output_variables= output_variables)
                                 
print(sis)
 
simulate( script_filename= script_filename,
          input_variables= input_variables,
          output_variables= output_variables,
          input_value_ts= sis.input_value_ts,
          initial_output_values= sis.initial_output_values )

# Repeating this simulation overwrites the result file
