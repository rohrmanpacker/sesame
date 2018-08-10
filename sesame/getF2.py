import warnings
from . import getF as f


def getF(sys, v, efn, efp, veq):
    warnings.warn("Method will be removed in next version", FutureWarning)
    return f.getF(sys,v,efn,efp,veq)
