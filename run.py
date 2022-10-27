from cmath import inf
from math import sqrt
from operator import le
from sqlite3 import Time
import sys # used to exit the program immediately

## disable pygame init message - "Hello from the pygame community..." ##
import contextlib

from trigger_events import TimedEvent
with contextlib.redirect_stdout(None):
    import pygame # used for input, audio and graphics

from random import randint

##### local imports #####
from config import *
from trajectory import calcTrajectory, findBestTrajectory
from audio import playSoundPitch
from load_level import loadData

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
drumRoll = pygame.mixer.Sound("resources/audio/sounds/drum_roll.ogg")
cymbal = pygame.mixer.Sound("resources/audio/sounds/cymbal.ogg")
longShotSound = pygame.mixer.Sound("resources/audio/sounds/long_shot.ogg")
sighSound = pygame.mixer.Sound("resources/audio/sounds/sigh.ogg")

def loadRandMusic():
    # play random music
    r = randint(1, 10)
    pygame.mixer.music.load("resources/audio/music/Peggle Beat " + str(r) + " (Peggle Deluxe).mp3")
        
    

#Background image
backgroundImg = pygame.image.load("resources/images/background960x720.jpg")
backgroundImg =  pygame.transform.scale(backgroundImg, (WIDTH, HEIGHT))

#font
ballCountFont = pygame.font.Font("resources/fonts/Evogria.otf", 30)
infoFont = pygame.font.Font("resources/fonts/Evogria.otf", 16)
debugFont = pygame.font.Font("resources/fonts/Evogria.otf", 14)
menuFont = pygame.font.Font("resources/fonts/Evogria.otf", 90)

##### drawing functions #####
def drawCircle(x, y, rad, rgb):
    pygame.draw.circle(screen, (rgb), [x, y], rad)

def drawLine(x1,y1,x2,y2):
    pygame.draw.line(screen, (255, 0, 0),[x1, y1],[x2,y2])

### testing stuff ###
balls = []
balls.append(Ball(WIDTH/2, HEIGHT/25))
ball = balls[0]

# iterate through each peg x,y position to determine its location on the screen
def assignPegScreenLocation(pegs, segmentCount):
    segmentWidth = WIDTH/segmentCount
    for p in pegs:
        for i in range(segmentCount+1):
            if p.pos.vx >= segmentWidth*(i-1) and p.pos.vx <= segmentWidth*i:
                p.pegScreenLocation = i
        
        # second check for cases where the peg is on the segment boundary from the right
        for i in range(segmentCount+1):
            if p.pegScreenLocation == i and (p.pos.vx >= segmentWidth*i -p.radius*2 and p.pos.vx <= segmentWidth*(i+1) +p.radius*2): 
                p.pegScreenLocation2 = i+1
                break
        # third check for cases where the peg is on the segment boundary from the left
        for i in range(segmentCount+1):
            if p.pegScreenLocation == i+1 and (p.pos.vx >= segmentWidth*(i-1) -p.radius*2 and p.pos.vx <= segmentWidth*i +p.radius*2): 
                p.pegScreenLocation2 = i
                break


def getBallScreenLocation(p, segmentCount):
    segmentWidth = WIDTH/segmentCount
    for i in range(segmentCount+1):
        if p.pos.vx > segmentWidth*(i-1) -p.radius and p.pos.vx < segmentWidth*i +p.radius:
            return i


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
    if pegsHit >= 10 and pegsHit < 15:
        multiplier *= 2
    elif pegsHit >= 15 and pegsHit < 18:
        multiplier *= 5
    elif pegsHit >= 18 and pegsHit < 22:
        multiplier *= 8
    elif pegsHit >= 22 and pegsHit < 25:
        multiplier *= 10
    elif pegsHit >= 25 and pegsHit < 35:
        multiplier *= 20
    elif pegsHit >= 35: # if you are hitting this many pegs with one ball, you are either very lucky or cheating but this is the reward either way
        multiplier *= 100
    return multiplier


