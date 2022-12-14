#  This is my own Vector module that I created for the fun of it
#  Plenty of vector libraries already exist that are more robust and have lots more features
#  but the goal here is to keep it simple

#  In here you will find a Vector class with methods for performing basic vector math
#  All vector math is 2-Dimensional meaning that all Vectors have just an x and y component

from math import atan2, sqrt, cos, sin
from random import randint  # used for random integers


#  add two vectors and return the resulting vector
def addVectors(vec1, vec2):
    sum_x = vec1.vx + vec2.vx
    sum_y = vec1.vy + vec2.vy

    return Vector(sum_x, sum_y)


#  subtract two vectors and return the resulting vector
def subVectors(vec1, vec2):
    diff_x = vec1.vx - vec2.vx
    diff_y = vec1.vy - vec2.vy

    return Vector(diff_x, diff_y)


# creates a random vector with a maximum and minimum based on random_max
def createRandomVector(random_max):
    rx = randint(-random_max, random_max)
    ry = randint(-random_max, random_max)

    return Vector(rx, ry)


class Vector:
    def __init__(self, x, y):
        self.vx = x
        self.vy = y
        self.angleRad = atan2(self.vy, self.vx)  # find the angle of the vector in radians

    def getMag(self):
        mag = abs((self.vx * self.vx) + (self.vy * self.vy))  # find the magnitude using pythagorean theorem
        mag = sqrt(mag)

        return mag

    #  given components x and y, this will normalize the vector
    def normalize(self):
        mag = self.getMag()
        if mag != 0:  # divide vector by magnitude to create a unit vector
            self.vx = self.vx / mag
            self.vy = self.vy / mag

    #  given a magnitude and components x and y, this will normalize and scale the given vector
    def setMag(self, mag):
        self.normalize()  # normalize

        self.vx *= mag  # scale the vector by the given magnitude
        self.vy *= mag

    #  similar to setMag but this function will only scale the vector if the magnitude is greater than the limit magnitude
    def limitMag(self, limit):
        if self.getMag() >= limit:
            self.setMag(limit)  # if the limit is reached then keep the magnitude set at the limit

    #  add another vector to self
    def add(self, vec):
        self.vx += vec.vx
        self.vy += vec.vy

    #  subtract another vector from self
    def sub(self, vec):
        self.vx -= vec.vx
        self.vy -= vec.vy

    #  multiply a scalar value to the vector
    def mult(self, m):
        self.vx *= m
        self.vy *= m
    
    #  divide each component by a scalar value
    def div(self, d):
        self.vx /= d
        self.vy /= d
    
    #  return the angle of the vector
    def getAngleRad(self):
        return atan2(self.vy, self.vx)
    
    # return the angle of the vector in degrees
    def getAngleDeg(self):
        return self.getAngleRad() * 180 / 3.14159265359
    
    #  set the angle of the vector in radians
    def setAngleRad(self, angle):
        mag = self.getMag()
        self.vx = mag * cos(angle)
        self.vy = mag * sin(angle)
    
    # set the angle of the vector in degrees
    def setAngleDeg(self, angle):
        self.setAngleRad(angle * 3.14159265359 / 180)
