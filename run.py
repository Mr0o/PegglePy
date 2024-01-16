import sys  # used to exit the program immediately
import time

##### local imports #####
try:
    from local.config import *
    from local.trajectory import calcTrajectory, findBestTrajectory
    from local.audio import playSoundPitch, loadRandMusic, playMusic, stopMusic, pauseMusic, unpauseMusic, setMusicVolume
    from local.resources import *  # pygame audio, fonts and images
    from local.misc import *
    from local.trigger_events import TimedEvent

    # refer to the vectors.py module for information on these functions
    from local.vectors import Vector, subVectors
    from local.collision import isBallTouchingPeg, resolveCollision, isBallTouchingPeg_old, resolveCollision_old

    from local.ball import Ball
    from local.peg import Peg
    from local.bucket import Bucket
except ImportError as e:
    print("ERROR: Unable to import local modules, this is likely due to a missing file or folder. Please make sure to run the script from within the PegglePy directory.")
    print(str(e))
    print("Exiting...")
    sys.exit(1)

from menu import mainMenu, getPauseScreen
from settingsMenu import settingsMenu
from editor import levelEditor
from loadLevelMenu import loadLevelMenu

import pygame

##### pygame stuff #####
pygame.init()
# set fullscreen
if FULLSCREEN:
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)  # display surface
else:
    screen = pygame.display.set_mode((WIDTH, HEIGHT))  # display surface

clock = pygame.time.Clock()  # game clock

pygame.display.set_caption("PegglePy")

# set the icon
pygame.display.set_icon(gameIconImg)


##### drawing functions #####
def drawCircle(x, y, rad=5, rgb=(255, 255, 255)):
    pygame.draw.circle(screen, (rgb), [x, y], rad)


def drawLine(x1, y1, x2, y2):
    pygame.draw.line(screen, (255, 0, 0), [x1, y1], [x2, y2])


### testing stuff ###
balls: list[Ball]
balls = []
balls.append(Ball(WIDTH/2, HEIGHT/25))
ball = balls[0]

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
launchAim = Vector(0, 0)

debugCollision = False
gamePaused = False
gameOver = False
alreadyPlayedOdeToJoy = False
closeBall = None
longShotBonus = False
debugTrajectory = False
firstSpookyHit = False
bestTrajectory = []
hasPegBeenHit = False
hasPegBeenRemoved = False
controllerInput = False
inputAim = Vector(WIDTH/2, (HEIGHT/25)+50)
gamePadFineTuneAmount = 0

longShotTextTimer = TimedEvent()

debugStaticImage: pygame.Surface = None

gameRunning = True

zoomInOnBall = False
zoom = 1

pegs: list[Peg]

### main menu ###
selection = "none"
editorSelection = "none"
while selection != "start" and selection != "quit":
    selection = mainMenu(screen)

    if selection == "quit":
        gameRunning = False
    elif selection == "editor":
        time.sleep(0.5)  # prevent accidental click on launch
        editorSelection, pegs = levelEditor(screen, clock, debug)
        if editorSelection == "quit":
            gameRunning = False
            selection = "quit"
        elif editorSelection == "play":
            selection = "start"

    elif selection == "settings":
        time.sleep(0.15)
        if settingsMenu(screen, debug) == "mainMenu":
            selection = "none"

# prevent accidental click on launch
delayTimer = TimedEvent(0.5)

if selection != "quit":
    if editorSelection != "play":
        pegs, originPegs, orangeCount, levelFileName = loadLevelMenu(screen, debug)
        #pegs, originPegs, orangeCount, levelFileName = loadDefaultLevel()

        delayTimer = TimedEvent(0.5)
    else:
        levelFileName = "Unsaved Editor Level"
        originPegs = pegs.copy()

        pegs = createPegColors(pegs)

        orangeCount = 0
        for peg in pegs:
            if peg.color == "orange":
                orangeCount += 1
        
    # set the caption to include the level name
    pygame.display.set_caption("PegglePy   -   " + levelFileName)

    # assign each peg a screen location, this is to better optimize collison detection (only check pegs on the same screen location as the ball)
    assignPegScreenLocation(pegs, segmentCount)

    staticImage = createStaticImage(pegs)

    loadRandMusic()
    setMusicVolume(musicVolume)
    if musicEnabled:
        playMusic()

else:
    gameRunning = False

