# Copyright 2017 University of Maryland.
#
# This file is part of Sesame. It is subject to the license terms in the file
# LICENSE.rst found in the top-level directory of this distribution.

import numpy as np
from .observables import *
from .defects import defectsF
import warnings
from . import getF as f


def getF(sys, v, efn, efp, veq):
    warnings.warn("Method will be removed in next version", FutureWarning)
    return f.getF(sys,v,efn,efp,veq)
