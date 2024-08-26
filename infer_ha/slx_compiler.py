from enum import Enum
from io import TextIOWrapper
import textwrap
from infer_ha.HA import HybridAutomaton, Assignment, Transition, Mode, Polynomial, Invariant
from dataclasses import dataclass, asdict

oneVersusOne_oneVersusRest : int = 1  #XXX enum?

class OdeSolverType(Enum):
    VARIABLE = "variable"
    FIXED = "fixed"

class InvariantMode(Enum):
    INCLUDE_BOTH = 0
    INCLUDE_OUTPUT = 1
    INCLUDE_NONE = 2

@dataclass
class HA(HybridAutomaton):
    ode_solver_type : OdeSolverType
    ode_solver : str
    simulink_model_name : str
    invariant_mode : InvariantMode
    variable_dict : dict[int, str]  # xi -> var.  Initialized by __post_init__
    variable_rev_dict : dict[str, int]  # var -> xi  Initialized by __post_init__

    def __post_init__(self) -> None:
        self.variable_dict = dict(enumerate(self.input_variables + self.output_variables))
        self.variable_rev_dict = { v:i for (i,v) in self.variable_dict.items() }

    def is_input_variable(self, v : str) -> bool:
        return v in self.input_variables

    def is_output_variable(self, v : str) -> bool:
        return v in self.output_variables

    def string_of_polynomial(self, p : Polynomial) -> str:
        return " + ".join([f"{v}{"" if k == "1" else f" * x{self.variable_rev_dict[k]}"}" for (k,v) in p.items()])

    def string_of_invariant(self, inv : Invariant) -> str:
        return " && ".join([f"{r.min} <= x{self.variable_rev_dict[v]} && x{self.variable_rev_dict[v]} <= {r.max}"
                            for (v, r) in inv.items()])

def build_HA(ha_orig : HybridAutomaton,
             ode_solver_type : OdeSolverType,
             ode_solver : str,
             simulink_model_name : str,
             invariant_mode : InvariantMode):
    d = ha_orig.__dict__
    d['ode_solver_type'] = ode_solver_type
    d['ode_solver'] = ode_solver
    d['simulink_model_name'] = simulink_model_name
    d['invariant_mode'] = invariant_mode
    d['variable_dict'] = {} # reinitialized by __post_init__
    d['variable_rev_dict'] = {} # reinitialized by __post_init__
    ha = HA(**d)
    if ha == None:
        assert False, "Invalid HA"
    return ha

def compile(out : TextIOWrapper,
            ha_orig : HybridAutomaton,
            ode_solver_type : OdeSolverType,
            ode_solver : str,
            simulink_model_name : str,
            invariant_mode : InvariantMode) -> None:
    ha : HA = build_HA(ha_orig, ode_solver_type, ode_solver, simulink_model_name, invariant_mode)

    out.write("%% Script file for generating Programmatically Simulink Model!\n")
    printDefinition(out, ha)

    if len(ha.modes) == 3 and oneVersusOne_oneVersusRest == 2:
        # Create random Matlab function only when non-deterministic situation arise
        addMatlabFunction(out)

    addLocations(out, ha)
    addTransitions(out, ha)
    addDefaultTransition(out, ha)
    variableCreation(out, ha)

    # Output ports from the Chart to be connected using lines to the outputComponents
    out.write("\n\n")
    out.write(f"chartOutSignal = get_param('{ha.simulink_model_name}/Chart', 'PortHandles'); \n\n")

    addInputComponents(out, ha) # when model has input variables
    addOutputComponents(out, ha)
    # addConnectionLines(out)

    out.write("\n\n")
    out.write(f"Simulink.BlockDiagram.arrangeSystem('{ha.simulink_model_name}');\n")
    out.write(f"Simulink.BlockDiagram.arrangeSystem('{ha.simulink_model_name}/Chart');\n\n")
    out.write(textwrap.dedent(
        """
        sfsave;
        sfclose;
        close_system;
        bdclose all;
        """)[1:-1])

