import sys # used to exit the program immediately
import pygame # used for input, audio and graphics
from random import randint

##### local imports #####
from config import WIDTH, HEIGHT, gravity, LAUNCH_FORCE, trajectoryDepth, bucketVelocity
from trajectory import calcTrajectory
from audio import playSoundPitch

# refer to the vectors.py module for information on these functions
from vectors import Vector, subVectors
from collision import isBallTouchingPeg, resolveCollision

from ball import Ball
from peg import Peg
from bucket import Bucket

##### pygame stuff #####
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))  # display surface
clock = pygame.time.Clock()  # game clock
pygame.display.set_caption("Peggle Clone")

# AUDIO
launch_sound = pygame.mixer.Sound("resources/audio/sounds/shoot_ball.ogg")
low_hit_sound = pygame.mixer.Sound("resources/audio/sounds/peghit_low.ogg")
normal_hit_sound = pygame.mixer.Sound("resources/audio/sounds/peghit.ogg")
max_hit_sound = pygame.mixer.Sound("resources/audio/sounds/peg_hit_max.ogg")
powerUpSpooky1 = pygame.mixer.Sound("resources/audio/sounds/powerup_spooky1.ogg")
powerUpSpooky2 = pygame.mixer.Sound("resources/audio/sounds/powerup_spooky2.ogg")
powerUpMultiBall = pygame.mixer.Sound("resources/audio/sounds/powerup_multiball.ogg")
freeBallSound = pygame.mixer.Sound("resources/audio/sounds/freeball2.ogg")

pygame.mixer.music.load("resources/audio/music/peggle_music_1.wav")
pygame.mixer.music.play(-1) # looping forever

#Background image
backgroundImg = pygame.image.load("resources/images/background960x720.jpg")
backgroundImg =  pygame.transform.scale(backgroundImg, (WIDTH, HEIGHT))


##### drawing functions #####
def drawCircle(x, y, rad, rgb):
    pygame.draw.circle(screen, (rgb), [x, y], rad)

def drawLine(x1,y1,x2,y2):
    pygame.draw.line(screen, (255, 0, 0),[x1, y1],[x2,y2])

### testing stuff ###
balls = []
balls.append(Ball(WIDTH/2, HEIGHT/25))
ball = balls[0]
# create pegs
pegs = []
def createPegs():
    for j in range(9):
        for i in range(25):
            i += 1
            if (j%2):
                newPeg = Peg(WIDTH-i * 50, 50 + HEIGHT - j*(HEIGHT/9))
            else:
                newPeg = Peg(75 + WIDTH-i * 50, 50 + HEIGHT - j*(HEIGHT/9))
            
            pegs.append(newPeg)

            # randomly create orange pegs
            if randint(0, 300) > 250:
                newPeg.isOrange= True
                newPeg.color = "orange"
                newPeg.update_color()
            
            # randomly create Green pegs
            if randint(0, 300) > 290:
                newPeg.isPowerUp= True
                newPeg.color = "green"
                newPeg.update_color()

createPegs()

i = 0 # this is stupid, I will remove this later
ballImg = pygame.image.load("resources/images/balls/16x16/ball.png")

bucket = Bucket()

ballsRemaining = 10
freeBall = False
powerUpType = "spooky"
powerUpActive = False
powerUpCount = 0
pitch = 1.0
pitchRaiseCount = 0
showCollision = False
previousAim = Vector(0,1)

