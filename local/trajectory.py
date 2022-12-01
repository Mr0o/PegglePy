import time

from local.vectors import Vector, subVectors
from local.ball import Ball
from local.peg import Peg
from local.config import LAUNCH_FORCE, trajectoryDepth, WIDTH, HEIGHT, segmentCount
from local.collision import isBallTouchingPeg, resolveCollision
from local.misc import getBallScreenLocation

def calcTrajectory(aim : Vector, startPos : Vector, pegs : list[Peg], bucketPegs, collisionGuideBall = False, depth = trajectoryDepth, debug = False):
    hit = False
    previousFakeBall = Ball(startPos.vx, startPos.vy)

    #include bucket pegs in the trajectory calculation
    for fakePeg in bucketPegs:
        pegs.append(fakePeg)

    fakeBalls = []
    for i in range(depth):
        fakeBall = Ball(previousFakeBall.pos.vx, previousFakeBall.pos.vy)
        
        if i == 0: # only on the first iteration
            traj = subVectors(aim, startPos)
            traj.setMag(LAUNCH_FORCE)
            fakeBall.applyForce(traj)

        if i != 0: # every iteration except the first
            fakeBall.applyForce(previousFakeBall.acc)
            fakeBall.applyForce(previousFakeBall.vel)


        #### collision ####
        ballScreenPosList = getBallScreenLocation(fakeBall, segmentCount)

        if hit:# ##powerup## if ball has collided then stop calculating and return
            for p in pegs:
                shouldCheckCollision = False
                for ballScreenPos in ballScreenPosList:
                    for pegScreenLocation in p.pegScreenLocations:
                        if ballScreenPos == pegScreenLocation:
                            shouldCheckCollision = True 
    
                if shouldCheckCollision:
                    if isBallTouchingPeg(p.pos.vx, p.pos.vy, p.radius, fakeBall.pos.vx, fakeBall.pos.vy, fakeBall.radius):
                        return fakeBalls
        elif collisionGuideBall and not hit: # if guideBall powerup is being used
            for p in pegs:
                shouldCheckCollision = False
                for ballScreenPos in ballScreenPosList:
                    for pegScreenLocation in p.pegScreenLocations:
                        if ballScreenPos == pegScreenLocation:
                            shouldCheckCollision = True 
                            
                if shouldCheckCollision:
                    if isBallTouchingPeg(p.pos.vx, p.pos.vy, p.radius, fakeBall.pos.vx, fakeBall.pos.vy, fakeBall.radius):
                        fakeBall = resolveCollision(fakeBall, p) # resolve elastic collision aginst the ball and peg
                        hit = True
        elif not collisionGuideBall: # ##normal## if ball has collided then stop calculating and return
            for p in pegs:
                shouldCheckCollision = False
                for ballScreenPos in ballScreenPosList:
                    for pegScreenLocation in p.pegScreenLocations:
                        if ballScreenPos == pegScreenLocation:
                            shouldCheckCollision = True 

                if shouldCheckCollision:
                    if isBallTouchingPeg(p.pos.vx, p.pos.vy, p.radius, fakeBall.pos.vx, fakeBall.pos.vy, fakeBall.radius):
                        if not debug:
                            return fakeBalls
                        else:
                            fakeBall = resolveCollision(fakeBall, p) # resolve elastic collision aginst the ball and peg

            
        fakeBall.update()
        
        if fakeBall.pos.vy > HEIGHT:
            break # if the ball has gone off the screen, then we can stop
        
        fakeBalls.append(fakeBall)

        previousFakeBall = fakeBall
        

    return fakeBalls


def findBestTrajectory(aim: Vector, startPos: Vector, pegs: list[Peg], maxRange = 21, depth = 9000):
    # default maxRange and depth were found using a performance test on a level with 120 pegs, which can be run with the 'performance_test.py' module
    # the default values are the values that gave the best performance (shortest time, but with the greatest depth and range possible)

    maxTimeAllowed = 4 # seconds (if the function takes longer than this, then it will return the best trajectory it has found so far)

    score = 0
    bestScore = 0
    bestAim = aim
    bestTrajectory = []

    ogAim = aim
    
    aim.vx += (round(maxRange*2))

    startTime = time.time()
    for i in range(maxRange):
        aim.vx -= i/2
        fakeBalls = []
        previousFakeBall = Ball(startPos.vx, startPos.vy)
        score = 0
        
        for j in range(depth):
            fakeBall = Ball(previousFakeBall.pos.vx, previousFakeBall.pos.vy)
            
            if j == 0:
                traj = subVectors(aim, startPos)
                traj.setMag(LAUNCH_FORCE)
                fakeBall.applyForce(traj)

            if j != 0:
                fakeBall.applyForce(previousFakeBall.acc)
                fakeBall.applyForce(previousFakeBall.vel)

            ballScreenPosList = getBallScreenLocation(fakeBall, segmentCount)

            #### collision ####
            for p in pegs:
                shouldCheckCollision = False
                for ballScreenPos in ballScreenPosList:
                    for pegScreenLocation in p.pegScreenLocations:
                        if ballScreenPos == pegScreenLocation:
                            shouldCheckCollision = True 
                            
                if shouldCheckCollision:
                    if isBallTouchingPeg(p.pos.vx, p.pos.vy, p.radius, fakeBall.pos.vx, fakeBall.pos.vy, fakeBall.radius):
                        fakeBall = resolveCollision(fakeBall, p) # resolve elastic collision aginst the ball and peg
                        # add points
                        if not p.isHit: 
                            p.isHit = True
                            if p.color == "orange":
                                score += 1000000 #(1 million points) this makes orange pegs a high priority
                            else:
                                score += 10

            fakeBall.update()

            if fakeBall.pos.vy > HEIGHT:
                fakeBall.vel.vx = 0
                fakeBall.vel.vy = 0
            
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
            if time.time() - startTime > maxTimeAllowed:
                return bestAim, bestScore, bestTrajectory

    return bestAim, bestScore, bestTrajectory

    