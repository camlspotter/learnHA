from typing import Optional, Any, Union
from pydantic.dataclasses import dataclass
from typeguard import typechecked

@dataclass
class Continuous:
    pass

@dataclass
class Pool:
    values : list[float]

@dataclass
class Constant:
    value : float

VarType = Union[Continuous, Pool, Constant]
VarTypeTbl = dict[int, VarType] # list[tuple[int, str, Optional[VarType]]] 
