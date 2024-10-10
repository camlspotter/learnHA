from enum import Enum
from io import TextIOWrapper
import textwrap
from dataclasses import dataclass

from hybridlearner.automaton import HybridAutomaton
from hybridlearner.types import Invariant
import hybridlearner.types
import hybridlearner.automaton
from hybridlearner.polynomial import (
    Polynomial,
    variable_annotated_to_polynomial,
    polynomial_to_variable_annotated,
)

oneVersusOne_oneVersusRest: int = 1  # XXX enum?


class OdeSolverType(Enum):
    VARIABLE = "variable"
    FIXED = "fixed"


class InvariantMode(Enum):
    INCLUDE_BOTH = 0
    INCLUDE_OUTPUT = 1
    INCLUDE_NONE = 2


@dataclass
class HA(HybridAutomaton):
    variable_dict: dict[int, str]  # xi -> var.  Initialized by __post_init__
    variable_rev_dict: dict[str, int]  # var -> xi  Initialized by __post_init__

    def __post_init__(self) -> None:
        self.variable_dict = dict(
            enumerate(self.input_variables + self.output_variables)
        )
        self.variable_rev_dict = {v: i for (i, v) in self.variable_dict.items()}

    def is_input_variable(self, v: str) -> bool:
        return v in self.input_variables

    def is_output_variable(self, v: str) -> bool:
        return v in self.output_variables

    def string_of_polynomial(self, p: Polynomial) -> str:
        # Damn, we must rename variables!
        def rename(k: dict[str, int]) -> dict[str, int]:
            return {f"x{self.variable_rev_dict[x]}": i for (x, i) in k.items()}

        p2 = variable_annotated_to_polynomial(
            [(rename(k), f) for (k, f) in polynomial_to_variable_annotated(p)]
        )
        return p2.string

    def string_of_invariant(self, inv: Invariant) -> str:
        return hybridlearner.types.string_of_invariant(
            {f"x{self.variable_rev_dict[k]}": r for (k, r) in inv.items()}
        )


# Adds variable-index tables
def extend_HA(ha_orig: HybridAutomaton) -> HA:
    d = ha_orig.__dict__
    d['variable_dict'] = {}  # reinitialized by __post_init__
    d['variable_rev_dict'] = {}  # reinitialized by __post_init__
    ha = HA(**d)
    if ha is None:
        assert False, "Invalid HA"
    return ha


def compile(
    out: TextIOWrapper,
    ha_orig: HybridAutomaton,
    ode_solver_type: OdeSolverType,
    ode_solver: str,
    simulink_model_name: str,
    invariant_mode: InvariantMode,
) -> None:
    # ha : HA = build_HA(ha_orig, ode_solver_type, ode_solver, simulink_model_name, invariant_mode)
    ha: HA = extend_HA(ha_orig)

    out.write("%%% Script file for generating programmatically Simulink Model %%%\n\n")

    printDefinition(out, simulink_model_name, ode_solver_type, ode_solver)

    # Create random Matlab function only when non-deterministic situation arise
    # XXX never used.
    if len(ha.modes) == 3 and oneVersusOne_oneVersusRest == 2:
        addMatlabFunction(out)

    addLocations(out, ha)
    addTransitions(out, ha, invariant_mode)
    addDefaultTransition(out, ha)
    variableCreation(out, ha)

    # IO ports from the Chart to be connected using lines to the IO components
    out.write(
        textwrap.dedent(
            f"""\
            %%% IO components %%%

            % chart ports are accessible via chartOutSignal.{{In,Out}}port(portId)
            chartOutSignal = get_param('{simulink_model_name}/Chart', 'PortHandles');

            """
        )
    )

    addInputComponents(out, ha, simulink_model_name)
    addOutputComponents(out, ha, simulink_model_name)
    # addConnectionPointLines(out)

    out.write(
        textwrap.dedent(
            f"""\
            %%% Rearrange object positions automatically %%%

            Simulink.BlockDiagram.arrangeSystem('{simulink_model_name}');
            Simulink.BlockDiagram.arrangeSystem('{simulink_model_name}/Chart');

            %%% Closing %%%

            sfsave;
            sfclose;
            close_system;
            bdclose all;
            """
        )
    )


