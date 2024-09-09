import csv
import numpy as np
from numpy.typing import NDArray
from typing import Optional, TypeVar, Callable, Iterator
from pydantic.dataclasses import dataclass
from pydantic import ConfigDict

Trajectory = tuple[ list[np.ndarray], list[np.ndarray] ]

# config is required to carry np.ndarray in pydantic's dataclass
@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class Trajectories:
    trajectories : list[ Trajectory ]
    stepsize : float

A = TypeVar('A')

def find_iterator(pred: Callable[[A], bool], xs : Iterator[A]) -> Optional[A]:
    def filter(i : Iterator[A]) -> Iterator[A]:
        for x in i:
            if pred(x):
                yield x
    return next(filter(xs), None)

def parse_trajectories(path : str) -> Trajectories:
    '''
    Load trajectories from a tsv file.
    
    - No check of stepsize uniqueness
    '''
    with open(path, 'r') as ic:
        reader = csv.reader(ic, delimiter='\t')

        tvs_list : list[tuple[float, list[float]]] = \
            list(map(lambda ss: (float(ss[0]), [float(s) for s in ss[1:]]), reader))

        zero_poses : list[int] = [ i for (i, (t,_vs)) in enumerate(tvs_list) if t == 0.0 ]
        ranges : list[tuple[int,int]] = \
            [ (zero_poses[i], zero_poses[i+1] if i + 1 < len(zero_poses) else len(tvs_list))
              for (i,_) in enumerate(zero_poses) ]

        tvs_group : list[list[tuple[float, list[float]]]] = [ tvs_list[start:end] for (start, end) in ranges ]

        # XXX Why singleton lists!?
        trajectories : list[Trajectory] = [ ( [np.array([t for (t, _) in tvs])],
                                              [np.array([vs for (_, vs) in tvs])] )
                                            for tvs in tvs_group ]

        stepsize = tvs_group[0][1][0] - tvs_group[0][0][0] # diff of the first 2 times in the first tvs

        return Trajectories(trajectories, stepsize)
