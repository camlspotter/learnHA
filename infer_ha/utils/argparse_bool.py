# Fix of type=bool of argparse
def argparse_bool(x : str) -> bool:
    match x.lower():
        case "true":
            return True
        case "false":
            return False
        case _:
            assert False, "invalid boolean value"
