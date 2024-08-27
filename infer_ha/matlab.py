from typing import Optional, Any
import matlab.engine as meng

MatlabEngine = Any

class Mlab():
    engine : Optional[MatlabEngine] = None

    def eng(self) -> MatlabEngine:
        if self.engine is None:
            print("Starting MATLAB engine")
            self.engine = meng.start_matlab()
            print("Started MATLAB engine")
        if self.engine is None:
            assert False
        else:
            return self.engine

    def run(self, fn : str) -> None:
        _eng = self.eng()
        print(f"Executing MATLAB script {fn}")
        _eng.run(fn, nargout = 0) # nargout=0 is required since x.m returns nothing.
        print(f"Executed MATLAB script {fn}")

matlab = Mlab()
