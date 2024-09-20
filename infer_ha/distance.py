from fastdtw import fastdtw     #https://pypi.org/project/fastdtw/
from infer_ha.types import MATRIX

def dtw_distance(a : MATRIX,  # output variable timeseries A, 2D  a[time][var]
                 b : MATRIX   # output variable timeseries B, 2D  b[time][var]
                 ) -> float:

    radius=5
    dist= None # p-norm
    return fastdtw(a, b, radius, dist)[0] # not intersted in the path