def printDefinition(
    out: TextIOWrapper,
    simulink_model_name: str,
    ode_solver_type: OdeSolverType,
    ode_solver: str,
) -> None:
    out.write(
        textwrap.dedent(
            f"""\
            %%% Opening %%%

            bdclose all;
            sfnew {simulink_model_name};
            rt = sfroot;
            ch = find(rt,'-isa','Stateflow.Chart');

            """
        )
    )

    solver_type: str
    step_parameter_key: str
    match ode_solver_type:
        case OdeSolverType.VARIABLE:
            solver_type = 'Variable-step'
            step_parameter_key = 'MaxStep'
        case OdeSolverType.FIXED:
            solver_type = 'Fixed-step'
            step_parameter_key = 'FixedStep'
        case _:
            assert False
    out.write(
        textwrap.dedent(
            f"""\
            %%% Set simulation parametors, such as sampling time %%%

            set_param(bdroot, ... % `...` for multiline code
                      'SolverType', '{solver_type}', ... 
                      'StopTime', 'timeFinal', ... % timeFinal = time_horizon
                      'SolverName', '{ode_solver}', ...
                      '{step_parameter_key}', 'timeStepMax'); % timeStepMax = sampling_time

            """
        )
    )

    out.write(
        textwrap.dedent(
            """\
            ch.ActionLanguage = 'C';
            ch.ChartUpdate = 'CONTINUOUS';
            ch.EnableZeroCrossings = 0;
            ch.ExecuteAtInitialization = true;

            """
        )
    )


def addMatlabFunction(out: TextIOWrapper) -> None:
    out.write(
        textwrap.dedent(
            """\
            %% Adding a Matlab Function that generates random number in the range -2 to +2
        
            function1 = Stateflow.EMFunction(ch);
            function1.LabelString = 'rOut = myRandomOut()';
            function1.Position = [10 390 120 60];
            str = ['function rOut=myRandomOut()',10, ...
                   'a=-2; %staring number-Range',10, ...
                   'b=2;  %ending number-Range',10, ...
                   'N=1;  %number of outputs',10, ...
               
                   'coder.cinclude("time.h")',10, ...
                   'sd=0;',10, ...
                   'sd=coder.ceval("time",[]);',10, ...
                   'rng(sd,"twister");',10, ...
               
                   'rOut = a + (b-a) * rand(N,1);',10, ...
                   'Nn=rOut;',10, ... % This line is just to add Manual break-point for debug
                   'end'];
            function1.Script=str;

            """
        )
    )


def addLocations(out: TextIOWrapper, ha: HA) -> None:
    out.write("%%% Adding Locations %%%\n\n")

    pos_x: int = 30
    pos_y: int = 30
    width: int = 90
    height: int = 60
    state_gap: int = 100

    for loc in ha.modes:
        loc_id = loc.id + 1
        out.write(
            textwrap.dedent(
                f"""\
                % Loc {loc_id}

                loc{loc_id} = Stateflow.State(ch);
                loc{loc_id}.Position = [{pos_x} {pos_y} {width} {height}];
                """
            )
        )

        # 10 here is ASCII char indicate newline char
        out.write(f"str = ['loc{loc_id}', 10, ... % 10 is for a newline char\n")

        # du: during action block, xi_dot = x0 * w0 + x1 * w1 + ... + 1 * wc
        out.write(" 'du: ', 10, ... % during action block for ODEs\n")
        for var, ode in loc.flow.items():
            var_id = f"x{ha.variable_rev_dict[var]}"
            out.write(
                f" '    {var_id}_dot = {ha.string_of_polynomial(ode)};', 10, ...\n"
            )

        # exit action block, xi_out = xi
        out.write("'exit: ', 10, ... % exit action block\n")
        for var, _ode in loc.flow.items():
            var_id = f"x{ha.variable_rev_dict[var]}"
            out.write(f" '    {var_id}_out = {var_id};', 10, ...\n")

        out.write(" ];\n")

        out.write(f"loc{loc_id}.LabelString = str;\n\n")

        pos_x = pos_x + width + state_gap