def printDefinition(out : TextIOWrapper, ha : HA) -> None:
    out.write("bdclose all;\n")
    out.write(f"sfnew {ha.simulink_model_name}\n")
    out.write("rt = sfroot;\n")
    out.write("ch = find(rt,'-isa','Stateflow.Chart');\n")
    # outfile << "set_param(bdroot, 'StopTime', 'timeFinal', 'MaxStep', 'timeStepMax'); \n";  //This is for variable-step with MaxStep as timeStepMax
    # Working with Fixed-step   outfile << "set_param(bdroot, 'SolverType','Fixed-step', 'StopTime', 'timeFinal', 'FixedStep', 'timeStepMax'); \n";  //This is for Fixed-step size

    match ha.ode_solver_type:
        case OdeSolverType.VARIABLE:
            # std::cout <<"ODE Solver Type: Variable-step" << std::endl;
            # This makes the model Variable-step
            out.write(f"set_param(bdroot, 'SolverType', 'Variable-step', 'StopTime', 'timeFinal', 'SolverName', '{ha.ode_solver}', 'MaxStep', 'timeStepMax');\n") 

        case OdeSolverType.FIXED:
            out.write(f"set_param(bdroot, 'SolverType', 'Fixed-step', 'StopTime', 'timeFinal', 'SolverName', '{ha.ode_solver}', 'FixedStep', 'timeStepMax');\n")

        case _:
            assert False

    out.write(textwrap.dedent(
        """
        ch.ActionLanguage = 'C';
        ch.ChartUpdate = 'CONTINUOUS';
        ch.EnableZeroCrossings = 0;
        ch.ExecuteAtInitialization = true;
        """)[1:-1])

def addMatlabFunction(out):
    out.write(txtwrap.dedent(
        """
        %% Adding a Matlab Function that generates random number in the range -2 to +2
        
        function1 = Stateflow.EMFunction(ch);
        function1.LabelString = 'rOut = myRandomOut()';
        function1.Position = [10 390 120 60];
        str = ['function rOut=myRandomOut()',10, ...
               'a=-2; %staring number-Range',10, ...
               'b=2;  %ending number-Range',10, ...
               'N=1;  %number of outputs',10, ...
           
               'coder.cinclude("time.h")',10, ...
               'sd=0;',10, ... \n")
               'sd=coder.ceval("time",[]);',10, ...
               'rng(sd,"twister");',10, ...
           
               'rOut = a + (b-a) * rand(N,1);',10, ...
               'Nn=rOut;',10, ... % This line is just to add Manual break-point for debug)
               'end']; \n")
        function1.Script=str;
        """)[1:-1])

def addLocations(out, ha : HA) -> None:
    out.write("\n\n%% Adding Locations or States with ODE\n")
 
    pos_x : int = 30
    pos_y : int = 30
    width : int = 90
    height : int = 60
    state_gap : int = 100

    print("HA", ha)

    for loc in ha.modes:
        loc_id = loc.id + 1
        out.write(f"loc{loc_id} = Stateflow.State(ch);\n")
        # Calculate the position properly later (dynamicall)
        # out << "loc" << loc->getLocId() << ".Position = [30 30 90 60];";
        out.write(f"loc{loc_id}.Position = [{pos_x} {pos_y} {width} {height}];\n")
 
        out.write(f"str = ['loc{loc_id}', 10, ...\n") # 10 here is ASCII char indicate newline char
        out.write(" 'du: ', 10, ...\n")
        # Now get the ODE for each variable_dot
        derivatives = loc.flow # list<flow_equation>
        # int var_index=0; // fixing this hard-coded indexing approach
        # string variableName="", prime_variableName;
        # size_t pos;
 
        # Loop for during block
        for (var, ode) in loc.flow.items():
            var_id = f"x{ha.variable_rev_dict[var]}"
            # XXX Filtering must be done outside of this printer
            assert ha.is_output_variable(var), "flow contains input variable's ODE"
            out.write(f" '    {var_id}_dot = {ha.string_of_polynomial(ode)};', 10, ...\n")

        out.write("'exit: ', 10, ...\n")

        # XXX dupe
        for (var, _ode) in loc.flow.items():
            var_id = f"x{ha.variable_rev_dict[var]}"
            assert ha.is_output_variable(var), "flow contains input variable's ODE"
            out.write(f" '    {var_id}_out = {var_id};', 10, ...\n")
 
        out.write(" ];\n")
 
        out.write(f"loc{loc_id}.LabelString = str;\n")
        out.write("\n\n")
 
        pos_x = pos_x + width + state_gap

