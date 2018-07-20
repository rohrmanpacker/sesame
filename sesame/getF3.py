# Copyright 2017 University of Maryland.
#
# This file is part of Sesame. It is subject to the license terms in the file
# LICENSE.rst found in the top-level directory of this distribution.

import numpy as np
from .observables import *
from .defects import defectsF

def getF(sys, v, efn, efp, veq):
    ###########################################################################
    #               organization of the right hand side vector                #
    ###########################################################################
    # A site with coordinates (i,j,k) corresponds to a site number s as follows:
    # k = s//(Nx*Ny)
    # j = s - s//Nx
    # i = s - j*Nx - k*Nx*Ny
    #
    # Rows for (efn_s, efp_s, v_s)
    # ----------------------------
    # fn_row = 3*s
    # fp_row = 3*s+1
    # fv_row = 3*s+2

    Nx, Ny, Nz = sys.xpts.shape[0], sys.ypts.shape[0], sys.zpts.shape[0]
    dx, dy, dz = sys.dx, sys.dy, sys.dz

    # right hand side vector
    global vec
    vec = np.zeros((3*Nx*Ny*Nz,))
    def update(fn, fp, fv, sites):
        global vec
        vec[3*sites] = fn
        vec[3*sites+1] = fp
        vec[3*sites+2] = fv


    ###########################################################################
    #                     For all sites in the system                         #
    ###########################################################################
    # carrier densities
    n = sys.Nc * np.exp(+sys.bl + efn + v)
    p = sys.Nv * np.exp(-sys.Eg - sys.bl - efp - v)

    # equilibrium carrier densities
    n_eq = sys.Nc * np.exp(+sys.bl + veq)
    p_eq = sys.Nv * np.exp(-sys.Eg - sys.bl - veq)

    # bulk charges
    rho = sys.rho - n + p

    # recombination rates
    r = get_bulk_rr(sys, n, p)

    # charge defects
    if len(sys.defects_list) != 0:
        defectsF(sys, sys.defects_list, n, p, rho, r)

    # charge devided by epsilon
    rho = rho / sys.epsilon  # TODO why????

    # reshape the array as array[y-indices, x-indices]
    _sites = np.arange(Nx*Ny*Nz, dtype=int).reshape(Nz, Ny, Nx)

    #
    def currents(sys, efn, efp, v, smNN_s, smN_s, s_spN, s_spNN, dx, dxm1, dy, dym1, dz, dzm1, sites):
        jnx_s, jnx_sm1, jny_s, jny_smN, jnz_s, jnz_smNN = 0, 0, 0, 0, 0, 0
        jpx_s, jpx_sm1, jpy_s, jpy_smN, jpz_s, jpz_smNN = 0, 0, 0, 0, 0, 0

        if dx.all() != 0:
            jnx_s = get_jn(sys, efn, v, sites, sites + 1, dx)
            jpx_s = get_jp(sys, efp, v, sites, sites + 1, dx)

            jnx_sm1 = get_jn(sys, efn, v, sites - 1, sites, dxm1)
            jpx_sm1 = get_jp(sys, efp, v, sites - 1, sites, dxm1)

            jny_s = get_jn(sys, efn, v, s_spN[0], s_spN[1], dy)
            jpy_s = get_jp(sys, efp, v, s_spN[0], s_spN[1], dy)

            jny_smN = get_jn(sys, efn, v, smN_s[0], smN_s[1], dym1)
            jpy_smN = get_jp(sys, efp, v, smN_s[0], smN_s[1], dym1)

            jnz_s = get_jn(sys, efn, v, s_spNN[0], s_spNN[1], dz)
            jpz_s = get_jp(sys, efp, v, s_spNN[0], s_spNN[1], dz)

            jnz_smNN = get_jn(sys, efn, v, smNN_s[0], smNN_s[1], dzm1)
            jpz_smNN = get_jp(sys, efp, v, smNN_s[0], smNN_s[1], dzm1)

        return jnx_s, jnx_sm1, jny_s, jny_smN, jnz_s, jnz_smNN, jpx_s, jpx_sm1, jpy_s, jpy_smN, jpz_s, jpz_smNN

    # Drift diffusion Poisson equations that determine fn, fp, fv
    def ddp(sys, efn, efp, v, smNN_s, smN_s, s_spN, s_spNN,\
           dx, dxm1, dy, dym1, dz, dzm1, sites):


        # lattice distances
        dxbar = (dx + dxm1) / 2.
        dybar = (dy + dym1) / 2.
        dzbar = (dz + dzm1) / 2.

        # compute currents
        jnx_s, jnx_sm1, jny_s, jny_smN, jnz_s, jnz_smNN,\
        jpx_s, jpx_sm1, jpy_s, jpy_smN, jpz_s, jpz_smNN = \
        currents(sys, efn, efp, v, smNN_s, smN_s, s_spN, s_spNN,\
                 dx, dxm1, dy, dym1, dz, dzm1, sites)

        # drift diffusion
        u = sys.g[sites] - r[sites]
        fn = (jnx_s - jnx_sm1) / dxbar + (jny_s - jny_smN) / dybar \
           + (jnz_s - jnz_smNN) / dzbar + u
        fp = (jpx_s - jpx_sm1) / dxbar + (jpy_s - jpy_smN) / dybar \
           + (jpz_s - jpz_smNN) / dzbar - u

        # Poisson
        dv_sm1, dv_sp1, dv_smN, dv_spN, dv_smNN, dv_spNN = 0, 0, 0, 0, 0, 0
        v_s = v[sites]
        dv_sp1 = (v[sites+1] - v_s) / dx
        dv_sm1 = (v_s - v[sites-1]) / dxm1
        dv_spN = (v[s_spN[1]] - v_s) / dy
        dv_smN = (v_s - v[smN_s[0]]) / dym1
        dv_spNN = (v[s_spNN[1]] - v_s) / dz
        dv_smNN = (v_s - v[smNN_s[0]]) / dzm1

        fv = (dv_sm1 - dv_sp1) / dxbar + (dv_smN - dv_spN) / dybar\
           + (dv_smNN - dv_spNN) / dzbar - rho[sites]

        # update vector
        update(fn, fp, fv, sites)

    def right_bc(sys, efn, efp, v, smNN_s, smN_s, s_spN, s_spNN, dy,\
                 dym1, dz, dzm1, sites):
    # We implement the right contact boundary conditions here.
        # lattice distances and sites
        dx = np.array([0])
        dxm1 = sys.dx[-1]
        dxbar = (dx + dxm1) / 2.
        dybar = (dy + dym1) / 2.
        dzbar = (dz + dzm1) / 2.
        sm1_s = [sites - 1, sites]

        # compute currents
        jnx_s, jnx_sm1, jny_s, jny_smN, jnz_s, jnz_smNN, jpx_s, jpx_sm1, jpy_s, jpy_smN, jpz_s, jpz_smNN = \
            currents(sys, efn, efp, v, smNN_s, smN_s, s_spN, s_spNN, dx, dxm1, dy, dym1, dz, dzm1, sites)

        jnx_s = jnx_sm1 + dxbar * (r[sites] - sys.g[sites] - (jny_s - jny_smN)/dybar\
                                   - (jnz_s - jnz_smNN)/dzbar)
        jpx_s = jpx_sm1 + dxbar * (sys.g[sites] - r[sites] - (jpy_s - jpy_smN)/dybar\
                                   - (jpz_s - jpz_smNN)/dzbar)

        # b_n, b_p and b_v values
        bn = jnx_s + sys.Scn[1] * (n[sites] - n_eq[sites])
        bp = jpx_s - sys.Scp[1] * (p[sites] - p_eq[sites])
        bv = 0 # Dirichlet BC
        # update right hand side vector
        update(bn, bp, bv, sites)



    ###########################################################################
    #       inside the system: 0 < i < Nx-1, 0 < j < Ny-1, 0 < k < Nz-1       #
    ###########################################################################
    # We compute fn, fp, fv  on the inner part of the system. All the edges
    # containing boundary conditions.

    # list of the sites inside the system
    sites = _sites[1:Nz-1, 1:Ny-1, 1:Nx-1].flatten()

    # lattice distances
    dx = np.tile(sys.dx[1:], (Ny-2)*(Nz-2))
    dy = np.repeat(sys.dy[1:], (Nx-2)*(Nz-2))
    dz = np.repeat(sys.dz[1:], (Nx-2)*(Ny-2))
    dxm1 = np.tile(sys.dx[:-1], (Ny-2)*(Nz-2))
    dym1 = np.repeat(sys.dy[:-1], (Nx-2)*(Nz-2))
    dzm1 = np.repeat(sys.dz[:-1], (Nx-2)*(Ny-2))

    # gather all relevant pairs of sites to compute the currents
    smNN_s = [sites - Nx*Ny, sites]
    smN_s = [sites - Nx, sites]
    s_spN = [sites, sites + Nx]
    s_spNN = [sites, sites + Nx*Ny]

    # compute fn, fp, fv
    ddp(sys, efn, efp, v, smNN_s, smN_s, s_spN, s_spNN, dx, dxm1, dy, dym1, dz, dzm1, sites)

    ###########################################################################
    #        left boundary: i = 0, 0 <= j <= Ny-1, 0 <= k <= Nz-1             #
    ###########################################################################
    # list of the sites on the left side
    sites = _sites[:, :, 0].flatten()

    # compute the currents
    jnx = get_jn(sys, efn, v, sites, sites + 1, sys.dx[0])
    jpx = get_jp(sys, efp, v, sites, sites + 1, sys.dx[0])

    # compute an, ap, av
    an = jnx - sys.Scn[0] * (n[sites] - n_eq[sites])
    ap = jpx + sys.Scp[0] * (p[sites] - p_eq[sites])
    av = 0 # to ensure Dirichlet BCs

    update(an, ap, av, sites)

    ###########################################################################
    #                            right boundaries                             #
    ###########################################################################


    ###########################################################################
    #         right boundary: i = Nx-1, 0 < j < Ny-1, 0 < k < Nz-1            #
    ###########################################################################
    # list of the sites on the right side
    sites = _sites[1:Nz-1, 1:Ny-1, Nx-1].flatten()

    # lattice distances
    dy = np.repeat(sys.dy[1:], Nz-2)
    dym1 = np.repeat(sys.dy[:-1], Nz-2)
    dz = np.repeat(sys.dz[1:], Ny-2)
    dzm1 = np.repeat(sys.dz[:-1], Ny-2)

    # sites for the currents
    smNN_s = [sites - Nx*Ny, sites]
    smN_s = [sites - Nx, sites]
    s_spN = [sites, sites + Nx]
    s_spNN = [sites, sites + Nx*Ny]

    # compute the BC and update the right hand side vector
    right_bc(sys, efn, efp, v, smNN_s, smN_s, s_spN, s_spNN, dy, dym1, dz, dzm1, sites)

    ###########################################################################
    #           right boundary: i = Nx-1, j = Ny-1, 0 < k < Nz-1              #
    ###########################################################################
    # list of the sites on the right side
    sites = _sites[1:Nz-1, Ny-1, Nx-1].flatten()

    # lattice distances
    dy = np.repeat((sys.dy[0] + sys.dy[-1]) / 2., Nz-2)
    dym1 = np.repeat(sys.dy[-1], Nz-2) 
    dz = sys.dz[1:]
    dzm1 = sys.dz[:-1]

    # compute the currents
    smNN_s = [sites - Nx*Ny, sites]
    smN_s = [sites - Nx, sites]
    s_spN = [sites, sites - Nx*(Ny-1)]
    s_spNN = [sites, sites + Nx*Ny]

    # compute the BC and update the right hand side vector
    right_bc(sys, efn, efp, v, smNN_s, smN_s, s_spN, s_spNN, dy, dym1, dz, dzm1, sites)
 
    ###########################################################################
    #              right boundary: i = Nx-1, j = 0, 0 < k < Nz-1              #
    ###########################################################################
    # list of the sites on the right side
    sites = _sites[1:Nz-1, 0, Nx-1].flatten()

    # lattice distances
    dy = np.repeat(sys.dy[-1], Nz-2)
    dym1 =  np.repeat((sys.dy[0] + sys.dy[-1]) / 2., Nz-2)
    dz = sys.dz[1:]
    dzm1 = sys.dz[:-1]

    # compute the currents
    smNN_s = [sites - Nx*Ny, sites]
    smN_s = [sites + Nx*(Ny-1), sites]
    s_spN = [sites, sites + Nx]
    s_spNN = [sites, sites + Nx*Ny]

    # compute the BC and update the right hand side vector
    right_bc(sys, efn, efp, v, smNN_s, smN_s, s_spN, s_spNN, dy, dym1, dz, dzm1, sites)
 
    ###########################################################################
    #           right boundary: i = Nx-1, 0 < j < Ny-1, k = Nz-1              #
    ###########################################################################
    # list of the sites on the right side
    sites = _sites[Nz-1, 1:Ny-1, Nx-1].flatten()

    # lattice distances
    dy = sys.dy[1:]
    dym1 = sys.dy[:-1]
    dz = np.repeat((sys.dz[-1] + sys.dz[0])/2., Ny-2)
    dzm1 = np.repeat(sys.dz[-1], Ny-2)

    # compute the currents
    smNN_s = [sites - Nx*Ny, sites]
    smN_s = [sites - Nx, sites]
    s_spN = [sites, sites + Nx]
    s_spNN = [sites, sites - Nx*Ny*(Nz-1)]

    # compute the BC and update the right hand side vector
    right_bc(sys, efn, efp, v, smNN_s, smN_s, s_spN, s_spNN, dy, dym1, dz, dzm1, sites)

    ###########################################################################
    #              right boundary: i = Nx-1, 0 < j < Ny-1, k = 0              #
    ###########################################################################
    # list of the sites on the right side
    sites = _sites[0, 1:Ny-1, Nx-1].flatten()

    # lattice distances
    dy = sys.dy[1:]
    dym1 = sys.dy[:-1]
    dz = np.repeat(sys.dz[0], Ny-2)
    dzm1 = np.repeat((sys.dz[-1] + sys.dz[0])/2., Ny-2)

    # compute the currents
    smNN_s = [sites + Nx*Ny*(Nz-1), sites]
    smN_s = [sites - Nx, sites]
    s_spN = [sites, sites + Nx]
    s_spNN = [sites, sites + Nx*Ny]

    # compute the BC and update the right hand side vector
    right_bc(sys, efn, efp, v, smNN_s, smN_s, s_spN, s_spNN, dy, dym1, dz, dzm1, sites)

    ###########################################################################
    #                  right boundary: i = Nx-1, j = Ny-1, k = 0              #
    ###########################################################################
    # list of the sites on the right side
    sites = _sites[0, Ny-1, Nx-1].flatten()

    # lattice distances
    dy = (sys.dy[0] + sys.dy[-1])/2.
    dym1 = sys.dy[-1]
    dz = sys.dz[0]
    dzm1 = (sys.dz[-1] + sys.dz[0])/2.

    # compute the currents
    smNN_s = [sites + Nx*Ny*(Nz-1), sites]
    smN_s = [sites - Nx, sites]
    s_spN = [sites, sites - Nx*(Ny-1)]
    s_spNN = [sites, sites + Nx*Ny]

    # compute the BC and update the right hand side vector
    right_bc(sys, efn, efp, v, smNN_s, smN_s, s_spN, s_spNN, dy, dym1, dz, dzm1, sites)

    ###########################################################################
    #                  right boundary: i = Nx-1, j = Ny-1, k = Nz-1           #
    ###########################################################################
    # list of the sites on the right side
    sites = _sites[Nz-1, Ny-1, Nx-1].flatten()

    # lattice distances
    dy = (sys.dy[0] + sys.dy[-1])/2.
    dym1 = sys.dy[-1]
    dz = (sys.dz[-1] + sys.dz[0])/2.
    dzm1 = sys.dz[-1]

    # compute the currents
    smNN_s = [sites - Nx*Ny, sites]
    smN_s = [sites - Nx, sites]
    s_spN = [sites, sites - Nx*(Ny-1)]
    s_spNN = [sites, sites - Nx*Ny*(Nz-1)]

    # compute the BC and update the right hand side vector
    right_bc(sys, efn, efp, v, smNN_s, smN_s, s_spN, s_spNN, dy, dym1, dz, dzm1, sites)
             
    ###########################################################################
    #                  right boundary: i = Nx-1, j = 0, k = Nz-1              #
    ###########################################################################
    # list of the sites on the right side
    sites = _sites[Nz-1, 0, Nx-1].flatten()

    # lattice distances
    dy = sys.dy[0]
    dym1 = (sys.dy[0] + sys.dy[-1])/2.
    dz = (sys.dz[-1] + sys.dz[0])/2.
    dzm1 = sys.dz[-1]

    # compute the currents
    smNN_s = [sites - Nx*Ny, sites]
    smN_s = [sites + Nx*(Ny-1), sites]
    s_spN = [sites, sites + Nx]
    s_spNN = [sites, sites - Nx*Ny*(Nz-1)]

    # compute the BC and update the right hand side vector
    right_bc(sys, efn, efp, v, smNN_s, smN_s, s_spN, s_spNN, dy, dym1, dz, dzm1, sites)

    ###########################################################################
    #                  right boundary: i = Nx-1, j = 0, k = 0                 #
    ###########################################################################
    # list of the sites on the right side
    sites = _sites[0, 0, Nx-1].flatten()

    # lattice distances
    dy = sys.dy[0]
    dym1 = (sys.dy[0] + sys.dy[-1])/2.
    dz = sys.dz[0]
    dzm1 = (sys.dz[-1] + sys.dz[0])/2.

    # compute the currents
    smNN_s = [sites + Nx*Ny*(Nz-1), sites]
    smN_s = [sites + Nx*(Ny-1), sites]
    s_spN = [sites, sites + Nx]
    s_spNN = [sites, sites + Nx*Ny]

    # compute the BC and update the right hand side vector
    right_bc(sys, efn, efp, v, smNN_s, smN_s, s_spN, s_spNN, dy, dym1, dz, dzm1, sites)



    ###########################################################################
    #            faces between contacts: 0 < i < Nx-1, j or k fixed           #
    ###########################################################################
    # Here we focus on the faces between the contacts. There are 4 cases.

    ###########################################################################
    #              z-face top: 0 < i < Nx-1, 0 < j < Ny-1, k = Nz-1           #
    ###########################################################################
    # list of the sites
    sites = _sites[Nz-1, 1:Ny-1, 1:Nx-1].flatten()

    # lattice distances
    dx = np.tile(sys.dx[1:], Ny-2)
    dy = np.repeat(sys.dy[1:], Nx-2)
    dz = np.repeat((sys.dz[0] + sys.dz[-1])/2., (Nx-2)*(Ny-2))
    dxm1 = np.tile(sys.dx[:-1], Ny-2)
    dym1 = np.repeat(sys.dy[:-1], Nx-2)
    dzm1 = np.repeat(sys.dz[-1], (Nx-2)*(Ny-2))

    # gather all relevant pairs of sites to compute the currents
    smNN_s = [sites - Nx*Ny, sites]
    smN_s = [sites - Nx, sites]
    s_spN = [sites, sites + Nx]
    s_spNN = [sites, sites - Nx*Ny*(Nz-1)] # haha 420

    # compute fn, fp, fv and update vector
    ddp(sys, efn, efp, v, smNN_s, smN_s, s_spN, s_spNN, dx, dxm1, dy, dym1, dz, dzm1, sites)

    ###########################################################################
    #             z- face bottom: 0 < i < Nx-1, 0 < j < Ny-1, k = 0           #
    ###########################################################################
    # list of the sites
    sites = _sites[0, 1:Ny-1, 1:Nx-1].flatten()

    # lattice distances
    dx = np.tile(sys.dx[1:], Ny-2)
    dy = np.repeat(sys.dy[1:], Nx-2)
    dz = np.repeat(sys.dz[0], (Nx-2)*(Ny-2))
    dxm1 = np.tile(sys.dx[:-1], Ny-2)
    dym1 = np.repeat(sys.dy[:-1], Nx-2)
    dzm1 = np.repeat((sys.dz[0] + sys.dz[-1])/2., (Nx-2)*(Ny-2))

    # gather all relevant pairs of sites to compute the currents
    smNN_s = [sites + Nx*Ny*(Nz-1), sites]
    smN_s = [sites - Nx, sites]
    s_spN = [sites, sites + Nx]
    s_spNN = [sites, sites + Nx*Ny]

    # compute fn, fp, fv and update vector
    ddp(sys, efn, efp, v, smNN_s, smN_s, s_spN, s_spNN, dx, dxm1, dy, dym1, dz, dzm1, sites)

    ###########################################################################
    #            y-face front: 0 < i < Nx-1, j = 0, 0 < k < Nz-1              #
    ###########################################################################
    # list of the sites
    sites = _sites[1:Nz-1, 0, 1:Nx-1].flatten()

    # lattice distances
    dx = np.tile(sys.dx[1:], Nz-2)
    dy = np.repeat(sys.dy[0], (Nx-2)*(Nz-2))
    dz = np.repeat(sys.dz[1:], (Nx-2))
    dxm1 = np.tile(sys.dx[:-1], Nz-2)
    dym1 = np.repeat((sys.dy[0] + sys.dy[-1])/2., (Nx-2)*(Nz-2))
    dzm1 = np.repeat(sys.dz[:-1], Nx-2)

    # gather all relevant pairs of sites to compute the currents
    smNN_s = [sites - Nx*Ny, sites]
    smN_s = [sites + Nx*(Ny-1), sites]
    s_spN = [sites, sites + Nx]
    s_spNN = [sites, sites + Nx*Ny]

    # compute fn, fp, fv and update vector
    ddp(sys, efn, efp, v, smNN_s, smN_s, s_spN, s_spNN, dx, dxm1, dy, dym1, dz, dzm1, sites)

    ###########################################################################
    #            y-face back: 0 < i < Nx-1, j = Ny-1, 0 < k < Nz-1            #
    ###########################################################################
    # list of the sites
    sites = _sites[1:Nz-1, Ny-1, 1:Nx-1].flatten()

    # lattice distances
    dx = np.tile(sys.dx[1:], Nz-2)
    dy = np.repeat((sys.dy[0] + sys.dy[-1])/2., (Nx-2)*(Nz-2))
    dz = np.repeat(sys.dz[1:], Nx-2)
    dxm1 = np.tile(sys.dx[:-1], Nz-2)
    dym1 = np.repeat(sys.dy[0], (Nx-2)*(Nz-2))
    dzm1 = np.repeat(sys.dz[:-1], Nx-2)

    # gather all relevant pairs of sites to compute the currents
    smNN_s = [sites - Nx*Ny, sites]
    smN_s = [sites - Nx, sites]
    s_spN = [sites, sites - Nx*(Ny-1)]
    s_spNN = [sites, sites + Nx*Ny]

    # compute fn, fp, fv and update vector
    ddp(sys, efn, efp, v, smNN_s, smN_s, s_spN, s_spNN, dx, dxm1, dy, dym1, dz, dzm1, sites)


    ###########################################################################
    #           edges between contacts: 0 < i < Nx-1, j and k fixed           #
    ###########################################################################
    # Here we focus on the edges between the contacts. There are 4 cases.

    # lattice distances
    dx = sys.dx[1:]
    dxm1 = sys.dx[:-1]

    ###########################################################################
    #         edge z top // y back: 0 < i < Nx-1, j = Ny-1, k = Nz-1          #
    ###########################################################################
    # list of the sites
    sites = _sites[Nz-1, Ny-1, 1:Nx-1].flatten()

    # lattice distances
    dy = np.repeat((sys.dy[0] + sys.dy[-1])/2., Nx-2)
    dz = np.repeat((sys.dz[0] + sys.dz[-1])/2., Nx-2)
    dym1 = np.repeat(sys.dy[-1], Nx-2)
    dzm1 = np.repeat(sys.dz[-1], Nx-2)

    # gather all relevant pairs of sites to compute the currents
    smNN_s = [sites - Nx*Ny, sites]
    smN_s = [sites - Nx, sites]
    s_spN = [sites, sites - Nx*(Ny-1)]
    s_spNN = [sites, sites - Nx*Ny*(Nz-1)]

    # compute fn, fp, fv and update vector
    ddp(sys, efn, efp, v, smNN_s, smN_s, s_spN, s_spNN, dx, dxm1, dy, dym1, dz, dzm1, sites)

    ###########################################################################
    #           edge z top // y front: 0 < i < Nx-1, j = 0, k = Nz-1          #
    ###########################################################################
    # list of the sites
    sites = _sites[Nz-1, 0, 1:Nx-1].flatten()

    # lattice distances
    dy = np.repeat(sys.dy[0], Nx-2)
    dz = np.repeat((sys.dz[0] + sys.dz[-1])/2., Nx-2)
    dym1 = np.repeat((sys.dy[0] + sys.dy[-1])/2., Nx-2)
    dzm1 = np.repeat(sys.dz[-1], Nx-2)

    # gather all relevant pairs of sites to compute the currents
    smNN_s = [sites - Nx*Ny, sites]
    smN_s = [sites + Nx*(Ny-1), sites]
    s_spN = [sites, sites + Nx]
    s_spNN = [sites, sites - Nx*Ny*(Nz-1)]

    # compute fn, fp, fv and update vector
    ddp(sys, efn, efp, v, smNN_s, smN_s, s_spN, s_spNN, dx, dxm1, dy, dym1, dz, dzm1, sites)

    ###########################################################################
    #          edge z bottom // y back: 0 < i < Nx-1, j = Ny-1, k = 0         #
    ###########################################################################
    # list of the sites
    sites = _sites[0, Ny-1, 1:Nx-1].flatten()

    # lattice distances
    dy = np.repeat((sys.dy[0] + sys.dy[-1])/2., Nx-2)
    dz = np.repeat(sys.dz[0], Nx-2)
    dym1 = np.repeat(sys.dy[-1], Nx-2)
    dzm1 = np.repeat((sys.dz[0] + sys.dz[-1])/2., Nx-2)

    # gather all relevant pairs of sites to compute the currents
    smNN_s = [sites + Nx*Ny*(Nz-1), sites]
    smN_s = [sites - Nx, sites]
    s_spN = [sites, sites - Nx*(Ny-1)]
    s_spNN = [sites, sites + Nx*Ny]

    # compute fn, fp, fv and update vector
    ddp(sys, efn, efp, v, smNN_s, smN_s, s_spN, s_spNN, dx, dxm1, dy, dym1, dz, dzm1, sites)

    ###########################################################################
    #         edge z bottom // y front: 0 < i < Nx-1, j = 0, k = 0            #
    ###########################################################################
    # list of the sites
    sites = _sites[0, 0, 1:Nx-1].flatten()

    # lattice distances
    dy = np.repeat(sys.dy[0], Nx-2)
    dz = np.repeat(sys.dz[0], Nx-2)
    dym1 = np.repeat((sys.dy[0] + sys.dy[-1])/2., Nx-2)
    dzm1 = np.repeat((sys.dz[0] + sys.dz[-1])/2., Nx-2)

    # gather all relevant pairs of sites to compute the currents
    smNN_s = [sites + Nx*Ny*(Nz-1), sites]
    smN_s = [sites + Nx*(Ny-1), sites]
    s_spN = [sites, sites + Nx]
    s_spNN = [sites, sites + Nx*Ny]

    # compute fn, fp, fv and update vector
    ddp(sys, efn, efp, v, smNN_s, smN_s, s_spN, s_spNN, dx, dxm1, dy, dym1, dz, dzm1, sites)

    return vec
