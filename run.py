import sys  # used to exit the program immediately
import time

##### local imports #####
try:
    from local.config import baseTimeScale, closeCallTimeScale, timeScale, speedHack, cheats, debugAutoRemovePegsTimer
    from local.config import closeCallTimeScale, baseTimeScale, odeToJoyTimeScale, longShotDistance, noGravityTimeLength
    from local.config import LAUNCH_FORCE, queryRectSize, autoRemovePegs, autoRemovePegsTimerValue
    from local.config import powerUpType, powerUpActive, powerUpCount, pitch, pitchRaiseCount, trajectoryDepth
    from local.config import ballsRemaining, shouldClear, previousAim
    from local.userConfig import configs, defaultConfigs, saveSettings
    from local.trajectory import calcTrajectory, findBestTrajectory
    from local.audio import playSoundPitch, loadRandMusic, playMusic, stopMusic, autoPauseMusic, newSong, setMusicVolume
    from local.resources import gameIconImg, backgroundImg, ballImg
    from local.resources import launch_sound, sighSound, longShotSound, low_hit_sound, normal_hit_sound, failSound, drumRoll, pegPopSound
    from local.resources import cymbal, freeBallSound, powerUpSpooky1, powerUpSpooky2, powerUpSpooky3, powerUpSpooky4
    from local.resources import powerUpMultiBall, powerUpGuideBall, powerUpZenBall, powerUpZenBallHit, powerUpNoGravity
    from local.resources import menuFont, ballCountFont, debugFont, infoFont
    from local.misc import createStaticImage, createStaticCircles, updateStaticImage
    from local.misc import distBetweenTwoPoints, resetGame
    
    from local.triggerEvents import TimedEvent
    from local.animate import AnimationFade, getPegAnimationFrame
    from local.vectors import Vector, subVectors
    from local.collision import isBallTouchingPeg, resolveCollision
    from local.quadtree import QuadtreePegs, Rectangle

    from local.ball import Ball
    from local.peg import Peg, createPegColors, getScoreMultiplier
    from local.bucket import Bucket
except ImportError as e:
    print("ERROR: Unable to import local modules, this is likely due to a missing file or folder. Please make sure to run the script from within the PegglePy directory.\n")
    print(str(e.msg))
    print("\nExiting...")
    sys.exit(1)

from menu import mainMenu, getPauseScreen
from settingsMenu import settingsMenu
from editor import levelEditor
from loadLevelMenu import loadLevelMenu

import pygame

##### pygame stuff #####
pygame.init()
# set fullscreen
screen = pygame.display.set_mode(((configs["WIDTH"], configs["HEIGHT"])))
if configs["FULLSCREEN"]:
    pygame.display.toggle_fullscreen()

# set the refresh rate if VSYNC is enabled
if configs["VSYNC"]:
    configs["REFRESH_RATE"] = pygame.display.get_current_refresh_rate()
else:
    configs["REFRESH_RATE"] = 0

clock = pygame.time.Clock()  # game clock

pygame.display.set_caption("PegglePy")

# set the icon
pygame.display.set_icon(gameIconImg)


##### drawing functions #####
def drawCircle(x, y, rad=5, rgb=(255, 255, 255)):
    pygame.draw.circle(screen, (rgb), [x, y], rad)


def drawLine(x1, y1, x2, y2):
    pygame.draw.line(screen, (255, 0, 0), [x1, y1], [x2, y2])


### main menu ###
selection = "none"
editorSelection = "none"
while selection != "start" and selection != "quit":
    selection = mainMenu(screen)

    if selection == "quit":
        gameRunning = False
    elif selection == "editor":
        time.sleep(0.5)  # prevent accidental click on launch
        editorSelection, pegs = levelEditor(screen, clock)
        if editorSelection == "quit":
            gameRunning = False
            selection = "quit"
        elif editorSelection == "play":
            selection = "start"

    elif selection == "settings":
        time.sleep(0.15)
        if settingsMenu(screen) == "mainMenu":
            selection = "none"

# prevent accidental click on launch
delayTimer = TimedEvent(0.2)

### testing stuff ###
balls: list[Ball]
balls = []
#balls.append(Ball(configs["WIDTH"]/2, configs["HEIGHT"]/25))
balls.append(Ball(configs["WIDTH"]/2, configs["HEIGHT"]/25))
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
#inputAim = Vector(configs["WIDTH"]/2, (configs["HEIGHT"]/25)+50)
inputAim = Vector(configs["WIDTH"]/2, (configs["HEIGHT"]/25)+50)
gamePadFineTuneAmount = 0
debugBallPrevPos = False


longShotTextTimer = TimedEvent()

debugStaticImage: pygame.Surface = None

gameRunning = True

zoomInOnBall = False
zoom = 1

noGravityPowerUpTimer = TimedEvent()
noGravityPowerUpTimer.setTimer(0.1)
physicsTimeDebug = False
totalTime = 0
physicsTime = 0
drawTime = 0
updateTime = 0
quadtreeDebug = False
useQuadtree = True
# transparent surface for the quadtree
quadtreeStaticScreen = pygame.Surface((configs["WIDTH"], configs["HEIGHT"]), pygame.SRCALPHA)
dt = 1
dtArray = [] # track previous dt values

pegs: list[Peg]

if selection != "quit":
    if editorSelection != "play":
        pegs, originPegs, orangeCount, levelFileName = loadLevelMenu(screen)
        #pegs, originPegs, orangeCount, levelFileName = loadDefaultLevel()
        #pegs, originPegs, orangeCount, levelFileName = loadLevel("levels/Level 1.lvl")

        delayTimer = TimedEvent(0.2)
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

    staticImage = createStaticImage(pegs)

    loadRandMusic()
    setMusicVolume(configs["MUSIC_VOLUME"])
    if configs["MUSIC_ENABLED"]:
        playMusic()
    else:
        stopMusic()

else:
    gameRunning = False
    
# Set up the quadtree
boundary = Rectangle(configs["WIDTH"]/2, configs["HEIGHT"]/2, configs["WIDTH"]/2, configs["HEIGHT"]/2)
quadtree = QuadtreePegs(boundary, 4)
queryRect = Rectangle(0, 0, 0, 0)
nearbyPegs = []

isNewGameAnimationSequenceActive = True
isNewGameAnimationSequenceStart = True
isNewGameAnimationSequenceDone = True

isRemovePegsAnimationSequenceActive = False
isRemovePegsAnimationSequenceStart = False
isRemovePegsAnimationSequenceDone = False

hitPegs: list[Peg] = []

