import numpy as np
from numpy.typing import NDArray
from pydantic.dataclasses import dataclass

MATRIX = NDArray[np.float64]

Assignment = tuple[MATRIX, # coeffs, 2d
                   MATRIX] # intercepts 1d

# SegmentedTrajectories: the required position data structures.
# (start_segment_pos, pre_end_segment_pos, end_segment_pos).
# This is used later in learning  transition's guard and assignment equations.
@dataclass
class SegmentedTrajectory:
    start : int
    end : int

# Triplet of type [pre_end_posi, end_posi, start_posi],
# where pre_end_posi and end_posi positions are on the source location,
# and start_posi is the position of the starting point of a segment in
# the destination location.
@dataclass
class Connection:
    src_end : int
    dst_start : int
