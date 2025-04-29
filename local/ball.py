# refer to the vectors.py module for information on these functions
from local.vectors import Vector

from local.config import gravity, maxBallVelocity, ballRad, defaultBallMass
from local.config import configs

class Ball:
    def __init__(self, x : int, y : int, mass = defaultBallMass):
        self.originX=x; self.originY=y # origin position for the reset method

        self.pos = Vector(x, y)  # position
        self.acc = Vector(0, 0)  # acceleration
        self.vel = Vector(0, 0)  # velocity

        self.mass = mass
        self.radius = ballRad

        self.isLaunch = False
        self.isAlive = False
        
        self.inBucket = False

        self.lastPegHit = None # used for when the ball gets stuck
        self.lastPegHitPos = None # used to determine long shot bonus
        
        # previous position of the ball (used for collision detection)
        self.prevPos = Vector(x, y)
        self.prevAcc = Vector(0, 0)
        self.prevVel = Vector(0, 0)
        

    # F = M*A 
    # Adds a force(Vector) to the velocity
    def applyForce(self, force : Vector):
        fx, fy = force.x, force.y
        fcopy = Vector(fx,fy) # create a copy of the force
        #fcopy.div(self.mass)
        self.vel.add(fcopy)

    def update(self, dt: float = 1, zeroGravity = False):
        self.prevPos = self.pos.copy()
        self.prevAcc = self.acc.copy()
        self.prevVel = self.vel.copy()
        
        if not zeroGravity:
            gravityCopy = gravity.copy()
            gravityCopy.mult(dt)
            self.applyForce(gravityCopy)
        
        self.vel.add(Vector(self.acc.x * dt, self.acc.y * dt))
        self.pos.add(Vector(self.vel.x * dt, self.vel.y * dt))
        self.acc.mult(0)

        self.vel.limitMag(maxBallVelocity) #stop the ball from going crazy, this resolves the occasional physics glitches

        # if ball collided with wall or has fallen through the floor
        if self.pos.x > (configs["WIDTH"] - self.radius) or self.pos.x < self.radius:
            if self.pos.x > (configs["WIDTH"] - self.radius): self.pos.x = configs["WIDTH"] - self.radius
            elif self.pos.x < self.radius: self.pos.x = self.radius
            self.vel.x *= -1
        if self.pos.y < self.radius:
            self.pos.y = self.radius
            self.vel.y *= -1
        # use prevPos instead of the current pos so that the spooky ball can warp before it 'dies'
        # (This is sort of a hack that fixes spooky ball at low framerates)
        if self.prevPos.y > (configs["HEIGHT"] + self.radius):
            self.isAlive = False

    def reset(self):
        self.vel.mult(0)
        self.acc.mult(0)
        self.pos = Vector(self.originX, self.originY)
        self.isLaunch = False
        self.isAlive = False
        self.inBucket = False
        self.lastPegHit = None
        self.lastPegHitPos = None
        self.prevPos = Vector(self.originX, self.originY)
        self.prevAcc = Vector(0, 0)
        self.prevVel = Vector(0, 0)