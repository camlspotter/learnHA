import argparse
from pydantic.dataclasses import dataclass

from hybridlearner.segmentation import ClusteringMethod


@dataclass
class Options:
    clustering_method: ClusteringMethod  # dtw/dbscan/piecelinear

    # For DBScan and Piecelinear
    modes: int  # default=1

    segmentation_error_tol: float  # default=0.01

    # exists but not used
    segmentation_fine_error_tol: float  # default=0.01

    lmm_step_size: int  # choices=[2, 3, 4, 5, 6], default=5

    # DTW options
    threshold_correlation: float
    threshold_distance: float
    ode_speedup: int

    # DBScan options, currently not used
    dbscan_eps_dist: float  # default=0.01
    dbscan_min_samples: int  # default=2


def add_argument_group(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group('Clustering options', 'Clustering options')

    group.add_argument(
        '-c',
        '--clustering-method',
        help='Clustering Algorithm. Options are: dtw (default), dbscan (disabled), piecelinear (disabled)',
        type=ClusteringMethod,
        default=ClusteringMethod.DTW,
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
        '--lmm-step-size',
        help='Options are: 2/3/4/5/6. Higher values computes more accurate derivatives. 5 is set default',
        type=int,
        choices=[2, 3, 4, 5, 6],
        default=5,
        required=False,
    )

    group = parser.add_argument_group(
        'DTW clustering options', 'DTW clustering options'
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
        '--ode-speedup',
        help='Maximum number of segments to include for ODE computation. Set to 10 by default',
        type=int,
        default=10,
        required=False,
    )

    group = parser.add_argument_group(
        'DBScan clustering options', 'DBScan clustering options'
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