def addTransitions(out: TextIOWrapper, ha: HA, invariant_mode: InvariantMode) -> None:
    out.write("%%% Transitions %%%\n\n")

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
        out.write(f"% Transitions for Location loc{loc_id}\n")
        exec_order: int = 1
        # start value Todo: proper calculation needed
        sourceOClock = 3.1 + different_position
        different_position += 1.1
        # If the model is a Single Location with no Transitions this Loop will not be executed
        transition_count: int = 0
        # list_guardToInvariant : list[str] # equality guard to NotEquality guard for locations' invariant (Matlab's unconditional fixes)
        # However, this fix is not correct when given guard is other than equality guard. For eg x >= 7. Here replacing Not will not work out.
        # Better, fix is to use the actual invariant of the location and replace it. So, here we must have invariant given.

        for tr in trans:
            assert loc.id == tr.src
            # ************* Using the Modified Guard which replace Equality guard into inequality guard for fixing MATLAB's issue *********
            # Note: converted equality into range by epsilon
            inequality_guard = ha.string_of_polynomial(tr.guard) + " <= 0"
            # Prints reset equations from a list of reset equations
            reset_statement_for_tr = resetPrinter2(ha, tr.assignments)
            reset_statement_for_tr = reset_statement_for_tr

            if loc.id == tr.dst:  # this means it's a Loop Transition
                addLoopTransitions(
                    out,
                    loc.id,
                    number_of_loop_trans,
                    pos_x,
                    next_height,
                    inequality_guard,
                    reset_statement_for_tr,
                )
                number_of_loop_trans += 1

            else:  # not a loop transition
                out.write(f"    t{tr.id} = Stateflow.Transition(ch);\n")
                out.write(f"    t{tr.id} = Stateflow.Transition(ch);\n")
                out.write(f"    t{tr.id}.Source = loc{loc_id};\n")
                out.write(f"    t{tr.id}.Destination = loc{tr.dst+1};\n")
                # XXX It is a constant!!
                out.write(f"    t{tr.id}.ExecutionOrder = {exec_order};\n")
                out.write(f"    t{tr.id}.SourceOClock = {sourceOClock}; \n")
                out.write(
                    f"    t{tr.id}.LabelPosition = [{x_pos} {y_pos} 31 {next_height}];\n"
                )

                out.write(
                    f"    t{tr.id}.LabelString = '[ {inequality_guard} ]{reset_statement_for_tr}';\n"
                )

                # ************* Using the Modified Guard which replace Equality guard into inequality guard for fixing MATLAB's issue *********

            exec_order += 1
            sourceOClock += 2  # Randomly added 2. Note OClock value ranges from 0 to 12, clock values.
            y_pos += next_height  # height of the Transition Label is set as 16. Need to check later
            transition_count += 1  # counts the number of transitions

        # exec_order this will be for loop-transtions now

        # ****** addLoopTransitions(out); #This is the Invariant Loop ******

        out.write(
            textwrap.dedent(
                f"""\

                % Loop Transition for loc{loc_id} to represent Invariant Condition
                % [loc{loc_id}] -<ca{loc_id}_{number_of_loop_trans}>-> (c{loc_id}_{number_of_loop_trans}) -<cb{loc_id}_{number_of_loop_trans}>-> [loc{loc_id}]
                % cb{loc_id}_{number_of_loop_trans} has a reset statement possibly with a invariant condition

                c{loc_id}_{number_of_loop_trans} = Stateflow.Junction(ch);
                c{loc_id}_{number_of_loop_trans}.Position.Center = [{pos_x - 20} 0];
                c{loc_id}_{number_of_loop_trans}.Position.Radius = 10;
                
                ca{loc_id}_{number_of_loop_trans} = Stateflow.Transition(ch);
                ca{loc_id}_{number_of_loop_trans}.Source = loc{loc_id};
                ca{loc_id}_{number_of_loop_trans}.Destination = c{loc_id}_{number_of_loop_trans};

                cb{loc_id}_{number_of_loop_trans} = Stateflow.Transition(ch);
                cb{loc_id}_{number_of_loop_trans}.Source = c{loc_id}_{number_of_loop_trans};
                cb{loc_id}_{number_of_loop_trans}.Destination = loc{loc_id};
                cb{loc_id}_{number_of_loop_trans}.LabelPosition = [{pos_x - 20} 10 31 {next_height}];

                """
            )
        )

        # Prints a simple identity reset equations. This is used below, in the invariant-loop-transition
        reset_statement_identity = resetPrinter(ha)

        condition_str: str
        if transition_count == 0:
            condition_str = ""
        else:
            # For one or more transitions
            # Get all guards (for multiple transitions and convert it into in-equilatity (~=) and concatenate with ||
            # Now it is better by replacing with the actual invariant constraints
            # ------------ new code --------------
            match invariant_mode:
                case InvariantMode.INCLUDE_BOTH:
                    # include both input and output constraints as invariant
                    condition_str = "[ " + ha.string_of_invariant(loc.invariant) + " ]"

                case InvariantMode.INCLUDE_OUTPUT:
                    # include only output constraints and remove input constraints as invariant
                    #
                    # check the constraint, I assume all constraints is of the form "left op val", where left is the variable involving the constraint, op is the operator
                    # valid operators are  >=, <= etc and val is the numeric value
                    # So, just check if the left is in input-variable list in the variable-mapping then discard this constraint, otherwise include it.
                    #
                    condition_str = "[ " + ha.string_of_invariant(loc.invariant) + " ]"

                case InvariantMode.INCLUDE_NONE:
                    condition_str = ""

                case _:
                    assert False, "invalid invariant_mode"

        out.write(
            f"cb{loc_id}_{number_of_loop_trans}.LabelString = '{condition_str}{reset_statement_identity}';\n\n"
        )

        number_of_loop_trans += 1  # every location has a loop-transition that represents an invariant #XXX WHOT!?
        pos_x += width + state_gap  # Next Location/State 's Position


