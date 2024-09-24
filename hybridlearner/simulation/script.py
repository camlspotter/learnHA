from os import path
from io import TextIOWrapper
import textwrap


def generate_simulation_script(
    out: TextIOWrapper,
    title: str,
    simulink_model_file: str,
    time_horizon: float,
    sampling_time: float,
    fixed_interval_data: bool,
    input_variables: list[str],
    output_variables: list[str],
) -> None:
    """
    - simulink_model_file: is the simulink model filename that has the automaton design
    Note: input-port in the simulink model must be assigned names as "x0In", "x1In", etc. Moreover, list of input and output variables must be supplied in the command-line.
    """
    assert path.isabs(simulink_model_file), (
        "generate_simulation_script: simulink_model_file cannot be relative: "
        + simulink_model_file
    )

    out.write(
        textwrap.dedent(
            f"""\
    %% ******** Simulate User Supplied Model ********
    %% ******** by generate_simulation_script ********
    % Run the simulation and generate a txt file containing a result of the simulation.
    % run this file with the following variables in the workspace
    %  - timeFinal:  is the simulation Stop time or the simulation Time-Horizon. Note, .slx must have it set in the Model Settings->Solver menu.
    %  - timeStepMax: is the Maximum simulation time-step or 'Max step size'. Note, .slx must set it in the Model Settings->Solver menu.
    %  - a0, a1, and so on...: the initial values for state/output variables should also be loaded in the workspace.
    %    x0_input:       control point for the first input variable
    %    x0_time:        time series for the first input variable
    %    x1_input:       control point for the second input variable
    %    x1_time:        time series for the second input variable ..... and so on.
    %
    % Note: If the .slx model has input variable, then the inport must be labelled as
    %   x0In for the first input variable, x1In for the second input variable ..... and so on.

    timeFinal = {time_horizon}; %Simulation Stop time or the simulation Time-Horizon
    timeStepMax = {sampling_time}; %Maximum simulation time-step

    % initial values for Simulation

    """
        )
    )

    out.write(
        textwrap.dedent(
            f"""\
    %% Load the model
    mdl ='{path.splitext(path.basename(simulink_model_file))[0]}';
    load_system('{simulink_model_file}');
    format shortG;
    """
        )
    )

    # Todo: obtain from the user-supplied parameters: Type:fixed-step/linear/sin-wave/spline
    # /Only If the input variable is present in the model, then create the input time-series data ds and load into the model as LoadExternalInput=on

    if len(input_variables) > 0:
        out.write(
            textwrap.dedent(
                """\
        %%%%% Non-deterministic inputs %%%%%%% These values are obtained from
        %%%%% our Tool using random bounded by initial input values or from CE
        % Make SimulationData.Dataset to feed to the Simulink model
        ds = Simulink.SimulationData.Dataset;
        %%
        """
            )
        )

        # cout <<"\nData Set Details are " << endl;
        # cout <<"Check-out size of time-signal per-simulation =" << init_point.size()<< endl;

        for varName in input_variables:
            # Eg., timeseriese_varName_input = timeseries(u_input, u_time); \n"
            input_data_varName = f"{varName}_input"
            input_time_varName = f"{varName}_time"
            timeseries_varName = f"timeseries_{input_data_varName}"
            timeseries_input_value = f"{timeseries_varName} = timeseries({input_data_varName}, {input_time_varName}); \n"
            out.write(timeseries_input_value)

            # Todo:
            # We have to assume here the input-port name would be "varName" followed by "In". Eg.,  "x0In" or "x1In"
            # This is the naming convention applied in the "txt2slx" process/engine. In general, when no name is assigned in the simulink model it is "In1" "In2" by default

            input_port_Name = f"{varName}In"

            # Note: the variable 'u' should be created as input_port in the simulink model
            out.write(
                f"ds = ds.addElement({timeseries_varName}, '{input_port_Name}');\n%%\n"
            )

        out.write("set_param(mdl, 'LoadExternalInput', 'on');\n")
        out.write(
            "set_param(mdl, 'ExternalInput', 'ds'); % Set the initial input values in the model.\n"
        )

    out.write(
        textwrap.dedent(
            f"""\
    simOut = sim(mdl, 'SaveOutput', 'on', 'OutputSaveName', 'yOut', 'SaveTime', 'on','TimeSaveName','tOut', 'LimitDataPoints', 'off', 'SaveFormat', 'Array');
    %% Plot the result
    y = simOut.get('yOut');
    t = simOut.get('tOut');
    % comment out this shows a plot
    % [rsize, csize] = size(y);
    % % *********** Plotting the original output from the Simulink model *****************
    % for i=1:csize
    %     figure(i);
    %     plot(t, y( : , i));
    %     title('{title}','FontSize',26, 'FontWeight', 'bold');
    %     xlabel('time', 'FontSize',26, 'FontWeight', 'bold');
    %     grid on;
    %     grid minor;
    % end
    """
        )
    )

    # *********** Plotting original output done *****************

    # ******* If Data Filtering required by the user ***********

    # XXX enum or bool
    # 0: variable outputs obtained from the model-solver. 1: get fixed timestep outputs.
    if fixed_interval_data:
        addFilteringCode(out)

    # *********** Data Filtering done ***********

    out.write("% Write the simulation result to the txt file\n")

    output_str = "result_matrix = [t, "

    output_str += ", ".join(  # Writing first the input variables, which is all followed by the output ports
        [
            f"y( : , {i+1})"
            for i in range(
                len(output_variables), len(input_variables) + len(output_variables)
            )
        ]
        +
        # Writing then the output variables, which are the starting output ports
        [f"y( : , {i+1})" for i in range(0, len(output_variables))]
    )

    output_str += "];\n"
    out.write(output_str)

    out.write(
        textwrap.dedent(
            f"""\
    % result_filename = 'output_file'; Now given by setvar
    writematrix(result_matrix, result_filename, 'Delimiter', 'tab');
    """
        )
    )


