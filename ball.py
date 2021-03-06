# refer to the vectors.py module for information on these functions
from vectors import Vector

from config import WIDTH, HEIGHT

class Ball:
    def __init__(self, x, y, mass = 6):
        self.originX=x; self.originY=y # origin position for the reset method

        self.pos = Vector(x, y)  # position
        self.acc = Vector(0, 0)  # acceleration
        self.vel = Vector(0, 0)  # velocity

        self.mass = mass
        self.radius = 8

        self.isLaunch = False
        self.isAlive = False
        
        

    # F = M*A 
    # Adds a force(Vector) to the velocity
    def applyForce(self, force : Vector):
        fx, fy = force.vx, force.vy
        fcopy = Vector(fx,fy) # create a copy of the force
        #fcopy.div(self.mass)
        self.vel.add(fcopy)

    def update(self):
        #self.vel.mult(0.999) #drag
        self.vel.add(self.acc)
        self.pos.add(self.vel)
        self.acc.mult(0)

        # if ball colided with wall or has fallen through the floor
        if self.pos.vx > (WIDTH - self.radius) or self.pos.vx < self.radius:
            self.vel.vx *= -1
        if self.pos.vy < self.radius:
            self.vel.vy *= -1
        if self.pos.vy > (HEIGHT + self.radius):
            self.isAlive = False

    def reset(self):
        self.vel.mult(0)
        self.acc.mult(0)
        self.pos = Vector(self.originX, self.originY)
        self.isLaunch = False
        self.isAlive = False