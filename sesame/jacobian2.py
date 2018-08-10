from . import getJ as j
import warnings


def getJ(sys, v, efn, efp, periodic = True):
    warnings.warn("Method will be removed in next version", FutureWarning)
    j.getJ(sys,v,efn,efp,periodic=True)