##### main loop #####
while gameRunning:
    startTotalTime = time.time()
    
    # minimum refresh rate is 120 (for now, this temporary fix allows the physics to update more frequently, improving accuracy)
    if configs["REFRESH_RATE"] <= 120 and configs["VSYNC"]:
        clock.tick(120)
    else:
        clock.tick(configs["REFRESH_RATE"])
    dtTemp = clock.get_time() / 5 # divide by 5 (magic number) to match the legacy code that ran at 144 fps
    
    # get the average dt over the last 10 frames
    dtArray.append(dtTemp)
    if len(dtArray) > 10:
        dtArray.pop(0)
    dt = sum(dtArray) / len(dtArray)
    dt *= timeScale
    
    
    if quadtree.pegs == [] and pegs != []:
        for p in pegs:
            quadtree.insert(p)
    
    launch_button = False
    gamePadFineTuneAmount = 0
    isNewGameAnimationSequenceStart = isNewGameAnimationSequenceDone and isNewGameAnimationSequenceStart and isNewGameAnimationSequenceActive
    isRemovePegsAnimationSequenceStart = isRemovePegsAnimationSequenceDone and isRemovePegsAnimationSequenceStart and isRemovePegsAnimationSequenceActive
    for event in pygame.event.get():  # check events and quit if the program is closed
        if event.type == pygame.QUIT:
            gameRunning = False
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                # horrifying function that resets the game
                ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, timeScale, longShotBonus, staticImage, quadtree = resetGame(
                    balls, createPegColors, bucket, pegs, originPegs, quadtree)
                if not configs["MUSIC_ENABLED"]:
                    stopMusic()
                isNewGameAnimationSequenceStart = True
            if event.key == pygame.K_1:  # enable or disable configs["DEBUG_MODE"] features
                configs["DEBUG_MODE"] = not configs["DEBUG_MODE"]
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
                    powerUpType = "no-gravity"
                elif powerUpType == "no-gravity":
                    powerUpType = "spooky"
            if event.key == pygame.K_4:  # toggle quadtreeDebug
                quadtreeDebug = not quadtreeDebug
                if quadtreeDebug:
                    quadtreeStaticScreen.fill((0, 0, 0, 0))
                    quadtree.show(quadtreeStaticScreen)
            if event.key == pygame.K_5:  # toggle quadtree vs brute force collision detection
                useQuadtree = not useQuadtree
            if event.key == pygame.K_6:  # toggle physics time debug
                physicsTimeDebug = not physicsTimeDebug
            if event.key == pygame.K_7:  # configs["DEBUG_MODE"] - enable or disable full trajectory drawing
                debugTrajectory = not debugTrajectory
            if event.key == pygame.K_l:  # load a new level
                stopMusic()
                pegs, originPegs, orangeCount, levelFileName = loadLevelMenu(screen)
                # set the caption to include the level name
                pygame.display.set_caption(
                    "PegglePy   -   " + levelFileName)
                # horrifying function that resets the game
                ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, timeScale, longShotBonus, staticImage, quadtree = resetGame(
                    balls,  createPegColors, bucket, pegs, originPegs, quadtree)
                if not configs["MUSIC_ENABLED"]:
                    stopMusic()
                delayTimer = TimedEvent(0.50)
                isNewGameAnimationSequenceStart = True
            if event.key == pygame.K_ESCAPE:  # enable or disable cheats
                gamePaused = not gamePaused
            if event.key == pygame.K_0:
                if timeScale != baseTimeScale:
                    timeScale = baseTimeScale
                else:
                    timeScale = closeCallTimeScale
            if event.key == pygame.K_m:
                configs["SOUND_ENABLED"] = not configs["SOUND_ENABLED"]
            if event.key == pygame.K_n:
                configs["MUSIC_ENABLED"] = not configs["MUSIC_ENABLED"]
                autoPauseMusic()
            if event.key == pygame.K_8:
                speedHack = not speedHack
            if event.key == pygame.K_9:
                debugAutoRemovePegsTimer = not debugAutoRemovePegsTimer
            # toggle zoom
            if event.key == pygame.K_x:
                zoomInOnBall = not zoomInOnBall
            # triple the time scale
            if event.key == pygame.K_t:
                if timeScale == baseTimeScale:
                    timeScale = baseTimeScale * 3
                else:
                    timeScale = baseTimeScale
            # toggle debugBallPrevPos
            if event.key == pygame.K_p:
                debugBallPrevPos = not debugBallPrevPos
            # toggle VSYNC
            if event.key == pygame.K_v:
                if configs["REFRESH_RATE"] == 0:
                    configs["VSYNC"] = True
                    configs["REFRESH_RATE"] = pygame.display.get_current_refresh_rate()
                else:
                    configs["VSYNC"] = False
                    configs["REFRESH_RATE"] = 0
                saveSettings()
                
            
            # toggle FULLSCREEN
            if event.key == pygame.K_f:
                if configs["FULLSCREEN"]:
                    #pygame.display.toggle_fullscreen()
                    # change window size to default user resolution
                    configs["WIDTH"], configs["HEIGHT"] = defaultConfigs["WIDTH"], defaultConfigs["HEIGHT"]
                    screen = pygame.display.set_mode(
                        (configs["WIDTH"], configs["HEIGHT"]))
                else:
                    #pygame.display.toggle_fullscreen()
                    # change window size to monitor resolution
                    screen = pygame.display.set_mode(
                        (0, 0), pygame.FULLSCREEN)
                    configs["WIDTH"], configs["HEIGHT"] = screen.get_size()
                        
                    
                configs["FULLSCREEN"] = not configs["FULLSCREEN"]
                saveSettings()
                
                # adjust the positions of every peg to be centered on the screen based on configs["WIDTH"] and configs["HEIGHT"]
                # get the position of the left most peg
                leftMostPeg = pegs[0]
                for peg in pegs:
                    if peg.pos.x < leftMostPeg.pos.x:
                        leftMostPeg = peg
                rightMostPeg = pegs[0]
                for peg in pegs:
                    if peg.pos.x > rightMostPeg.pos.x:
                        rightMostPeg = peg

                # find the center of the left most and right most pegs
                centerOfLeftAndRightPegs = (leftMostPeg.pos.x + rightMostPeg.pos.x)/2
                # find the center of the screen
                screenCenter = configs["WIDTH"]/2
                # find the difference between the center of the screen and the center of the left and right most pegs
                difference = screenCenter - centerOfLeftAndRightPegs

                # adjust the position of every peg by the difference
                for peg in pegs:
                    peg.pos.x += difference
                    
                # adjust the position of each ball by the difference
                for ball in balls:
                    ball.pos.x += difference
                    
                
                # Do same process again for the Y axis
                topMostPeg = pegs[0]
                for peg in pegs:
                    if peg.pos.y < topMostPeg.pos.y:
                        topMostPeg = peg
                bottomMostPeg = pegs[0]
                for peg in pegs:
                    if peg.pos.y > bottomMostPeg.pos.y:
                        bottomMostPeg = peg
                    
                # find the center of the top most and bottom most pegs
                centerOfTopAndBottomPegs = (topMostPeg.pos.y + bottomMostPeg.pos.y)/2
                # find the center of the screen
                screenCenter = configs["HEIGHT"]/2
                # find the difference between the center of the screen and the center of the top and bottom most pegs
                difference = screenCenter - centerOfTopAndBottomPegs
                
                # adjust the position of every peg by the difference
                for peg in pegs:
                    peg.pos.y += difference
                
                # adjust the position of each ball by the difference
                for ball in balls:
                    ball.pos.y += difference
                    
                # update ball position if none of the balls are alive
                if not any([ball.isAlive for ball in balls]):
                    ball.pos = Vector(configs["WIDTH"]/2, configs["HEIGHT"]/25)
                    ball.prevPos = ball.pos.copy()
                    
                    inputAim = Vector(configs["WIDTH"]/2, (configs["HEIGHT"]/25)+50)
                    
                # update the quadtree boundary
                boundary = Rectangle(configs["WIDTH"]/2, configs["HEIGHT"]/2, configs["WIDTH"]/2, configs["HEIGHT"]/2)
                
                # update the quadtree
                quadtree = QuadtreePegs(boundary, 4)
                queryRect = Rectangle(0, 0, 0, 0)
                nearbyPegs = []
                
                # update the bucket y position to be at the bottom of the screen
                bucket.pos = Vector(configs["WIDTH"]/2, configs["HEIGHT"] - bucket.bucketBackImg.get_height())  # position
                                
                # update the static image
                staticImage = createStaticImage(pegs)
                    
            # open the main menu
            if event.key == pygame.K_z:
                selection = mainMenu(screen)

                if selection == "quit":
                    gameRunning = False
                elif selection == "editor":
                    time.sleep(0.5)  # prevent accidental click on launch
                    levelEditor(screen, clock)

                # reset the game
                ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, timeScale, longShotBonus, staticImage, quadtree = resetGame(
                    balls,  createPegColors, bucket, pegs, originPegs, quadtree)

                # prevent accidental click on launch
                delayTimer = TimedEvent(0.50)
                
                isNewGameAnimationSequenceStart = True

                if not configs["MUSIC_ENABLED"]:
                    # change the song
                    newSong()

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
                        powerUpType = "no-gravity"
                    elif powerUpType == "no-gravity":
                        powerUpType = "spooky"
                if event.button == 2:  # the '△'/triangle button on a ps4 controller
                    # reset the game
                    ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, timeScale, longShotBonus, staticImage, quadtree = resetGame(
                        balls,  createPegColors, bucket, pegs, originPegs, quadtree)  # horrifying function that resets the game
                    if not configs["MUSIC_ENABLED"]:
                        stopMusic()
                    isNewGameAnimationSequenceStart = True
                if event.button == 4:  # the 'L1' button on a ps4 controller
                    # rumble test
                    if pygame.joystick.get_count() > 0:
                        if configs["DEBUG_MODE"]:
                            print("rumble test - 100 ms")
                        joystick = pygame.joystick.Joystick(0)
                        joystick.rumble(1, 1, 100)
                if event.button == 5:  # the 'R1' button on a ps4 controller
                    # cheats
                    cheats = not cheats
                if event.button == 8:  # the 'share' button on a ps4 controller
                    # enable or disable configs["DEBUG_MODE"]
                    configs["DEBUG_MODE"] = not configs["DEBUG_MODE"]
                if event.button == 9:  # the 'options' button on a ps4 controller
                    # pause the game
                    gamePaused = not gamePaused
                if event.button == 11 or event.button == 12:  # the 'L3' or 'R3' joystick buttons on a ps4 controller
                    # enable or disable sound and music
                    if configs["MUSIC_ENABLED"]:
                        autoPauseMusic()
                    else:
                        stopMusic() 

                    configs["SOUND_ENABLED"] = not configs["SOUND_ENABLED"]

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
                        powerUpType = "no-gravity"
                    elif powerUpType == "no-gravity":
                        powerUpType = "spooky"
                if event.button == 3:  # the 'Y' button on an xbox controller
                    # reset the game
                    ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, timeScale, longShotBonus, staticImage, quadtree = resetGame(
                        balls,  createPegColors, bucket, pegs, originPegs, quadtree)
                    if not configs["MUSIC_ENABLED"]:
                        stopMusic()
                    isNewGameAnimationSequenceStart = True
                if event.button == 6:  # the 'start' button on an xbox controller
                    configs["DEBUG_MODE"] = not configs["DEBUG_MODE"]
                if event.button == 7:  # the 'back' button on an xbox controller
                    gamePaused = not gamePaused
                # the 'left stick' or 'right stick' buttons on an xbox controller
                if event.button == 9 or event.button == 10:
                    if configs["MUSIC_ENABLED"]:
                        autoPauseMusic()
                    else:
                        stopMusic()
                        
                    configs["SOUND_ENABLED"] = not configs["SOUND_ENABLED"]
                if event.button == 4:  # the 'left bumper' button on an xbox controller
                    # rumble test
                    if pygame.joystick.get_count() > 0:
                        if configs["DEBUG_MODE"]:
                            print("rumble test - 100 ms")
                        joystick = pygame.joystick.Joystick(0)
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
        delayTimer = TimedEvent(0.50)
        # horrifying function that resets the game
        ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, timeScale, longShotBonus, staticImage, quadtree = resetGame(
            balls,  createPegColors, bucket, pegs, originPegs, quadtree)
        if not configs["MUSIC_ENABLED"]:
            stopMusic()
            
    if isNewGameAnimationSequenceStart:
        isNewGameAnimationSequenceStart = False
        isNewGameAnimationSequenceActive = True
        isNewGameAnimationSequenceDone = False
    
        # set a delay incremental to each pegs index in the pegs list
        for i, peg in enumerate(pegs):
            # scale the delay based on the length of the pegs list
            # this is to keep the animation time consistent regardless of the number of pegs
            animationTime = 50 
            peg.animation.startFadeIn(((animationTime / len(pegs)) * i) + 10)

    if isNewGameAnimationSequenceActive:
        tempDt = dt
        if not delayTimer.isTriggered or gamePaused:
            tempDt = 0

        animationFrameScreen = getPegAnimationFrame(pegs, tempDt)

        # check if the animation is done
        for peg in pegs:
            if peg.animation.done:
                isNewGameAnimationSequenceDone = True
            else:
                isNewGameAnimationSequenceDone = False
                break
        
        if isNewGameAnimationSequenceDone:
            isNewGameAnimationSequenceActive = False
            isNewGameAnimationSequenceDone = True
                
    if isRemovePegsAnimationSequenceStart:
        isRemovePegsAnimationSequenceStart = False
        isRemovePegsAnimationSequenceActive = True
        isRemovePegsAnimationSequenceDone = False

        # set a delay incremental to each pegs index in the pegs list
        for i, peg in enumerate(hitPegs):
            peg.animation.startFadeOut(20 + peg.animation.duration*0.25 * i)
            
        animationStartTime = time.time()
            
    if isRemovePegsAnimationSequenceActive:
        tempDt = dt
        if not delayTimer.isTriggered or gamePaused:
            tempDt = 0
            
        # play sound when a peg has started its animation (startTrigger)
        for i, peg in enumerate(hitPegs):
            if peg.animation.startTrigger:
                if peg.animation.fadeOut:
                    if configs["SOUND_ENABLED"] and configs["SOUND_VOLUME"] > 0:
                        playSoundPitch(pegPopSound, volume=configs["SOUND_VOLUME"] + 0.05)
        
        # track elapsed animation time and increase the speed if its taking longer
        # (shouldn't be an issue unless the level has hundreds of pegs or more)
        elapsedTime = time.time() - animationStartTime
        if elapsedTime > 5 and elapsedTime < 15:
            animationFrameScreen = getPegAnimationFrame(hitPegs, tempDt*2)
        elif elapsedTime > 15 and elapsedTime < 25:
            animationFrameScreen = getPegAnimationFrame(hitPegs, tempDt*5)
        elif elapsedTime > 25:
            animationFrameScreen = getPegAnimationFrame(hitPegs, tempDt*15)
        else:
            animationFrameScreen = getPegAnimationFrame(hitPegs, tempDt)

        if len(hitPegs) == 0:
            # if there are no pegs to remove, set the animation to done
            isRemovePegsAnimationSequenceDone = True
            isRemovePegsAnimationSequenceActive = False
            isRemovePegsAnimationSequenceStart = False
        
        # check if the animation is done
        for peg in hitPegs:
            if peg.animation.done:
                isRemovePegsAnimationSequenceDone = True
            else:
                isRemovePegsAnimationSequenceDone = False
                break
        
        if isRemovePegsAnimationSequenceDone:
            isRemovePegsAnimationSequenceActive = False
            isRemovePegsAnimationSequenceDone = True
                
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
                ), quadtree, dt, (powerUpType == "guideball" and powerUpActive), trajectoryDepth, debugTrajectory)
        previousAim = Vector(launchAim.x, launchAim.y)

        delayTimer.update()  # prevent the ball from launching instantly after the game is reset
        # if mouse clicked then trigger ball launch
        if launch_button and not ball.isAlive and delayTimer.isTriggered and len(balls) < 2 and not isNewGameAnimationSequenceActive and not isRemovePegsAnimationSequenceActive:
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
                if configs["SOUND_ENABLED"]:
                    playSoundPitch(launch_sound)
                ball.isLaunch = False
                shouldClear = True
            # if powerup type is zenball and it is not active then normal launch
            elif not powerUpActive and powerUpType == "zenball":
                launchForce = subVectors(launchAim, ball.pos)
                launchForce.setMag(LAUNCH_FORCE)
                ball.applyForce(launchForce)
                if configs["SOUND_ENABLED"]:
                    playSoundPitch(launch_sound)
                ball.isLaunch = False
                shouldClear = True
                drawTrajectory = False

        # cheats (force enable power up)
        if cheats:
            powerUpActive = True

        # if active zenball powerup - launch
        if ball.isLaunch and ball.isAlive and powerUpType == "zenball" and powerUpActive:
            # find the best shot
            if configs["SOUND_ENABLED"]:
                playSoundPitch(powerUpZenBall, 0.93)
            if configs["DEBUG_MODE"]:
                print("Debug: Zenball launched")
                startTime = time.time()
            bestAim, bestScore, bestTrajectory = findBestTrajectory(Vector(
                launchAim.x, launchAim.y), Vector(ball.pos.x, ball.pos.y), pegs.copy(), quadtree, dt)

            if configs["DEBUG_MODE"]:
                print("Debug: Zenball best aim found in " +
                      str(time.time() - startTime) + " seconds")

            for p in pegs:
                p.isHit = False

            if bestScore >= 10:
                if configs["SOUND_ENABLED"]:
                    playSoundPitch(powerUpZenBall, 0.99)
                ball.applyForce(bestAim)
            elif bestScore < 10:  # if there is no possible shot with the zen ball to earn points then it has failed
                if configs["SOUND_ENABLED"]:
                    playSoundPitch(failSound)
                # apply original launch aim
                ball.applyForce(subVectors(launchAim, ball.pos))

            if configs["SOUND_ENABLED"]:
                playSoundPitch(launch_sound)
            ball.isLaunch = False
            shouldClear = True
            powerUpCount -= 1
            if powerUpCount < 1:
                powerUpActive = False or cheats

        # cheats, place ball anywhere on screen with right click
        if cheats and mouseClicked[2] and ball.isAlive and not ball.isLaunch:
            isValidPlacement = True
            for ball in balls:
                mouseBall = Ball(mx, my)
                if isBallTouchingPeg(ball, mouseBall, 1):
                    isValidPlacement = False
            if isValidPlacement:
                newCheatBall = Ball(mx, my)
                newCheatBall.isAlive = True
                balls.append(newCheatBall)
                ball = newCheatBall
                
        # if no-gravity powerup is active
        noGravityPowerUpActive = False
        if powerUpActive and powerUpType == "no-gravity":
            noGravityPowerUpTimer.update()
            noGravityPowerUpActive = True
            if noGravityPowerUpTimer.isTriggered:
                noGravityPowerUpActive = False
                noGravityPowerUpTimer.cancelTimer()
                powerUpCount -= 1
                powerUpActive = False or cheats
        else:
            noGravityPowerUpActive = False

        # measure performance of the physics calculations loop
        startPhysicsTime = time.time()
        
        # update ball physics and pegs, additional game logic
        for b in balls:
            if b.isAlive:
                #### collision ####
                # get the pegs that are in the same screen location as the ball (scaled by queryRectSize)
                queryRect = Rectangle(b.pos.x, b.pos.y, queryRectSize, queryRectSize)
                if useQuadtree:
                    nearbyPegs = quadtree.query(queryRect)
                else:
                    nearbyPegs = pegs
                for p in nearbyPegs:
                    # if the current peg is the last remaining orange peg then apply special effects
                    if p.color == "orange" and orangeCount == 1 and not p.isHit:
                        largerRadPeg = Peg(p.pos.x, p.pos.y)
                        largerRadPeg.radius = p.radius * 5
                        ballTouchingPeg = isBallTouchingPeg(b, largerRadPeg, dt)
                        if ballTouchingPeg:
                            if timeScale != closeCallTimeScale and len(balls) < 2:
                                # only play sound once
                                if configs["SOUND_ENABLED"]:
                                    playSoundPitch(drumRoll)
                            timeScale = closeCallTimeScale # slow motion
                            closeBall = b
                        elif timeScale != baseTimeScale:
                            # only play sound once
                            if configs["SOUND_ENABLED"]:
                                playSoundPitch(sighSound)
                            timeScale = baseTimeScale

                    # ball physics and game logic
                    ballTouchingPeg = isBallTouchingPeg(b, p, dt)
                    if ballTouchingPeg:
                        # resolve the collision between the ball and peg
                        b = resolveCollision(b, nearbyPegs, dt)

                        # save the peg that was last hit, used for when the ball is stuck and for bonus points
                        # p is the quadtree quary, so lets find the actual peg in the pegs list
                        for peg in pegs:
                            if peg.pos.x == p.pos.x and peg.pos.y == p.pos.y:
                                b.lastPegHit = peg
                                break

                        # automatically remove pegs that a ball is stuck on
                        if autoRemovePegs:
                            p.ballStuckTimer.update()

                            # when timer has triggered, remove the last hit peg
                            if p.ballStuckTimer.isTriggered and b.lastPegHit != None:
                                pegs.remove(b.lastPegHit)  # remove the peg
                                b.lastPegHit = None
                                hasPegBeenRemoved = True
                                p.ballStuckTimer.cancelTimer()
                                # update quadtree before updating ball physics
                                quadtree = QuadtreePegs(boundary, len(pegs))
                                for peg in pegs:
                                    quadtree.insert(peg)
                                if quadtreeDebug:
                                    quadtreeStaticScreen.fill((0, 0, 0, 0))
                                    quadtree.show(quadtreeStaticScreen)

                            # if the velocity is less than 1.5 then it might be stuck, wait a few seconds and remove the peg its stuck on
                            if b.vel.getMag() <= 1.5 and p.ballStuckTimer.isActive == False:
                                p.ballStuckTimer.setTimer(
                                    autoRemovePegsTimerValue)
                            elif b.vel.getMag() > 1.5:
                                p.ballStuckTimer.cancelTimer()
                                b.lastPegHit = None

                        # check for long shot bonus
                        if b.lastPegHitPos != p.pos and b.lastPegHitPos != None and p.color == "orange" and not p.isHit:
                            if distBetweenTwoPoints(b.lastPegHitPos.x, b.lastPegHitPos.y, p.pos.x, p.pos.y) > longShotDistance:
                                if not longShotBonus:
                                    if configs["SOUND_ENABLED"]:
                                        playSoundPitch(longShotSound)
                                    score += 25000
                                    b.lastPegHitPos = None
                                    longShotBonus = True

                                    # used for showing the bonus score
                                    longShotPos = Vector(
                                        p.pos.x, p.pos.y)

                                    if pygame.joystick.get_count() > 0 and controllerInput:
                                        if configs["DEBUG_MODE"]:
                                            print("Debug: Rumble")
                                        joystick = pygame.joystick.Joystick(
                                            0)
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
                                        if configs["SOUND_ENABLED"]:
                                            playSoundPitch(powerUpSpooky1)
                                        firstSpookyHit = True
                                    elif powerUpCount == 1:
                                        if configs["SOUND_ENABLED"]:
                                            playSoundPitch(powerUpSpooky2)
                                        firstSpookyHit = False
                                if powerUpType == "multiball":
                                    if configs["SOUND_ENABLED"]:
                                        playSoundPitch(powerUpMultiBall)
                                    addNewBall = True
                                if powerUpType == "zenball":
                                    if configs["SOUND_ENABLED"]:
                                        playSoundPitch(powerUpZenBallHit)
                                if powerUpType == "guideball":
                                    if configs["SOUND_ENABLED"]:
                                        playSoundPitch(powerUpGuideBall)
                                    powerUpCount += 2
                                if powerUpType == "spooky-multiball":
                                    if configs["SOUND_ENABLED"]:
                                        playSoundPitch(powerUpMultiBall)
                                    addNewBall = True
                                    powerUpCount += 1
                                if powerUpType == "no-gravity":
                                    if powerUpCount < 1:
                                        # start the no gravity powerup timer
                                        noGravityPowerUpTimer.setTimer(
                                            noGravityTimeLength)
                                    if configs["SOUND_ENABLED"]:
                                        playSoundPitch(powerUpNoGravity, 1.9)
                                        playSoundPitch(powerUpNoGravity, 0.8)
                                    
                                    
                                powerUpCount += 1
                                powerUpActive = True

                            # peg hit sounds
                            if pitchRaiseCount <= 7:
                                if not p.isPowerUp:
                                    if configs["SOUND_ENABLED"]:
                                        playSoundPitch(low_hit_sound, pitch)
                                pitch -= 0.05  # magic number
                            if pitchRaiseCount == 7:
                                pitch = 1.32  # magic number
                            elif pitchRaiseCount > 7 and pitchRaiseCount < 26:
                                if not p.isPowerUp:
                                    if configs["SOUND_ENABLED"]:
                                        playSoundPitch(normal_hit_sound, pitch)
                                pitch -= 0.045  # magic number
                            elif pitchRaiseCount >= 26:
                                if not p.isPowerUp:
                                    if configs["SOUND_ENABLED"]:
                                        playSoundPitch(normal_hit_sound, pitch)

                            # cheats
                            if cheats:
                                if powerUpType == "spooky":
                                    # if configs["SOUND_ENABLED"]:
                                    #   playSoundPitch(powerUpSpooky1)
                                    powerUpCount += 1
                                if powerUpType == "multiball":
                                    if configs["SOUND_ENABLED"]:
                                        playSoundPitch(powerUpMultiBall)
                                    addNewBall = True
                                    powerUpCount += 1
                                if powerUpType == "guideball":
                                    powerUpCount += 2
                                if powerUpType == "spooky-multiball":
                                    if configs["SOUND_ENABLED"]:
                                        playSoundPitch(powerUpMultiBall)
                                    # if configs["SOUND_ENABLED"]:
                                    #   playSoundPitch(powerUpSpooky1)
                                    addNewBall = True
                                    powerUpCount += 2
                                if powerUpType == "zenball":
                                    powerUpCount += 1
                                if powerUpType == "no-gravity":
                                    noGravityPowerUpActive = True

                            # keep track of points earned
                            # pointsEarned.append(p.points)
                            score += (p.points *
                                        getScoreMultiplier(orangeCount, pegsHit))

                            if speedHack:
                                # update the static image to show the peg has been hit (can increase performance, but at the cost of visual wierdness)
                                staticImage = updateStaticImage(
                                    staticImage, p)

                #if no-gravity powerup is active
                if noGravityPowerUpActive:
                    # keep a minimum velocity
                    if b.vel.getMag() < 1.5:
                        b.vel.setMag(1.5)
                    if b.vel.getMag() < 0.2:
                        b.vel.add(Vector(0, 1))
                
                # check if ball has hit the sides of the bucket (this is a special case handled after the pegs have been checked)
                collidedPeg = bucket.isBallCollidingWithBucketEdge(b, dt)
                if collidedPeg:
                    b = resolveCollision(b, [collidedPeg], dt)
                    
                b.update(dt, noGravityPowerUpActive)

                # if active spooky powerup
                if powerUpActive and (powerUpType == "spooky" or powerUpType == "spooky-multiball"):
                    if b.pos.y + b.radius > configs["HEIGHT"]:
                        b.pos.y = 0 + b.radius
                        b.inBucket = False
                        # set previous values to current values to prevent collision detection breaking during screen wrap
                        b.prevPos = Vector(b.pos.x, b.pos.y)
                        b.prevAcc = Vector(b.acc.x, b.acc.y)
                        b.prevVel = Vector(b.vel.x, b.vel.y)
                        if powerUpCount == 1 and firstSpookyHit:
                            if configs["SOUND_ENABLED"]:
                                playSoundPitch(powerUpSpooky2)
                        elif powerUpCount == 1 and not firstSpookyHit:
                            if configs["SOUND_ENABLED"]:
                                playSoundPitch(powerUpSpooky4)
                        elif powerUpCount == 2 and not firstSpookyHit:
                            if configs["SOUND_ENABLED"]:
                                playSoundPitch(powerUpSpooky3)
                        elif cheats:
                            if configs["SOUND_ENABLED"]:
                                playSoundPitch(powerUpSpooky2)
                        powerUpCount -= 1
                        if powerUpCount < 1:
                            powerUpActive = False or cheats

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
                    if configs["SOUND_ENABLED"]:
                        playSoundPitch(freeBallSound)
                    ballsRemaining += 1

            # remove any 'dead' balls
            elif not b.isAlive and b != ball:
                balls.remove(b)
                
        # save time for physics calculations
        physicsTime = time.time() - startPhysicsTime

        # if a peg was hit or removed this frame, update the static image (this is an optimazation to prevent the static image from being updated more than once per frame)
        if hasPegBeenHit and not speedHack:
            # generate new static image to show the peg has been hit or removed (can cause pefromance hiccups especially when there are lots of pegs in the level)
            staticImage = createStaticImage(pegs)
            hasPegBeenHit = False

        # regardless of speedHack, update the static image if a peg was removed
        if hasPegBeenRemoved:
            hasPegBeenRemoved = False
            staticImage = createStaticImage(pegs)
            # update quadtree before updating ball physics
            quadtree = QuadtreePegs(boundary, len(pegs))
            for peg in pegs:
                quadtree.insert(peg)
                quadtree.insert(peg)
            if quadtreeDebug:
                quadtreeStaticScreen.fill((0, 0, 0, 0))
                quadtree.show(quadtreeStaticScreen)

        # this little loop and if statement will determine if any of the balls are still alive and therfore if everything should be cleared/reset or not
        done = True
        for b in balls:
            if b.isAlive:
                done = False
                break

        # check if their are any orange pegs or if the player has no balls (lol)
        if done and (orangeCount == 0 or ballsRemaining < 1) and gameOver == False:
            if isRemovePegsAnimationSequenceDone:
                gameOver = True
                if ballsRemaining < 1 and orangeCount > 0:
                    if configs["SOUND_ENABLED"]:
                        playSoundPitch(failSound)

        # check if the last orange peg has been hit, play ode to joy and change the buckets
        if orangeCount < 1 and not ballsRemaining < 1 and not alreadyPlayedOdeToJoy:
            pygame.mixer.music.load("resources/audio/music/ode_to_joy.wav")
            if configs["MUSIC_ENABLED"]:
                pygame.mixer.music.play(-1)
            if configs["SOUND_ENABLED"]:
                playSoundPitch(cymbal)
            alreadyPlayedOdeToJoy = True
            timeScale = odeToJoyTimeScale # slow motion but not as slow as close call

        # reset everything and remove hit pegs
        if done and shouldClear:
            shouldClear = False
            balls.clear()  # clear all the balls
            # recreate the original ball
            #balls.append(Ball(configs["WIDTH"]/2, configs["HEIGHT"]/25))
            balls.append(Ball(configs["WIDTH"]/2, configs["HEIGHT"]/25))
            ball = balls[0]
            ball.reset()
            pitch = 1.0
            pitchRaiseCount = 0
            freeBall = False
            done = False
            ballsRemaining -= 1
            pegsHit = 0
            longShotBonus = False
            timeScale = baseTimeScale
            # forces the trajectory to be recalculated in case the mouse aim has not changed
            previousAim = Vector(0, 1)
            if powerUpType == "multiball" or powerUpType == "spooky-multiball":
                powerUpActive = False or cheats
                powerUpCount = 0
            
            # save hit pegs for animation
            hitPegs = [p for p in pegs if p.isHit]

            # start the peg removal animation sequence
            isRemovePegsAnimationSequenceStart = True
            isRemovePegsAnimationSequenceActive = True
            isRemovePegsAnimationSequenceDone = True
            
            animationFrameScreen = createStaticImage(pegs)
            
            delayTimer = TimedEvent(0.25)  
            
            # remove hit pegs
            pegs = [p for p in pegs if not p.isHit]
            for s in pointsEarned:
                score += s
            staticImage = createStaticImage(pegs)
            
            # quadtree update
            quadtree = QuadtreePegs(boundary, len(pegs))
            for peg in pegs:
                quadtree.insert(peg)
            if quadtreeDebug:
                quadtreeStaticScreen.fill((0, 0, 0, 0))
                quadtree.show(quadtreeStaticScreen)

        # bucket, pass the power up info for the bucket to update its collison and image
        bucket.update(dt, powerUpType, powerUpActive)

    # measure time for draw calls
    startDrawTime = time.time()

    ##### draw #####
    if isNewGameAnimationSequenceActive:
        backgroundImg = pygame.transform.scale(
            backgroundImg, (configs["WIDTH"], configs["HEIGHT"]))
        screen.blit(backgroundImg, (0, 0))
        screen.blit(animationFrameScreen, (0, 0))
    else:
        screen.blit(staticImage, (0, 0))
        if isRemovePegsAnimationSequenceActive:
            screen.blit(animationFrameScreen, (0, 0))
    
    # draw back of bucket
    bucketBackImg, bucketFrontImg = bucket.getImage(powerUpType, powerUpActive)
    screen.blit(bucketBackImg, (bucket.pos.x, bucket.pos.y))
    # draw ball(s)
    if not gameOver and not isNewGameAnimationSequenceActive and not isRemovePegsAnimationSequenceActive:
        for b in balls:
            screen.blit(ballImg, (b.prevPos.x - ballImg.get_width() /
                        2, b.prevPos.y - ballImg.get_height()/2))
    # draw front of bucket
    screen.blit(bucketFrontImg, (bucket.pos.x, bucket.pos.y))
    # draw trajectory path
    done = True
    for b in balls:
        if b.isAlive:
            done = False
    if done and not gameOver and not gamePaused and not isNewGameAnimationSequenceActive and not isRemovePegsAnimationSequenceActive:
        for fb in trajectory:
            # draw line from each point in the trajectory
            pygame.draw.line(screen, (10, 70, 163), (fb.prevPos.x, fb.prevPos.y), (fb.pos.x, fb.pos.y), 6)

    # "zoom in" on the ball by transorming the image
    # scale the image and blit it at the position of the ball
    if zoomInOnBall:
        # zoom in
        zoom += 0.005
        if zoom > 1.8:
            zoom = 1.8

        zoomedScreen = pygame.transform.smoothscale(screen, (int(configs["WIDTH"]*zoom), int(configs["HEIGHT"]*zoom)))

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
        elif zoomedScreenPos[0] < configs["WIDTH"] - zoomedScreen.get_width():
            zoomedScreenPos = (configs["WIDTH"] - zoomedScreen.get_width(), zoomedScreenPos[1])
        
        # if the zoomedScreen moves too far up or down, then set the y position to the edge of the screen
        if zoomedScreenPos[1] > 0:
            zoomedScreenPos = (zoomedScreenPos[0], 0)
        elif zoomedScreenPos[1] < configs["HEIGHT"] - zoomedScreen.get_height():
            zoomedScreenPos = (zoomedScreenPos[0], configs["HEIGHT"] - zoomedScreen.get_height())

        screen.blit(zoomedScreen, zoomedScreenPos)
    else:
        # zoom out
        if zoom > 1.0:
            if alreadyPlayedOdeToJoy or timeScale == closeCallTimeScale:
                zoom -= 0.0025
            else:
                zoom -= 0.005
            
            zoomedScreen = pygame.transform.smoothscale(screen, (int(configs["WIDTH"]*zoom), int(configs["HEIGHT"]*zoom)))

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
            elif zoomedScreenPos[0] < configs["WIDTH"] - zoomedScreen.get_width():
                zoomedScreenPos = (configs["WIDTH"] - zoomedScreen.get_width(), zoomedScreenPos[1])
            
            # if the zoomedScreen moves too far up or down, then set the y position to the edge of the screen
            if zoomedScreenPos[1] > 0:
                zoomedScreenPos = (zoomedScreenPos[0], 0)
            elif zoomedScreenPos[1] < configs["HEIGHT"] - zoomedScreen.get_height():
                zoomedScreenPos = (zoomedScreenPos[0], configs["HEIGHT"] - zoomedScreen.get_height())

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
        if noGravityPowerUpActive:
            powerUpText = infoFont.render(
                powerUpType + ": " + str(round(noGravityPowerUpTimer.timeRemaining, 1)), False, powerUpTextColor)
        else:
            powerUpText = infoFont.render(
                powerUpType + ": " + str(powerUpCount), False, powerUpTextColor)
        screen.blit(powerUpText, (int(configs["WIDTH"]/2 - powerUpText.get_width()/2), 5))

    # show if paused
    if gamePaused and not gameOver:
        pauseScreen, pauseSelection = getPauseScreen(mx, my, mouseClicked[0])
        screen.blit(pauseScreen, (0, 0))
        if pauseSelection == "resume":
            gamePaused = False
            delayTimer = TimedEvent(0.50)
        elif pauseSelection == "restart":
            # reset the game
            ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, timeScale, longShotBonus, staticImage, quadtree = resetGame(
                balls,  createPegColors, bucket, pegs, originPegs, quadtree)
            if not configs["MUSIC_ENABLED"]:
                stopMusic()
            gamePaused = False
            delayTimer = TimedEvent(0.50)
            isNewGameAnimationSequenceStart = True
        elif pauseSelection == "load":
            pygame.mixer.music.stop()
            pegs, originPegs, orangeCount, levelFileName = loadLevelMenu(screen)
            # set the caption to include the level name
            pygame.display.set_caption(
                "PegglePy   -   " + levelFileName)
            # horrifying function that resets the game
            ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, timeScale, longShotBonus, staticImage, quadtree = resetGame(
                balls,  createPegColors, bucket, pegs, originPegs, quadtree)
            if not configs["MUSIC_ENABLED"]:
                stopMusic()
            gamePaused = False
            delayTimer = TimedEvent(0.50)
            isNewGameAnimationSequenceStart = True
        elif pauseSelection == "quit":
            gameRunning = False
            time.sleep(0.15)
        elif pauseSelection == "mainMenu":
            gamePaused = False
            # run the main menu until either the editor or start button is selected
            selection = "mainMenu"
            while selection == "mainMenu":
                selection = mainMenu(screen)
                if selection == "quit":
                    gameRunning = False
                elif selection == "editor":
                    time.sleep(0.5)  # prevent accidental click on launch
                    levelEditorPauseSelection, editorPegs = levelEditor(screen, clock)
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
                        ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, timeScale, longShotBonus, staticImage, quadtree = resetGame(
                            balls,  createPegColors, bucket, pegs, originPegs, quadtree)
                        
                        isNewGameAnimationSequenceStart = True

                elif selection == "settings":
                    if settingsMenu(screen) == "mainMenu":
                        selection = "mainMenu"

            # reset the game
            ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, timeScale, longShotBonus, staticImage, quadtree = resetGame(
                balls,  createPegColors, bucket, pegs, originPegs, quadtree)

            isNewGameAnimationSequenceStart = True

            # prevent accidental click on launch
            delayTimer = TimedEvent(0.50)

            #change the song
            if configs["MUSIC_ENABLED"]:
                newSong()

            # set the caption to include the level name
            pygame.display.set_caption(
                "PegglePy   -   " + levelFileName)

        elif pauseSelection == "editor":
            gamePaused = False
            time.sleep(0.5)  # prevent accidental click on launch
            levelEditorPauseSelection, editorPegs = levelEditor(screen, clock, False, originPegs.copy())
            if levelEditorPauseSelection == "quit":
                gameRunning = False
            elif levelEditorPauseSelection == "mainMenu":
                selection = "mainMenu"
                while selection == "mainMenu":
                    selection = mainMenu(screen)
                    if selection == "quit":
                        gameRunning = False
                    elif selection == "editor":
                        time.sleep(0.5)
                        levelEditorPauseSelection, editorPegs = levelEditor(screen, clock)
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
                            ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, timeScale, longShotBonus, staticImage, quadtree = resetGame(
                                balls,  createPegColors, bucket, pegs, originPegs, quadtree)
                            
                            delayTimer = TimedEvent(0.50)
                            
                            isNewGameAnimationSequenceStart = True
                        
                        
                    elif selection == "settings":
                        if settingsMenu(screen) == "mainMenu":
                            selection = "mainMenu"
                    
                # reset the game
                ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, timeScale, longShotBonus, staticImage, quadtree = resetGame(
                    balls,  createPegColors, bucket, pegs, originPegs, quadtree)
                
                isNewGameAnimationSequenceStart = True
                
                # prevent accidental click on launch
                delayTimer = TimedEvent(0.50)

                if configs["MUSIC_ENABLED"]:
                    newSong()
                    

            elif levelEditorPauseSelection == "play":
                levelFileName = "Unsaved Editor Level"
                originPegs = editorPegs.copy()

                pegs = createPegColors(editorPegs.copy())

                orangeCount = 0
                for peg in pegs:
                    if peg.color == "orange":
                        orangeCount += 1

                # reset the game
                ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, timeScale, longShotBonus, staticImage, quadtree = resetGame(
                    balls,  createPegColors, bucket, pegs, originPegs, quadtree)

                delayTimer = TimedEvent(0.50)

                isNewGameAnimationSequenceStart = True
        
        elif pauseSelection == "settings":
            isFullscreen = configs["FULLSCREEN"] # check state before settings menu opens
            settingsMenu(screen)
            # Clear any pending mouse button down events (to prevent triggering the setting button again)
            pygame.event.clear(pygame.MOUSEBUTTONDOWN)
            # Wait until the mouse button is released
            while pygame.mouse.get_pressed()[0]:
                pygame.event.pump()
            
            if configs["MUSIC_ENABLED"]:
                newSong()
                
            # if the fullscreen state has changed, update positions to handle fullscreen toggle
            if configs["FULLSCREEN"] != isFullscreen:
                # adjust the positions of every peg to be centered on the screen based on configs["WIDTH"] and configs["HEIGHT"]
                # get the position of the left most peg
                leftMostPeg = pegs[0]
                for peg in pegs:
                    if peg.pos.x < leftMostPeg.pos.x:
                        leftMostPeg = peg
                rightMostPeg = pegs[0]
                for peg in pegs:
                    if peg.pos.x > rightMostPeg.pos.x:
                        rightMostPeg = peg

                # find the center of the left most and right most pegs
                centerOfLeftAndRightPegs = (leftMostPeg.pos.x + rightMostPeg.pos.x)/2
                # find the center of the screen
                screenCenter = configs["WIDTH"]/2
                # find the difference between the center of the screen and the center of the left and right most pegs
                difference = screenCenter - centerOfLeftAndRightPegs

                # adjust the position of every peg by the difference
                for peg in pegs:
                    peg.pos.x += difference
                    
                # adjust the position of each ball by the difference
                for ball in balls:
                    ball.pos.x += difference
                    
                
                # Do same process again for the Y axis
                topMostPeg = pegs[0]
                for peg in pegs:
                    if peg.pos.y < topMostPeg.pos.y:
                        topMostPeg = peg
                bottomMostPeg = pegs[0]
                for peg in pegs:
                    if peg.pos.y > bottomMostPeg.pos.y:
                        bottomMostPeg = peg
                    
                # find the center of the top most and bottom most pegs
                centerOfTopAndBottomPegs = (topMostPeg.pos.y + bottomMostPeg.pos.y)/2
                # find the center of the screen
                screenCenter = configs["HEIGHT"]/2
                # find the difference between the center of the screen and the center of the top and bottom most pegs
                difference = screenCenter - centerOfTopAndBottomPegs
                
                # adjust the position of every peg by the difference
                for peg in pegs:
                    peg.pos.y += difference
                
                # adjust the position of each ball by the difference
                for ball in balls:
                    ball.pos.y += difference
                    
                # update ball position if none of the balls are alive
                if not any([ball.isAlive for ball in balls]):
                    ball.pos = Vector(configs["WIDTH"]/2, configs["HEIGHT"]/25)
                    ball.prevPos = ball.pos.copy()
                    
                    inputAim = Vector(configs["WIDTH"]/2, (configs["HEIGHT"]/25)+50)
                    
                # update the quadtree boundary
                boundary = Rectangle(configs["WIDTH"]/2, configs["HEIGHT"]/2, configs["WIDTH"]/2, configs["HEIGHT"]/2)
                
                # update the quadtree
                quadtree = QuadtreePegs(boundary, 4)
                queryRect = Rectangle(0, 0, 0, 0)
                nearbyPegs = []
                
                # update the bucket y position to be at the bottom of the screen
                bucket.pos = Vector(configs["WIDTH"]/2, configs["HEIGHT"] - bucket.bucketBackImg.get_height())  # position
                                
                # update the static image
                staticImage = createStaticImage(pegs)
                

    # show if gameOver
    if gameOver:
        pauseText = menuFont.render("Game Over", False, (255, 255, 255))
        screen.blit(pauseText, (configs["WIDTH"]/2 - pauseText.get_width()/2, configs["HEIGHT"]/4))
        if ballsRemaining >= 0 and orangeCount < 1:
            # add commas to the score (e.g. 1000000 -> 1,000,000)
            formattedScore = ""
            for i in range(len(str(score))):
                formattedScore += str(score)[i]
                if (len(str(score)) - i - 1) % 3 == 0 and i != len(str(score)) - 1:
                    formattedScore += ","

            scoreText = menuFont.render(formattedScore, False, (20, 60, 255))
            screen.blit(scoreText, (configs["WIDTH"]/2 - scoreText.get_width()/2, configs["HEIGHT"]/3 + 50))
        else:
            tryAgainText = menuFont.render("Try Again", False, (255, 60, 20))
            screen.blit(tryAgainText, (configs["WIDTH"]/2 - tryAgainText.get_width()/2, configs["HEIGHT"]/2.2))

    # show the long shot score text only for a few seconds
    longShotTextTimer.update()
    if longShotTextTimer.isTriggered:
        longShotBonus = False
        longShotTextTimer.cancelTimer()

    if longShotBonus and not longShotTextTimer.isActive:
        longShotTextTimer.setTimer(1.25)

    if longShotBonus and not longShotTextTimer.isTriggered:
        # show the long shot score
        longShotText = infoFont.render("25,000", False, (255, 110, 0))
        screen.blit(longShotText, (longShotPos.x-28, longShotPos.y+11))
        # show the long shot text
        longShotText = infoFont.render("Long Shot!", False, (255, 110, 0))
        screen.blit(longShotText, (longShotPos.x-35, longShotPos.y-20))
        
    # save the draw time
    drawTime = time.time() - startDrawTime

    # debugging stuff
    if configs["DEBUG_MODE"]:
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
        if len(balls) > 1:
            # draw number of balls in ball array
            ballCountText = debugFont.render(
                str(len(balls)) + " balls", False, (255, 255, 255))
            screen.blit(ballCountText, (265, 50))
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
            screen.blit(joystickText, (configs["WIDTH"]-300, 10))

        # draw bucket fake pegs
        for fakePeg in bucket.fakePegs.copy():
            drawCircle(fakePeg.pos.x, fakePeg.pos.y,
                       fakePeg.radius, (255, 0, 0))

        if speedHack:
            speedHackText = debugFont.render(
                "Speed Hack: ON", False, (255, 255, 255))
            screen.blit(speedHackText, (245, 5))

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
                    
        # draw the quadtree
        if quadtreeDebug:
            screen.blit(quadtreeStaticScreen, (0, 0))
            if useQuadtree:
                # draw red circle around each peg in the query
                for p in nearbyPegs:
                    drawCircle(p.pos.x, p.pos.y, p.radius, (255, 0, 0))
                
            # draw white rectangle around the query rect
            pygame.draw.rect(screen, (0, 255, 0), (queryRect.x-queryRectSize, queryRect.y-queryRectSize, queryRectSize*2, queryRectSize*2), 2)
            
            # draw the quadtree capacity
            capacityText = debugFont.render("Capacity: "+str(quadtree.capacity), False, (255, 255, 255))
            screen.blit(capacityText, (configs["WIDTH"]-200, 20))
            
        # draw text to show if the quadtree is being used
        if not useQuadtree:
            quadtreeText = debugFont.render("Quadtree: OFF", False, (255, 255, 255))
            screen.blit(quadtreeText, (configs["WIDTH"]-200, 5))
            
        # draw performance information
        if physicsTimeDebug:
            physicsTimeText = debugFont.render("Physics Time: "+str(round(physicsTime*1000, 2))+" ms", False, (255, 255, 255))
            screen.blit(physicsTimeText, (configs["WIDTH"]-200, 35))
            
            # draw the percent of the frame time that the physics calculations take up
            physicsPercent = 0
            if physicsTime > 0 and clock.get_time() > 0:
                physicsPercent = physicsTime / (clock.get_time() / 1000)
            
            physicsPercentText = debugFont.render("Physics Percent: "+str(round(physicsPercent*100, 2))+"%", False, (255, 255, 255))
            screen.blit(physicsPercentText, (configs["WIDTH"]-200, 50))
            
            drawTimeText = debugFont.render("Draw Time: "+str(round(drawTime*1000, 2))+" ms", False, (255, 255, 255))
            screen.blit(drawTimeText, (configs["WIDTH"]-200, 65))
            
            totalTimeText = debugFont.render("Total Time: "+str(round(totalTime*1000, 2))+" ms", False, (255, 255, 255))
            screen.blit(totalTimeText, (configs["WIDTH"]-200, 80))
            
            # draw the fps
            fpsText = debugFont.render("FPS: "+str(round(clock.get_fps(), 2)), False, (255, 255, 255))
            screen.blit(fpsText, (configs["WIDTH"]-200, 95)) 
            
            # draw the dt (delta time)
            dtText = debugFont.render("Time Step (dt): "+str(round(dt, 2))+" s", False, (255, 255, 255))
            screen.blit(dtText, (configs["WIDTH"]-200, 125))
            
        # draw ball previous position and draw line to the current position
        if debugBallPrevPos:
            for b in balls:
                if b.isAlive:
                    # draw the current position
                    drawCircle(b.pos.x, b.pos.y, 5, (0, 255, 0))
                    # draw a line from the previous position to the current position
                    pygame.draw.line(screen, (255, 0, 0), (b.prevPos.x, b.prevPos.y), (b.pos.x, b.pos.y), 2)
                    # draw a line from the previous velocity to the current position
                    pygame.draw.line(screen, (255, 0, 255), (b.prevPos.x, b.prevPos.y), (b.prevPos.x + b.prevVel.x*10, b.prevPos.y + b.prevVel.y*10), 2)
                    # draw a line from the current velocity to the next position
                    pygame.draw.line(screen, (0, 255, 255), (b.pos.x, b.pos.y), (b.pos.x + b.vel.x*10, b.pos.y + b.vel.y*10), 2)
        
    # display red text indicating if cheats are enabled
    if cheats:
        cheatsIcon = debugFont.render("CHEATS ENABLED", False, (255, 0, 0))
        screen.blit(cheatsIcon, (100, 6))

    pygame.display.update()
    
    totalTime = time.time() - startTotalTime

print("Goodbye")
