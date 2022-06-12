import sys # used to exit the program immediately
import pygame # used for input, audio and graphics
from random import randint

##### local imports #####
from config import WIDTH, HEIGHT, gravity, LAUNCH_FORCE, trajectoryDepth, powerUpType, ballsRemaining, ballImg, freeBall, powerUpActive, powerUpCount, pitch, pitchRaiseCount, previousAim, shouldClear, debug
from trajectory import calcTrajectory, findBestTrajectory
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
powerUpZenBall = pygame.mixer.Sound("resources/audio/sounds/gong.ogg")
powerUpZenBallHit = pygame.mixer.Sound("resources/audio/sounds/powerup_zen3.ogg")
powerUpGuideBall = pygame.mixer.Sound("resources/audio/sounds/powerup_guide.ogg")
freeBallSound = pygame.mixer.Sound("resources/audio/sounds/freeball2.ogg")
failSound = pygame.mixer.Sound("resources/audio/sounds/fail.ogg")


# play random music
r = randint(1, 3)
if r == 1:
    pygame.mixer.music.load("resources/audio/music/peggle_music_1.wav")
if r == 2:
    pygame.mixer.music.load("resources/audio/music/peggle_music_2.wav")
if r == 3:
    pygame.mixer.music.load("resources/audio/music/peggle_music_9.wav")
pygame.mixer.music.play(-1) # looping forever

#Background image
backgroundImg = pygame.image.load("resources/images/background960x720.jpg")
backgroundImg =  pygame.transform.scale(backgroundImg, (WIDTH, HEIGHT))

#font
ballCountFont = pygame.font.Font("resources/fonts/Evogria.otf", 30)
infoFont = pygame.font.Font("resources/fonts/Evogria.otf", 16)
debugFont = pygame.font.Font("resources/fonts/Evogria.otf", 12)

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
orangeCount = 35
pegs = []
def createPegs(orangeCount):
    for j in range(7):
        for i in range(23):
            if (j%2):
                newPeg = Peg((WIDTH-i * 50) - 50, 50 + HEIGHT - j*(HEIGHT/8) - 120)
            else:
                newPeg = Peg((25 + WIDTH-i * 50) - 50, 50 + HEIGHT - j*(HEIGHT/8) - 120)
            
            pegs.append(newPeg)

    #create orange pegs
    for _ in range(orangeCount):
        i = randint(0, len(pegs)-1)
        p = pegs[i]
        p.color = "orange"
        p.isOrang = True
        p.update_color()
    #create green pegs
    for _ in range(2):
        i = randint(0, len(pegs)-1)
        p = pegs[i]
        p.color = "green"
        p.isPowerUp = True
        p.update_color()

createPegs(orangeCount)

def getScoreMultiplier(remainingOrangePegs, pegsHit = 0):
    #first multiplier based on remaining orange pegs
    multiplier = 1
    if remainingOrangePegs >= 30:
        multiplier = 1
    elif remainingOrangePegs >= 25 and remainingOrangePegs < 30:
        multiplier = 2
    elif remainingOrangePegs >= 15 and remainingOrangePegs < 25:
        multiplier = 5
    elif remainingOrangePegs >= 5 and remainingOrangePegs < 15:
        multiplier = 100
    elif remainingOrangePegs >= 2 and remainingOrangePegs < 5:
        multiplier = 500
    elif remainingOrangePegs >= 1 and remainingOrangePegs < 2:
        multiplier = 2000
    #second multiplier based on number of pegs hit by the current ball
    if pegsHit >= 5 and pegsHit < 8:
        multiplier *= 2
    elif pegsHit >= 8 and pegsHit < 12:
        multiplier *= 5
    elif pegsHit >= 12 and pegsHit < 16:
        multiplier *= 8
    elif pegsHit >= 16 and pegsHit < 25:
        multiplier *= 10
    elif pegsHit >= 25:
        multiplier *= 20
    return multiplier

bucket = Bucket()
pointsEarned = []
score = 0
drawTrajectory = False

addNewBall = False
done = False
pegsHit = 0

fineTuneAmount = 0

trajectory = []
launchAim = Vector(0,0)

