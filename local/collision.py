from math import sqrt
from local.ball import Ball
from local.peg import Peg
from local.config import debug, useCPhysics

import ctypes

# use the c implementation as per the config
if useCPhysics:
    try:
        # check which platform we are running on
        import platform
        if platform.system() == "Windows":
            # windows
            collisionLib = ctypes.CDLL('./bin/collision.dll')
        elif platform.system() == "Linux":
            # linux
            collisionLib = ctypes.CDLL('./bin/collision.so')
        else:
            raise Exception("Unsupported platform: " + platform.system())

        isBallTouchingPegFunc = collisionLib.isBallTouchingPeg
        resolveCollisionFunc = collisionLib.resolveCollision

        isBallTouchingPegFunc.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
        isBallTouchingPegFunc.restype = ctypes.c_int

        resolveCollisionFunc.argtypes = [ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float]
        resolveCollisionFunc.restype = ctypes.POINTER(ctypes.c_float * 4)
    except Exception as e:
        # if exception is unsupported platform, print a warning and use the python implementation instead
        # check if the exception contains the words unsupported platform
        if str(e).find("Unsupported platform") != -1:
            print("WARN: " + str(e))
            print("Unable to use collision C shared library. Using python implementation instead.")
        else:
            print(str(e))
            print("Traceback:")
            print(str(e.__traceback__))
            print("WARN: Failed to load the collision C shared library. Using python implementation instead.")

        collisionLib = None

        # swap the c functions with the 'old' functions
        def isBallTouchingPeg(b1x, b1y, b1r, b2x, b2y, b2r) -> bool:
            return isBallTouchingPeg_old(b1x, b1y, b1r, b2x, b2y, b2r)
        
        def resolveCollision(ball : Ball, peg : Peg) -> Ball:
            return resolveCollision_old(ball, peg)
        
# we will not use the c implementation as per the config
else:
    collisionLib = None

    # swap the c functions with the 'old' functions
    def isBallTouchingPeg(b1x, b1y, b1r, b2x, b2y, b2r) -> bool:
        return isBallTouchingPeg_old(b1x, b1y, b1r, b2x, b2y, b2r)
    
    def resolveCollision(ball : Ball, peg : Peg) -> Ball:
        return resolveCollision_old(ball, peg)
    
    print("NOTE: UseCPhysics is set to False, using python implementation of collision functions.")

    


def isBallTouchingPeg_old(b1x, b1y, b1r, b2x, b2y, b2r) -> bool:
    return ((b1x-b2x)*(b1x-b2x) + (b1y-b2y)*(b1y-b2y)) < (b1r+b2r)*(b1r+b2r)


def resolveCollision_old(ball : Ball, peg : Peg) -> Ball:
    """
    (old) Resolve elastic collisions against two spheres:

    - Both arguments are expected to be objects with a mass, radius, position and velocity\n
    - Returns an object with the updated position and velocity from the collision
    """

    #find the distance between ball and peg centers
    distance = sqrt((ball.pos.x - peg.pos.x)*(ball.pos.x - peg.pos.x) + (ball.pos.y - peg.pos.y)*(ball.pos.y - peg.pos.y))
    #find the amount of overlap between the ball and peg
    overlap =  1.0 * (distance - ball.radius - peg.radius)

    #prevent division by zero
    if (distance == 0):
        distance = 0.0001  # arbitrary small number

    #displace the ball
    ball.pos.x -= overlap * (ball.pos.x - peg.pos.x) / distance
    ball.pos.y -= overlap * (ball.pos.y - peg.pos.y) / distance

    ## workout dynamic collisions
    #normal
    nx = (ball.pos.x - peg.pos.x) / distance
    ny = (ball.pos.y - peg.pos.y) / distance

    #tangent
    tx = -ny
    ty = nx

    #dot product tangent
    dpTan = ball.vel.x * tx + ball.vel.y * ty

    #dot product normal
    dpNorm1 = ball.vel.x * nx + ball.vel.y * ny
    dpNorm2 = peg.vel.x * nx + peg.vel.y * ny

    #conservation of momentum in 1D
    m = (dpNorm1 * (ball.mass - peg.mass) + 2.0 * peg.mass * dpNorm2) / (ball.mass + peg.mass)

    #update velocity of the ball
    ball.vel.x = tx * dpTan + nx * m
    ball.vel.y = ty * dpTan + ny * m


    return ball


if collisionLib is not None:
    def isBallTouchingPeg(b1x : float, b1y : float, b1r : float, b2x : float, b2y : float, b2r : float) -> bool:
        # use the c function to check if the ball is touching the peg
        # args: (float b1x, float b1y, float b1r, float p1x, float p1y, float p1r)
        results = collisionLib.isBallTouchingPeg(b1x, b1y, b1r, b2x, b2y, b2r)

        if results == 1:
            return True
        else:
            return False


    # c function implementation of resolveCollision 
    # in theory this *should* be faster than the python implementation
    def resolveCollision(ball : Ball, peg : Peg) -> Ball:
        ballx = ball.pos.x
        bally = ball.pos.y
        ballvx = ball.vel.x
        ballvy = ball.vel.y
        ballRad = ball.radius
        ballMass = ball.mass
        pegRad = peg.radius
        pegx = peg.pos.x
        pegy = peg.pos.y


        # use the c function to resolve the collision
        # args: (float ballx, float bally, float ballvx, float ballvy, float ballRad, float ballMass, float pegRad, float pegx, float pegy)
        results = resolveCollisionFunc(ballx, bally, ballvx, ballvy, ballRad, ballMass, pegRad, pegx, pegy).contents

        # the c function returns a pointer to a float array (ballx, bally, ballVelocityX, ballVelocityY)

        # update the ball position and velocity
        ball.pos.x = results[0]
        ball.pos.y = results[1]
        ball.vel.x = results[2]
        ball.vel.y = results[3]

        return ball