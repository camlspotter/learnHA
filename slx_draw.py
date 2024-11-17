#!/usr/bin/env pipenv-shebang

import argparse
import os.path
from hybridlearner.matlab import engine_with_display
from pydantic.dataclasses import dataclass
from typeguard import typechecked


@dataclass
class Options:
    files: list[str]


@typechecked
def get_options() -> Options:
    parser = argparse.ArgumentParser(description="Draw SLX models in SVG")
    parser.add_argument('files', help='SLX model files', type=str, nargs='+')
    return Options(**vars(parser.parse_args()))


opts = get_options()

for fn in opts.files:
    (body, ext) = os.path.splitext(fn)
    out = body + ".svg"
    print(f'Draw {fn} to {out}...')
    engine_with_display.eval0(f"""\
    mdl = load_system('{fn}');
    mdlname = get_param(mdl, 'Name');
    print(['-s' mdlname], '-dsvg', '{out}');
    """)
