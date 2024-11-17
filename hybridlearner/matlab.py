from typing import Optional, Any
import matlab.engine
from matlab import double

MatlabEngine = Any


class Matlab:
    no_display: bool

    def __init__(self, no_display: bool = True) -> None:
        self.no_display = no_display

    e: Optional[MatlabEngine] = None

    def engine(self) -> MatlabEngine:
        if self.e is None:
            print("Starting MATLAB engine")
            if self.no_display:
                self.e = matlab.engine.start_matlab('-nodisplay')
            else:
                self.e = matlab.engine.start_matlab('')
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

    def eval(self, s: str, nargout: int) -> Any:
        _eng = self.engine()
        return _eng.eval(s, nargout=nargout)

    def eval0(self, s: str) -> None:
        """
        Evaluate MATLAB code returning nothing.
        """
        self.eval(s, 0)

    def eval1(self, s: str) -> Any:
        """
        Evaluate MATLAB code returning a value.
        """
        return self.eval(s, 1)

    def setvar(self, var: str, val: Any) -> None:
        _eng = self.engine()
        # print(f"Set MATLAB variable {var}")
        _eng.workspace[var] = val

    def getvar(self, var: str) -> Any:
        _eng = self.engine()
        # print(f"Get MATLAB variable {var}")
        return _eng.workspace[var]


engine = Matlab()

engine_with_display = Matlab(no_display=False)
