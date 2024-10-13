% Load the original model
load_system('original')
load_system('learned')

% New empty model, which will be saved as merged.slx
new_system('merged');

% Make a subsystem in the new model at merged/original
add_block('built-in/Subsystem', 'merged/original');

% Copy the contents of the original to merged/original:
Simulink.BlockDiagram.copyContentsToSubsystem('original', 'merged/original');

% Make a subsystem in the new model at merged/learned
add_block('built-in/Subsystem', 'merged/learned');

% Copy the contents of the learned to merged/learned:
Simulink.BlockDiagram.copyContentsToSubsystem('learned', 'merged/learned');

% Arrange the subsystem positions automatically
Simulink.BlockDiagram.arrangeSystem('merged');

%%

learnedPorts = get_param('merged/learned', 'PortHandles');
originalPorts = get_param('merged/original', 'PortHandles');

add_block('simulink/Sources/In1', 'merged/xIn');
xInput = get_param('merged/xIn', 'PortHandles');
set_param('merged/xIn', 'Port', '1');
set_param('merged/xIn', 'SignalType', 'auto');
set_param('merged/xIn', 'position', [-100,0,-60,15]);
add_line('merged', xInput.Outport(1), learnedPorts.Inport(1));
add_line('merged', xInput.Outport(1), originalPorts.Inport(1));

%%

add_block('simulink/Sinks/Out1', 'merged/learnedOut1');
learnedOut1Ports = get_param('merged/learnedOut1', 'PortHandles');
set_param('merged/learnedOut1', 'Port', '1');
set_param('merged/learnedOut1', 'SignalType', 'auto');
set_param('merged/learnedOut1', 'position', [100,-60,140,-45]);
add_line('merged', learnedPorts.Outport(1), learnedOut1Ports.Inport(1));

add_block('simulink/Sinks/Out1', 'merged/learnedOut2');
learnedOut2Ports = get_param('merged/learnedOut2', 'PortHandles');
set_param('merged/learnedOut2', 'Port', '2');
set_param('merged/learnedOut2', 'SignalType', 'auto');
set_param('merged/learnedOut2', 'position', [100,-40,140,-25]);
add_line('merged', learnedPorts.Outport(2), learnedOut2Ports.Inport(1));

add_block('simulink/Sinks/Out1', 'merged/learnedOut3');
learnedOut3Ports = get_param('merged/learnedOut3', 'PortHandles');
set_param('merged/learnedOut3', 'Port', '3');
set_param('merged/learnedOut3', 'SignalType', 'auto');
set_param('merged/learnedOut3', 'position', [100,-20,140,-5]);
add_line('merged', learnedPorts.Outport(3), learnedOut3Ports.Inport(1));

%%

add_block('simulink/Sinks/Out1', 'merged/originalOut1');
originalOut1Ports = get_param('merged/originalOut1', 'PortHandles');
set_param('merged/originalOut1', 'Port', '4');
set_param('merged/originalOut1', 'SignalType', 'auto');
set_param('merged/originalOut1', 'position', [100,15,140,30]);
add_line('merged', originalPorts.Outport(1), originalOut1Ports.Inport(1));

add_block('simulink/Sinks/Out1', 'merged/originalOut2');
originalOut2Ports = get_param('merged/originalOut2', 'PortHandles');
set_param('merged/originalOut2', 'Port', '5');
set_param('merged/originalOut2', 'SignalType', 'auto');
set_param('merged/originalOut2', 'position', [100,35,140,50]);
add_line('merged', originalPorts.Outport(2), originalOut2Ports.Inport(1));

add_block('simulink/Sinks/Out1', 'merged/originalOut3');
originalOut3Ports = get_param('merged/originalOut3', 'PortHandles');
set_param('merged/originalOut3', 'Port', '6');
set_param('merged/originalOut3', 'SignalType', 'auto');
set_param('merged/originalOut3', 'position', [100,55,140,70]);
add_line('merged', originalPorts.Outport(3), originalOut3Ports.Inport(1));

Simulink.BlockDiagram.arrangeSystem('merged');

% Save the new model as new.slx
save_system('merged')
