import sesame
from sesame.ui import sim
from sesame import analyzer, utils, builder
from sesame.solvers import Solver
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.figure as fig
length = 6e-4  # length of the system in cm

pop_up_spam = False # if you want the band diagrams to pop up
# this is the directory where the files will go
direcc = 'C:/Users/njr3/Downloads/sesame-master/sesame-master/test1/'

mesh = np.linspace(0, length)
# doping amounts [1/cm^3]
nD = 1e+16
nA = 1e+16

# tau values to iterate through
tau_to_test = [1e-9,1e-8,1e-7,1e-6,1e-5]
# center values to iterate through
center = np.linspace(2e-4,5e-4,20)


def gen(system, solverSettings, generation, paramName,):

    loopValues, simName, fmt, BCs, contacts_bcs, contacts_WF, Sc, \
    tol, maxiter, useMumps, iterative, ramp, iterPrec, htpy = solverSettings

    solver = Solver(use_mumps=useMumps)

    # Equilibrium guess
    guess = solver.make_guess(system)
    # Solve Poisson equation
    solver.common_solver('Poisson', system, guess, tol, BCs, maxiter, True, iterative, iterPrec, htpy)

    if solver.equilibrium is not None:
        print("Equilibrium electrostatic potential obtained")
        # Construct the solution dictionary
        efn = np.zeros_like(solver.equilibrium)
        efp = np.zeros_like(solver.equilibrium)
        v = np.copy(solver.equilibrium)
        solution = {'efn': efn, 'efp': efp, 'v': v}
    else:
        print("The solver failed to converge for the electrostatic potential")
        return


    for idx, p in enumerate(loopValues):
        print(idx, p)
        # give the named parameter its value
        exec(paramName + '=' + str(p), globals())
        print("Parameter value: {0} = {1}".format(paramName, p))
        # create callable
        if system.dimension == 1:
            f = eval('lambda x, {0}:'.format(paramName) + generation)
        elif system.dimension == 2:
            f = eval('lambda x, y, {0}:'.format(paramName) + generation)
        elif system.dimension == 3:
            f = eval('lambda x, y, z, {0}:'.format(paramName) + generation)
        # update generation rate of the system
        try:
            system.generation(f, args=(p,))
        except Exception:
            print("**  The generation rate could not be interpreted  **")
            return

        system.g /= 10 ** ramp
        for a in range(ramp + 1):
            print("Amplitude divided by {0}".format(10 ** (ramp - a)))
            solution = solver.common_solver('all', system, solution,tol, BCs, maxiter, True, iterative, iterPrec, htpy)
            system.g *= 10
            if solution is None:
                print("**  The calculations failed  **")
                return

        if solution is not None:
            name = simName + "_{0}".format(idx)
            # add some system settings to the saved results
            solution.update({'x': system.xpts, 'y': system.ypts,
                             'z': system.zpts, 'affinity': system.bl,
                             'Eg': system.Eg, 'Nc': system.Nc,
                             'Nv': system.Nv, 'epsilon': system.epsilon})

            if fmt == '.mat':
                utils.save_sim(system, solution, name, fmt='mat')
            else:
                filename = "%s.gzip" % name
                utils.save_sim(system, solution, filename)
                # signal a new file has been created to the main thread

        else:
            print("The solver failed to converge for the parameter value {0} (index {1}).".format(p, idx))
            print("Aborting now.")
            return
    if solution is not None:
        print("** Calculations completed successfully **")

for i in range(len(tau_to_test)):
    sys = builder.Builder(mesh)

    # Add the doping
    sys.add_donor(nD, lambda x: x < 3e-4)
    sys.add_acceptor(nA, lambda x: x > 3e-4)
    # Define Ohmic contacts
    sys.contact_type('Ohmic', 'Ohmic')
    # Define the surface recombination velocities for electrons and holes [cm/s]
    Sn_left, Sp_left, Sn_right, Sp_right = 1e5, 0, 0, 1e5
    sys.contact_S(Sn_left, Sp_left, Sn_right, Sp_right)
    # create the material
    material = {'Nc': 1e+19, 'Nv': 1e+19, 'Eg': 1.1, 'affinity': 0, 'epsilon': 10,
                'mu_e': 300, 'mu_h': 300, 'tau_e': tau_to_test[i], 'tau_h': tau_to_test[i], 'Et': 0}
    sys.add_material(material)
    gen(sys, [np.linspace(2e-4,5e-4,20),direcc+f'test{i}','.gzip', True, ['Ohmic', 'Ohmic'], ['', ''],
              [100000.0, 100000.0, 100000.0, 100000.0],1e-06, 100, False, False, 0, 1e-06, 1],
               '(1e19) * np.exp((-(x-x0)**2)/((2e-6)**2))', 'x0')

    # this pops up the band diagrams, not really needed if you're going to use sesame to look at them
    if pop_up_spam:
        for j in range(20):
            sys_load, data = utils.load_sim(direcc+f'test{i}_{j}.gzip')
            anal = analyzer.Analyzer(sys_load, data)
            # full_current
            # n density as a function of position, fix x0 to be a single value, far fron depletion region, 5 curves (one for each tau)
            anal.band_diagram(((0, 0), (0.0006, 0)))
# plt.clf()
# plt.cla()
currents = np.zeros(5)
labels = []
for i in range(len(currents)):
    sys_load, data = utils.load_sim(direcc + f'test{i}_19.gzip')
    anal = analyzer.Analyzer(sys_load,data)
    currents[i]=anal.full_current()
    labels.append(f'{tau_to_test[i]}')

fix, ax = plt.subplots()
bar_width = 0.35
index = np.arange(5)
ax.bar(index, currents, bar_width)
ax.set_xticks(index + bar_width / 2)
ax.set_xticklabels(labels)
plt.subplot(111).bar(index, currents, bar_width)
plt.xlabel("tau values")
plt.ylabel("current")

plt.show()





