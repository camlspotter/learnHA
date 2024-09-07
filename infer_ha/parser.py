import pyparsing as pp
from infer_ha.astdsl import parse_expr, Variable, Expr, Tuple
from infer_ha.range import Range

variable = pp.Word(pp.alphas, pp.alphanums+"_")

def delimited_list(p : pp.ParserElement, delim : str) -> pp.ParserElement:
    return pp.Optional(pp.DelimitedList(p, delim= delim))

def comma_separated_variables(s : str) -> list[str]:
    if s.strip() == "":
        return []
    else:
        e = parse_expr(s)
        def unvar(e : Expr) -> str:
            match e:
                case Variable(v):
                    return v
                case _:
                    assert False, f"Variable expected: {e}"
        match e:
            case Variable(v):
                return [v]
            case Tuple(es):
                return [ unvar(e) for e in es ]
            case _:
                assert False, f"Comma separated list of variables expected: {s}"

inequality = \
    variable + pp.one_of("<= >=") + pp.common.number \
    ^ pp.common.number + pp.one_of("<= >=") + variable

def check_inequality(tkns) -> None:
    match tkns:
        case [[a, b, c]]:
            if isinstance(a, (int, float)) and isinstance(c, str):
                match b:
                    case ">=":
                       b = "<="
                    case "<=":
                       b = ">="
                    case _:
                       assert False
                return [[((c, b), a)]]
            if isinstance(c, (int, float)) and isinstance(a, str):
                return [[((a, b), c)]]
            assert False, "Invalid inequality: " + tkns
        case _:
            assert False

def check_and(tkns):
    match tkns:
        case [[a, "&&", c]]:
            return [a + c]
        case _:
            assert False
        
invariant = pp.infix_notation(
    pp.common.number ^ variable,
    [ (pp.one_of("<= >="), 2, pp.opAssoc.RIGHT, check_inequality),

      (pp.one_of("&&"), 2, pp.opAssoc.RIGHT, check_and)
     ])

def check_invariant(inv):
    match inv:
        case [ineqs]:
            invariant : Invariant = {}
            variables = { x for ((x, _), _) in ineqs }
            d = dict(ineqs)
            for x in variables:
                try:
                    min = d[(x, ">=")]
                    max = d[(x, "<=")]
                except KeyError:
                    assert False, f"Invalid range specification for {x}: missing one of range limits: {ineqs}"
                try:
                    invariant[x] = Range(min, max)
                except:
                    assert False, f"Invalid range specification for {x}: Range({min}, {max})"
            return invariant
        case _:
            assert False