def addTransitions(out, ha : HA) -> None:
    out.write("\n\n%% Adding Transition for each Locations or States\n")

    pos_x = 30
    width = 90
    state_gap = 100
    x_pos = pos_x + width + state_gap * 0.5
    y_pos = 0
    next_height = 16
    number_of_loop_trans = 0
    different_position = 1.1

    for loc in ha.modes:
        # addMainTransitions(out); Maybe I should do it in this function itself

        loc_id = loc.id + 1
        trans = ha.outgoing_transitions(loc.id)
        out.write(f"\n%%Transitions for Location loc{loc_id}\n")
        exec_order : int = 1
        sourceOClock = 3.1 + different_position #start value Todo: proper calculation needed
        different_position += 1.1
        # If the model is a Single Location with no Transitions this Loop will not be executed
        transition_count : int = 0
        list_guardToInvariant : list[str] # equality guard to NotEquality guard for locations' invariant (Matlab's unconditional fixes)
        # However, this fix is not correct when given guard is other than equality guard. For eg x >= 7. Here replacing Not will not work out.
        # Better, fix is to use the actual invariant of the location and replace it. So, here we must have invariant given.

        for tr in trans:
            assert loc.id == tr.src
            # ************* Using the Modified Guard which replace Equality guard into inequality guard for fixing MATLAB's issue *********
            # Note: converted equality into range by epsilon
            inequality_guard = ha.string_of_polynomial(tr.guard) + " <= 0"
            reset_statement_for_tr = resetPrinter2(ha, tr.assignments) # Prints reset equations from a list of reset equations
            reset_statement_for_tr = reset_statement_for_tr

            if loc.id == tr.dst: #this means it's a Loop Transition
                addLoopTransitions(out, loc.id, number_of_loop_trans, pos_x, next_height, inequality_guard, reset_statement_for_tr)
                number_of_loop_trans += 1

            else: # not a loop transition
                out.write(f"    t{tr.id} = Stateflow.Transition(ch);\n")
                out.write(f"    t{tr.id}.Source = loc{loc_id};\n")
                out.write(f"    t{tr.id}.Destination = loc{tr.dst+1};\n")
                out.write(f"    t{tr.id}.ExecutionOrder = {exec_order};\n")  # XXX It is a contant!!
                out.write(f"    t{tr.id}.SourceOClock = {sourceOClock}; \n")
                out.write(f"    t{tr.id}.LabelPosition = [{x_pos} {y_pos} 31 {next_height}];\n")

                out.write(f"    t{tr.id}.LabelString = '[ {inequality_guard} ]{reset_statement_for_tr}';")
                # ************* Using the Modified Guard which replace Equality guard into inequality guard for fixing MATLAB's issue *********

            exec_order += 1
            sourceOClock +=2 # Randomly added 2. Note OClock value ranges from 0 to 12, clock values.
            y_pos +=next_height # height of the Transition Label is set as 16. Need to check later
            transition_count += 1  #counts the number of transitions

        #exec_order this will be for loop-transtions now

        # ****** addLoopTransitions(out); #This is the Invariant Loop ******
        out.write("\n\n") # Adding blank lines before Invariants handling (using Connectives-Self Loops)
        out.write("%% Adding Loop Transition to represent Invariant Condition\n")
        out.write(f"c{loc_id}_{number_of_loop_trans} = Stateflow.Junction(ch);\n")
        out.write(f"c{loc_id}_{number_of_loop_trans}.Position.Center = [{pos_x - 20} 0];\n")
        out.write(f"c{loc_id}_{number_of_loop_trans}.Position.Radius = 10;\n")

        out.write("\n") # Adding blank lines
        out.write(f"ca{loc_id}_{number_of_loop_trans} = Stateflow.Transition(ch);\n")
        out.write(f"ca{loc_id}_{number_of_loop_trans}.Source = loc{loc_id};\n")
        out.write(f"ca{loc_id}_{number_of_loop_trans}.Destination = c{loc_id}_{number_of_loop_trans};\n")

        out.write("\n") # Adding blank lines
        out.write(f"cb{loc_id}_{number_of_loop_trans} = Stateflow.Transition(ch);\n")
        out.write(f"cb{loc_id}_{number_of_loop_trans}.Source = c{loc_id}_{number_of_loop_trans};\n")
        out.write(f"cb{loc_id}_{number_of_loop_trans}.Destination = loc{loc_id};\n")
        out.write(f"cb{loc_id}_{number_of_loop_trans}.LabelPosition = [{pos_x - 20} 10 31 {next_height}];\n")

        reset_statement_identity = resetPrinter(ha) # Prints a simple identity reset equations. This is used below, in the invariant-loop-transition

        if transition_count == 0:
            out.write(f"cb{loc_id}_{number_of_loop_trans}.LabelString = '{reset_statement_identity}';\n")
        else: #For one or more transitions
            # Get all guards (for multiple transitions and convert it into in-equilatity (~=) and concatenate with ||
            #Now it is better by replacing with the actual invariant constraints
            #------------ new code --------------
            condition_str = ""
            cnt = 0

            match ha.invariant_mode:
                case InvariantMode.INCLUDE_BOTH:
                  #include both input and output constraints as invariant
                  condition_str = ha.string_of_invariant(loc.invariant)
                  out.write(f"cb{loc_id}_{number_of_loop_trans}.LabelString = '[{condition_str}]{reset_statement_identity}';\n")

                case InvariantMode.INCLUDE_OUTPUT:
                  # include only output constraints and remove input constraints as invariant
                  #
                  # check the constraint, I assume all constraints is of the form "left op val", where left is the variable involving the constraint, op is the operator
                  # valid operators are  >=, <= etc and val is the numeric value
                  # So, just check if the left is in input-variable list in the variable-mapping then discard this constraint, otherwise include it.
                  #
                  condition_str = ha.string_of_invariant(loc.invariant)
                  out.write(f"cb{loc_id}_{number_of_loop_trans}.LabelString = '[{condition_str}]{reset_statement_identity}';\n");

                case InvariantMode.INCLUDE_NONE:
                  out.write(f"cb{loc_id}_{number_of_loop_trans}.LabelString = '{reset_statement_identity}';\n")

                case _:
                  assert False, "invalid invariant_mode"

                #       /* Old code: used simple conjunction of other guards with their negation
                #        * std::string condition_str="";
                #       std::list<std::string>::iterator list_guard_inv = list_guardToInvariant.begin();
                #       for (unsigned int cnt = 0; cnt < transition_count; cnt++) {
                #               condition_str.append((*list_guard_inv));
                #               if ((transition_count > 1) && (cnt < (transition_count - 1))){
                #                       #condition_str.append(" || ");
                #                       condition_str.append(" && ");   #modified to && since when all other outgoing transition are not satified then the loop transitions takes
                #               }
                #               list_guard_inv++;
                #       }
                #       out.write( f"cb{loc_id}.LabelString = '[{condition_str}]{reset_statement_identity<<"';\n";*/

        number_of_loop_trans += 1 # every location has a loop-transition that represents an invariant #XXX WHOT!?
        pos_x += width + state_gap      #Next Location/State 's Position

