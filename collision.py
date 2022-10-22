from math import sqrt
from ball import Ball
from peg import Peg


def isBallTouchingPeg(b1x, b1y, b1r, b2x, b2y, b2r):
    return ((b1x-b2x)*(b1x-b2x) + (b1y-b2y)*(b1y-b2y)) < (b1r+b2r)*(b1r+b2r)


def resolveCollision(ball : Ball, peg : Peg):
    """
    Resolve elastic collisions against two spheres:

    - Both arguments are expected to be objects with a mass, radius, position and velocity\n
    - Returns an object with the updated position and velocity from the collision
    """

    #find the distance between ball and peg centers
    distance = sqrt((ball.pos.vx - peg.pos.vx)*(ball.pos.vx - peg.pos.vx) + (ball.pos.vy - peg.pos.vy)*(ball.pos.vy - peg.pos.vy))
    #find the amount of overlap between the ball and peg
    overlap =  1.0 * (distance - ball.radius - peg.radius)

    #displace the ball
    ball.pos.vx -= overlap * (ball.pos.vx - peg.pos.vx) / distance
    ball.pos.vy -= overlap * (ball.pos.vy - peg.pos.vy) / distance

    ## workout dynamic collisions
    #normal
    nx = (ball.pos.vx - peg.pos.vx) / distance
    ny = (ball.pos.vy - peg.pos.vy) / distance

    #tangent
    tx = -ny
    ty = nx

    #dot product tangent
    dpTan = ball.vel.vx * tx + ball.vel.vy * ty

    #dot product normal
    dpNorm1 = ball.vel.vx * nx + ball.vel.vy * ny
    dpNorm2 = peg.vel.vx * nx + peg.vel.vy * ny

    #conservation of momentum in 1D
    m = (dpNorm1 * (ball.mass - peg.mass) + 2.0 * peg.mass * dpNorm2) / (ball.mass + peg.mass)

    #update velocity of the ball
    ball.vel.vx = tx * dpTan + nx * m
    ball.vel.vy = ty * dpTan + ny * m


    return ball
