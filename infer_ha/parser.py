import pyparsing as pp
from infer_ha.astdsl import parse_expr, Variable, Expr, Tuple

variable = pp.Word(pp.alphas, pp.alphanums+"_")

def delimited_list(p, delim):
    return pp.Optional(pp.DelimitedList(p, delim= delim))

def comma_separated_variables(s : str) -> list[str]:
    if s.strip() == "":
        return []
    else:
        e = parse_expr(s)
        def unvar(e : Expr):
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
