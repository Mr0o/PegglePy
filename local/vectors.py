#  This is my own Vector module that I created for the fun of it
#  Plenty of vector libraries already exist that are more robust and have lots more features
#  but the goal here is to keep it simple

#  In here you will find a Vector class with methods for performing basic vector math
#  All vector math is 2-Dimensional meaning that all Vectors have just an x and y component

from math import atan2, sqrt, cos, sin
from random import randint  # used for random integers

class Vector:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.angleRad = atan2(self.y, self.x)  # find the angle of the vector in radians

    # return a copy of the vector
    def copy(self) -> 'Vector':
        return Vector(self.x, self.y)

    def getMag(self) -> float:
        mag = abs((self.x * self.x) + (self.y * self.y))  # find the magnitude using pythagorean theorem
        mag = sqrt(mag)

        return mag

    #  given components x and y, this will normalize the vector
    def normalize(self) -> None:
        mag = self.getMag()
        if mag != 0:  # divide vector by magnitude to create a unit vector
            self.x = self.x / mag
            self.y = self.y / mag

    #  given a magnitude and components x and y, this will normalize and scale the given vector
    def setMag(self, mag: float) -> None:
        self.normalize()  # normalize

        self.x *= mag  # scale the vector by the given magnitude
        self.y *= mag

    #  similar to setMag but this function will only scale the vector if the magnitude is greater than the limit magnitude
    def limitMag(self, limit: float) -> None:
        if self.getMag() >= limit:
            self.setMag(limit)  # if the limit is reached then keep the magnitude set at the limit

    #  add another vector to self
    def add(self, vec: 'Vector') -> None:
        self.x += vec.x
        self.y += vec.y

    #  subtract another vector from self
    def sub(self, vec: 'Vector') -> None:
        self.x -= vec.x
        self.y -= vec.y

    #  multiply a scalar value to the vector
    def mult(self, m: float) -> None:
        self.x *= m
        self.y *= m
    
    #  divide each component by a scalar value
    def div(self, d: float) -> None:
        self.x /= d
        self.y /= d
    
    #  return the angle of the vector
    def getAngleRad(self) -> float:
        return atan2(self.y, self.x)
    
    # return the angle of the vector in degrees
    def getAngleDeg(self) -> float:
        return self.getAngleRad() * 180 / 3.14159265359
    
    #  set the angle of the vector in radians
    def setAngleRad(self, angle: float) -> None:
        mag = self.getMag()
        self.x = mag * cos(angle)
        self.y = mag * sin(angle)
    
    # set the angle of the vector in degrees
    def setAngleDeg(self, angle: float) -> None:
        self.setAngleRad(angle * 3.14159265359 / 180)


#  add two vectors and return the resulting vector
def addVectors(vec1: Vector, vec2: Vector) -> Vector:
    sum_x = vec1.x + vec2.x
    sum_y = vec1.y + vec2.y

    return Vector(sum_x, sum_y)


#  subtract two vectors and return the resulting vector
def subVectors(vec1: Vector, vec2: Vector) -> Vector:
    diff_x = vec1.x - vec2.x
    diff_y = vec1.y - vec2.y

    return Vector(diff_x, diff_y)


# creates a random vector with a maximum and minimum based on random_max
def createRandomVector(random_max: int) -> Vector:
    rx = randint(-random_max, random_max)
    ry = randint(-random_max, random_max)

    return Vector(rx, ry)