def addDefaultTransition(out: TextIOWrapper, ha: HA) -> None:
    init_mode = ha.init_mode

    # x1 = a1; x2 = a2; ... for output variables
    initial_values = (
        "{ "
        + " ".join(
            [
                f"x{i} = a{i};"
                for i in range(
                    len(ha.input_variables),
                    len(ha.input_variables) + len(ha.output_variables),
                )
            ]
        )
        + " }"
    )

    # Note a0, a1 are the initial values for the variable;
    out.write(
        textwrap.dedent(
            f"""\
            
            % Initial Transition
            % Set `xi = ai` for all the output variables `xi`
            % The host program must set `ai` for the initial value of each output variable of index `i`

            init{init_mode+1} = Stateflow.Transition(ch);
            init{init_mode+1}.Destination = loc{init_mode+1};
            init{init_mode+1}.LabelString = '{initial_values}';
            init{init_mode+1}.DestinationOClock = 0;
            init{init_mode+1}.SourceEndpoint = init{init_mode+1}.DestinationEndpoint - [0 30];
            init{init_mode+1}.Midpoint = init{init_mode+1}.DestinationEndpoint - [0 15];

            """
        )
    )


def generateInitialValues(ha: HA) -> str:
    init_str = "{"

    for index, var in ha.variable_dict.items():
        if ha.is_output_variable(var):
            var_id = f"x{ha.variable_rev_dict[var]}"
            init_str += f"{var_id} = a{index};"

    init_str += "}"
    return init_str


def variableCreation(out: TextIOWrapper, ha: HA) -> None:
    out.write("%%% Variable Declarations %%%\n\n")
    inputVariableCreation(out, ha)
    outputVariableCreation(out, ha)
    localVariableCreation(out, ha)
    parameterVariableCreation(out, ha)


def addInputComponents(out: TextIOWrapper, ha: HA, simulink_model_name: str) -> None:
    out.write("%%% Input components %%%\n\n")

    y_pos = 18
    height = 33
    next_height = 40
    portNo = 1  # Assuming the order is maintained

    for var in ha.input_variables:
        var_id = f"x{ha.variable_rev_dict[var]}"
        out.write(
            textwrap.dedent(
                f"""\
                % Add input port number {portNo} for input variable {var_id}

                add_block('simulink/Sources/In1', '{simulink_model_name}/{var_id}In');
                {var_id}Input = get_param('{simulink_model_name}/{var_id}In', 'PortHandles');
                set_param('{simulink_model_name}/{var_id}In', 'Port', '{portNo}');
                set_param('{simulink_model_name}/{var_id}In', 'SignalType', 'auto');
                set_param('{simulink_model_name}/{var_id}In', 'position', [-40, {y_pos}, 0, {height}]);
                % {var_id}Input ---> Input {portNo} of Chart
                add_line('{simulink_model_name}', {var_id}Input.Outport(1), chartOutSignal.Inport({portNo}));

            """
            )
        )

        height += next_height
        y_pos += next_height
        portNo += 1


