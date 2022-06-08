from vectors import Vector, subVectors
from ball import Ball
from config import LAUNCH_FORCE, gravity, trajectoryDepth, HEIGHT
from collision import isBallTouchingPeg, resolveCollision

def calcTrajectory(aim : Vector, startPos : Vector, pegs, collision = False, depth = trajectoryDepth):
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
        if collision:
            for p in pegs:
                if(isBallTouchingPeg(p.pos.vx, p.pos.vy, p.radius, fakeBall.pos.vx, fakeBall.pos.vy, fakeBall.radius)):
                    fakeBall = resolveCollision(fakeBall, p) # resolve elastic collision aginst the ball and peg
        else: # if ball has collided then stop calculating and return
            for p in pegs:
                if(isBallTouchingPeg(p.pos.vx, p.pos.vy, p.radius, fakeBall.pos.vx, fakeBall.pos.vy, fakeBall.radius)):
                    return fakeBalls

        fakeBall.applyForce(gravity)
        fakeBall.update()
        
        if fakeBall.pos.vy > HEIGHT:
            break

        if (i % 2):
            fakeBalls.append(fakeBall)

        previousFakeBall = fakeBall
        

    return fakeBalls