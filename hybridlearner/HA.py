from typeguard import typechecked
# pydantic.dataclasses is required for JSON conversions of nested dataclasses
from pydantic.dataclasses import dataclass
from pydantic import ConfigDict
import numpy as np
from hybridlearner.invariant import Invariant
from hybridlearner.range import Range
from hybridlearner.inference.transition import Transition as RawTransition
from hybridlearner.inference.transition.assignment import Assignment
from hybridlearner.inference import Raw

Polynomial = dict[str,float] # Σ_i1x_i +c

def string_of_polynomial(p : Polynomial) -> str:
    return " + ".join([( f"{v}" if k == "1" else f"{v} * {k}") for (k,v) in p.items()])

@dataclass
class Transition:
    id : int
    src : int
    dst : int
    guard : Polynomial
    assignments : dict[str, Polynomial]

def build_polynomial(vars : list[str], coeffs_and_intercept : list[float] ) -> Polynomial:
    assert len(vars) + 1 == len(coeffs_and_intercept)
    return { (vars[i] if i < len(coeffs_and_intercept) - 1 else "1"): c
             for (i, c) in enumerate(coeffs_and_intercept) }

def build_assignments(vars : list[str], output_vars : list[str], assignment : Assignment) -> dict[str, Polynomial]:
    (coeffs, intercepts) = assignment
    (nvs1, nvs2) = coeffs.shape
    (nvs3,) = intercepts.shape  # syntax for 1 element tuple
    assert nvs1 == nvs2
    assert nvs1 == nvs3
    assignments = [build_polynomial(vars, list(coeffs) + [intercept]) for (coeffs, intercept) in zip(coeffs, intercepts)]
    return { vars[i]: a for (i, a) in enumerate(assignments) if vars[i] in output_vars }

def build_Transition(id : int,
                     vars : list[str],
                     output_vars : list[str],
                     trans : RawTransition) -> Transition:
    (src, dst, guard_coeffs, assignment) = trans

    guard = build_polynomial(vars, guard_coeffs)
    assignments = build_assignments(vars, output_vars, assignment)
    return Transition(id= id,
                      src= src,
                      dst= dst,
                      guard= guard,
                      assignments= assignments)

@dataclass
class Mode:
    id : int
    invariant : Invariant
    flow : dict[str, Polynomial] # ODE

def build_invariant(vars : list[str], inv : list[tuple[float, float]]) -> Invariant:
    return { vars[i]: Range(min, max) for (i,(min,max)) in enumerate(inv) }

# XXX Very simliar to build_guard
def build_ode(vars : list[str], ode : np.ndarray) -> Polynomial:
    return { (vars[i] if i < len(ode) - 1 else "1"): c for (i, c) in enumerate(ode) }

def build_odes(vars : list[str], output_vars : list[str], odes : np.ndarray) -> dict[str, Polynomial]:
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
class HybridAutomaton:
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

    assert (len(raw.G) == len(raw.mode_inv)), f"len(G) = {len(raw.G)}  len(mode_inv) = {len(raw.mode_inv)}"

    vars = raw.input_variables + raw.output_variables

    modes = [ build_Mode (id, vars, raw.output_variables, inv, odes) for (id, (inv, odes)) in enumerate(zip(mode_inv, raw.G)) ]

    transs : list[Transition] = [ build_Transition(id, vars, raw.output_variables, trans) for (id, trans) in enumerate(raw.transitions) ]

    return HybridAutomaton(init_mode= raw.initial_location,
                           modes= modes,
                           transitions= transs,
                           input_variables= raw.input_variables,
                           output_variables = raw.output_variables)
