import numpy as np
import matplotlib.pyplot as plt
import math


class Particle():
    
    def __init__(self, x, y, v_x, v_y, m):
        self.x = x
        self.y = y
        self.v_x = v_x
        self.v_y = v_y
        self.m = m
        self.cool = 0  # if > 0 this particle is not allowed to collide again, it will then work as a counter how often it is not allowed to collide
    

    def copy(self):
        return Particle(self.x, self.y, self.v_x, self.v_y, self.m)
    

    def apply_periodic_border(self, L):
        """
        Sets the particle back to the defined periodic box

        L -- length of the box
        """
        while self.x >= L:
            self.x = self.x - L
        while self.x < 0:
            self.x = self.x + L
        
        while self.y >= L:
            self.y = self.y - L
        while self.y < 0:
            self.y = self.y + L
    

    def move(self, delta_t):
        """
        move the particle for a specific time step without any collisions

        delta_t -- timestep
        """
        self.x = self.x + delta_t * self.v_x
        self.y = self.y + delta_t * self.v_y

    def update_cool(self):
        """
        update the cool field, -> reduce by one if > 0
        """
        if self.cool > 0:
            self.cool -= 1
    

    def distance(self, other, L):
        """
        calculates the distance of to another particle in the periodic box

        other -- the other particle
        L -- length of the box
        """
        delta_x = abs(self.x - other.x)
        if delta_x > L / 2:  # the way through the border is shorter
            delta_x = L - delta_x
        
        delta_y = abs(self.y - other.y)
        if delta_y > L / 2:  # the way through the border is shorter
            delta_y = L - delta_y
        
        return math.sqrt(delta_x**2 + delta_y**2)
    

    def collision_speed_update(self, other):
        """
        Update the speed after a collision with another particle

        other -- other particle of the collision
        """
        self.v_x = (self.m * self.v_x + other.m * (2 * other.v_x - self.v_x)) / (self.m + other.m)
        self.v_y = (self.m * self.v_y + other.m * (2 * other.v_y - self.v_y)) / (self.m + other.m)
    

    def collide(self, other, r, L, collision_cool_down):
        """
        Collide with another particle if it is close enough

        other -- other particle to collide with
        r -- maximal distance between particles for a collision to take place
        L -- length of the periodic box
        collision_cool_down -- number of iterations a particle is noty allowed to collide again after a collision
        """
        dist = self.distance(other, L)

        if dist <= r and self.cool == 0 and other.cool == 0:  # check that the particles are close enough to collide and are cool
            other_backup = other.copy()  # copy the other object because the old status is needed to update the speed of self
            other.collision_speed_update(self)
            self.collision_speed_update(other_backup)
            self.cool = collision_cool_down + 1  # the + 1 is because the cool field is updated before the collision is evaluated
            other.cool = collision_cool_down + 1


def simulate(n_particles, t, delta_t, L, r, collision_cool_down):
    """
    Simulate a gas (well we kicked out most of the physics so it is more a billard table) with a specific number of particles (atoms or molecules) in a periodic 2D box

    n_particles -- number of particles in the box
    t -- the time that is simulated
    delta_t -- the timestep of the simulation
    L -- length of the box
    r -- maximal distance between particles for a collision to take place
    collision_cool_down -- number of iterations a particle is noty allowed to collide again after a collision
    """
    particles = []
    pos = np.random.random((n_particles, 2)) * L
    vel = (np.random.random((n_particles, 2)) - 0.5) / 5
    mass = np.ones(n_particles)
    # use the following line to particls with different mass
    #mass = np.random.random(n_particles) * 2 + 0.5
    for i in range(n_particles):
        particles.append(Particle(pos[i, 0], pos[i, 1], vel[i, 0], vel[i, 1], mass[i]))


    plt.ion()
    figure = plt.figure()

    for i in np.arange(0, t, delta_t):
        for par in particles:
            plt.plot(par.x, par.y, marker='o')
            par.move(delta_t)
            par.apply_periodic_border(L)
            par.update_cool()
        for j in range(len(particles)):
            for k in range(j + 1, len(particles)):
                particles[j].collide(particles[k], r, L, collision_cool_down)
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
    collision_cool_down = 3  # number of iterations a particle is noty allowed to collide again after a collision

    simulate(N_Particles, T, Delta_T, Box_Length, R, collision_cool_down)
