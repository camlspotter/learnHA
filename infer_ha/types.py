import numpy as np
from numpy.typing import NDArray
from pydantic.dataclasses import dataclass

MATRIX = NDArray[np.float64]

Assignment = tuple[MATRIX, # coeffs, 2d
                   MATRIX] # intercepts 1d

# Like range but in integers inclusive
@dataclass
class Span:
    start : int
    end : int # included

    def stop(self) -> int:
        return self.end + 1

    def range(self) -> range:
        return range(self.start, self.end+1)

# Triplet of type [pre_end_posi, end_posi, start_posi],
# where pre_end_posi and end_posi positions are on the source location,
# and start_posi is the position of the starting point of a segment in
# the destination location.
@dataclass
class ConnectionPoint:
    src_end : int
    dst_start : int

@dataclass
class Connection:
    src_mode : int
    dst_mode : int
    links : list[ConnectionPoint]
