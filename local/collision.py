from math import sqrt
from local.ball import Ball
from local.peg import Peg
from local.config import debug

def isBallTouchingPeg(b1x, b1y, b1r, b2x, b2y, b2r) -> bool:
    return ((b1x-b2x)*(b1x-b2x) + (b1y-b2y)*(b1y-b2y)) < (b1r+b2r)*(b1r+b2r)


def resolveCollision(ball : Ball, peg : Peg) -> Ball:
    """
    Resolve elastic collisions against two spheres:

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