def addOutputComponents(out: TextIOWrapper, ha: HA, simulink_model_name: str) -> None:
    # The number of output components is equal to the number of variables. Not anymore now they are separate.
    out.write("%%% Output components %%%\n\n")

    portNo = 1  # Assuming the order is maintained
    y_pos = 18
    height = 33
    next_height = 40

    # For the output variables
    for var in ha.output_variables:
        # connecting the output port of the Chart to input port of the Output component
        # Creating an output-component for every variable (both input and output variables)
        var_id = f"x{ha.variable_rev_dict[var]}"
        out.write(
            textwrap.dedent(
                f"""\
                % Add output port number {portNo} for output variable {var_id}

                add_block('simulink/Sinks/Out1', '{simulink_model_name}/{var_id}Out');
                {var_id}Output = get_param('{simulink_model_name}/{var_id}Out', 'PortHandles');
                set_param('{simulink_model_name}/{var_id}Out', 'SignalName', '{var_id}Out');
                set_param('{simulink_model_name}/{var_id}Out', 'Port', '{portNo}');
                set_param('{simulink_model_name}/{var_id}Out', 'SignalType', 'auto');
                set_param('{simulink_model_name}/{var_id}Out', 'position', [140, {y_pos}, 180, {height}]);
                % Outport {portNo} of Chart ---> {var_id}Output
                add_line('{simulink_model_name}', chartOutSignal.Outport({portNo}), {var_id}Output.Inport(1));

                """
            )
        )

        height += next_height
        y_pos += next_height
        portNo += 1

    # For the input variables
    # portNo will follow the sequence Output variable followed by Input variables
    for var in ha.input_variables:
        var_id = f"x{ha.variable_rev_dict[var]}"
        out.write(
            textwrap.dedent(
                f"""\
                % Add output port number {portNo} for input variable {var_id}

                add_block('simulink/Sinks/Out1', '{simulink_model_name}/{var_id}Out');
                {var_id}Output = get_param('{simulink_model_name}/{var_id}Out', 'PortHandles');
                set_param('{simulink_model_name}/{var_id}Out', 'SignalName', '{var_id}Out');
                set_param('{simulink_model_name}/{var_id}Out', 'Port', '{portNo}');
                set_param('{simulink_model_name}/{var_id}Out', 'SignalType', 'auto');
                set_param('{simulink_model_name}/{var_id}Out', 'position', [140, {y_pos}, 180, {height}]);
                % {var_id}Input ---> {var_id}Output.  The input values are simpliy copied to the output               
                add_line('{simulink_model_name}', {var_id}Input.Outport(1), {var_id}Output.Inport(1));

                """
            )
        )

        height += next_height
        y_pos += next_height
        portNo += 1


def addLoopTransitions(
    out: TextIOWrapper,
    sourceLoc: int,
    number_loop_trans: int,
    pos_x: int,
    next_height: int,
    condition_str: str,
    reset_str: str,
) -> None:
    pos_x += 10
    next_height += 10

    loc_id = sourceLoc + 1

    junction_object_name = f"c{loc_id}_{number_loop_trans}"
    trans_loc_to_junction = f"ca{loc_id}_{number_loop_trans}"
    trans_junction_to_loc = f"cb{loc_id}_{number_loop_trans}"

    # exec_order this will be for loop-transtions now
    # Adding blank lines before Invariants handling (using Connectives-Self Loops)
    out.write(
        textwrap.dedent(
            f"""\
            % Loop Transition for loc{loc_id} to represent Invariant Condition
            % [loc{loc_id}] -<{trans_loc_to_junction}>-> ({junction_object_name}) -<{trans_junction_to_loc}>-> [loc{loc_id}]
            % {trans_junction_to_loc} has an invariant condition and an assignment

            {junction_object_name} = Stateflow.Junction(ch);
            {junction_object_name}.Position.Center = [{pos_x - 20} 0];
            {junction_object_name}.Position.Radius = 10;

            {trans_loc_to_junction} = Stateflow.Transition(ch);
            {trans_loc_to_junction}.Source = loc{loc_id};
            {trans_loc_to_junction}.Destination = {junction_object_name};

            {trans_junction_to_loc} = Stateflow.Transition(ch);
            {trans_junction_to_loc}.Source = {junction_object_name};
            {trans_junction_to_loc}.Destination = loc{loc_id};
            {trans_junction_to_loc}.LabelPosition = [{pos_x - 20} 10 31 {next_height}];
            {trans_junction_to_loc}.LabelString = '[{condition_str}]{reset_str}';
            """
        )
    )

    # createConnectiveJunction(out);
    # completeLoopTransitions(out);


