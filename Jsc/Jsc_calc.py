from sesame import builder, solvers, utils, analyzer,plotter
import numpy as np
import matplotlib.pyplot as plt
# creating the system
x = np.concatenate((np.linspace(0,.75e-4,5,False),np.linspace(.75e-4,1e-4,10,False),
                    np.linspace(1e-4,2e-4,50,False),np.linspace(2e-4,2.25e-4,10,False),
                    np.linspace(2.25e-4,3e-4,5)))
y = np.concatenate((np.linspace(0,1.25e-4,60,False),np.linspace(1.25e-4,1.75e-4,80,False),np.linspace(1.75e-4,3e-4,60)))
# 0, 3e-4

material = {'Nc':8e17, 'Nv':1.8e19, 'Eg':1.5, 'affinity':3.9, 'epsilon':9.4,
        'mu_e':100, 'mu_h':100, 'tau_e':10e-9, 'tau_h':10e-9, 'Et':0} # arbitrary values


junction = 1.5e-4 # extent of the junction from the left contact [cm]
def n_region(pos):
    x = pos[0]
    return x < junction

def p_region(pos):
    x = pos[0]
    return x >= junction

# Add the donors
nD = 1e16 # [cm^-3]


# Add the acceptors
nA = 1e16 # [cm^-3]


# Define contacts: CdS and CdTe contacts are Ohmic

# Define the surface recombination velocities for electrons and holes [cm/s]
Sn_left, Sp_left, Sn_right, Sp_right = 1e7, 0, 0, 1e7
# This function specifies the simulation contact recombination velocity

# GB defect state properties
rho_GB = [1e10, 1e14]               # defect density [1/cm^2]
S_GB = 1e-14                # capture cross section [cm^2]
# Specify the two points that make the line containing additional charges
p1 = (1e-4, 1.5e-4)      # [cm]
p2 = (2e-4, 1.5e-4)     # [cm]
currents = []

def makesystem(rho_GB):
    sys = builder.Builder(x, y)
    sys.add_material(material)
    sys.add_donor(nD, n_region)
    sys.add_acceptor(nA, p_region)
    sys.contact_type('Ohmic', 'Ohmic')
    sys.contact_S(Sn_left, Sp_left, Sn_right, Sp_right)
    sys.add_line_defects([p1, p2], rho_GB, S_GB, E=E_GB, transition=(1, -1))

    return(sys)


E_GB_to_test = [-.5,-.4,-.3,-.2,-.1,0,.1,.2,.3,.4,.5]
G_for_guess = [1e15,1e17,1e19,1e20,1e21]

for E_GB in E_GB_to_test: # energy of gap state from intrinsic level [eV]
    #building system
    sys = makesystem(rho_GB[1])
    sys.generation(lambda x, y: 1e15)
    equilibrium = solvers.solve_equilibrium(sys)
    solution = solvers.solve(sys, equilibrium)

    equilibrium = solvers.solve_equilibrium(sys)
    for g in G_for_guess:
        sys.generation(lambda x, y: g)
        solution = solvers.solve(sys, equilibrium)
    print(E_GB)
    analyze = analyzer.Analyzer(sys, solution)

    currents.append(analyze.full_current() * sys.scaling.current * sys.scaling.length / 3e-4)  # units A/cm^2

    print(str(analyze.full_current() * sys.scaling.current * sys.scaling.length / 3e-4) + " Amp/cm^2")
    # .03 Amp/cm^2 is usual
    name = "GB_test_{0}".format(E_GB)
    # add some system settings to the saved results
    filename = "%s.gzip" % name
    utils.save_sim(sys, solution, filename)
plt.plot(E_GB_to_test,currents)
plt.title("EGB vs Jsc")
plt.show()