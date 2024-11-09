import os
from io import TextIOWrapper
import textwrap


def merge(
    out: TextIOWrapper,
    fn_a: str,
    fn_b: str,
    fn_merged: str,
    input_variables: list[str],
    output_variables: list[str],
) -> str:
    '''
    Merge 2 SLX models into 1

    The models must share the same IO ports:

      - Their input ports are for the input variables.
      - Their output ports are for the output and input variables:
        the outputs come first then the inputs follow.

    The merged model has the same number of input ports of the names of input variables.
    The merged model has 2 sets of output ports:

      - a_v: for the output variable v of the first model
      - b_v: for the output variable v of the second model

    The merged model has another set of output ports diff_v for the differences
    of the output ports a_v and b_v of the models.  The difference is computed as
    the integral of the absolute difference of the 2 signals.

    Try
      pipenv run python3 -m unittest hybridlearner.slx.test_merger
    then check
      _out/merged.slx
    '''
    merged = merge_without_save(
        out, fn_a, fn_b, fn_merged, input_variables, output_variables
    )
    save_system(out, fn_merged, merged)
    return merged


def merge_without_save(
    out: TextIOWrapper,
    fn_a: str,
    fn_b: str,
    fn_merged: str,
    input_variables: list[str],
    output_variables: list[str],
) -> str:
    a = os.path.splitext(os.path.basename(fn_a))[0]
    b = os.path.splitext(os.path.basename(fn_b))[0]
    merged = os.path.splitext(fn_merged)[0]

    fn_a = os.path.abspath(fn_a)
    fn_b = os.path.abspath(fn_b)

    merge_system(
        out, fn_a, fn_b, fn_merged, a, b, merged, input_variables, output_variables
    )
    return merged


def merge_system(
    out: TextIOWrapper,
    fn_a: str,
    fn_b: str,
    fn_merged: str,
    a: str,
    b: str,
    merged: str,
    input_variables: list[str],
    output_variables: list[str],
) -> None:
    out.write(
        textwrap.dedent(
            f"""\
            bdclose all;
            % clear;
    
            % Load the original model
            load_system('{fn_a}');
            load_system('{fn_b}');
            
            % New empty model, which will be saved as {fn_merged}
            h = new_system();
            set_param(h, 'Name', '{merged}')
    
            % Make a subsystem in the new model at {merged}/{a}
            add_block('built-in/Subsystem', '{merged}/{a}');
    
            % Copy the contents of the original to {merged}/{a}:
            Simulink.BlockDiagram.copyContentsToSubsystem('{a}', '{merged}/{a}');
     
            % Make a subsystem in the new model at {merged}/{b}
            add_block('built-in/Subsystem', '{merged}/{b}');
     
            % Copy the contents of the learned to {merged}/{b}:
            Simulink.BlockDiagram.copyContentsToSubsystem('{b}', '{merged}/{b}');
     
            % Arrange the subsystem positions automatically
            Simulink.BlockDiagram.arrangeSystem('{merged}');
    
            %% Connect ports
 
            aPorts = get_param('{merged}/{a}', 'PortHandles');
            bPorts = get_param('{merged}/{b}', 'PortHandles');

            assert(length(aPorts.Inport) == length(bPorts.Inport), 'Models must have the same number of Inports');
            assert(length(aPorts.Outport) == length(bPorts.Outport), 'Models must have the same number of Outports');

            %% In-ports

            % vi ---+---> Inport(i) of a
            %       |
            %       +---> Inport(i) of b 
            """
        )
    )

    for i, iv in enumerate(input_variables):
        out.write(
            textwrap.dedent(
                f"""\
                inblock = '{merged}/{iv}';
                add_block('simulink/Sources/In1', inblock);
                inPorts = get_param(inblock, 'PortHandles');
                set_param(inblock, 'SignalType', 'auto');
                add_line('{merged}', inPorts.Outport(1), aPorts.Inport({i+1}));
                add_line('{merged}', inPorts.Outport(1), bPorts.Inport({i+1}));

                """
            )
        )

    out.write(
        textwrap.dedent(
            f"""\
            %% Out-ports

            % Outport(i) of a ------> a_vi
            """
        )
    )

    for i, ov in enumerate(output_variables):
        out.write(
            textwrap.dedent(
                f"""\
                outblock = '{merged}/a_{ov}';
                add_block('simulink/Sinks/Out1', outblock);
                aOutPorts = get_param(outblock, 'PortHandles');
                set_param(outblock, 'SignalType', 'auto');
                add_line('{merged}', aPorts.Outport({i+1}), aOutPorts.Inport(1));
                """
            )
        )

    out.write("% Outport(i) of b ------> b_vi\n")

    for i, ov in enumerate(output_variables):
        out.write(
            textwrap.dedent(
                f"""\
                outblock = '{merged}/b_{ov}';
                add_block('simulink/Sinks/Out1', outblock);
                bOutPorts = get_param(outblock, 'PortHandles');
                set_param(outblock, 'SignalType', 'auto');
                add_line('{merged}', bPorts.Outport({i+1}), bOutPorts.Inport(1));
                """
            )
        )

    out.write(
        textwrap.dedent(
            f"""\
            % Outport(i) of a -->(+)+--------+    +---+    +---------+     +-------+
            %                       |Subtract| -> |Abs| -> |Integrate| --> |diff_vi|  
            % Outport(i) of b -->(-)+--------+    +---+    +---------+     +-------+
            """
        )
    )

    for i, ov in enumerate(output_variables):
        out.write(
            textwrap.dedent(
                f"""\
                diff = '{merged}/diff_{ov}';
                add_block('simulink/Sinks/Out1', diff);
                diffports = get_param(diff, 'PortHandles');
           
                integrator = '{merged}/integrator_{ov}';
                add_block('simulink/Continuous/Integrator', integrator);
                integratorports = get_param(integrator, 'PortHandles');
           
                add_line('{merged}', integratorports.Outport(1), diffports.Inport(1));
           
                abs = '{merged}/abs_{ov}';
                add_block('simulink/Math Operations/Abs', abs);
                % Simulation does not terminate if ZeroCross = 'on' (default)
                set_param(abs, 'ZeroCross', 'off');
                absports = get_param(abs, 'PortHandles');
           
                add_line('{merged}', absports.Outport(1), integratorports.Inport(1));
           
                sub = '{merged}/sub_{ov}';
                add_block('simulink/Math Operations/Subtract', sub);
                subports = get_param(sub, 'PortHandles');
           
                add_line('{merged}', aPorts.Outport({i+1}), subports.Inport(1));
                add_line('{merged}', bPorts.Outport({i+1}), subports.Inport(2));
                add_line('{merged}', subports.Outport(1), absports.Inport(1));
                """
            )
        )

    out.write(f"Simulink.BlockDiagram.arrangeSystem('{merged}');\n")


def save_system(out: TextIOWrapper, fn_merged: str, merged: str) -> None:
    out.write(
        textwrap.dedent(
            f"""\
            % Save the new model as {fn_merged}
            save_system('{merged}')
            """
        )
    )
