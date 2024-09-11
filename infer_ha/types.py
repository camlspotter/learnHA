import numpy as np
from numpy.typing import NDArray

MATRIX = NDArray[np.float64]

Assignment = tuple[MATRIX, # coeffs, 2d
                   MATRIX] # intercepts 1d

