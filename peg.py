# refer to the vectors.py module for information on these functions
from vectors import Vector

from config import bluePegImg, hitBluePegImg, orangePegImg, hitOrangePegImg, greenPegImg, hitGreenPegImg


class Peg:
    def __init__(self, x, y, color = "blue"):
        self.pos = Vector(x, y)  # position
        self.vel = Vector(0, 0)  # velocity, used for collision calculation

        self.radius = 14

        self.mass = 20 # magic number, just pulled this one out of thin air

        self.isHit = False
        self.isVisible = True
        self.isPowerUp = False
        self.isOrange = False

        self.color = color
        # set the appropiate color peg image
        if self.color == "blue":
            self.pegImg = bluePegImg
        if self.color == "orange":
            self.pegImg = orangePegImg
        if self.color == "green":
            self.pegImg = greenPegImg  

    def update_color(self):
        # set the appropiate color peg image if it is has been hit or not
        if self.isHit:
            if self.color == "blue":
                self.pegImg = hitBluePegImg
            if self.color == "orange":
                self.pegImg = hitOrangePegImg
            if self.color == "green":
                self.pegImg = hitGreenPegImg 
        else:
            if self.color == "blue":
                self.pegImg = bluePegImg
            if self.color == "orange":
                self.pegImg = orangePegImg
            if self.color == "green":
                self.pegImg = greenPegImg
            