##### main loop #####
while gameRunning:
    launch_button = False
    gamePadFineTuneAmount = 0
    for event in pygame.event.get():  # check events and quit if the program is closed
        if event.type == pygame.QUIT:
            gameRunning = False
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                # horrifying function that resets the game
                ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, frameRate, longShotBonus, staticImage = resetGame(
                    balls, assignPegScreenLocation, createPegColors, bucket, pegs, originPegs)
                if not musicEnabled:
                    pygame.mixer.music.stop()
            if event.key == pygame.K_1:  # enable or disable debug features
                debug = not debug
            if event.key == pygame.K_2:  # enable or disable cheats
                cheats = not cheats
            if event.key == pygame.K_3:  # cycle through all power up types
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
            if event.key == pygame.K_4:  # enable or disable debug view of collision segments
                debugCollision = not debugCollision
            if event.key == pygame.K_5:  # debug - decrease collision segment count
                segmentCount -= 1
                # reassign each pegs segment location
                assignPegScreenLocation(pegs, segmentCount)
            if event.key == pygame.K_6:  # debug - increase collision segment count
                segmentCount += 1
                # reassign each pegs segment location
                assignPegScreenLocation(pegs, segmentCount)
            if event.key == pygame.K_7:  # debug - enable or disable full trajectory drawing
                debugTrajectory = not debugTrajectory
            if event.key == pygame.K_l:  # load a new level
                pygame.mixer.music.stop()
                pegs, originPegs, orangeCount, levelFileName = loadLevelMenu(screen, debug)
                # set the caption to include the level name
                pygame.display.set_caption(
                    "PegglePy   -   " + levelFileName)
                # horrifying function that resets the game
                ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, frameRate, longShotBonus, staticImage = resetGame(
                    balls, assignPegScreenLocation, createPegColors, bucket, pegs, originPegs)
                if not musicEnabled:
                    pygame.mixer.music.stop()
                delayTimer = TimedEvent(0.50)
            if event.key == pygame.K_ESCAPE:  # enable or disable cheats
                gamePaused = not gamePaused
            if event.key == pygame.K_0:
                if frameRate == 144:
                    frameRate = 30
                else:
                    frameRate = 144
            if event.key == pygame.K_m:
                soundEnabled = not soundEnabled
            if event.key == pygame.K_n:
                if musicEnabled == False:
                    musicEnabled = True
                    pygame.mixer.music.play(-1)
                else:
                    musicEnabled = False
                    pygame.mixer.music.stop()
            if event.key == pygame.K_8:
                speedHack = not speedHack
            if event.key == pygame.K_9:
                debugAutoRemovePegsTimer = not debugAutoRemovePegsTimer
            if event.key == pygame.K_r:
                useCPhysics = not useCPhysics
            # toggle zoom
            if event.key == pygame.K_x:
                zoomInOnBall = not zoomInOnBall
            # open the main menu
            if event.key == pygame.K_z:
                selection = mainMenu(screen, debug)

                if selection == "quit":
                    gameRunning = False
                elif selection == "editor":
                    time.sleep(0.5)  # prevent accidental click on launch
                    levelEditor(screen, clock, debug)

                # reset the game
                ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, frameRate, longShotBonus, staticImage = resetGame(
                    balls, assignPegScreenLocation, createPegColors, bucket, pegs, originPegs)

                # prevent accidental click on launch
                delayTimer = TimedEvent(0.5)

                if not musicEnabled:
                    # change the song
                    pygame.mixer.music.stop()
                    loadRandMusic()
                    pygame.mixer.music.play(-1)  # looping forever

                # set the caption to include the level name
                pygame.display.set_caption(
                    "PegglePy   -   " + levelFileName)

        if event.type == pygame.MOUSEWHEEL:
            fineTuneAmount -= event.y / 12

        if event.type == pygame.MOUSEMOTION and controllerInput:
            controllerInput = False
            pygame.mouse.set_visible(True)

        # check for gamepad dpad buttons
        if event.type == pygame.JOYHATMOTION:
            if event.value == (0, 1):
                gamePadFineTuneAmount += 0.11
            if event.value == (0, -1):
                gamePadFineTuneAmount -= 0.11
            if event.value == (1, 0):
                gamePadFineTuneAmount += 0.11
            if event.value == (-1, 0):
                gamePadFineTuneAmount -= 0.11

        if event.type == pygame.JOYAXISMOTION and not controllerInput:
            if event.axis == 0 or event.axis == 1:
                if abs(event.value) > 0.15:
                    controllerInput = True
                    pygame.mouse.set_visible(False)
        if event.type == pygame.JOYBUTTONDOWN:
            # if the controller is a 'sony' or 'playstation' controller (Sometimes "Wireless Controller" is the name of the ps4 controller, so we will include that as well)
            if joystick.get_name().lower().find("sony") != -1 or joystick.get_name().lower().find("playstation") != -1 or joystick.get_name().lower().find("wireless") != -1:
                if event.button == 0:  # the 'X'/cross button on a ps4 controller
                    launch_button = True
                if event.button == 3:  # the '[]'/square button on a ps4 controller
                    launch_button = True
                if event.button == 1:  # the 'O'/circle button on a ps4 controller
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
                if event.button == 2:  # the '△'/triangle button on a ps4 controller
                    # reset the game
                    ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, frameRate, longShotBonus, staticImage = resetGame(
                        balls, assignPegScreenLocation, createPegColors, bucket, pegs, originPegs)  # horrifying function that resets the game
                    if not musicEnabled:
                        pygame.mixer.music.stop()
                if event.button == 4:  # the 'L1' button on a ps4 controller
                    # rumble test
                    if pygame.joystick.get_count() > 0:
                        if debug:
                            print("rumble test - 100 ms")
                        joystick = pygame.joystick.Joystick(0)
                        joystick.init()
                        joystick.rumble(1, 1, 100)
                if event.button == 5:  # the 'R1' button on a ps4 controller
                    # cheats
                    cheats = not cheats
                if event.button == 8:  # the 'share' button on a ps4 controller
                    # enable or disable debug
                    debug = not debug
                if event.button == 9:  # the 'options' button on a ps4 controller
                    # pause the game
                    gamePaused = not gamePaused
                if event.button == 11 or event.button == 12:  # the 'L3' or 'R3' joystick buttons on a ps4 controller
                    # enable or disable sound and music
                    if musicEnabled == False:
                        musicEnabled = True
                        pygame.mixer.music.play(-1)
                    else:
                        musicEnabled = False
                        pygame.mixer.music.stop()

                    soundEnabled = not soundEnabled

            else:  # xbox controller (default)
                if event.button == 0:  # the 'A' button on an xbox controller
                    launch_button = True
                if event.button == 2:  # the 'X' button on an xbox controller
                    launch_button = True
                if event.button == 1:  # the 'B' button on an xbox controller
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
                if event.button == 3:  # the 'Y' button on an xbox controller
                    # reset the game
                    ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, frameRate, longShotBonus, staticImage = resetGame(
                        balls, assignPegScreenLocation, createPegColors, bucket, pegs, originPegs)
                    if not musicEnabled:
                        pygame.mixer.music.stop()
                if event.button == 6:  # the 'start' button on an xbox controller
                    debug = not debug
                if event.button == 7:  # the 'back' button on an xbox controller
                    gamePaused = not gamePaused
                # the 'left stick' or 'right stick' buttons on an xbox controller
                if event.button == 9 or event.button == 10:
                    if musicEnabled == False:
                        musicEnabled = True
                        pygame.mixer.music.play(-1)
                    else:
                        musicEnabled = False
                        pygame.mixer.music.stop()
                    if soundEnabled == False:
                        soundEnabled = True
                    else:
                        soundEnabled = False
                if event.button == 4:  # the 'left bumper' button on an xbox controller
                    # rumble test
                    if pygame.joystick.get_count() > 0:
                        if debug:
                            print("rumble test - 100 ms")
                        joystick = pygame.joystick.Joystick(0)
                        joystick.init()
                        joystick.rumble(1, 1, 100)
                if event.button == 5:  # the 'right bumper' button on an xbox controller
                    cheats = not cheats

    mouseClicked = pygame.mouse.get_pressed()  # get the mouse click state
    mx, my = pygame.mouse.get_pos()  # get mouse position as 'mx' and 'my'
    # get mouse relative position as 'mx_rel' and 'my_rel'
    mx_rel, my_rel = pygame.mouse.get_rel()

    # check for joystick
    if pygame.joystick.get_count() > 0:
        # connect to the first controller
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        # 0 is the x axis on the left joystick (at least on xbox controllers)
        joystickX = joystick.get_axis(0)
    else:
        controllerInput = False
        pygame.mouse.set_visible(True)
        if mouseClicked[0]:
            launch_button = True

    if controllerInput and not ball.isAlive:  # controller joystick
        maxAngleDegrees = 200
        minAngleDegrees = -20

        minJoystickValue = 0.15

        if abs(joystickX) < 0.70:
            angleStep = joystickX * 0.35
        elif abs(joystickX) < 0.80:
            angleStep = joystickX * 0.65
        elif abs(joystickX) < 0.90:
            angleStep = joystickX * 0.90
        else:
            angleStep = joystickX * 1.15

        angle = inputAim.getAngleDeg()

        if abs(angleStep) > minJoystickValue:
            angle -= angleStep

        inputAim.setAngleDeg(angle + gamePadFineTuneAmount)
        inputAim.setMag(500)

        gamePadFineTuneAmount = 0

        posX = inputAim.x + ball.pos.x
        posY = inputAim.y + ball.pos.y
    elif not controllerInput:  # mouse
        inputAim = Vector(mx, my)
        mouseAim = subVectors(inputAim, ball.pos)
        # adjust the angle of the mouseAim to account for gravity
        mouseAim.setAngleDeg(mouseAim.getAngleDeg())

        # print(inputAim.x, inputAim.y)

        # use angle of reach to find angle needed for the projectile to hit the mouse position
        # adjustedAngle = findAngleToTarget(ball.pos, Vector(mx, my))
        # inputAim.setAngleDeg(adjustedAngle)

        # apply the fine tune amount
        inputAim.setAngleDeg(inputAim.getAngleDeg() + fineTuneAmount)

        posX = inputAim.x
        posY = inputAim.y
        # check if the mouse is clicked (and that the size of the balls collections is less than 1)
        if mouseClicked[0]:
            launch_button = True

    # reset the game when the game is over and the mouse is clicked
    if launch_button and gameOver:
        # prevent the click from instantly launching a ball
        delayTimer = TimedEvent(0.25)
        # horrifying function that resets the game
        ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, frameRate, longShotBonus, staticImage = resetGame(
            balls, assignPegScreenLocation, createPegColors, bucket, pegs, originPegs)
        if not musicEnabled:
            pygame.mixer.music.stop()

    # do not update any game physics or game logic if the game is paused or over
    if not gamePaused and not gameOver:
        # use the mouse position as a vector to calculate the path that is being aimed
        launchAim = Vector(posX, posY)
        # check if the mouse is being moved to determine whether or not to use the fine tune amount
        if mx_rel != 0 and my_rel != 0:
            fineTuneAmount = 0

        # calculate trajectory
        if not ball.isAlive:
            if powerUpActive and powerUpType == "guideball":
                trajectoryDepth = 750  # powerup
            else:
                trajectoryDepth = 75  # normal
                if debugTrajectory:
                    trajectoryDepth = 2500
            # only calculate the trajectory if the mouse has been moved - reduces cpu time
            if previousAim.x != launchAim.x or previousAim.y != launchAim.y:
                trajectory = calcTrajectory(launchAim, ball.pos, pegs.copy(), bucket.fakePegs.copy(
                ), (powerUpType == "guideball" and powerUpActive), trajectoryDepth, debugTrajectory)
        previousAim = Vector(launchAim.x, launchAim.y)

        delayTimer.update()  # prevent the ball from launching instantly after the game is reset
        # if mouse clicked then trigger ball launch
        if launch_button and not ball.isAlive and delayTimer.isTriggered and len(balls) < 2:
            if powerUpActive and powerUpType == "guideball":
                powerUpCount -= 1
                if powerUpCount < 1:
                    powerUpActive = False
            ball.isLaunch = True
            ball.isAlive = True

        # launch ball
        if ball.isLaunch and ball.isAlive:
            if not powerUpType == "zenball":  # if powerup type is anything but zenball, launch normal
                launchForce = subVectors(launchAim, ball.pos)
                launchForce.setMag(LAUNCH_FORCE)
                ball.applyForce(launchForce)
                if soundEnabled:
                    playSoundPitch(launch_sound, volume=soundVolume)
                ball.isLaunch = False
                shouldClear = True
            # if powerup type is zenball and it is not active then normal launch
            elif not powerUpActive and powerUpType == "zenball":
                launchForce = subVectors(launchAim, ball.pos)
                launchForce.setMag(LAUNCH_FORCE)
                ball.applyForce(launchForce)
                if soundEnabled:
                    playSoundPitch(launch_sound, volume=soundVolume)
                ball.isLaunch = False
                shouldClear = True
                drawTrajectory = False

        # cheats (force enable power up)
        if cheats:
            powerUpActive = True

        # if active zenball powerup - launch
        if ball.isLaunch and ball.isAlive and powerUpType == "zenball" and powerUpActive:
            # find the best shot
            if soundEnabled:
                playSoundPitch(powerUpZenBall, 0.93, soundVolume)
            if debug:
                print("Debug: Zenball launched")
                startTime = time.time()
            bestAim, bestScore, bestTrajectory = findBestTrajectory(Vector(
                launchAim.x, launchAim.y), Vector(ball.pos.x, ball.pos.y), pegs.copy())

            if debug:
                print("Debug: Zenball best aim found in " +
                      str(time.time() - startTime) + " seconds")

            for p in pegs:
                p.isHit = False

            if bestScore >= 10:
                if soundEnabled:
                    playSoundPitch(powerUpZenBall, 0.99, soundVolume)
                ball.applyForce(bestAim)
            elif bestScore < 10:  # if there is no possible shot with the zen ball to earn points then it has failed
                if soundEnabled:
                    playSoundPitch(failSound, volume=soundVolume)
                # apply original launch aim
                ball.applyForce(subVectors(launchAim, ball.pos))

            if soundEnabled:
                playSoundPitch(launch_sound, volume=soundVolume)
            ball.isLaunch = False
            shouldClear = True
            powerUpCount -= 1
            if powerUpCount < 1:
                powerUpActive = False

        # cheats, place ball anywhere on screen with right click
        if cheats and mouseClicked[2] and ball.isAlive and not ball.isLaunch:
            isValidPlacement = True
            for ball in balls:
                if isBallTouchingPeg(ball.pos.x, ball.pos.y, ball.radius, mx, my, ball.radius):
                    isValidPlacement = False
            if isValidPlacement:
                newCheatBall = Ball(mx, my)
                newCheatBall.isAlive = True
                balls.append(newCheatBall)
                ball = newCheatBall

        # update ball physics and pegs, additional game logic
        for b in balls:
            if b.isAlive:
                ballScreenPosList = getBallScreenLocation(b, segmentCount)
                #### collision ####
                for p in pegs:

                    # if the current peg is the last remaining orange peg then apply special effects
                    if p.color == "orange" and orangeCount == 1 and not p.isHit:
                        if useCPhysics:
                            ballTouchingPeg = isBallTouchingPeg(
                                p.pos.x, p.pos.y, p.radius*5, b.pos.x, b.pos.y, b.radius)
                        else:
                            ballTouchingPeg = isBallTouchingPeg_old(
                                p.pos.x, p.pos.y, p.radius*5, b.pos.x, b.pos.y, b.radius)
                        if ballTouchingPeg:
                            if frameRate != 27 and len(balls) < 2:
                                if soundEnabled:
                                    # only play sound once
                                    playSoundPitch(drumRoll, volume=soundVolume)
                            frameRate = 27  # gives the "slow motion" effect
                            closeBall = b
                        elif frameRate != 144:
                            if soundEnabled:
                                # only play sound once
                                playSoundPitch(sighSound, volume=soundVolume)
                            frameRate = 144

                    # ball physics and game logic
                    shouldCheckCollision = False
                    for ballScreenPos in ballScreenPosList:
                        for pegScreenLocation in p.pegScreenLocations:
                            if ballScreenPos == pegScreenLocation:
                                shouldCheckCollision = True

                    if shouldCheckCollision:
                        if useCPhysics:
                            ballTouchingPeg = isBallTouchingPeg(
                                p.pos.x, p.pos.y, p.radius, b.pos.x, b.pos.y, b.radius)
                        else:
                            ballTouchingPeg = isBallTouchingPeg_old(
                                p.pos.x, p.pos.y, p.radius, b.pos.x, b.pos.y, b.radius)
                        if ballTouchingPeg:
                            # resolve the collision between the ball and peg
                            if useCPhysics:
                                # use the c implementation of the collision check
                                b = resolveCollision(b, p)
                            else:
                                # use the python implementation of the collision check
                                b = resolveCollision_old(b, p)

                            # save the peg that was last hit, used for when the ball is stuck and for bonus points
                            b.lastPegHit = p

                            # automatically remove pegs that a ball is stuck on
                            if autoRemovePegs:
                                p.ballStuckTimer.update()

                                # when timer has triggered, remove the last hit peg
                                if p.ballStuckTimer.isTriggered and b.lastPegHit != None:
                                    pegs.remove(b.lastPegHit)  # remove the peg
                                    b.lastPegHit = None
                                    hasPegBeenRemoved = True
                                    p.ballStuckTimer.cancleTimer()

                                # if the velocity is less than 0.5 then it might be stuck, wait a few seconds and remove the peg its stuck on
                                if b.vel.getMag() <= 0.5 and p.ballStuckTimer.isActive == False:
                                    p.ballStuckTimer.setTimer(
                                        autoRemovePegsTimerValue)
                                elif b.vel.getMag() > 0.5:
                                    p.ballStuckTimer.cancleTimer()
                                    b.lastPegHit = None

                            # check for long shot bonus
                            if b.lastPegHitPos != p.pos and b.lastPegHitPos != None and p.color == "orange" and not p.isHit:
                                if distBetweenTwoPoints(b.lastPegHitPos.x, b.lastPegHitPos.y, p.pos.x, p.pos.y) > longShotDistance:
                                    if not longShotBonus:
                                        if soundEnabled:
                                            playSoundPitch(longShotSound, volume=soundVolume)
                                        score += 25000
                                        b.lastPegHitPos = None
                                        longShotBonus = True

                                        # used for showing the bonus score
                                        longShotPos = Vector(
                                            p.pos.x, p.pos.y)

                                        if pygame.joystick.get_count() > 0 and controllerInput:
                                            if debug:
                                                print("Debug: Rumble")
                                            joystick = pygame.joystick.Joystick(
                                                0)
                                            joystick.init()
                                            joystick.rumble(1, 1, 100)

                            # used for long shot check
                            b.lastPegHitPos = p.pos

                            # peg color update and powerup sounds
                            if not p.isHit:
                                hasPegBeenHit = True  # has a peg been hit this frame
                                p.isHit = True
                                pegsHit += 1
                                p.update_color()  # change the color to signify it has been hit
                                pitchRaiseCount += 1
                                if p.color == "orange":
                                    orangeCount -= 1
                                if p.isPowerUp:
                                    if powerUpType == "spooky":
                                        if powerUpCount < 1:
                                            if soundEnabled:
                                                playSoundPitch(powerUpSpooky1, volume=soundVolume)
                                            firstSpookyHit = True
                                        elif powerUpCount == 1:
                                            if soundEnabled:
                                                playSoundPitch(powerUpSpooky2, volume=soundVolume)
                                            firstSpookyHit = False
                                    if powerUpType == "multiball":
                                        if soundEnabled:
                                            if soundEnabled:
                                                playSoundPitch(
                                                    powerUpMultiBall)
                                        addNewBall = True
                                    if powerUpType == "zenball":
                                        if soundEnabled:
                                            playSoundPitch(powerUpZenBallHit, volume=soundVolume)
                                    if powerUpType == "guideball":
                                        if soundEnabled:
                                            playSoundPitch(powerUpGuideBall, volume=soundVolume)
                                        powerUpCount += 2
                                    if powerUpType == "spooky-multiball":
                                        if soundEnabled:
                                            playSoundPitch(powerUpMultiBall, volume=soundVolume)
                                        addNewBall = True
                                        powerUpCount += 1
                                    powerUpCount += 1
                                    powerUpActive = True

                                # peg hit sounds
                                if pitchRaiseCount <= 7:
                                    if not p.isPowerUp:
                                        if soundEnabled:
                                            playSoundPitch(
                                                low_hit_sound, pitch, volume=soundVolume)
                                    pitch -= 0.05  # magic number
                                if pitchRaiseCount == 7:
                                    pitch = 1.32  # magic number
                                elif pitchRaiseCount > 7 and pitchRaiseCount < 26:
                                    if not p.isPowerUp:
                                        if soundEnabled:
                                            playSoundPitch(
                                                normal_hit_sound, pitch, soundVolume)
                                    pitch -= 0.045  # magic number
                                elif pitchRaiseCount >= 26:
                                    if not p.isPowerUp:
                                        if soundEnabled:
                                            playSoundPitch(
                                                normal_hit_sound, pitch, soundVolume)

                                # cheats
                                if cheats:
                                    if powerUpType == "spooky":
                                        # if soundEnabled: playSoundPitch(powerUpSpooky1)
                                        powerUpCount += 1
                                    if powerUpType == "multiball":
                                        if soundEnabled:
                                            playSoundPitch(powerUpMultiBall, volume=soundVolume)
                                        addNewBall = True
                                        powerUpCount += 1
                                    if powerUpType == "guideball":
                                        powerUpCount += 2
                                    if powerUpType == "spooky-multiball":
                                        if soundEnabled:
                                            playSoundPitch(powerUpMultiBall, volume=soundVolume)
                                        # if soundEnabled: playSoundPitch(powerUpSpooky1)
                                        addNewBall = True
                                        powerUpCount += 2

                                # keep track of points earned
                                # pointsEarned.append(p.points)
                                score += (p.points *
                                          getScoreMultiplier(orangeCount, pegsHit))

                                if speedHack:
                                    # update the static image to show the peg has been hit (can increase performance, but at the cost of visual wierdness)
                                    staticImage = updateStaticImage(
                                        staticImage, p)

                b.update()

                # check if ball has hit the sides of the bucket
                isBallCollidedBucket, collidedPeg = bucket.isBallCollidingWithBucketEdge(
                    b)
                if isBallCollidedBucket:
                    if useCPhysics:
                        # use the c implementation of the collision check
                        b = resolveCollision(b, collidedPeg)
                    else:
                        # use the python implementation of the collision check
                        b = resolveCollision_old(b, collidedPeg)

                # if active spooky powerup
                if powerUpActive and (powerUpType == "spooky" or powerUpType == "spooky-multiball"):
                    if b.pos.y + b.radius > HEIGHT:
                        b.pos.y = 0 + b.radius
                        b.inBucket = False
                        if powerUpCount == 1 and firstSpookyHit:
                            if soundEnabled:
                                playSoundPitch(powerUpSpooky2, volume=soundVolume)
                        elif powerUpCount == 1 and not firstSpookyHit:
                            if soundEnabled:
                                playSoundPitch(powerUpSpooky4, volume=soundVolume)
                        elif powerUpCount == 2 and not firstSpookyHit:
                            if soundEnabled:
                                playSoundPitch(powerUpSpooky3, volume=soundVolume)
                        elif cheats:
                            if soundEnabled:
                                playSoundPitch(powerUpSpooky2, volume=soundVolume)
                        powerUpCount -= 1
                        if powerUpCount < 1:
                            powerUpActive = False

                # if active multiball powerup
                if addNewBall and (powerUpType == "multiball" or powerUpType == "spooky-multiball"):
                    newBall = Ball(b.pos.x, b.pos.y)
                    newBall.vel.x = b.vel.x * -1
                    newBall.vel.y = b.vel.y * -1
                    newBall.isAlive = True
                    balls.append(newBall)
                    addNewBall = False

                # if ball went in the bucket
                if not b.inBucket and bucket.isInBucket(b.pos.x, b.pos.y):
                    b.inBucket = True  # prevent the ball from triggering it multiple times
                    if soundEnabled:
                        playSoundPitch(freeBallSound, volume=soundVolume)
                    ballsRemaining += 1

            # remove any 'dead' balls
            elif not b.isAlive and b != ball:
                balls.remove(b)

        # if a peg was hit or removed this frame, update the static image (this is an optimazation to prevent the static image from being updated more than once per frame)
        if hasPegBeenHit and not speedHack:
            # generate new static image to show the peg has been hit or removed (can cause pefromance hiccups especially when there are lots of pegs in the level)
            staticImage = createStaticImage(pegs)
            hasPegBeenHit = False

        # regardless of speedHack, update the static image if a peg was removed
        if hasPegBeenRemoved:
            hasPegBeenRemoved = False
            staticImage = createStaticImage(pegs)

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
                if soundEnabled:
                    playSoundPitch(failSound, volume=soundVolume)

        # check if the last orange peg has been hit, play ode to joy and change the buckets
        if orangeCount < 1 and not ballsRemaining < 1 and not alreadyPlayedOdeToJoy:
            pygame.mixer.music.load("resources/audio/music/ode_to_joy.wav")
            if musicEnabled:
                pygame.mixer.music.play(-1)
            if soundEnabled:
                playSoundPitch(cymbal, volume=soundVolume)
            alreadyPlayedOdeToJoy = True
            frameRate = 60  # still kinda slow motion, but a little bit faster

        # reset everything and remove hit pegs
        if done and shouldClear:
            shouldClear = False
            balls.clear()  # clear all the balls
            # recreate the original ball
            balls.append(Ball(WIDTH/2, HEIGHT/25))
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
            # forces the trajectory to be recalculated in case the mouse aim has not changed
            previousAim = Vector(0, 1)
            if powerUpType == "multiball" or powerUpType == "spooky-multiball":
                powerUpActive = False
                powerUpCount = 0
            for _ in range(8):  # temporary fix to bug with pegs not being removed
                for p in pegs:
                    if p.isHit:
                        pegs.remove(p)
            for s in pointsEarned:
                score += s
            staticImage = createStaticImage(pegs)

        # bucket, pass the power up info for the bucket to update its collison and image
        bucket.update(powerUpType, powerUpActive)

    ##### draw #####
    screen.blit(staticImage, (0, 0))
    # draw back of bucket
    bucketBackImg, bucketFrontImg = bucket.getImage(powerUpType, powerUpActive)
    screen.blit(bucketBackImg, (bucket.pos.x, bucket.pos.y))
    # draw ball(s)
    if not gameOver:
        for b in balls:
            screen.blit(ballImg, (b.pos.x - ballImg.get_width() /
                        2, b.pos.y - ballImg.get_height()/2))
    # draw front of bucket
    screen.blit(bucketFrontImg, (bucket.pos.x, bucket.pos.y))
    # draw trajectory path
    done = True
    for b in balls:
        if b.isAlive:
            done = False
    if done and not gameOver and not gamePaused:
        for fb in trajectory:
            drawCircle(fb.pos.x, fb.pos.y, 4, (10, 70, 163)) 
        

    # "zoom in" on the ball by transorming the image
    # scale the image and blit it at the position of the ball
    if frameRate == 27 or zoomInOnBall:
        # zoom in
        zoom += 0.005
        if zoom > 1.8:
            zoom = 1.8

        zoomedScreen = pygame.transform.smoothscale(screen, (int(WIDTH*zoom), int(HEIGHT*zoom)))

        # calculate the position of the zoomedScreen
        # if there is only one orange peg left, then zoom in on the orange peg
        if orangeCount < 2:
            # get the psosition of the orange peg
            for p in pegs:
                if p.color == "orange" and not p.isHit:
                    zoomedScreenPos = (zoomedScreen.get_width()/zoom/2 - p.pos.x*zoom, zoomedScreen.get_height()/zoom/2 - p.pos.y*zoom)
                    break
        else:
            # zoom in on the ball
            zoomedScreenPos = (zoomedScreen.get_width()/zoom/2 - ball.pos.x*zoom, zoomedScreen.get_height()/zoom/2 - ball.pos.y*zoom)

        # if the zoomedScreen moves too far to the left or right, then set the x position to the edge of the screen
        if zoomedScreenPos[0] > 0:
            zoomedScreenPos = (0, zoomedScreenPos[1])
        elif zoomedScreenPos[0] < WIDTH - zoomedScreen.get_width():
            zoomedScreenPos = (WIDTH - zoomedScreen.get_width(), zoomedScreenPos[1])
        
        # if the zoomedScreen moves too far up or down, then set the y position to the edge of the screen
        if zoomedScreenPos[1] > 0:
            zoomedScreenPos = (zoomedScreenPos[0], 0)
        elif zoomedScreenPos[1] < HEIGHT - zoomedScreen.get_height():
            zoomedScreenPos = (zoomedScreenPos[0], HEIGHT - zoomedScreen.get_height())

        screen.blit(zoomedScreen, zoomedScreenPos)
    else:
        # zoom out
        if zoom > 1.0:
            if alreadyPlayedOdeToJoy or frameRate == 27:
                zoom -= 0.0025
            else:
                zoom -= 0.005
            
            zoomedScreen = pygame.transform.smoothscale(screen, (int(WIDTH*zoom), int(HEIGHT*zoom)))

            # calculate the position of the zoomedScreen
            # if there is only one orange peg left, then zoom in on the orange peg
            if orangeCount < 2:
                # get the psosition of the orange peg
                for p in pegs:
                    if p.color == "orange":
                        zoomedScreenPos = (zoomedScreen.get_width()/zoom/2 - p.pos.x*zoom, zoomedScreen.get_height()/zoom/2 - p.pos.y*zoom)
                        break
            else:
                # zoom in on the ball
                zoomedScreenPos = (zoomedScreen.get_width()/zoom/2 - ball.pos.x*zoom, zoomedScreen.get_height()/zoom/2 - ball.pos.y*zoom)

            # if the zoomedScreen moves too far to the left or right, then set the x position to the edge of the screen
            if zoomedScreenPos[0] > 0:
                zoomedScreenPos = (0, zoomedScreenPos[1])
            elif zoomedScreenPos[0] < WIDTH - zoomedScreen.get_width():
                zoomedScreenPos = (WIDTH - zoomedScreen.get_width(), zoomedScreenPos[1])
            
            # if the zoomedScreen moves too far up or down, then set the y position to the edge of the screen
            if zoomedScreenPos[1] > 0:
                zoomedScreenPos = (zoomedScreenPos[0], 0)
            elif zoomedScreenPos[1] < HEIGHT - zoomedScreen.get_height():
                zoomedScreenPos = (zoomedScreenPos[0], HEIGHT - zoomedScreen.get_height())

            screen.blit(zoomedScreen, zoomedScreenPos)
        else:
            zoom = 1.0

    # draw text
    if not gameOver:
        # show how many balls are left
        ballText = ballCountFont.render(
            str(ballsRemaining), False, (200, 200, 200))
        screen.blit(ballText, (50, 50))
        # show the score
        # add commas to the score (e.g. 1000000 -> 1,000,000)
        formattedScore = ""
        for i in range(len(str(score))):
            formattedScore += str(score)[i]
            if (len(str(score)) - i - 1) % 3 == 0 and i != len(str(score)) - 1:
                formattedScore += ","
        scoreText = ballCountFont.render(formattedScore, False, (20, 60, 255))
        screen.blit(scoreText, (150, 50))
        # show the powerup information
        if powerUpActive:
            powerUpTextColor = (50, 255, 20)
        else:
            powerUpTextColor = (50, 170, 20)
        powerUpText = infoFont.render(
            powerUpType + ": " + str(powerUpCount), False, powerUpTextColor)
        screen.blit(powerUpText, (int(WIDTH/2 - powerUpText.get_width()/2), 5))

    # show if paused
    if gamePaused and not gameOver:
        pauseScreen, pauseSelection = getPauseScreen(mx, my, mouseClicked[0])
        screen.blit(pauseScreen, (0, 0))
        if pauseSelection == "resume":
            gamePaused = False
            delayTimer = TimedEvent(0.50)
        elif pauseSelection == "restart":
            # reset the game
            ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, frameRate, longShotBonus, staticImage = resetGame(
                balls, assignPegScreenLocation, createPegColors, bucket, pegs, originPegs)
            if not musicEnabled:
                pygame.mixer.music.stop()
            gamePaused = False
            delayTimer = TimedEvent(0.50)
        elif pauseSelection == "load":
            pygame.mixer.music.stop()
            pegs, originPegs, orangeCount, levelFileName = loadLevelMenu(screen, debug)
            # set the caption to include the level name
            pygame.display.set_caption(
                "PegglePy   -   " + levelFileName)
            # horrifying function that resets the game
            ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, frameRate, longShotBonus, staticImage = resetGame(
                balls, assignPegScreenLocation, createPegColors, bucket, pegs, originPegs)
            if not musicEnabled:
                pygame.mixer.music.stop()
            gamePaused = False
            delayTimer = TimedEvent(0.50)
        elif pauseSelection == "quit":
            gameRunning = False
            time.sleep(0.15)
        elif pauseSelection == "mainMenu":
            gamePaused = False
            # run the main menu until either the editor or start button is selected
            selection = "mainMenu"
            while selection == "mainMenu":
                selection = mainMenu(screen, debug)
                if selection == "quit":
                    gameRunning = False
                elif selection == "editor":
                    time.sleep(0.5)  # prevent accidental click on launch
                    levelEditorPauseSelection, editorPegs = levelEditor(screen, clock, debug)
                    if levelEditorPauseSelection == "quit":
                        gameRunning = False
                    elif levelEditorPauseSelection == "mainMenu":
                        selection = "mainMenu"
                    elif levelEditorPauseSelection == "play":
                        levelFileName = "Unsaved Editor Level"
                        originPegs = editorPegs.copy()

                        pegs = createPegColors(editorPegs.copy())

                        orangeCount = 0
                        for peg in pegs:
                            if peg.color == "orange":
                                orangeCount += 1

                        # reset the game
                        ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, frameRate, longShotBonus, staticImage = resetGame(
                            balls, assignPegScreenLocation, createPegColors, bucket, pegs, originPegs)

                elif selection == "settings":
                    if settingsMenu(screen, debug) == "mainMenu":
                        selection = "mainMenu"

            # reset the game
            ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, frameRate, longShotBonus, staticImage = resetGame(
                balls, assignPegScreenLocation, createPegColors, bucket, pegs, originPegs)

            # prevent accidental click on launch
            delayTimer = TimedEvent(0.5)

            if not musicEnabled:
                # change the song
                pygame.mixer.music.stop()
                loadRandMusic()
                pygame.mixer.music.play(-1)  # looping forever

            # set the caption to include the level name
            pygame.display.set_caption(
                "PegglePy   -   " + levelFileName)

        elif pauseSelection == "editor":
            gamePaused = False
            time.sleep(0.5)  # prevent accidental click on launch
            levelEditorPauseSelection, editorPegs = levelEditor(screen, clock, debug, False, originPegs.copy())
            if levelEditorPauseSelection == "quit":
                gameRunning = False
            elif levelEditorPauseSelection == "mainMenu":
                selection = "mainMenu"
                while selection == "mainMenu":
                    selection = mainMenu(screen, debug)
                    if selection == "quit":
                        gameRunning = False
                    elif selection == "editor":
                        time.sleep(0.5)
                        levelEditorPauseSelection, editorPegs = levelEditor(screen, clock, debug)
                        if levelEditorPauseSelection == "quit":
                            gameRunning = False
                        elif levelEditorPauseSelection == "mainMenu":
                            selection = "mainMenu"
                        elif levelEditorPauseSelection == "play":
                            levelFileName = "Unsaved Editor Level"
                            originPegs = editorPegs.copy()

                            pegs = createPegColors(editorPegs.copy())

                            orangeCount = 0
                            for peg in pegs:
                                if peg.color == "orange":
                                    orangeCount += 1

                            # reset the game
                            ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, frameRate, longShotBonus, staticImage = resetGame(
                                balls, assignPegScreenLocation, createPegColors, bucket, pegs, originPegs)
                            
                            delayTimer = TimedEvent(0.50)
                        
                        
                    elif selection == "settings":
                        if settingsMenu(screen, debug) == "mainMenu":
                            selection = "mainMenu"
                    
                # reset the game
                ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, frameRate, longShotBonus, staticImage = resetGame(
                    balls, assignPegScreenLocation, createPegColors, bucket, pegs, originPegs)
                
                # prevent accidental click on launch
                delayTimer = TimedEvent(0.5)

                if not musicEnabled:
                    # change the song
                    pygame.mixer.music.stop()
                    loadRandMusic()
                    pygame.mixer.music.play(-1)

            elif levelEditorPauseSelection == "play":
                levelFileName = "Unsaved Editor Level"
                originPegs = editorPegs.copy()

                pegs = createPegColors(editorPegs.copy())

                orangeCount = 0
                for peg in pegs:
                    if peg.color == "orange":
                        orangeCount += 1

                # reset the game
                ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, frameRate, longShotBonus, staticImage = resetGame(
                    balls, assignPegScreenLocation, createPegColors, bucket, pegs, originPegs)
                
                delayTimer = TimedEvent(0.50)

                

    # show if gameOver
    if gameOver:
        pauseText = menuFont.render("Game Over", False, (255, 255, 255))
        screen.blit(pauseText, (WIDTH/2 - pauseText.get_width()/2, HEIGHT/4))
        if ballsRemaining >= 0 and orangeCount < 1:
            # add commas to the score (e.g. 1000000 -> 1,000,000)
            formattedScore = ""
            for i in range(len(str(score))):
                formattedScore += str(score)[i]
                if (len(str(score)) - i - 1) % 3 == 0 and i != len(str(score)) - 1:
                    formattedScore += ","

            scoreText = menuFont.render(formattedScore, False, (20, 60, 255))
            screen.blit(scoreText, (WIDTH/2 - scoreText.get_width()/2, HEIGHT/3 + 50))
        else:
            tryAgainText = menuFont.render("Try Again", False, (255, 60, 20))
            screen.blit(tryAgainText, (WIDTH/2 - tryAgainText.get_width()/2, HEIGHT/2.2))

    # show the long shot score text only for a few seconds
    longShotTextTimer.update()
    if longShotTextTimer.isTriggered:
        longShotBonus = False
        longShotTextTimer.cancleTimer()

    if longShotBonus and not longShotTextTimer.isActive:
        longShotTextTimer.setTimer(1.25)

    if longShotBonus and not longShotTextTimer.isTriggered:
        # show the long shot score
        longShotText = infoFont.render("25,000", False, (255, 110, 0))
        screen.blit(longShotText, (longShotPos.x-28, longShotPos.y+11))
        # show the long shot text
        longShotText = infoFont.render("Long Shot!", False, (255, 110, 0))
        screen.blit(longShotText, (longShotPos.x-35, longShotPos.y-20))

    # debugging stuff
    if debug:
        if (clock.get_rawtime() < 10):  # decide whether green text or red text
            frameColor = (0, 255, 50)  # green
        else:
            frameColor = (255, 50, 0)  # red
        # print frametime
        frameTime = debugFont.render(
            str(clock.get_rawtime()) + " ms", False, (frameColor))
        screen.blit(frameTime, (5, 10))
        framesPerSec = debugFont.render(
            str(round(clock.get_fps())) + " fps", False, (255, 255, 255))
        screen.blit(framesPerSec, (5, 25))
        # print number of orange pegs remaining and score multiplier
        orangeCountText = debugFont.render(
            str(orangeCount) + " orange pegs left", False, (255, 255, 255))
        screen.blit(orangeCountText, (100, 35))
        scoreMultiplierText = debugFont.render(
            "x"+str(getScoreMultiplier(orangeCount, pegsHit)), False, (255, 255, 255))
        screen.blit(scoreMultiplierText, (100, 50))
        # print total number of pegs in the pegs list
        pegCountText = debugFont.render(
            str(len(pegs)) + " total pegs left", False, (255, 255, 255))
        screen.blit(pegCountText, (245, 35))
        # print ball velocity
        ballVelText = debugFont.render(
            "Velocity: " + str(ball.vel.getMag()), False, (255, 255, 255))
        screen.blit(ballVelText, (100, 20))
        # print which collision method is being used
        if useCPhysics:
            collisionMethodText = debugFont.render(
                "Using Ctypes: True", False, (255, 255, 255))
            screen.blit(collisionMethodText, (245, 50))
        # draw zenball trajectory (can cause a noticable performance hit due to the number of circles being drawn)
        if not done and powerUpType == "zenball" and bestTrajectory:
            if debugStaticImage == None:
                debugStaticImage = createStaticCircles(bestTrajectory)
            screen.blit(debugStaticImage, (0, 0))
        else:
            debugStaticImage = None
            bestTrajectory = None

        # draw line for joystick aim vector
        if controllerInput and not ball.isAlive and len(balls) < 2:
            drawLine(ball.pos.x, ball.pos.y, inputAim.x +
                     ball.pos.x, inputAim.y+ball.pos.y)
        elif not controllerInput and not ball.isAlive and len(balls) < 2:
            drawLine(ball.pos.x, ball.pos.y, mouseAim.x +
                     ball.pos.x, mouseAim.y+ball.pos.y)

        if controllerInput:
            joystickText = debugFont.render(
                joystick.get_name(), False, (255, 255, 255))
            screen.blit(joystickText, (WIDTH-300, 10))

        # draw bucket fake pegs
        for fakePeg in bucket.fakePegs.copy():
            drawCircle(fakePeg.pos.x, fakePeg.pos.y,
                       fakePeg.radius, (255, 0, 0))

        if speedHack:
            speedHackText = debugFont.render(
                "Speed Hack: ON", False, (255, 255, 255))
            screen.blit(speedHackText, (245, 5))

        if debugCollision:
            collSegmentDisp = debugFont.render(
                "Collision Segments: " + str(segmentCount), False, (0, 255, 255))
            screen.blit(collSegmentDisp, (230, 7))
            # draw collision sections
            segmentWidth = WIDTH/segmentCount
            for i in range(segmentCount):
                drawLine(segmentWidth*i, 0, segmentWidth*i, HEIGHT)

        # draw each pegs ballStuckTimer value
        if autoRemovePegs and debugAutoRemovePegsTimer:
            for p in pegs:
                if p.ballStuckTimer.timeRemaining > 0:
                    stuckTimerText = debugFont.render(
                        str(round(p.ballStuckTimer.timeRemaining, 3)), False, (255, 20, 10))
                    screen.blit(stuckTimerText, (p.pos.x, p.pos.y))
                else:
                    stuckTimerText = debugFont.render(
                        str(round(autoRemovePegsTimerValue, 3)), False, (255, 255, 255))
                    screen.blit(stuckTimerText, (p.pos.x, p.pos.y))

    # display red text indicating if cheats are enabled
    if cheats:
        cheatsIcon = debugFont.render("CHEATS ENABLED", False, (255, 0, 0))
        screen.blit(cheatsIcon, (100, 6))

    pygame.display.update()
    # lock game framerate to a specified tickrate (default is 144)
    if gamePaused:
        clock.tick(30)  # no need for high tickrate when paused
    else:
        clock.tick(frameRate)
    

print("Goodbye")
