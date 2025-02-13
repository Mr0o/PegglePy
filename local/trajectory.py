import time

from local.vectors import Vector, subVectors
from local.ball import Ball
from local.peg import Peg
from local.config import LAUNCH_FORCE, trajectoryDepth, queryRectSize
from local.config import configs
from local.collision import isBallTouchingPeg, resolveCollision
from local.quadtree import QuadtreePegs, Rectangle

def calcTrajectory(aim : Vector, startPos : Vector, pegs : list[Peg], bucketPegs, quadtree : QuadtreePegs, collisionGuideBall = False, depth = trajectoryDepth, debugTrajectory = False):
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
                ballTouchingPeg = isBallTouchingPeg(p.pos.x, p.pos.y, p.radius, fakeBall.pos.x, fakeBall.pos.y, fakeBall.radius)
                if ballTouchingPeg:
                    return fakeBalls
        elif collisionGuideBall and not hit: # if guideBall powerup is being used
            queryRect = Rectangle(fakeBall.pos.x, fakeBall.pos.y, queryRectSize, queryRectSize)
            pegsInRange = quadtree.query(queryRect)
            for p in pegsInRange:         
                ballTouchingPeg = isBallTouchingPeg(p.pos.x, p.pos.y, p.radius, fakeBall.pos.x, fakeBall.pos.y, fakeBall.radius)
                if ballTouchingPeg:
                    fakeBall = resolveCollision(fakeBall, p)
                    hit = True
        elif not collisionGuideBall: # ##normal## if ball has collided then stop calculating and return
            queryRect = Rectangle(fakeBall.pos.x, fakeBall.pos.y, queryRectSize, queryRectSize)
            pegsInRange = quadtree.query(queryRect)
            for p in pegsInRange:
                ballTouchingPeg = isBallTouchingPeg(p.pos.x, p.pos.y, p.radius, fakeBall.pos.x, fakeBall.pos.y, fakeBall.radius)
                if ballTouchingPeg:
                    if not debugTrajectory:
                        return fakeBalls
                    else:
                        fakeBall = resolveCollision(fakeBall, p)

            
        fakeBall.update()
        
        if fakeBall.pos.y > configs["HEIGHT"]:
            break # if the ball has gone off the screen, then we can stop
        
        fakeBalls.append(fakeBall)

        previousFakeBall = fakeBall
        

    return fakeBalls


def findBestTrajectory(aim: Vector, startPos : Vector, pegs : list[Peg], quadtree : QuadtreePegs, maxRangeDegrees = 21, depth = 9000, setTimeLimit = 25):
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
            queryRect = Rectangle(fakeBall.pos.x, fakeBall.pos.y, fakeBall.radius*1.5, fakeBall.radius*1.5)
            pegsInRange = quadtree.query(queryRect)
            for p in pegsInRange:
                ballTouchingPeg = isBallTouchingPeg(p.pos.x, p.pos.y, p.radius, fakeBall.pos.x, fakeBall.pos.y, fakeBall.radius)
                if ballTouchingPeg:
                    fakeBall = resolveCollision(fakeBall, p)
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

    