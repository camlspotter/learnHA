modelPath = "../data/models/ex_sldemo_bounce_Input.slx";
mdl = load_system(modelPath);
modelName = get_param(mdl, 'Name');
res = getfullname(Simulink.findBlocksOfType(mdl, 'Outport'));
disp(res{1});

