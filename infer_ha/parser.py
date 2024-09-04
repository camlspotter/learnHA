import pyparsing as pp
from infer_ha.astdsl import parse_expr, Variable, Expr, List

variable = pp.Word(pp.alphas, pp.alphanums+"_")

def delimited_list(p, delim):
    return pp.Optional(pp.DelimitedList(p, delim= delim))

def comma_separated_varaibles(s : str) -> list[str]:
    e = parse_expr(s)
    match e:
        case List(es):
            def unvar(e : Expr):
                match e:
                    case Variable(v):
                        return v
                    case _:
                        assert False, f"Variable expected: {e}"
            return [ unvar(e) for e in es ]
        case _:
            assert False, f"Comma separated list of variables expected: {s}"
