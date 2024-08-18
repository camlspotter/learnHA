from typeguard import typechecked
from dataclasses import dataclass
import numpy as np

@dataclass
class Range():
    min : float
    max : float

    def __init__(self, min, max):
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

ODE = dict[str,float]    # Σ_i1x_i + a_

Guard = dict[str,float]  # Σ_i1x_i + a_c<= 0

Assignment = dict[str,float]  # Σ_i1x_i + a_

@dataclass
class Transition():
    src : int
    dst : int
    guard : Guard
    assignments : dict[str, Assignment]

def build_guard( guard_coeffs : list[float] ) -> Guard:
    return { ("x" + str(i) if i < len(guard_coeffs) - 1 else "1"): c for (i, c) in enumerate(guard_coeffs) }

assert str(build_guard([1,2,3,4])) == "{'x0': 1, 'x1': 2, 'x2': 3, '1': 4}", "build_guard bug"

def build_assignment(coeffs : np.ndarray, intercept : float) -> Assignment:
    d = { ("x" + str(i)): c for (i, c) in enumerate(coeffs) }
    d["1"] = intercept
    return d

# XXX Should I cnovert np.float64 to float ?
assert (str(build_assignment( np.array([1.0,2.1,3.2]), 4.3 ))
        == "{'x0': np.float64(1.0), 'x1': np.float64(2.1), 'x2': np.float64(3.2), '1': 4.3}"), "build_assignment bug"

def build_assignments(coeffs : np.ndarray, intercepts : np.ndarray) -> dict[str,Assignment]:
    (nvs1, nvs2) = coeffs.shape
    (nvs3,) = intercepts.shape  # syntax for 1 element tuple
    assert nvs1 == nvs2
    assert nvs1 == nvs3
    assignments = [build_assignment(coeffs, intercept) for (coeffs, intercept) in zip(coeffs, intercepts)]
    return { ("x" + str(i)): a for (i, a) in enumerate(assignments) }

assert (str(build_assignments( np.array([ [1,2,3], [4,5,6], [7,8,9] ]), np.array( [10, 11, 12] )))
        == "{'x0': {'x0': np.int64(1), 'x1': np.int64(2), 'x2': np.int64(3), '1': np.int64(10)}, 'x1': {'x0': np.int64(4), 'x1': np.int64(5), 'x2': np.int64(6), '1': np.int64(11)}, 'x2': {'x0': np.int64(7), 'x1': np.int64(8), 'x2': np.int64(9), '1': np.int64(12)}}")

def build_Transition(trans : tuple[int,
                                   int,
                                   list[float],
                                   np.ndarray,
                                   np.ndarray
                                   ]) -> Transition:
    (src, dst, guard_coeffs, assignment_coeffs, assignment_intercepts) = trans

    guard = build_guard(guard_coeffs)
    assignments = build_assignments(assignment_coeffs, assignment_intercepts)
    return Transition(src= src,
                      dst= dst,
                      guard= guard,
                      assignments= assignments)

@dataclass
class Mode():
    id : int
    invariant : Invariant
    flow : dict[str,ODE]

def build_invariant(inv : list[tuple[float, float]]) -> Invariant:
    return { ("x" + str(i)): Range(min, max) for (i,(min,max)) in enumerate(inv) }

# XXX Very simliar to build_guard
def build_ode(ode : np.ndarray) -> ODE:
    return { ("x" + str(i) if i < len(ode) - 1 else "1"): c for (i, c) in enumerate(ode) } 

def build_odes(odes : np.ndarray) -> dict[str,ODE]:
    return { ("x" + str(i)): o for (i,o) in enumerate([build_ode(ode) for ode in odes]) }

def build_Mode(id : int,
               inv : list[tuple[float, float]],
               odes : np.ndarray) -> Mode:
    invariant = build_invariant(inv)
    flow = build_odes(odes)
    return Mode(id= id, invariant= invariant, flow= flow)


@dataclass
class HybridAutomaton():
    init_mode : int
    modes : list[Mode]
    transitions : list[Transition]

@typechecked
def build(init_mode : int,
          G : list[np.ndarray],
          mode_inv : list[ list[tuple[float, float]] ],
          transitions : list[tuple[int,
                                   int,
                                   list[float],
                                   np.ndarray,
                                   np.ndarray
                                   ]]) -> HybridAutomaton:
    # if invariant_enabled == 2, mode_inv is empty!
    if mode_inv == []:
        mode_inv = [[]] * len(G)  # empty invariants
    else:
        assert (len(G) == len(mode_inv)), f"len(G) = {len(G)}  len(mode_inv) = {len(mode_inv)}"

    modes = [ build_Mode (id, inv, odes) for (id, (inv, odes)) in enumerate(zip(mode_inv, G)) ]

    transs : list[Transition] = [ build_Transition(trans) for trans in transitions ]

    return HybridAutomaton(init_mode= init_mode, modes= modes, transitions= transs)