def addDefaultTransition(out, ha : HA) -> None:
    init_mode = ha.init_mode

    # x1 = a1; x2 = a2; ... for output variables
    initial_values = \
        "{ " \
        + " ".join([f"x{i} = a{i};" for i in range(len(ha.input_variables),
                                                   len(ha.input_variables) + len(ha.output_variables))]) \
        + " }"
    
    out.write("\n\n")  #Adding blank lines
    out.write("%% Default or Initial Transition\n")
    out.write(f"init{init_mode+1} = Stateflow.Transition(ch);\n")
    out.write(f"init{init_mode+1}.Destination = loc{init_mode+1};\n")
    out.write(f"init{init_mode+1}.LabelString = '{initial_values}';\n") #Note a0, a1 are the initial values for the variable;
    out.write(f"init{init_mode+1}.DestinationOClock = 0;\n")
    out.write(f"init{init_mode+1}.SourceEndpoint = init{init_mode+1}.DestinationEndpoint - [0 30];\n")
    out.write(f"init{init_mode+1}.Midpoint = init{init_mode+1}.DestinationEndpoint - [0 15];\n")

def generateInitialValues(ha : HA) -> str:
    init_str = "{"

    for (index, var) in ha.variable_dict.items():
        if ha.is_output_variable(var):
            var_id = f"x{ha.variable_rev_dict[var]}"
            init_str += f"{var_id} = a{index};"

    init_str += "}"
    return init_str

