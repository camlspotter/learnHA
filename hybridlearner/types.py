import numpy as np
from numpy.typing import NDArray
from pydantic.dataclasses import dataclass

MATRIX = NDArray[np.float64]

# Like range but in integers inclusive
@dataclass
class Span:
    start : int
    end : int # included

    def stop(self) -> int:
        return self.end + 1

    def range(self) -> range:
        return range(self.start, self.end+1)

