# MATLAB and me (and you 🫵 of course)

MATLAB is a combination of interpreter and GUI.

## Installation

Using [`mpm`](https://jp.mathworks.com/help/install/ug/get-mpm-os-command-line.html) is the best option I think.

```
$ ./mpm install --release R2022b  --products=MATLAB Simulink
```

Activation requires X:

```
$ /usr/local/MATLAB/R2022b/bin/activate_matlab.sh
```

## Issue on Mac + XQuartz

### Slow

Since XQuartz is slow.

### Non active windows turn black:

Put the following `java.opts` file at the lauching directory:
  ```
  -Dsun.java2d.xrender=false
  -Dsun.java2d.pmoffscreen=false   
  ```

## Use GUI

It has a nice value inspector and a debugger.

## Pathetic language

- `double` is used for references (=pointer values).
- ``...`` is required to change a line in a statement.
   ```
   f(a, ...
     b, ...
     c)   % 🤪
   ```
- Statement without `;` at the end prints its result.
- `disp(e);` to print something.
- `clear;` to forget the already bound variables
- `bdclose all;` to close all the Simulink models opened.
- `x'` is matrix transposition.

## Model handling

`mdl = load_system(path)` loads a model, but `mdl` is not a model but a reference:

```
>> mdl = load_system('data/models/cars1.slx')

mdl =

  179.0001  🤪
```

Get the name of the model, since some functions do not take the reference but the name:

```
>> mdlName = get_param(mdl, 'Name')

mdlName =

    'cars1'
```

The parameters of the model:

```
>> get_param(mdl, 'ObjectParameters')
...
```

These parameters can be obtained by `get_param` and may be set by `set_param`.

## Modifying models

Write MATLAB code to draw blocks:

Build a new model of name 'merged':

```
h = new_system();
set_param(h, 'Name', 'merged');
```

Block names such as `simulink/Sources/In1` are fond in Simulink editor: Library Browser > Library:

```
% Add a block at inblock
add_block('simulink/Sources/In1', inblock);

% Get port handles of inblock
inPorts = get_param(inblock, 'PortHandles');

% Set a parameter of inblock
set_param(inblock, 'SignalType', 'auto');

% Connect an outport and an inport:
add_line('{merged}', inPorts.Outport(1), aPorts.Inport({i+1}));
```

Sub-system to include other Simulink models:

```
% Make a subsystem in the new model at foo/bar
add_block('built-in/Subsystem', 'merged/sub');

% Copy the contents of the src to merged/sub
Simulink.BlockDiagram.copyContentsToSubsystem('src', 'merged/sub');
```


Arrange the positions of the blocks at the end:

```
% Arrange the subsystem positions automatically 
Simulink.BlockDiagram.arrangeSystem('modified');
```

Save it:

```
save_ssytem('modified')
```

### From Python

See `hybridlearner.matlab`

### Draw SVG of a model

`slx_draw.py` should help you.