def variableCreation(out, ha : HA) -> None:
    out.write("\n\n%% *** Variable Declaration Block ****\n")
    inputVariableCreation(out, ha)
    outputVariableCreation(out, ha)
    localVariableCreation(out, ha)
    parameterVariableCreation(out, ha)

def addInputComponents(out, ha : HA) -> None:
    out.write("\n%% *** Adding Input  components ****\n")

    y_pos = 18
    height = 33
    next_height = 40
    portNo = 1  # Assuming the order is maintained

    for var in ha.input_variables:
        var_id = f"x{ha.variable_rev_dict[var]}"
        out.write(f"add_block('simulink/Sources/In1', '{ha.simulink_model_name}/{var_id}In');\n")
        out.write(f"{var_id}Input = get_param('{ha.simulink_model_name}/{var_id}In', 'PortHandles');\n")
        out.write(f"set_param('{ha.simulink_model_name}/{var_id}In', 'Port', '{portNo}');\n")
        out.write(f"set_param('{ha.simulink_model_name}/{var_id}In', 'SignalType', 'auto');\n")
        out.write(f"set_param('{ha.simulink_model_name}/{var_id}In', 'position', [-40, {y_pos}, 0, {height}]);\n")
        out.write("\n\n")
        out.write(f"add_line('{ha.simulink_model_name}', {var_id}Input.Outport(1), chartOutSignal.Inport({portNo}));\n")
        out.write("\n\n")

        height += next_height;
        y_pos += next_height;
        portNo += 1

