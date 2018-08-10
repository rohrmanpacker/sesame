from . import getFandJ_eq as FandJ
import warnings

def getFandJ_eq(sys, v, periodic_bcs):
    warnings.warn("Method will be removed in next version", FutureWarning)
    return FandJ.getFandJ_eq(sys,v,periodic_bcs)