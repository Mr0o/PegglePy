from vectors import Vector, subVectors
from ball import Ball
from config import LAUNCH_FORCE, trajectoryDepth, WIDTH, HEIGHT, segmentCount
from collision import isBallTouchingPeg, resolveCollision

# copied from run.py (kinda sloppy ngl)
def getBallScreenLocation(p, segmentCount):
    segmentWidth = WIDTH/segmentCount
    for i in range(segmentCount+1):
        if p.pos.vx > segmentWidth*(i-1) -p.radius and p.pos.vx < segmentWidth*i +p.radius:
            return i

def calcTrajectory(aim : Vector, startPos : Vector, pegs, collisionGuideBall = False, depth = trajectoryDepth, debug = False):
    hit = False
    previousFakeBall = Ball(startPos.vx, startPos.vy)

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

        ballScreenPos = getBallScreenLocation(fakeBall, segmentCount)

        #### collision ####
        if hit:# ##powerup## if ball has collided then stop calculating and return
            for p in pegs:
                if ballScreenPos == p.pegScreenLocation or ballScreenPos == p.pegScreenLocation2:
                    if isBallTouchingPeg(p.pos.vx, p.pos.vy, p.radius, fakeBall.pos.vx, fakeBall.pos.vy, fakeBall.radius):
                        return fakeBalls
        elif collisionGuideBall and not hit: # if guideBall powerup is being used
            for p in pegs:
                if ballScreenPos == p.pegScreenLocation or ballScreenPos == p.pegScreenLocation2:
                    if isBallTouchingPeg(p.pos.vx, p.pos.vy, p.radius, fakeBall.pos.vx, fakeBall.pos.vy, fakeBall.radius):
                        fakeBall = resolveCollision(fakeBall, p) # resolve elastic collision aginst the ball and peg
                        hit = True
        elif not collisionGuideBall: # ##normal## if ball has collided then stop calculating and return
            for p in pegs:
                if ballScreenPos == p.pegScreenLocation or ballScreenPos == p.pegScreenLocation2:
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


def findBestTrajectory(aim : Vector, startPos : Vector, pegs, maxRange = 40, depth = 1200):
    score = 0
    bestScore = 0
    bestAim = aim
    bestTrajectory = []

    ogAim = aim

    #maxRange = 40 #max range of trajectories to check
    #depth = 1200 #how many steps to take in the trajectory calculation
    
    aim.vx += (round(maxRange*2))
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

            ballScreenPos = getBallScreenLocation(fakeBall, segmentCount)

            #### collision ####
            for p in pegs:
                if ballScreenPos == p.pegScreenLocation or ballScreenPos == p.pegScreenLocation2:
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


        # restore all peg hit states
        for p in pegs:
            p.isHit = False

    return bestAim, bestScore, bestTrajectory

    