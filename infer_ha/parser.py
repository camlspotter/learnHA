import pyparsing as pp

variable = pp.Word(pp.alphas, pp.alphanums+"_")

def delimited_list(p, delim):
    return pp.Optional(pp.DelimitedList(p, delim= delim))
