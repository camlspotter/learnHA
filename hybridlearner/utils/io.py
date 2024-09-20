import os
from io import TextIOWrapper

def open_for_write(path : str) -> TextIOWrapper:
    """
    Same as open(path, "w") but mkdir the directory if necessary
    """
    if os.path.exists(path):
        os.remove(path)
    dir = os.path.dirname(path)
    if dir != "":
        os.makedirs(dir, exist_ok=True)
    return open(path, "w")

    