def addFilteringCode(out: TextIOWrapper) -> None:
    """
     Addon code called from create_runScript_for_simu_engine() to perform Data Filtering
     Filtering: Extract simulation data based on fixed timestep values and discard the data obtained due to variable Solver used in the Simulink model.

     Assumption:
         This being an addon code, it assume that the data are in the matlab variable 't' and 'y'.
         Variable t is one-dimensional array of variable timestep values with values containing at least one instance of fixed timestep value for each increasing timestep.
         Variable y is n-dimensional array of variable containing values for each n dimensions corresponding t values.
               rsize and csize is obtained using [rsize, csize] = size(y); in the calling function.

    ***************** Actual Matlab Code for Data Filtering *****************


          tstep=0;
          seq_index=1;
          totalSamples = timeFinal / timeStepMax + 1;
          t_temp1 = zeros(totalSamples, 1);
          y_temp1 = zeros(totalSamples, csize);
          firstFound = 1;
          for i= 1:rsize  %rsize is the total rows of y or y_temp
             diffVal = t(i) - tstep; %initially time-step will be >= 0
             if (diffVal >= 0)
                     firstFound = 1;
             end
             if (diffVal >= 0 && firstFound == 1)   %1st value that matches, i.e., positive value
                       t_temp1(seq_index) = t(i);
                       for j = 1:csize
                               y_temp1(seq_index, j) = y(i, j);
                       end

                       seq_index = seq_index +1;
                       tstep = tstep + timeStepMax;
                       firstFound = 0;
             end
          end
          t = t_temp1;
          y = y_temp1;
    """

    out.write(
        textwrap.dedent(
            """\
    tstep = 0;
    seq_index = 1;
    totalSamples = timeFinal / timeStepMax + 1;
    t_temp1 = zeros(totalSamples, 1);
    y_temp1 = zeros(totalSamples, csize);
    firstFound = 1;
    for i = 1:rsize     %rsize is the total rows of y or y_temp
       diffVal = t(i) - tstep;     %initially time-step will be >= 0
       if (diffVal >= 0)
           firstFound = 1;
       end
       if (diffVal >= 0 && firstFound == 1)  %1st value that matches, i.e., positive value
                t_temp1(seq_index) = t(i);
                for j = 1:csize     %csize is the total columns of y or y_temp, i.e., for each variables
                        y_temp1(seq_index, j) = y(i, j);
                end

                seq_index = seq_index + 1;
                tstep = tstep + timeStepMax;
                firstFound = 0;
       end
    end
    """
        )
    )

    # ***************** Code for creating variables *****************

    # ******* Fixing minor bug *************
    # Due to variable time-step sometime some fixed timestep values are missed (unavailable in the simulation result).
    # Observed: Usually happened only one record for eg., 0.0010 is missed. Further inspection on more than one miss is required
    # Fix: we just replace the last zero values to non-zero value.

    out.write(
        textwrap.dedent(
            """\
    last_row = y_temp1(totalSamples, :);
    if last_row == 0
        secondlast_row = y_temp1(totalSamples - 1, :);
        y_temp1(totalSamples, :) = secondlast_row;
        secondlast_row_time = t_temp1(totalSamples - 1);
        t_temp1(totalSamples) = secondlast_row_time;
    end
    """
        )
    )

    # replacing the filtered data back to the original variable t
    out.write("t = t_temp1;\n")
    # replacing the filtered data back to the original variable y
    out.write("y = y_temp1;\n")
