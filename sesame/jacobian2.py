# Copyright 2017 University of Maryland.
#
# This file is part of Sesame. It is subject to the license terms in the file
# LICENSE.rst found in the top-level directory of this distribution.

import warnings
from . import jacobian as j


def getJ(sys, v, efn, efp):
    warnings.warn("Method will be removed in next version", FutureWarning)
    return j.getJ(sys, v, efn, efp)