def createPegColors(pegs) -> list[Peg]:
    orangeCount = 25

    if len(pegs) < 25:
        if debug: print("WARN: Level has less than 25 pegs, continuing anyway...")
        orangeCount = len(pegs) - 1
    elif len(pegs) > 120:
        if debug: print("WARN: Level has excessive number of pegs, expect performance issues...")

    #create orange pegs
    numOfOrangePegs = 0
    while(numOfOrangePegs < orangeCount):
        i = randint(0, len(pegs)-1)
        p = pegs[i]
        p.color = "orange"
        p.isOrang = True
        p.update_color()

        # must have exactly 25 orange pegs
        numOfOrangePegs = 0
        for peg in pegs:
            if peg.color == "orange":
                numOfOrangePegs += 1
        
        # invalid level, but we'll allow it with a warning
        

        

    #create green pegs
    for _ in range(2):
        i = randint(0, len(pegs)-1)
        p = pegs[i]
        p.color = "green"
        p.isPowerUp = True
        p.update_color()

    return pegs


def loadLevel(createPegColors):
    # load the pegs from a level file (pickle)
    pegs = loadData()
    originPegs = pegs.copy()

    pegs = createPegColors(pegs)

    orangeCount = 0
    for peg in pegs:
        if peg.color == "orange": orangeCount += 1

    return pegs, originPegs, orangeCount


def resetGame(balls, assignPegScreenLocation, createPegColors, bucket, pegs, originPegs):
    #reset everything
    shouldClear = False
    balls.clear() # clear all the balls
    balls.append(Ball(WIDTH/2, HEIGHT/25)) # recreate the original ball
    ball = balls[0]
    ball.reset()
    pitch = 1.0
    pitchRaiseCount = 0
    done = False
    powerUpActive = False
    powerUpCount = 0
    ball = balls[0]
    pegs.clear()
    pegs = originPegs.copy()
    for peg in pegs: 
        peg.reset()
    pegs = createPegColors(pegs)
    assignPegScreenLocation(pegs, segmentCount)
    orangeCount = 0
    for peg in pegs:
        if peg.color == "orange": orangeCount += 1
    score = 0
    ballsRemaining = 10
    pegsHit = 0
    bucket.reset()
    lastHitPeg = None
    gameOver = False
    alreadyPlayedOdeToJoy = False
    frameRate = 144
    LongShotBonus = False
    # change the song
    pygame.mixer.music.stop()
    loadRandMusic()
    pygame.mixer.music.play(-1) # looping forever
    return ballsRemaining,powerUpActive,powerUpCount,pitch,pitchRaiseCount,ball,score,pegsHit,pegs,orangeCount,gameOver,alreadyPlayedOdeToJoy,frameRate,LongShotBonus


def distBetweenTwoPoints(x1,y1, x2,y2):
    return sqrt(((x1-x2)**2) + ((y1-y2)**2))


# some extra global variable initialization stuff

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

debugCollision = False
gamePaused = False
gameOver = False
alreadyPlayedOdeToJoy = False
closeBall = None
longShotBonus = False
debugTrajectory = False


longShotTextTimer = TimedEvent()
delayTimer = TimedEvent(1)

pegs, originPegs, orangeCount = loadLevel(createPegColors)

#createPegs(orangeCount) # must create pegs BEFORE locations are assigned
assignPegScreenLocation(pegs, segmentCount)

loadRandMusic()
pygame.mixer.music.play(-1) # looping forever