##### main loop #####
while True:
    for event in pygame.event.get():  # check events and quit if the program is closed
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                ball.reset()
                balls.clear()
                balls.append(Ball(WIDTH/2, HEIGHT/25))
                ball = balls[0]
                pegs.clear()
                createPegs()
            if event.key == pygame.K_1:
                if showCollision == False:
                    showCollision = True
                else:
                    showCollision = False
            if event.key == pygame.K_2:
                if trajectoryDepth == 3000:
                    trajectoryDepth = 75
                else:
                    trajectoryDepth = 3000
            previousAim = Vector(0,1)

    mouseClicked = pygame.mouse.get_pressed() # get the mouse click state
    mx, my = pygame.mouse.get_pos()  # get mouse position as 'mx' and 'my'

    launchAim = Vector(mx,my) # use the mouse position as a vector to calculate the path that is being aimed

    #print the frametime
    elapsedTime = clock.get_time()
    print(elapsedTime)

    # calculate trajectory
    if not ball.isAlive:
        if previousAim.vy != launchAim.vy or previousAim.vx != launchAim.vx: # only calculate the trajectory if the mouse has been moved - reduces cpu time
            trajectory = calcTrajectory(launchAim, ball.pos, pegs, showCollision, trajectoryDepth)

    previousAim = Vector(mx, my)

    if mouseClicked[0] and not ball.isAlive:
        ball.isLaunch = True
        ball.isAlive = True

    #launch ball
    if ball.isLaunch == True and ball.isAlive == True:
        launchForce = subVectors(launchAim, ball.pos)
        launchForce.setMag(LAUNCH_FORCE)
        ball.applyForce(launchForce)
        pygame.mixer.Sound.play(launch_sound)
        ball.isLaunch = False
        i = 1 # this is also stupid, I will remove this later

    #update balls physics
    for b in balls:
        if b.isAlive:
            #### collision ####
            for p in pegs:
                if(isBallTouchingPeg(p.pos.vx, p.pos.vy, p.radius, b.pos.vx, b.pos.vy, b.radius)):
                    b = resolveCollision(b, p)

                    #Peg hit sounds and peg color update
                    if not p.isHit: 
                        p.isHit = True
                        p.update_color() # change the color to signify it has been hit
                        pitchRaiseCount += 1
                        if p.isPowerUp:
                            if powerUpType == "spooky": 
                                playSoundPitch(powerUpSpooky1)
                                powerUpCount += 1
                            if powerUpType == "multiball": 
                                playSoundPitch(powerUpMultiBall)
                            powerUpActive = True
                        if pitchRaiseCount <= 7:
                            playSoundPitch(low_hit_sound, pitch)
                            pitch -= 0.05 #magic number
                        if pitchRaiseCount == 7: pitch = 1.32 #magic number
                        elif pitchRaiseCount > 7 and pitchRaiseCount < 26:
                            playSoundPitch(normal_hit_sound, pitch)
                            pitch -= 0.045 #magic number
                        elif pitchRaiseCount >= 26:
                            playSoundPitch(normal_hit_sound, pitch)
                            #playSoundPitch(max_hit_sound)

            b.applyForce(gravity)
            b.vel.limitMag(7) #stop the ball from going crazy, this resolves the occasional physics glitches
            b.update()

            # if active spooky powerup
            if powerUpActive and powerUpType == "spooky":
                if b.pos.vy + b.radius > HEIGHT:
                    b.pos.vy = 0 + b.radius 
                    powerUpCount -= 1
                    playSoundPitch(powerUpSpooky2)
                    if powerUpCount < 1:
                        powerUpActive = False 

            if powerUpActive and powerUpType == "multiball":
                newBall =  Ball(b.pos.vx, b.pos.vy)
                newBall.vel.vx = b.vel.vx * -1
                newBall.vel.vy = b.vel.vy * -1
                newBall.isAlive = True
                balls.append(newBall)
                powerUpActive = False

            if not freeBall and bucket.isInBucket(b.pos.vx, b.pos.vy):
                playSoundPitch(freeBallSound)
                freeBall = True
                ballsRemaining += 1

        # this little loop and if statement will determine if all the balls are done       
        done = True
        for b in balls:
            if b.isAlive:
                done = False
    
    #reset everything and remove hit pegs
    if done and i !=0: # this is why its stupid, I need to get rid of the stupid i variable
        balls.clear() # clear all the balls
        balls.append(Ball(WIDTH/2, HEIGHT/25)) # recreate the original ball
        ball = balls[0]
        ball.reset()
        pitch = 1.0
        pitchRaiseCount = 0
        powerUpActive = False
        powerUpCount = 0
        freeBall = False
        done = False
        i = 0
        for p in pegs:
            i =+ 1
            if p.isHit:
                p.isVisible = False
                pegs.remove(p)

    ##bucket
    bucket.update()

    ##### draw #####
    screen.fill((0, 0, 0))  # black screen
    screen.blit(backgroundImg, (0, 0))
    #draw back of bucket
    screen.blit(bucket.bucketBackImg, (bucket.pos.vx, bucket.pos.vy))
    #draw ball(s)
    for b in balls:
        screen.blit(ballImg, (b.pos.vx - b.radius, b.pos.vy - b.radius))
    #draw front of bucket
    screen.blit(bucket.bucketFrontImg, (bucket.pos.vx , bucket.pos.vy))
    #draw pegs
    for p in pegs:
        screen.blit(p.pegImg, (p.pos.vx - p.posAdjust, p.pos.vy - p.posAdjust))
    #draw trajectory path
    done = True
    for b in balls:
        if b.isAlive:
            done = False
    if done:
        for fb in trajectory:
            drawCircle(fb.pos.vx, fb.pos.vy, 5, (0 ,75 ,153))
            

    pygame.display.update()
    clock.tick(144)  # lock game framerate to 144 fps