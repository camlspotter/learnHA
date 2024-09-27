import os
import argparse
from typing import Optional, Any
from pydantic.dataclasses import dataclass
from typeguard import typechecked
from hybridlearner.utils.argparse_bool import argparse_bool
from hybridlearner.inference.annotation import AnnotationDict, parse_annotation_dict
from hybridlearner.inference.clustering import options as clustering_options
import hybridlearner.parser


@dataclass
class Options(clustering_options.Options):
    output_directory: str
    ode_degree: int  # default=1
    guard_degree: int  # default=1
    segmentation_error_tol: float  # default=0.01
    segmentation_fine_error_tol: float  # default=0.01
    annotations: AnnotationDict
    is_invariant: bool  # default=True
    filter_last_segment: bool  # default=False


def add_argument_group(parser: argparse.ArgumentParser) -> None:
    clustering_options.add_argument_group(parser)

    group = parser.add_argument_group('Inference options', 'Inference options')

    group.add_argument(
        '--output-directory',
        type=os.path.abspath,
        help='output directory',
        required=True,
    )
    group.add_argument(
        '-d',
        '--ode-degree',
        help='Degree of polynomial in ODE. Set to 1 by default',
        type=int,
        default=1,
        required=False,
    )
    group.add_argument(
        '-b',
        '--guard-degree',
        help='Degree of polynomial inequalities for Guards. Set to 1 by default',
        type=int,
        default=1,
        required=False,
    )
    group.add_argument(
        '--annotations',
        help='Variable annotations',
        type=parse_annotation_dict,
        default={},
        required=False,
    )
    group.add_argument(
        '--is-invariant',
        help='Values True (default) computes invariant and False disables computation',
        type=argparse_bool,  # Beware! argparse's type=bool is broken
        default=True,
        required=False,
    )

    group.add_argument(
        '--filter-last-segment',
        help='True to enable and False to disable (default) filtering out the last segment from a trajectory during segmentation',
        type=argparse_bool,  # Beware! argparse's type=bool is broken
        default=False,
        required=False,
    )
