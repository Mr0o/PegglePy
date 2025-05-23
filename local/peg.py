from random import randint

# refer to the vectors.py module for information on these functions
from local.triggerEvents import TimedEvent
from local.vectors import Vector
from local.animate import AnimationFade

from local.config import pegRad, defaultPegMass, configs

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
        
        # create pop‐in animation
        self.animation: AnimationFade = AnimationFade(self.pos,
                                   duration=90.0,
                                   start_scale=3.00)


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


    def set_color(self, color: str):
        # set the appropiate color peg image if it is has been hit or not
        self.color = color
        if self.color == "orange":
            self.points = 100
            self.isOrange = True
        elif self.color == "green":
            self.points = 10
            self.isPowerUp = True
        else:
            self.isOrange = False
            self.isPowerUp = False

        self.update_color()
        
        
    def update_color(self):
        # set the appropiate color peg image if it is has been hit or not
        if not self.isHit:
            if self.color == "orange":
                self.points = 100
            if self.color == "green":
                self.points = 10
            

    def update_animation(self, dt: float):
        # drive animation every frame
        if not self.animation.done:
            self.animation.update(dt)

    def draw_animation(self):
        if not self.animation.done:
            # still popping in
            self.animation.draw()


def getScoreMultiplier(remainingOrangePegs, pegsHit=0) -> int:
    # first multiplier based on remaining orange pegs
    multiplier = 1
    if remainingOrangePegs <= 3:
        multiplier = 10
    elif remainingOrangePegs <= 6:
        multiplier = 5
    elif remainingOrangePegs <= 10:
        multiplier = 3
    elif remainingOrangePegs <= 15:
        multiplier = 2

    # second multiplier based on number of pegs hit by the current ball
    if pegsHit >= 10 and pegsHit < 15:
        multiplier *= 2
    elif pegsHit >= 15 and pegsHit < 18:
        multiplier *= 5
    elif pegsHit >= 18 and pegsHit < 22:
        multiplier *= 8
    elif pegsHit >= 22 and pegsHit < 25:
        multiplier *= 10
    elif pegsHit >= 25 and pegsHit < 35:
        multiplier *= 20
    elif pegsHit >= 35:  # if you are hitting this many pegs with one ball, you are either very lucky or cheating but this is the reward either way
        multiplier *= 100
    return multiplier

def createPegColors(pegs: list[Peg], color_map: list = None) -> list[Peg]:
    if color_map:
        # update peg colors with a fixed map
        for i in range(0, len(pegs)):
            peg = pegs[i]
            peg.color = color_map[i]
            if peg.color == "orange":
                peg.isOrange = True
            elif peg.color == "green":
                peg.isPowerUp = True
            peg.update_color()
    else:
        target_oranges = 25
        target_greens = 2

        if len(pegs) < 25:
            if configs["DEBUG_MODE"]:
                print("WARN: Level has less than 25 pegs, continuing anyway...")
            target_oranges = 1 if len(pegs) <= 3 else len(pegs) - 2
            if len(pegs) <= 2:
                target_greens = len(pegs) - target_oranges
        elif len(pegs) > 120:
            if configs["DEBUG_MODE"]:
                print(
                    "WARN: Level has excessive number of pegs, expect performance issues...")

        peg_pool = pegs.copy()

        # create orange pegs
        orange_count = 0
        while orange_count < target_oranges:
            i = randint(0, len(peg_pool) - 1)
            p = peg_pool.pop(i)
            p.color = "orange"
            p.isOrange = True
            p.update_color()

            orange_count += 1

        # create green pegs
        for _ in range(target_greens):
            i = randint(0, len(peg_pool) - 1)
            p = peg_pool.pop(i)
            p.color = "green"
            p.isPowerUp = True
            p.update_color()

    return pegs