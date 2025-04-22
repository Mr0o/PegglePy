# refer to the vectors.py module for information on these functions
from local.trigger_events import TimedEvent
from local.vectors import Vector

from local.config import pegRad, defaultPegMass

class Peg:
    def __init__(self, x : int, y : int, color = "blue"):
        self.pos = Vector(x, y)  # position
        self.vel = Vector(0, 0)  # velocity, used for collision calculation

        self.radius = pegRad

        self.mass = defaultPegMass # magic number, just pulled this one out of thin air

        self.posAdjust = self.radius # this is used to draw the image for the peg in the correct position
        self.isHit = False
        self.isVisible = True
        self.isPowerUp = False
        self.isOrange = False
        
        self.color = color
        self.points = 10

        self.ballStuckTimer = TimedEvent() # used for when the ball gets stuck


    def reset(self):
        self.vel = Vector(0, 0)  # velocity, used for collision calculation

        self.radius = pegRad

        self.mass = defaultPegMass

        self.posAdjust = self.radius # this is used to draw the image for the peg in the correct position
        self.isHit = False
        self.isVisible = True
        self.isPowerUp = False
        self.isOrange = False
        
        self.color = "blue"
        self.points = 10

        self.pegScreenLocations = [] # list of screen segment locations (it is possible for a peg to cross multiple segments)

        self.ballStuckTimer = TimedEvent() # used for when the ball gets stuck


    def update_color(self):
        # set the appropiate color peg image if it is has been hit or not
        if not self.isHit:
            if self.color == "orange":
                self.points = 100
            if self.color == "green":
                self.points = 10
            
