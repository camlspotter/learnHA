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

@dataclass
class ConnectionPoint:
    src_end : int
    dst_start : int

@dataclass
class Connection:
    src_mode : int
    dst_mode : int
    links : list[ConnectionPoint]
