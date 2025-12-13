import numpy as np
import matplotlib.pyplot as plt
import math





def simulate(n_particles, t, delta_t, L, r):
    """
    Simulate a gas (well we kicked out most of the physics so it is more a billard table) with a specific number of particles (atoms or molecules) in a periodic 2D box

    n_particles -- number of particles in the box
    t -- the time that is simulated
    delta_t -- the timestep of the simulation
    L -- length of the box
    r -- maximal distance between particles for a collision to take place
    """
    particles = []
    pos = np.random.random((n_particles, 2)) * L  # generate particle positions (x and y coordinate)
    vel = (np.random.random((n_particles, 2)) - 0.5) / 5  # generate particle velocities (x and y coordinate)
    mass = np.random.random(n_particles) * 2 + 0.5  # generate particle masses
    for i in range(n_particles):
        #TODO particles.append(<particle at position pos[i] with velocity vel[i] and mass[i]>)


    plt.ion()  # enable interactive plotting
    figure = plt.figure()

    for i in np.arange(0, t, delta_t):  # timesteps
        for par in particles:
            #TODO plt.plot(<x-position of par>, <y-position of par>, marker='o')  # plot the particles
            #TODO move the particle for a timestep delta t
            #TODO if not done already, move particles that left the periodic box back into the box
        #TODO do all the collisions (maybe you have to add more than a single line)
        plt.xlim(0, L)
        plt.ylim(0, L)
        figure.canvas.draw()
        figure.canvas.flush_events()
        plt.clf()


if __name__ == '__main__':
    N_Particles = 40  # number of particles
    T = 100  # simulation time
    Delta_T = 0.1  # simulation time step
    Box_Length = 1  # length of the box
    R = 0.03  # maximal distance between particles for a collision to take place

    simulate(N_Particles, T, Delta_T, Box_Length, R)