def addOutputComponents(out, ha : HA) -> None:
    # The number of output components is equal to the number of variables. Not anymore now they are separate.
    out.write("\n\n%% *** Adding Output components ****\n")

    portNo = 1 # Assuming the order is maintained
    y_pos = 18
    height = 33
    next_height = 40

    # For the output variables
    for var in ha.output_variables:
        # connecting the output port of the Chart to input port of the Output component
        #Creating an output-component for every variable (both input and output variables)
        var_id = f"x{ha.variable_rev_dict[var]}"
        out.write(f"add_block('simulink/Sinks/Out1', '{ha.simulink_model_name}/{var_id}Out');\n")
        out.write(f"{var_id}Output = get_param('{ha.simulink_model_name}/{var_id}Out', 'PortHandles');\n")
        out.write(f"set_param('{ha.simulink_model_name}/{var_id}Out', 'SignalName', '{var_id}Out');\n")
        out.write(f"set_param('{ha.simulink_model_name}/{var_id}Out', 'Port', '{portNo}');\n")
        out.write(f"set_param('{ha.simulink_model_name}/{var_id}Out', 'SignalType', 'auto');\n")
        out.write(f"set_param('{ha.simulink_model_name}/{var_id}Out', 'position', [140, {y_pos}, 180, {height}]);\n")

        out.write("\n\n")
        out.write(f"add_line('{ha.simulink_model_name}', chartOutSignal.Outport({portNo}), {var_id}Output.Inport(1));\n")
        out.write("\n\n")
        height += next_height;
        y_pos += next_height;
        portNo += 1

    # For the input variables
    # portNo will follow the sequence Output variable followed by Input variables
    for var in ha.input_variables:
        var_id = f"x{ha.variable_rev_dict[var]}"
        out.write(f"add_block('simulink/Sinks/Out1', '{ha.simulink_model_name}/{var_id}Out');\n")
        out.write(f"{var_id}Output = get_param('{ha.simulink_model_name}/{var_id}Out', 'PortHandles');\n")
        out.write(f"set_param('{ha.simulink_model_name}/{var_id}Out', 'SignalName', '{var_id}Out');\n")
        out.write(f"set_param('{ha.simulink_model_name}/{var_id}Out', 'Port', '{portNo}');\n")
        out.write(f"set_param('{ha.simulink_model_name}/{var_id}Out', 'SignalType', 'auto');\n")
        out.write(f"set_param('{ha.simulink_model_name}/{var_id}Out', 'position', [140, {y_pos}, 180, {height}]);\n")
        out.write(f"add_line('{ha.simulink_model_name}', {var_id}Input.Outport(1), {var_id}Output.Inport(1));\n")
        out.write("\n\n")

        height += next_height;
        y_pos += next_height;
        portNo += 1

def addLoopTransitions(out,
                       sourceLoc : int,
                       number_loop_trans : int,
                       pos_x : int,
                       next_height : int,
                       condition_str : str,
                       reset_str : str) -> None:
    out.write("%% Transition to represent Invariants: Current fix is using Junction Connection to avoid inner Transitions\n")

    pos_x += 10
    next_height += 10

    junction_object_name = f"c{sourceLoc+1}_{number_loop_trans}"
    trans_loc_to_junction = f"ca{sourceLoc+1}_{number_loop_trans}"
    trans_junction_to_loc = f"cb{sourceLoc+1}_{number_loop_trans}"

    #exec_order this will be for loop-transtions now
    out.write("\n\n")  #Adding blank lines before Invariants handling (using Connectives-Self Loops)
    out.write("%% Adding Loop Transition to represent Invariant Condition\n")
    out.write(f"{junction_object_name} = Stateflow.Junction(ch);\n")
    out.write(f"{junction_object_name}.Position.Center = [{pos_x - 20} 0];\n")
    out.write(f"{junction_object_name}.Position.Radius = 10;\n")
    out.write("\n")
    out.write(f"{trans_loc_to_junction} = Stateflow.Transition(ch);\n")
    out.write(f"{trans_loc_to_junction}.Source = loc{sourceLoc+1};\n")
    out.write(f"{trans_loc_to_junction}.Destination = {junction_object_name};\n")
    out.write("\n") #Adding blank lines
    out.write(f"{trans_junction_to_loc} = Stateflow.Transition(ch);\n")
    out.write(f"{trans_junction_to_loc}.Source = {junction_object_name};\n")
    out.write(f"{trans_junction_to_loc}.Destination = loc{sourceLoc+1};\n")
    out.write(f"{trans_junction_to_loc}.LabelPosition = [{pos_x - 20} 10 31 {next_height}];\n")
    out.write(f"{trans_junction_to_loc}.LabelString = '[{condition_str}]{reset_str}';\n")

    #createConnectiveJunction(out);
    #completeLoopTransitions(out);


