from typing import Optional, Any
import matlab.engine
from matlab import double

MatlabEngine = Any


class Matlab:
    e: Optional[MatlabEngine] = None

    def engine(self) -> MatlabEngine:
        if self.e is None:
            print("Starting MATLAB engine")
            self.e = matlab.engine.start_matlab()
            print("Started MATLAB engine")
        if self.e is None:
            assert False
        else:
            return self.e

    def run(self, fn: str) -> None:
        _eng = self.engine()
        print(f"Executing MATLAB script {fn}")
        _eng.run(fn, nargout=0)  # nargout=0 is required since x.m returns nothing.
        print(f"Executed MATLAB script {fn}")

    def setvar(self, var: str, val: Any) -> None:
        _eng = self.engine()
        _eng.workspace[var] = val

    def getvar(self, var: str) -> Any:
        _eng = self.engine()
        return _eng.eval(var, nargout=1)


engine = Matlab()
