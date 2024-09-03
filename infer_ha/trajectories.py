import numpy as np
from numpy.typing import NDArray
from pydantic.dataclasses import dataclass
from pydantic import ConfigDict

Trajectory = tuple[ list[np.ndarray], list[np.ndarray] ]

# config is required to carry np.ndarray in pydantic's dataclass
@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class Trajectories:
    trajectories : list[ Trajectory ]
    stepsize : float
    dimension : int
