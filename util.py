from contextlib import contextmanager
import os, sys
import torch

@contextmanager
def suppress_stdout():
    """ From: https://stackoverflow.com/a/25061573 """
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:  
            yield
        finally:
            sys.stdout = old_stdout
