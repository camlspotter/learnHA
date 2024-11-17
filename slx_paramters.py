#!/usr/bin/env pipenv-shebang

import argparse
from hybridlearner.slx.info import get_all_params
from pydantic.dataclasses import dataclass
from typeguard import typechecked


@dataclass
class Options:
    files: list[str]


@typechecked
def get_options() -> Options:
    parser = argparse.ArgumentParser(description="List SLX model properties")
    parser.add_argument('files', help='SLX model files', type=str, nargs='+')
    return Options(**vars(parser.parse_args()))


opts = get_options()

for fn in opts.files:
    print(fn)
    for k, v in get_all_params(fn).items():
        print(f'''{k} : {v['Type']}''')
        print(f'''  Attrs: {", ".join(v['Attributes'])}''')
        if v['Enum'] != []:
            print(f'''  Enums: {" | ".join(v['Enum'])}''')