def inputVariableCreation(out: TextIOWrapper, ha: HA) -> None:
    out.write("%%% Input Variable Declaration %%%\n\n")
    portNo = 1
    for var in ha.input_variables:
        var_id = f"x{ha.variable_rev_dict[var]}"
        out.write(
            textwrap.dedent(
                f"""\
                % Input variable {var_id}_in in Chart connected at port {portNo} for input variable {var}

                {var_id}_in  = Stateflow.Data(ch);
                {var_id}_in.Name = '{var_id}';
                {var_id}_in.Scope = 'Input';
                {var_id}_in.Port = {portNo};
                {var_id}_in.Props.Type.Method = 'Inherited';
                {var_id}_in.DataType = 'Inherit: Same as Simulink';
                {var_id}_in.UpdateMethod = 'Discrete';

                """
            )
        )
        portNo += 1


def outputVariableCreation(out: TextIOWrapper, ha: HA) -> None:
    out.write("%%% Output Variable Declaration %%%\n\n")

    portNo = 1  # Assuming the order is maintained
    for var in ha.output_variables:
        var_id = f"x{ha.variable_rev_dict[var]}"
        out.write(
            textwrap.dedent(
                f"""\
                % Output variable {var_id}_out in Chart connected at port {portNo} for output variable {var}

                {var_id}_out = Stateflow.Data(ch);
                {var_id}_out.Name = '{var_id}_out';
                {var_id}_out.Scope = 'Output';
                {var_id}_out.Port = {portNo};
                {var_id}_out.Props.Type.Method = 'Inherited';
                {var_id}_out.DataType = 'Inherit: Same as Simulink';
                {var_id}_out.UpdateMethod = 'Discrete';

                """
            )
        )
        portNo += 1


def localVariableCreation(out: TextIOWrapper, ha: HA) -> None:
    out.write("%%% Local Variable Declaration %%%\n\n")

    for var in ha.output_variables:
        var_id = f"x{ha.variable_rev_dict[var]}"
        out.write(
            textwrap.dedent(
                f"""\
                % Local variable {var_id} in Chart for output variable {var}
                
                {var_id} = Stateflow.Data(ch);
                {var_id}.Name = '{var_id}';
                {var_id}.Scope = 'Local';
                {var_id}.UpdateMethod = 'Continuous';

                """
            )
        )


def parameterVariableCreation(out: TextIOWrapper, ha: HA) -> None:
    out.write("%%% Parameter Variable Declaration %%%\n\n")

    # print only for output variables and not for input variables
    for var in ha.output_variables:
        index = ha.variable_rev_dict[var]
        out.write(
            textwrap.dedent(
                f"""\
                % Parameter a{index}: the initial value of output variable {var}
                % It must be set by the host program.

                a{index} = Stateflow.Data(ch);
                a{index}.Name = 'a{index}';
                a{index}.Scope = 'Parameter';
                a{index}.Tunable = true;
                a{index}.Props.Type.Method = 'Inherited';
                a{index}.DataType = 'Inherit: Same as Simulink';
                
                """
            )
        )


def resetPrinter(ha: HA) -> str:
    var_ids = [f"x{ha.variable_rev_dict[var]}" for var in ha.output_variables]

    return "{ " + "".join([f"{var_id} = {var_id}; " for var_id in var_ids]) + "}"


def resetPrinter2(ha: HA, reset_list: dict[str, Polynomial]) -> str:
    reset_str: str = ""

    for var, assignment in reset_list.items():
        var_id = f"x{ha.variable_rev_dict[var]}"
        assert ha.is_output_variable(var)
        reset_str += f"{var_id} = {ha.string_of_polynomial(assignment)}; "

    return "{" + reset_str + "}"