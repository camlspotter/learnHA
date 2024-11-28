import os
from io import TextIOWrapper
import textwrap


def embed(
    out: TextIOWrapper,
    fn: str,
    fn_embeded: str,
    input_variables: list[str],
    output_variables: list[str],
) -> str:
    '''
    Embed 1 SLX model

    Getting the port names of an SLX model seems lots of coding...
    instead of it, we embed the model in another model with our own port names.

         - Its input ports are for the input variables.
         - Its output ports are for the output and input variables:
           the outputs come first then the inputs follow.

    Try
      pipenv run python3 -m unittest hybridlearner.slx.test_embed
    then check
      _out/embeded.slx
    '''
    embeded = embed_without_save(out, fn, fn_embeded, input_variables, output_variables)
    save_system(out, fn_embeded, embeded)
    return embeded


def embed_without_save(
    out: TextIOWrapper,
    fn: str,
    fn_embeded: str,
    input_variables: list[str],
    output_variables: list[str],
) -> str:
    a = os.path.splitext(os.path.basename(fn))[0]
    embeded = os.path.splitext(fn_embeded)[0]

    fn = os.path.abspath(fn)

    embed_system(out, fn, fn_embeded, a, embeded, input_variables, output_variables)
    return embeded


def embed_system(
    out: TextIOWrapper,
    fn: str,
    fn_embeded: str,
    a: str,
    embeded: str,
    input_variables: list[str],
    output_variables: list[str],
) -> None:
    out.write(
        textwrap.dedent(
            f"""\
            bdclose all;
            % clear;
    
            % Load the original model
            load_system('{fn}');
            
            % New empty model, which will be saved as {fn_embeded}
            h = new_system();
            set_param(h, 'Name', '{embeded}')
    
            % Make a subsystem in the new model at {embeded}/{a}
            add_block('built-in/Subsystem', '{embeded}/{a}');
    
            % Copy the contents of the original to {embeded}/{a}:
            Simulink.BlockDiagram.copyContentsToSubsystem('{a}', '{embeded}/{a}');
     
            % Arrange the subsystem positions automatically
            % Simulink.BlockDiagram.arrangeSystem('{embeded}');

            %% Connect ports
 
            aPorts = get_param('{embeded}/{a}', 'PortHandles');

            %% In-ports

            """
        )
    )

    for i, v in enumerate(input_variables):
        out.write(
            textwrap.dedent(
                f"""\
                % {v} -------> Inport(i) of a
                inblock = '{embeded}/{v}';
                add_block('simulink/Sources/In1', inblock);
                inPorts = get_param(inblock, 'PortHandles');
                set_param(inblock, 'SignalType', 'auto');
                add_line('{embeded}', inPorts.Outport(1), aPorts.Inport({i+1}));

                """
            )
        )

    for i, v in enumerate(output_variables):
        out.write(
            textwrap.dedent(
                f"""\
                % Outport(i) of a ------> {v}
                outblock = '{embeded}/{v}';
                add_block('simulink/Sinks/Out1', outblock);
                outPorts = get_param(outblock, 'PortHandles');
                set_param(outblock, 'SignalType', 'auto');
                add_line('{embeded}', aPorts.Outport({i+1}), outPorts.Inport(1));

                """
            )
        )

    out.write(f"""\
    % arrangeSystem fails if nothing is modified in R2024b
    try
        Simulink.BlockDiagram.arrangeSystem('{embeded}');
    catch
    end
    """)


def save_system(out: TextIOWrapper, fn_embeded: str, embeded: str) -> None:
    out.write(
        textwrap.dedent(
            f"""\
            % Save the new model as {fn_embeded}
            save_system('{embeded}')
            """
        )
    )