def inputVariableCreation(out, ha : HA) -> None:
    out.write("\n%% *** Input Variable Declaration ****\n")
    portNo = 1
    for var in ha.input_variables:
        var_id = f"x{ha.variable_rev_dict[var]}"
        out.write(f"{var_id}_in  = Stateflow.Data(ch);\n")
        out.write(f"{var_id}_in.Name = '{var_id}';\n")
        out.write(f"{var_id}_in.Scope = 'Input';\n")
        out.write(f"{var_id}_in.Port = {portNo};\n")
        out.write(f"{var_id}_in.Props.Type.Method = 'Inherit';\n")
        out.write(f"{var_id}_in.DataType = 'Inherit: Same as Simulink';\n")
        out.write(f"{var_id}_in.UpdateMethod = 'Discrete';\n")
        out.write("\n")
        portNo += 1

def outputVariableCreation(out, ha : HA) -> None:
    out.write("\n%% *** Output Variable Declaration ****\n")

    portNo = 1 # Assuming the order is maintained
    for var in ha.output_variables:
        var_id = f"x{ha.variable_rev_dict[var]}"
        out.write(f"{var_id}_out = Stateflow.Data(ch);\n")
        out.write(f"{var_id}_out.Name = '{var_id}_out';\n")
        out.write(f"{var_id}_out.Scope = 'Output';\n")
        out.write(f"{var_id}_out.Port = {portNo};\n")
        out.write(f"{var_id}_out.Props.Type.Method = 'Inherit';\n")
        out.write(f"{var_id}_out.DataType = 'Inherit: Same as Simulink';\n")
        out.write(f"{var_id}_out.UpdateMethod = 'Discrete';\n")
        out.write("\n")
        portNo += 1

def localVariableCreation(out, ha : HA) -> None:
    out.write("\n\n %% *** Local Variable Declaration ****\n")

    for var in ha.output_variables:
        var_id = f"x{ha.variable_rev_dict[var]}"
        out.write(f"{var_id} = Stateflow.Data(ch);\n")
        out.write(f"{var_id}.Name = '{var_id}';\n")
        out.write(f"{var_id}.Scope = 'Local';\n")
        out.write(f"{var_id}.UpdateMethod = 'Continuous';\n")
        out.write("\n")

def parameterVariableCreation(out, ha : HA) -> None:
    out.write("\n\n%% *** Parameter Variable Declaration ****\n")

    for (index, var) in ha.variable_dict.items():
        if ha.is_output_variable(var): #print only for output variables and not for input variables
           out.write(f"a{index} = Stateflow.Data(ch);\n")
           out.write(f"a{index}.Name = 'a{index}';\n")
           out.write(f"a{index}.Scope = 'Parameter';\n")
           out.write(f"a{index}.Tunable = true;\n")
           out.write(f"a{index}.Props.Type.Method = 'Inherit';\n")
           out.write(f"a{index}.DataType = 'Inherit: Same as Simulink';\n")
           out.write("\n")

#Printing an identity mapping for reset equations
def resetPrinter(ha : HA) -> str:
    #Read any one of the location and parse through the ODE's varName this contains the prime-variable

    reset_str : str = ""

    for var in ha.output_variables:
        var_id = f"x{ha.variable_rev_dict[var]}"
        reset_str += f"{var_id} = {var_id};"

    return "{" + reset_str + "}"

def resetPrinter2(ha : HA, reset_list : dict[str, Assignment]) -> str:

    reset_str : str = ""

    for (var, assignment) in reset_list.items():
        var_id = f"x{ha.variable_rev_dict[var]}"
        assert ha.is_output_variable(var)
        reset_str += f"{var_id} = {ha.string_of_polynomial(assignment)}; "

    return "{" + reset_str + "}"
