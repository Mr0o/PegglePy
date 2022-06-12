from vectors import Vector, subVectors
from ball import Ball
from config import LAUNCH_FORCE, gravity, trajectoryDepth, HEIGHT
from collision import isBallTouchingPeg, resolveCollision

def calcTrajectory(aim : Vector, startPos : Vector, pegs, collisionGuideBall = False, depth = trajectoryDepth):
    hit = False
    previousFakeBall = Ball(startPos.vx, startPos.vy)

    fakeBalls = []
    for i in range(depth):
        fakeBall = Ball(previousFakeBall.pos.vx, previousFakeBall.pos.vy)
        
        if i == 0:
            traj = subVectors(aim, startPos)
            traj.setMag(LAUNCH_FORCE)
            fakeBall.applyForce(traj)

        if i != 0:
            fakeBall.applyForce(previousFakeBall.acc)
            fakeBall.applyForce(previousFakeBall.vel)

        #### collision ####
        if hit:# ##powerup## if ball has collided then stop calculating and return
            for p in pegs:
                if(isBallTouchingPeg(p.pos.vx, p.pos.vy, p.radius, fakeBall.pos.vx, fakeBall.pos.vy, fakeBall.radius)):
                    return fakeBalls
        elif collisionGuideBall and not hit: # if guideBall powerup is being used
            for p in pegs:
                if(isBallTouchingPeg(p.pos.vx, p.pos.vy, p.radius, fakeBall.pos.vx, fakeBall.pos.vy, fakeBall.radius)):
                    fakeBall = resolveCollision(fakeBall, p) # resolve elastic collision aginst the ball and peg
                    hit = True
        elif not collisionGuideBall: # ##normal## if ball has collided then stop calculating and return
             for p in pegs:
                if(isBallTouchingPeg(p.pos.vx, p.pos.vy, p.radius, fakeBall.pos.vx, fakeBall.pos.vy, fakeBall.radius)):
                    return fakeBalls
            

        fakeBall.applyForce(gravity)
        fakeBall.vel.limitMag(5) #stop the ball from going crazy, this resolves the occasional physics glitches
        fakeBall.update()
        
        if fakeBall.pos.vy > HEIGHT:
            break
        
        if (i % 2):
            fakeBalls.append(fakeBall)

        previousFakeBall = fakeBall
        

    return fakeBalls

def findBestTrajectory(aim : Vector, startPos : Vector, pegs):
    score = 0
    bestScore = 0
    bestAim = aim
    bestTrajectory = []

    maxRange = 40 #max range of trajectories to check
    depth = 1200 #how many steps to take in the trajectory calculation
    #aim.setMag(100)
    aim.vx -= (maxRange/8)
    for i in range(maxRange):
        aim.vx += i/4
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

            #### collision ####
            for p in pegs:
                if(isBallTouchingPeg(p.pos.vx, p.pos.vy, p.radius, fakeBall.pos.vx, fakeBall.pos.vy, fakeBall.radius)):
                    fakeBall = resolveCollision(fakeBall, p) # resolve elastic collision aginst the ball and peg
                    # add points
                    if not p.isHit: 
                        p.isHit = True
                        if p.color == "orange":
                            score += 1000000 #(1 million points) this makes orange pegs a higher priority
                        else:
                            score += p.points

            fakeBall.applyForce(gravity)
            fakeBall.vel.limitMag(5) #stop the ball from going crazy, this resolves the occasional physics glitches
            fakeBall.update()

            if fakeBall.pos.vy > HEIGHT:
                fakeBall.vel.vx = 0
                fakeBall.vel.vy = 0
            
            fakeBalls.append(fakeBall)
            previousFakeBall = fakeBall


            if score > bestScore:
                bestScore = score
                bestAim = traj
                bestTrajectory = fakeBalls


        # restore all peg hit states
        for p in pegs:
            p.isHit = False

    return bestAim, bestScore, bestTrajectory

    