#!/usr/bin/env pipenv-shebang

import argparse
from hybridlearner.slx.info import get_IOports
from pydantic.dataclasses import dataclass
from typeguard import typechecked


@dataclass
class Options:
    files: list[str]


@typechecked
def get_options() -> Options:
    parser = argparse.ArgumentParser(description="List SLX model port names")
    parser.add_argument('files', help='SLX model files', type=str, nargs='+')
    return Options(**vars(parser.parse_args()))


opts = get_options()

for fn in opts.files:
    print((fn, get_IOports(fn)))