##### main loop #####
while True:
    for event in pygame.event.get():  # check events and quit if the program is closed
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                # horrifying function that resets the game
                ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver ,alreadyPlayedOdeToJoy, frameRate, longShotBonus = resetGame(balls, assignPegScreenLocation, createPegColors, bucket, pegs, originPegs)
            if event.key == pygame.K_1: # enable or disable debug features
                if debug == False:
                    debug = True
                else:
                    debug = False
            if event.key == pygame.K_2: # enable or disable cheats
                if cheats == False:
                    cheats = True
                else:
                    cheats = False
            if event.key == pygame.K_3: # cycle through all powerpegs, originPegs = loadLevel(createPegColors) up types
                if powerUpType == "spooky":
                    powerUpType = "multiball"
                elif powerUpType == "multiball":
                    powerUpType = "zenball"
                elif powerUpType == "zenball":
                    powerUpType = "guideball"
                elif powerUpType == "guideball":
                    powerUpType = "spooky-multiball"
                elif powerUpType == "spooky-multiball":
                    powerUpType = "spooky"
            if event.key == pygame.K_4: # enable or disable debug view of collision segments
                if debugCollision == False:
                    debugCollision = True
                else:
                    debugCollision = False
            if event.key == pygame.K_5: # debug - decrease collision segment count
                segmentCount -= 1
                assignPegScreenLocation(pegs, segmentCount) # reassign each pegs segment location
            if event.key == pygame.K_6: # debug - increase collision segment count
                segmentCount += 1
                assignPegScreenLocation(pegs, segmentCount) # reassign each pegs segment location
            if event.key == pygame.K_7: # debug - enable or disable full trajectory drawing
                if debugTrajectory == False:
                    debugTrajectory = True
                else:
                    debugTrajectory = False
            if event.key == pygame.K_l: # load a new level
                pygame.mixer.music.stop()
                pegs, originPegs, orangeCount = loadLevel(createPegColors)
                # horrifying function that resets the game
                ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver ,alreadyPlayedOdeToJoy, frameRate, longShotBonus = resetGame(balls, assignPegScreenLocation, createPegColors, bucket, pegs, originPegs)
            if event.key == pygame.K_ESCAPE: # enable or disable cheats
                if gamePaused == False:
                    gamePaused = True
                else:
                    gamePaused = False
            if event.key == pygame.K_0:
                if frameRate == 144:
                    frameRate = 30
                else:
                    frameRate = 144

        if event.type == pygame.MOUSEWHEEL:
            fineTuneAmount += event.y
    
    mouseClicked = pygame.mouse.get_pressed() # get the mouse click state
    mx, my =  pygame.mouse.get_pos()  # get mouse position as 'mx' and 'my'
    mx_rel, my_rel = pygame.mouse.get_rel() # get mouse relative position as 'mx_rel' and 'my_rel'      

    # reset the game when the game is over and the mouse is clicked
    if mouseClicked[0] and gameOver:
        delayTimer = TimedEvent(0.25) # prevent the click from instantly launching a ball
        # horrifying function that resets the game
        ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver ,alreadyPlayedOdeToJoy, frameRate, longShotBonus = resetGame(balls, assignPegScreenLocation, createPegColors, bucket, pegs, originPegs)


    # do not update any game physics or game logic if the game is paused or over
    if not gamePaused and not gameOver:
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
                if debugTrajectory:
                    trajectoryDepth = 2500
            if previousAim.vx != launchAim.vx or previousAim.vy != launchAim.vy: # only calculate the trajectory if the mouse has been moved - reduces cpu time
                trajectory = calcTrajectory(launchAim, ball.pos, pegs, (powerUpType == "guideball" and powerUpActive), trajectoryDepth, debugTrajectory)
        previousAim = Vector(launchAim.vx, launchAim.vy)

        delayTimer.update() # prevent the ball from launching instantly after the game is reset
        #if mouse clicked then trigger ball launch 
        if mouseClicked[0] and not ball.isAlive and delayTimer.isTriggered:
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
        
        # cheats (force enable power up)
        if cheats:
            powerUpActive = True

        # if active zenball powerup - launch
        if ball.isLaunch and ball.isAlive and powerUpType == "zenball" and powerUpActive:
            # find the best shot
            playSoundPitch(powerUpZenBall, 0.93)
            bestAim, bestScore, bestTrajectory = bestShotLaunch = findBestTrajectory(launchAim, ball.pos, pegs, 80, 1800)

            if bestScore >= 10: 
                playSoundPitch(powerUpZenBall, 0.99)
                ball.applyForce(bestAim)
            elif bestScore < 10: # if there is no possible shot with the zen ball to earn points then it has failed
                playSoundPitch(failSound)
                ball.applyForce(subVectors(launchAim, ball.pos)) # apply original launch aim

            #for debug
            drawTrajectory = True
            
            pygame.mixer.Sound.play(launch_sound)
            ball.isLaunch = False
            shouldClear = True
            powerUpCount -= 1
            if powerUpCount < 1:
                powerUpActive = False

        #update ball physics and pegs, additional game logic
        for b in balls:
            if b.isAlive:
                ballScreenPos = getBallScreenLocation(b, segmentCount)
                #### collision ####
                for p in pegs:

                    # if the current peg is the last remaining orange peg then apply special effects
                    if p.color == "orange" and orangeCount == 1 and not p.isHit:
                        if isBallTouchingPeg(p.pos.vx, p.pos.vy, p.radius*5, b.pos.vx, b.pos.vy, b.radius):
                            if frameRate != 27 and len(balls) < 2: 
                                playSoundPitch(drumRoll) # only play sound once
                            frameRate = 27 # gives the "slow motion" effect
                            closeBall = b
                        elif frameRate != 144:
                            frameRate = 144
                            playSoundPitch(sighSound) # only play sound once


                    # ball physics and game logic
                    if ballScreenPos == p.pegScreenLocation or ballScreenPos == p.pegScreenLocation2:
                        if isBallTouchingPeg(p.pos.vx, p.pos.vy, p.radius, b.pos.vx, b.pos.vy, b.radius):
                            b = resolveCollision(b, p) # resolve the collision between the ball and peg
                            
                            # save the peg that was last hit, used for when the ball is stuck and for bonus points
                            b.lastPegHit = p

                            # automatically remove pegs that a ball is stuck on
                            if autoRemovePegs:
                                p.ballStuckTimer.update()

                                # when timer has triggered, remove the last hit peg
                                if p.ballStuckTimer.isTriggered and b.lastPegHit != None:
                                    pegs.remove(b.lastPegHit) # remove the peg
                                    b.lastPegHit = None
                                    p.ballStuckTimer.cancleTimer()

                                # if the velocity is less than 0.5 then it might be stuck, wait a few seconds and remove the peg its stuck on
                                if b.vel.getMag() <= 0.5 and p.ballStuckTimer.isActive == False:
                                    p.ballStuckTimer.setTimer(0.8)
                                elif b.vel.getMag() > 0.5:
                                    p.ballStuckTimer.cancleTimer()
                                    b.lastPegHit = None

                            # check for long shot bonus
                            if b.lastPegHitPos != p.pos and b.lastPegHitPos != None and p.color == "orange" and not p.isHit:
                                if distBetweenTwoPoints(b.lastPegHitPos.vx, b.lastPegHitPos.vy, p.pos.vx, p.pos.vy) > longShotDistance:
                                    if not longShotBonus:
                                        playSoundPitch(longShotSound) 
                                        score += 1000
                                        b.lastPegHitPos = None
                                        longShotBonus = True

                                        # used for showing the bonus score
                                        longShotPos = Vector(p.pos.vx, p.pos.vy)

                            # used for long shot check
                            b.lastPegHitPos = p.pos

                            #peg color update and powerup sounds
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
                                    if powerUpType == "spooky-multiball": 
                                        playSoundPitch(powerUpMultiBall)
                                        addNewBall = True
                                        powerUpCount += 1
                                    powerUpCount += 1   
                                    powerUpActive = True
                                
                                # peg hit sounds
                                if pitchRaiseCount <= 7:
                                    if not p.isPowerUp: playSoundPitch(low_hit_sound, pitch)
                                    pitch -= 0.05 #magic number
                                if pitchRaiseCount == 7: pitch = 1.32 #magic number
                                elif pitchRaiseCount > 7 and pitchRaiseCount < 26:
                                    if not p.isPowerUp: playSoundPitch(normal_hit_sound, pitch)
                                    pitch -= 0.045 #magic number
                                elif pitchRaiseCount >= 26:
                                    if not p.isPowerUp: playSoundPitch(normal_hit_sound, pitch)
                                
                                #cheats
                                if cheats:
                                    if powerUpType == "spooky": 
                                        playSoundPitch(powerUpSpooky1)
                                        powerUpCount += 1 
                                    if powerUpType == "multiball": 
                                        playSoundPitch(powerUpMultiBall)
                                        addNewBall = True
                                        powerUpCount += 1 
                                    if powerUpType == "guideball":
                                        powerUpCount += 2
                                    if powerUpType == "spooky-multiball":
                                        playSoundPitch(powerUpMultiBall)
                                        playSoundPitch(powerUpSpooky1)
                                        addNewBall = True
                                        powerUpCount += 2 


                                #keep track of points earned
                                #pointsEarned.append(p.points)
                                score += (p.points * getScoreMultiplier(orangeCount, pegsHit))
        
                b.update()

                #check if ball has hit the sides of the bucket
                isBallCollidedBucket, collidedPeg = bucket.isBallCollidingWithBucketEdge(b)
                if isBallCollidedBucket:
                    b = resolveCollision(b, collidedPeg)

                # if active spooky powerup
                if powerUpActive and (powerUpType == "spooky" or powerUpType == "spooky-multiball"):
                    if b.pos.vy + b.radius > HEIGHT:
                        b.pos.vy = 0 + b.radius 
                        b.inBucket = False
                        powerUpCount -= 1
                        playSoundPitch(powerUpSpooky2)
                        if powerUpCount < 1:
                            powerUpActive = False 

                # if active multiball powerup
                if addNewBall and (powerUpType == "multiball" or powerUpType == "spooky-multiball"):
                    newBall =  Ball(b.pos.vx, b.pos.vy)
                    newBall.vel.vx = b.vel.vx * -1
                    newBall.vel.vy = b.vel.vy * -1
                    newBall.isAlive = True
                    balls.append(newBall)
                    addNewBall = False

                # if ball went in the bucket
                if not b.inBucket and bucket.isInBucket(b.pos.vx, b.pos.vy):
                    b.inBucket = True # prevent the ball from triggering it multiple times
                    playSoundPitch(freeBallSound)
                    ballsRemaining += 1
            
            # remove any 'dead' balls
            elif not b.isAlive and b != ball:
                balls.remove(b)

        

        # this little loop and if statement will determine if any of the balls are still alive and therfore if everything should be cleared/reset or not     
        done = True
        for b in balls:
            if b.isAlive:
                done = False
                break
        
        # check if their are any orange pegs or if the player has no balls (lol)
        if done and (orangeCount == 0 or ballsRemaining < 1) and gameOver == False:
            gameOver = True
            if ballsRemaining < 1 and orangeCount > 0:
                playSoundPitch(failSound)
        
        # check if the last orange peg has been hit, play ode to joy and change the buckets
        if orangeCount < 1 and not ballsRemaining < 1 and not alreadyPlayedOdeToJoy:
            pygame.mixer.music.load("resources/audio/music/ode_to_joy.wav")
            pygame.mixer.music.play(-1)
            playSoundPitch(cymbal)
            alreadyPlayedOdeToJoy = True
            frameRate = 60 # still kinda slow motion, but a little bit faster


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
            longShotBonus = False
            frameRate = 144
            previousAim = Vector(0,1) # forces the trajectory to be recalculated in case the mouse aim has not changed
            if powerUpType == "multiball" or powerUpType == "spooky-multiball":
                powerUpActive = False
                powerUpCount = 0
            for _ in range(8): # temporary fix to bug with pegs not being removed
                for p in pegs:
                    if p.isHit:
                        pegs.remove(p)
            for s in pointsEarned:
                score += s

        ##bucket
        bucket.update()

    ##### draw #####
    screen.fill((0, 0, 0))  # black screen
    screen.blit(backgroundImg, (0, 0))
    #draw back of bucket
    screen.blit(bucket.bucketBackImg, (bucket.pos.vx, bucket.pos.vy))
    #draw ball(s)
    if not gameOver:
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
    if done and not gameOver and not gamePaused:
        for fb in trajectory:
            drawCircle(fb.pos.vx, fb.pos.vy, 4, (10 ,70 ,163))
    #draw text
    if not gameOver:
        #show how many balls are left
        ballText = ballCountFont.render(str(ballsRemaining), False, (200, 200, 200))
        screen.blit(ballText,(50, 50))
        #show the score
        scoreText = ballCountFont.render(str(score), False, (20, 60, 255))
        screen.blit(scoreText,(150, 50))
        #show the powerup information
        if powerUpActive:
            powerUpTextColor = (50, 255, 20)
        else:
            powerUpTextColor = (50, 170, 20)
        powerUpText = infoFont.render(powerUpType + ": " + str(powerUpCount), False, powerUpTextColor)
        screen.blit(powerUpText, (int(WIDTH/2 - 50), 5))

    #show if paused
    if gamePaused and not gameOver:
        pauseText = menuFont.render("PAUSED", False, (255, 255, 255))
        screen.blit(pauseText,(WIDTH/2.65, HEIGHT/4))

    #show if gameOver
    if gameOver:
        pauseText = menuFont.render("Game Over", False, (255, 255, 255))
        screen.blit(pauseText,(WIDTH/3.3, HEIGHT/4))
        if ballsRemaining >= 0 and orangeCount < 1:
            scoreText = menuFont.render(str(score), False, (20, 60, 255))
            screen.blit(scoreText,(WIDTH/3.3, HEIGHT/2.2))
        else:
            tryAgainText = menuFont.render("Try Again", False, (255, 60, 20))
            screen.blit(tryAgainText,(WIDTH/3.1, HEIGHT/2.2))

    # show the long shot score text only for a few seconds
    longShotTextTimer.update()
    if longShotTextTimer.isTriggered:
        longShotBonus = False
        longShotTextTimer.cancleTimer()

    if longShotBonus and not longShotTextTimer.isActive:
        longShotTextTimer.setTimer(1.25)
    
    if longShotBonus and not longShotTextTimer.isTriggered:
        longShotText = infoFont.render("25,000", False, (255, 80, 40))
        screen.blit(longShotText,(longShotPos.vx-28, longShotPos.vy+11))

    #debugging stuff
    if debug:
        if (clock.get_rawtime() < 10): # decide whether green text or red text
            frameColor = (0, 255, 50) # green
        else:
            frameColor = (255, 50, 0) #red
        #print frametime
        frameTime = debugFont.render(str(clock.get_rawtime()) + " ms" , False, (frameColor))
        screen.blit(frameTime,(5, 10))
        framesPerSec = debugFont.render(str(round(clock.get_fps())) + " fps" , False, (255,255,255))
        screen.blit(framesPerSec,(5, 25))
        #print number of orange pegs remaining and score multiplier
        orangeCountText = debugFont.render(str(orangeCount) + " orange pegs left" , False, (255,255,255))
        screen.blit(orangeCountText,(100, 35))
        scoreMultiplierText = debugFont.render("x"+str(getScoreMultiplier(orangeCount, pegsHit)) , False, (255,255,255))
        screen.blit(scoreMultiplierText,(100, 50))
        #print total number of pegs in the pegs list
        pegCountText = debugFont.render(str(len(pegs)) + " total pegs left" , False, (255,255,255))
        screen.blit(pegCountText,(245, 35))
        #print ball velocity
        ballVelText = debugFont.render("Velocity: " + str(ball.vel.getMag()), False, (255,255,255))
        screen.blit(ballVelText, (100,20))
        #draw zenball trajectory
        if drawTrajectory and not done and powerUpType == "zenball":
            for fb in bestTrajectory:
                drawCircle(fb.pos.vx, fb.pos.vy, 1, (0 ,153 ,10))

        #draw bucket fake pegs
        for fakePeg in bucket.fakePegs.copy():
            drawCircle(fakePeg.pos.vx, fakePeg.pos.vy, fakePeg.radius, (255,0,0))

        
        if debugCollision:
            collSegmentDisp = debugFont.render("Collision Segments: " + str(segmentCount), False, (0,255,255))
            screen.blit(collSegmentDisp, (230,7))
            #draw collision sections
            segmentWidth = WIDTH/segmentCount
            for i in range(segmentCount):
                drawLine(segmentWidth*i, 0, segmentWidth*i, HEIGHT)

    # display red text indicating if cheats are enabled       
    if cheats:
        cheatsIcon = debugFont.render("CHEATS ENABLED" , False, (255,0,0))
        screen.blit(cheatsIcon,(100, 6))

    pygame.display.update()
    clock.tick(frameRate)  # lock game framerate to a specified tickrate (default is 144)