# Fix of type=bool of argparse
# type=bool is NOT supported by argparse, but it is NOT rejected and behaves strangely. See:
#   https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
def argparse_bool(x: str) -> bool:
    match x.lower():
        case "true":
            return True
        case "false":
            return False
        case _:
            assert False, "invalid boolean value"