##### main loop #####
while True:
    for event in pygame.event.get():  # check events and quit if the program is closed
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                #reset everything
                shouldClear = False
                balls.clear() # clear all the balls
                balls.append(Ball(WIDTH/2, HEIGHT/25)) # recreate the original ball
                ball = balls[0]
                ball.reset()
                pitch = 1.0
                pitchRaiseCount = 0
                freeBall = False
                done = False
                powerUpActive = False
                powerUpCount = 0
                ball = balls[0]
                pegs.clear()
                orangeCount = 30
                createPegs(orangeCount)
                score = 0
                ballsRemaining = 10
                pegsHit = 0
            if event.key == pygame.K_1:
                if debug == False:
                    debug = True
                else:
                    debug = False
        if event.type == pygame.MOUSEWHEEL:
            fineTuneAmount += event.y


    elapsedTime = clock.get_time()

    mouseClicked = pygame.mouse.get_pressed() # get the mouse click state
    mx, my =  pygame.mouse.get_pos()  # get mouse position as 'mx' and 'my'
    mx_rel, my_rel = pygame.mouse.get_rel()
    
    if mx_rel == 0 and my_rel == 0:
        launchAim = Vector(mx + fineTuneAmount, my) # use the mouse position as a vector to calculate the path that is being aimed
    else:
        launchAim = Vector(mx,my) # use the mouse position as a vector to calculate the path that is being aimed
        fineTuneAmount = 0

    # calculate trajectory
    if not ball.isAlive:
        if powerUpActive and powerUpType == "guideball":
            trajectoryDepth = 750 #powerup
        else:
            trajectoryDepth = 75 #normal
        if previousAim.vx != launchAim.vx or previousAim.vy != launchAim.vy: # only calculate the trajectory if the mouse has been moved - reduces cpu time
            trajectory = calcTrajectory(launchAim, ball.pos, pegs, (powerUpType == "guideball" and powerUpActive), trajectoryDepth)
    previousAim = Vector(launchAim.vx, launchAim.vy)

    #if mouse clicked then trigger ball launch 
    if mouseClicked[0] and not ball.isAlive:
        if powerUpActive and powerUpType == "guideball":
            powerUpCount -= 1
            if powerUpCount < 1:
                powerUpActive = False
        ball.isLaunch = True
        ball.isAlive = True

    #launch ball
    if ball.isLaunch and ball.isAlive:
        if not powerUpType == "zenball": # if powerup type is anything but zenball, launch normal
            launchForce = subVectors(launchAim, ball.pos)
            launchForce.setMag(LAUNCH_FORCE)
            ball.applyForce(launchForce)
            pygame.mixer.Sound.play(launch_sound)
            ball.isLaunch = False
            shouldClear = True
        elif not powerUpActive and powerUpType == "zenball": # if powerup type is zenball and it is not active then normal launch
            launchForce = subVectors(launchAim, ball.pos)
            launchForce.setMag(LAUNCH_FORCE)
            ball.applyForce(launchForce)
            pygame.mixer.Sound.play(launch_sound)
            ball.isLaunch = False
            shouldClear = True
            drawTrajectory = False
    
    # if active zenball powerup - launch
    if ball.isLaunch and ball.isAlive and powerUpType == "zenball" and powerUpActive:
        # find the best shot
        playSoundPitch(powerUpZenBall, 0.94)
        bestAim, bestScore, bestTrajectory = bestShotLaunch = findBestTrajectory(launchAim, ball.pos, pegs)

        if bestScore > 0: 
            playSoundPitch(powerUpZenBall, 0.98)
            ball.applyForce(bestAim)
        elif bestScore < 1: # if there is no possible shot with the zen ball to earn points then it has failed
            playSoundPitch(failSound)
            ball.applyForce(bestAim)

        #for debug
        drawTrajectory = True
        
        pygame.mixer.Sound.play(launch_sound)
        ball.isLaunch = False
        shouldClear = True
        powerUpCount -= 1
        if powerUpCount < 1:
            powerUpActive = False

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
                        pegsHit += 1
                        p.update_color() # change the color to signify it has been hit
                        pitchRaiseCount += 1
                        if p.color == "orange":
                            orangeCount -= 1
                        if p.isPowerUp:
                            if powerUpType == "spooky": 
                                playSoundPitch(powerUpSpooky1)
                            if powerUpType == "multiball": 
                                playSoundPitch(powerUpMultiBall)
                                addNewBall = True
                            if powerUpType == "zenball":
                                playSoundPitch(powerUpZenBallHit)
                            if powerUpType == "guideball":
                                playSoundPitch(powerUpGuideBall)
                                powerUpCount += 2
                            powerUpCount += 1   
                            powerUpActive = True
                        if pitchRaiseCount <= 7:
                            if not p.isPowerUp: playSoundPitch(low_hit_sound, pitch)
                            pitch -= 0.05 #magic number
                        if pitchRaiseCount == 7: pitch = 1.32 #magic number
                        elif pitchRaiseCount > 7 and pitchRaiseCount < 26:
                            if not p.isPowerUp: playSoundPitch(normal_hit_sound, pitch)
                            pitch -= 0.045 #magic number
                        elif pitchRaiseCount >= 26:
                            if not p.isPowerUp: playSoundPitch(normal_hit_sound, pitch)
                        
                        #keep track of points earned
                        #pointsEarned.append(p.points)
                        score += (p.points * getScoreMultiplier(orangeCount, pegsHit))
                            
            b.applyForce(gravity)
            b.vel.limitMag(5) #stop the ball from going crazy, this resolves the occasional physics glitches
            b.update()

            # if active spooky powerup
            if powerUpActive and powerUpType == "spooky":
                if b.pos.vy + b.radius > HEIGHT:
                    b.pos.vy = 0 + b.radius 
                    powerUpCount -= 1
                    playSoundPitch(powerUpSpooky2)
                    if powerUpCount < 1:
                        powerUpActive = False 

            # if active multiball powerup
            if addNewBall and powerUpType == "multiball":
                newBall =  Ball(b.pos.vx, b.pos.vy)
                newBall.vel.vx = b.vel.vx * -1
                newBall.vel.vy = b.vel.vy * -1
                newBall.isAlive = True
                balls.append(newBall)
                addNewBall = False
                
                    
            if not freeBall and bucket.isInBucket(b.pos.vx, b.pos.vy):
                playSoundPitch(freeBallSound)
                freeBall = True
                ballsRemaining += 1

    # this little loop and if statement will determine if any of the balls are still alive and therfore if it is done or not     
    done = True
    for b in balls:
        if b.isAlive:
            done = False
    #reset everything and remove hit pegs
    if done and shouldClear:
        shouldClear = False
        balls.clear() # clear all the balls
        balls.append(Ball(WIDTH/2, HEIGHT/25)) # recreate the original ball
        ball = balls[0]
        ball.reset()
        pitch = 1.0
        pitchRaiseCount = 0
        freeBall = False
        done = False
        ballsRemaining -= 1
        pegsHit = 0
        previousAim = Vector(0,1)
        if powerUpType == "multiball":
            powerUpActive = False
            powerUpCount = 0
        for _ in range(5): # temporary fix to bug with pegs not being removed
            for p in pegs:
                if p.isHit:
                    pegs.remove(p)
        for s in pointsEarned:
            score += s
        print(score)

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
    #draw text
    #show how many balls are left
    ballText = ballCountFont.render(str(ballsRemaining), False, (200, 200, 200))
    screen.blit(ballText,(50, 50))
    #show the score
    scoreText = ballCountFont.render(str(score), False, (255, 60, 20))
    screen.blit(scoreText,(150, 50))
    #show the powerup information
    if powerUpActive:
        powerUpText = infoFont.render(powerUpType + ": " + str(powerUpCount), False, (50, 255, 20))
        screen.blit(powerUpText, (int(WIDTH/2 - 50), 5))
    else:
        powerUpText = infoFont.render(powerUpType + ": " + str(powerUpCount), False, (50, 170, 20))
        screen.blit(powerUpText, (int(WIDTH/2 - 50), 5))
    
    #debugging stuff
    if debug:
        if (elapsedTime < 10): # decide whether green text or red text
            frameColor = (0, 255, 50) # green
        else:
            frameColor = (255, 50, 0) #red
        #print frametime
        frameTime = debugFont.render(str(elapsedTime) + " ms" , False, (frameColor))
        screen.blit(frameTime,(5, 10))
        #print number of orange pegs remaining and score multiplier
        orangeCountText = debugFont.render(str(orangeCount) + " orange pegs left" , False, (255,255,255))
        screen.blit(orangeCountText,(100, 35))
        scoreMultiplierText = debugFont.render("x"+str(getScoreMultiplier(orangeCount, pegsHit)) , False, (255,255,255))
        screen.blit(scoreMultiplierText,(100, 50))
        #print ball velocity
        ballPosText = debugFont.render("Velocity: X:" + str(ball.vel.vx) +" Y:"+str(ball.vel.vy), False, (255,255,255))
        screen.blit(ballPosText, (100,20))
        #draw zenball trajectory
        if drawTrajectory and not done and powerUpType == "zenball":
            for fb in bestTrajectory:
                drawCircle(fb.pos.vx, fb.pos.vy, 1, (0 ,153 ,10))
                
            

    pygame.display.update()
    clock.tick(144)  # lock game framerate to 144 fps