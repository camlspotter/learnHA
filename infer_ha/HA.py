from typeguard import typechecked
from dataclasses import dataclass
import numpy as np

@dataclass
class Raw():
    num_mode : int          # num_mode
    G : list[np.ndarray]    # ODE coeffs, called Flow in the paper.  The array size is (#v + 1) * #o
    mode_inv : list[ list[ tuple[ float, float ] ] ]  # Variable invariants per mode
    transitions : list[tuple[int,          # src
                             int,          # dest
                             list[float],  # guard coeffs [ci], defines the guard:  x1 * c1 + x2 * c2 + .. + 1 * cn <= 0
                             np.ndarray,   # assignment coeffs. 2D
                             np.ndarray    # assignment intercepts. 1D
                             # x'j = x1 * cj1 + x2 * cj2 + .. + xn *cjn + ij
                             ]]
    initial_location : int
    ode_degree : int         # required for printing
    guard_degree : int       # required for printing

    input_variables : list[str]
    output_variables : list[str]

@dataclass
class Range():
    min : float
    max : float

    def __init__(self, min : float, max : float):
        assert min <= max, "Invalid range"
        self.min= min
        self.max= max

    def contains(self, x : float) -> bool:
        return self.min <= x <= self.max

assert Range(1,2).contains(1.5), "Range.contains failure"
ex_Range : Range = Range(1, 2)
assert str(ex_Range) == "Range(min=1, max=2)", "Range bug"
ex_Range2 : Range = Range(min=1, max=2)
assert str(ex_Range2) == "Range(min=1, max=2)", "Range bug"

Invariant = dict[str,Range]  # ∧a_i <= x_i <= b_i

Polynomial = dict[str,float] # Σ_i1x_i +c

def string_of_polynomial(p : Polynomial) -> str:
    return " + ".join([(f"{v}" if k == "1" else f"{k} * {v}") for (k,v) in p.items()])

ODE = Polynomial

Guard = Polynomial

Assignment = Polynomial

@dataclass
class Transition():
    id : int
    src : int
    dst : int
    guard : Guard
    assignments : dict[str, Assignment]

def build_guard(vars : list[str], guard_coeffs : list[float] ) -> Guard:
    return { (vars[i] if i < len(guard_coeffs) - 1 else "1"): c for (i, c) in enumerate(guard_coeffs) }

assert str(build_guard(["a", "b", "c"], [1,2,3,4])) == "{'a': 1, 'b': 2, 'c': 3, '1': 4}", "build_guard bug"

def build_assignment(vars : list[str], coeffs : np.ndarray, intercept : float) -> Assignment:
    d = { vars[i]: c for (i, c) in enumerate(coeffs) }
    d["1"] = intercept
    return d

# XXX Should I cnovert np.float64 to float ?
assert (str(build_assignment(["a", "b", "c"], np.array([1.0,2.1,3.2]), 4.3 ))
        == "{'a': np.float64(1.0), 'b': np.float64(2.1), 'c': np.float64(3.2), '1': 4.3}"), "build_assignment bug"

def build_assignments(vars : list[str], output_vars : list[str], coeffs : np.ndarray, intercepts : np.ndarray) -> dict[str,Assignment]:
    (nvs1, nvs2) = coeffs.shape
    (nvs3,) = intercepts.shape  # syntax for 1 element tuple
    assert nvs1 == nvs2
    assert nvs1 == nvs3
    assignments = [build_assignment(vars, coeffs, intercept) for (coeffs, intercept) in zip(coeffs, intercepts)]
    return { vars[i]: a for (i, a) in enumerate(assignments) if vars[i] in output_vars }

assert (str(build_assignments( ["a", "b", "c"], ["a", "b", "c"], np.array([ [1,2,3], [4,5,6], [7,8,9] ]), np.array( [10, 11, 12] )))
        == "{'a': {'a': np.int64(1), 'b': np.int64(2), 'c': np.int64(3), '1': np.int64(10)}, 'b': {'a': np.int64(4), 'b': np.int64(5), 'c': np.int64(6), '1': np.int64(11)}, 'c': {'a': np.int64(7), 'b': np.int64(8), 'c': np.int64(9), '1': np.int64(12)}}")

def build_Transition(id : int,
                     vars : list[str],
                     output_vars : list[str],
                     trans : tuple[int,
                                   int,
                                   list[float],
                                   np.ndarray,
                                   np.ndarray
                                   ]) -> Transition:
    (src, dst, guard_coeffs, assignment_coeffs, assignment_intercepts) = trans

    guard = build_guard(vars, guard_coeffs)
    assignments = build_assignments(vars, output_vars, assignment_coeffs, assignment_intercepts)
    return Transition(id= id,
                      src= src,
                      dst= dst,
                      guard= guard,
                      assignments= assignments)

@dataclass
class Mode():
    id : int
    invariant : Invariant
    flow : dict[str,ODE]

def build_invariant(vars : list[str], inv : list[tuple[float, float]]) -> Invariant:
    return { vars[i]: Range(min, max) for (i,(min,max)) in enumerate(inv) }

# XXX Very simliar to build_guard
def build_ode(vars : list[str], ode : np.ndarray) -> ODE:
    return { (vars[i] if i < len(ode) - 1 else "1"): c for (i, c) in enumerate(ode) }

def build_odes(vars : list[str], output_vars : list[str], odes : np.ndarray) -> dict[str,ODE]:
    iodes = [ (i, ode) for (i, ode) in enumerate(odes) if vars[i] in output_vars ]
    return { vars[i] : build_ode(vars, ode) for (i, ode) in iodes }

def build_Mode(id : int,
               vars : list[str],
               output_vars : list[str],
               inv : list[tuple[float, float]],
               odes : np.ndarray) -> Mode:
    invariant = build_invariant(vars, inv)
    flow = build_odes(vars, output_vars, odes)
    return Mode(id= id, invariant= invariant, flow= flow)


@dataclass
class HybridAutomaton():
    init_mode : int
    modes : list[Mode]
    transitions : list[Transition]
    input_variables : list[str]
    output_variables : list[str]

    def outgoing_transitions(self, mode_id : int) -> list[Transition]:
        return [tr for tr in self.transitions if tr.src == mode_id ]

@typechecked
def build(raw : Raw) -> HybridAutomaton:
    mode_inv = raw.mode_inv
    # if invariant_enabled == 2, mode_inv is empty!
    if mode_inv == []:
        mode_inv = [[]] * len(raw.G)  # empty invariants
    else:
        assert (len(raw.G) == len(raw.mode_inv)), f"len(G) = {len(raw.G)}  len(mode_inv) = {len(raw.mode_inv)}"

    vars = raw.input_variables + raw.output_variables

    modes = [ build_Mode (id, vars, raw.output_variables, inv, odes) for (id, (inv, odes)) in enumerate(zip(raw.mode_inv, raw.G)) ]

    transs : list[Transition] = [ build_Transition(id, vars, raw.output_variables, trans) for (id, trans) in enumerate(raw.transitions) ]

    return HybridAutomaton(init_mode= raw.initial_location,
                           modes= modes,
                           transitions= transs,
                           input_variables= raw.input_variables,
                           output_variables = raw.output_variables)
