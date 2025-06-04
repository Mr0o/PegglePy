import time
from math import sqrt, atan, pi

from local.vectors import Vector, subVectors
from local.ball import Ball
from local.peg import Peg
from local.config import LAUNCH_FORCE, trajectoryDepth, queryRectSize
from local.config import configs, gravity
from local.collision import isBallTouchingPeg, resolveCollision
from local.quadtree import QuadtreePegs, Rectangle

def calcTrajectory(aim : Vector, startPos : Vector, pegs : list[Peg], bucketPegs, quadtree : QuadtreePegs, dt, collisionGuideBall = False, depth = trajectoryDepth, debugTrajectory = False):
    hit = False
    previousFakeBall = Ball(startPos.x, startPos.y)
            
    #include bucket pegs in the trajectory calculation
    for fakePeg in bucketPegs:
        pegs.append(fakePeg)

    fakeBalls = []
    for i in range(depth):
        fakeBall = Ball(previousFakeBall.pos.x, previousFakeBall.pos.y)
        
        if i == 0: # only on the first iteration
            traj = subVectors(aim, startPos)
            traj.setMag(LAUNCH_FORCE)
            fakeBall.applyForce(traj)

        if i != 0: # every iteration except the first
            fakeBall.applyForce(previousFakeBall.acc)
            fakeBall.applyForce(previousFakeBall.vel)


        #### collision ####

        if hit:# ##powerup## if ball has collided then stop calculating and return
            queryRect = Rectangle(fakeBall.pos.x, fakeBall.pos.y, queryRectSize, queryRectSize)
            pegsInRange = quadtree.query(queryRect)
            for p in pegsInRange:
                ballTouchingPeg = isBallTouchingPeg(fakeBall, p, dt)
                if ballTouchingPeg:
                    return fakeBalls
        elif collisionGuideBall and not hit: # if guideBall powerup is being used
            queryRect = Rectangle(fakeBall.pos.x, fakeBall.pos.y, queryRectSize, queryRectSize)
            pegsInRange = quadtree.query(queryRect)
            for p in pegsInRange:         
                ballTouchingPeg = isBallTouchingPeg(fakeBall, p, dt)
                if ballTouchingPeg:
                    fakeBall = resolveCollision(fakeBall, [p], dt)
                    hit = True
        elif not collisionGuideBall: # ##normal## if ball has collided then stop calculating and return
            queryRect = Rectangle(fakeBall.pos.x, fakeBall.pos.y, queryRectSize, queryRectSize)
            pegsInRange = quadtree.query(queryRect)
            for p in pegsInRange:
                ballTouchingPeg = isBallTouchingPeg(fakeBall, p, dt)
                if ballTouchingPeg:
                    if not debugTrajectory:
                        return fakeBalls
                    else:
                        fakeBall = resolveCollision(fakeBall, [p], dt)
            
        fakeBall.update()
        
        if fakeBall.pos.y > configs["HEIGHT"]:
            break # if the ball has gone off the screen, then we can stop
        
        fakeBalls.append(fakeBall)

        previousFakeBall = fakeBall
        

    return fakeBalls


def findBestTrajectory(aim: Vector, startPos : Vector, pegs : list[Peg], quadtree : QuadtreePegs, dt, maxRangeDegrees = 21, depth = 2500, setTimeLimit = 6):
    # default maxRange and depth were found using a performance test on a level with 120 pegs, which can be run with the 'performance_test.py' module
    # the default values are the values that gave the best performance (shortest time, but with the greatest depth and range possible)

    timeLimit = setTimeLimit# seconds (if the function takes longer than this, then it will return the best trajectory it has found so far)
    # set to 0 to disable time limit

    score = 0
    bestScore = 0
    bestAim = aim
    bestTrajectory = []

    ogAim = aim
    aim.setAngleDeg(aim.getAngleDeg() - maxRangeDegrees/2)

    startTime = time.time()
    for _ in range(maxRangeDegrees*2):
        aim.setAngleDeg(aim.getAngleDeg() + 0.5)
        fakeBalls = []
        previousFakeBall = Ball(startPos.x, startPos.y)
        score = 0
        
        for j in range(depth):
            fakeBall = Ball(previousFakeBall.pos.x, previousFakeBall.pos.y)
            
            if j == 0:
                traj = subVectors(aim, startPos)
                traj.setMag(LAUNCH_FORCE)
                fakeBall.applyForce(traj)

            if j != 0:
                fakeBall.applyForce(previousFakeBall.acc)
                fakeBall.applyForce(previousFakeBall.vel)

            #### collision ####
            queryRect = Rectangle(fakeBall.pos.x, fakeBall.pos.y, queryRectSize, queryRectSize)
            pegsInRange = quadtree.query(queryRect)
            for p in pegsInRange:
                ballTouchingPeg = isBallTouchingPeg(fakeBall, p, dt)
                if ballTouchingPeg:
                    fakeBall = resolveCollision(fakeBall, [p], dt)
                    # add points
                    if not p.isHit: 
                        p.isHit = True
                        if p.color == "orange":
                            score += 1000000 #(1 million points) this makes orange pegs a high priority
                        else:
                            score += 10

            fakeBall.update()

            if fakeBall.pos.y > configs["HEIGHT"]:
                fakeBall.vel.x = 0
                fakeBall.vel.y = 0
            
            fakeBalls.append(fakeBall)
            previousFakeBall = fakeBall

            if bestScore < 10:
                bestScore = 0
                bestAim = subVectors(ogAim, startPos)

            if score > bestScore:
                bestScore = score
                bestAim = traj
                bestTrajectory = fakeBalls

            # if time is up, then return the best trajectory
            if time.time() - startTime > timeLimit and timeLimit != 0:
                return bestAim, bestScore, bestTrajectory

    return bestAim, bestScore, bestTrajectory


def getLaunchAngles(start: Vector,
                     target: Vector,
                     speed: float = LAUNCH_FORCE) -> list[float]:
    """
    Compute the two possible launch angles (in radians) required
    to hit `target` from `start` at given scalar launch `speed`.
    Returns [low_angle, high_angle], or [] if unreachable.
    """
    dx = target.x - start.x
    # screen y grows DOWN, so invert for physics y-up
    dy = start.y - target.y

    v2 = speed*speed
    g  = gravity.y

    # guard vertical shot
    if abs(dx) < 1e-6:
        # max height = v^2/(2g)
        if dy > v2/(2*g):
            # unreachable
            return []
        return [3/2*pi]   # 270 degrees, straight down

    # discriminant of v^4 - g*(g x^2 + 2 y v^2)
    disc = v2*v2 - g*(g*dx*dx + 2*dy*v2)
    if disc < 0:
        return []

    sqrt_d = sqrt(disc)
    # θ = atan( (v^2 ± sqrt(disc)) / (g·x) )
    low  = atan((v2 - sqrt_d)/(g*dx))
    high = atan((v2 + sqrt_d)/(g*dx))

    # if target is left of start, shift both angles by pi
    if dx < 0:
        low  += pi
        high += pi
    return [low, high]