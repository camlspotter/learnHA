# Merge 2 SLX models into 1
# The models must share the same IO ports.

import os
from io import TextIOWrapper
import textwrap


def merge_without_save(out: TextIOWrapper, fn_a: str, fn_b: str, fn_merged: str) -> str:
    a = os.path.splitext(os.path.basename(fn_a))[0]
    b = os.path.splitext(os.path.basename(fn_b))[0]
    merged = os.path.splitext(fn_merged)[0]

    fn_a = os.path.abspath(fn_a)
    fn_b = os.path.abspath(fn_b)

    merge_system(out, fn_a, fn_b, fn_merged, a, b, merged)
    connect_ports(out, fn_a, fn_b, fn_merged, a, b, merged)
    return merged


def merge(out: TextIOWrapper, fn_a: str, fn_b: str, fn_merged: str) -> None:
    merged = merge_without_save(out, fn_a, fn_b, fn_merged)
    save_system(out, fn_merged, merged)


def merge_system(
    out: TextIOWrapper,
    fn_a: str,
    fn_b: str,
    fn_merged: str,
    a: str,
    b: str,
    merged: str,
) -> None:
    out.write(
        textwrap.dedent(
            f"""\
        bdclose all;
        clear;

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

        """
        )
    )


def connect_ports(
    out: TextIOWrapper,
    fn_a: str,
    fn_b: str,
    fn_merged: str,
    a: str,
    b: str,
    merged: str,
) -> None:
    out.write(
        textwrap.dedent(
            f"""
            %% Connect ports
 
            aPorts = get_param('{merged}/{a}', 'PortHandles');
            bPorts = get_param('{merged}/{b}', 'PortHandles');

            assert(length(aPorts.Inport) == length(bPorts.Inport), 'Models must have the same number of Inports');
            assert(length(aPorts.Outport) == length(bPorts.Outport), 'Models must have the same number of Outports');

            %% In-ports

            % in_i ---+---> Inport(i) of a
            %         |
            %         +---> Inport(i) of b 

            for i = 1:length(aPorts.Inport)
                inport = sprintf('{merged}/in_%d', i);

                add_block('simulink/Sources/In1', inport);
    
                xiInput = get_param(inport, 'PortHandles');
                % port number is automatically assigned.
                % set_param(inport, 'Port', num2str(i));
                set_param(inport, 'SignalType', 'auto');
                add_line('{merged}', xiInput.Outport(i), aPorts.Inport(i));
                add_line('{merged}', xiInput.Outport(i), bPorts.Inport(i));
            end

            %% Out-ports

            % Outport(i) of a ------> out_ai

            for i = 1:length(aPorts.Outport)
                outport = sprintf('{merged}/out_a%d', i);

                add_block('simulink/Sinks/Out1', outport);
                aOutPorts = get_param(outport, 'PortHandles');
                % set_param(outport, 'Port', num2str(i));
                set_param(outport, 'SignalType', 'auto');
                add_line('{merged}', aPorts.Outport(i), aOutPorts.Inport(1));
            end

            % Outport(i) of b ------> out_bi  

            for i = 1:length(bPorts.Outport)
                outport = sprintf('{merged}/out_b%d', i);

                add_block('simulink/Sinks/Out1', outport);
                bOutPorts = get_param(outport, 'PortHandles');
                % set_param(outport, 'Port', num2str(i + length(aPorts.Outport)));
                set_param(outport, 'SignalType', 'auto');
                add_line('{merged}', bPorts.Outport(i), bOutPorts.Inport(1));
            end

            Simulink.BlockDiagram.arrangeSystem('{merged}');

            """
        )
    )


def save_system(out: TextIOWrapper, fn_merged: str, merged: str) -> None:
    out.write(
        textwrap.dedent(
            f"""\
            % Save the new model as {fn_merged}
            save_system('{merged}')
            """
        )
    )
