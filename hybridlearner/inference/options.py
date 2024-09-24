import os
from enum import Enum
import argparse
from typing import Optional, Any
from pydantic.dataclasses import dataclass
from typeguard import typechecked
from hybridlearner.utils.argparse_bool import argparse_bool
from hybridlearner.inference.annotation import AnnotationDict, parse_annotation_dict
import hybridlearner.parser


# @dataclass # We cannot use @dataclass with Enum: @dataclass overrides __eq__
class ClusteringMethod(Enum):
    DTW = "dtw"
    DBSCAN = "dbscan"
    PIECELINEAR = "piecelinear"


@dataclass
class Options:
    output_directory: str
    ode_degree: int  # default=1
    modes: int  # default=1
    guard_degree: int  # default=1
    segmentation_error_tol: float  # default=0.01
    segmentation_fine_error_tol: float  # default=0.01
    threshold_distance: float  # default=0.1
    threshold_correlation: float  # default=0.8
    dbscan_eps_dist: float  # default=0.01
    dbscan_min_samples: int  # default=2
    annotations: AnnotationDict
    ode_speedup: int  # , default=10
    is_invariant: bool  # default=True
    filter_last_segment: bool  # default=False
    lmm_step_size: int  # choices=[2, 3, 4, 5, 6], default=5
    clustering_method: ClusteringMethod  # dtw/dbscan/piecelinear


def add_argument_group(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group('Inference options', 'Inference options')

    group.add_argument(
        '--output-directory',
        type=os.path.abspath,
        help='output directory',
        required=True,
    )
    group.add_argument(
        '-c',
        '--clustering-method',
        help='Clustering Algorithm. Options are: dtw (default), dbscan, piecelinear',
        type=ClusteringMethod,
        default=ClusteringMethod.DTW,
        required=False,
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
        '-m',
        '--modes',
        help='Number of modes. Used only in piecelinear clustering algorithm. Set to 1 by default',
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
        '--segmentation-error-tol',
        help='Maximal relative-difference (FwdBwd) error tolerated during segmentation. Set to 0.01 by default',
        type=float,
        default=0.01,
        required=False,
    )
    group.add_argument(
        '--segmentation-fine-error-tol',
        help='Maximal relative-difference (Bwd) fine-error tolerated during segmentation. Set to 0.01 by default',
        type=float,
        default=0.01,
        required=False,
    )
    group.add_argument(
        '--threshold-distance',
        help='Maximal threshold for distance in DTW clustering algorithm. Set to 0.1 by default',
        type=float,
        default=0.1,
        required=False,
    )
    group.add_argument(
        '--threshold-correlation',
        help='Maximal threshold for correlation value in DTW clustering algorithm. Set to 0.8 by default',
        type=float,
        default=0.8,
        required=False,
    )
    group.add_argument(
        '--dbscan-eps-dist',
        help='Maximal threshold for distance in DBSCAN clustering algorithm. Set to 0.01 by default',
        type=float,
        default=0.01,
        required=False,
    )
    group.add_argument(
        '--dbscan-min-samples',
        help='Maximal threshold for min-samples in DBSCAN clustering algorithm. Set to 2 by default',
        type=int,
        default=2,
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
        '--ode-speedup',
        help='Maximum number of segments to include for ODE computation. Set to 10 by default',
        type=int,
        default=10,
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
    group.add_argument(
        '--lmm-step-size',
        help='Options are: 2/3/4/5/6. Higher values computes more accurate derivatives. 5 is set default',
        type=int,
        choices=[2, 3, 4, 5, 6],
        default=5,
        required=False,
    )
