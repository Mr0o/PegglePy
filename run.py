import time
from math import cos, sin
from collections.abc import Callable

##### local imports #####
from local.userConfig import configs, defaultConfigs, saveSettings
from local.trajectory import (
    BestTrajectorySearch,
    getLaunchAngles,
    TrajectoryCalculation,
)
from local.audio import playSoundPitch, loadRandMusic, playMusic, stopMusic, autoPauseMusic, newSong, setMusicVolume
from local.resources import gameIconImg
from local.resources import launch_sound, sighSound, longShotSound, low_hit_sound, normal_hit_sound, failSound, drumRoll, pegPopSound
from local.resources import cymbal, freeBallSound, powerUpSpooky1, powerUpSpooky2, powerUpSpooky3, powerUpSpooky4
from local.resources import powerUpMultiBall, powerUpGuideBall, powerUpZenBall, powerUpZenBallHit, powerUpNoGravity
from local.misc import createStaticImage, updateStaticImagePegs
from local.misc import distBetweenTwoPoints

from local.triggerEvents import TimedEvent
from local.animate import (
    MAX_ANIMATED_PEGS,
    getPegAnimationFrame,
    shouldAnimatePegs,
)
from local.vectors import Vector, subVectors
from local.collision import (
    isBallTouchingPeg,
    resolveCollision,
    resolveCollisionAndGetPeg,
    updateSweptCollisionBounds,
)
from local.quadtree import QuadtreePegs, Rectangle
from local.events import (
    EventType, clearEventList, consumeEvent, eventOccured, postEvent, subscribe,
)
from local.game import Game
from local.performance import PerformanceMetrics
from local.rendering import GameRenderer

from local.ball import Ball
from local.peg import Peg, createPegColors, getScoreMultiplier


from local.menu_controller import MenuController
from loadLevelMenu import (
    LEVEL_DATA_PROGRESS_END,
    LoadingScreenProgress,
)

STATIC_IMAGE_PROGRESS_END = 0.8
IMMEDIATE_LOADING_SCREEN_PEG_THRESHOLD = MAX_ANIMATED_PEGS
levelDataProgressPending = False

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
performance = PerformanceMetrics()
renderer = GameRenderer(screen)
menus = MenuController()
animationFrameScreen = pygame.Surface(
    (configs["WIDTH"], configs["HEIGHT"]), pygame.SRCALPHA
)
completedAnimationFrameScreen = pygame.Surface(
    (configs["WIDTH"], configs["HEIGHT"]), pygame.SRCALPHA
)
renderer.prepare_spawn_frame(completedAnimationFrameScreen)

pygame.display.set_caption("PegglePy")

# set the icon
pygame.display.set_icon(gameIconImg)


gameVars: Game = Game()
loadingLevelName = "level"
loadingScreenProgress = LoadingScreenProgress(screen)


def renderLoadingProgress(progress: float, status: str) -> None:
    loadingScreenProgress.set_level(loadingLevelName)
    loadingScreenProgress(progress, status)


# Keep the remaining legacy names backed by their corresponding game state.
ball = gameVars.ball
bucket = gameVars.bucket
inputAim = gameVars.inputAim
debugTrajectory = gameVars.debugTrajectory
firstSpookyHit = gameVars.firstSpookyHit
longShotTextTimer = gameVars.longShotTextTimer
noGravityPowerUpTimer = gameVars.noGravityPowerUpTimer
quadtreeStaticScreen = gameVars.quadtreeStaticScreen


def createStaticImageMeasured(
    pegs: list[Peg],
    progress_callback: Callable[[float, str], None] | None = None,
) -> pygame.Surface:
    with performance.measure("static_image_build"):
        return createStaticImage(pegs, progress_callback=progress_callback)


def updateStaticImageMeasured(
    image: pygame.Surface,
    pegs: list[Peg],
    changed_pegs: list[Peg],
    removed_pegs: list[Peg] = (),
) -> pygame.Surface:
    with performance.measure("static_image_update"):
        return updateStaticImagePegs(
            image,
            pegs,
            changed_pegs,
            removed_pegs,
        )


def renderPegAnimationFrame(
    pegs: list[Peg],
    dt: float,
    target: pygame.Surface,
    completed_target: pygame.Surface | None = None,
) -> pygame.Surface:
    with performance.measure("animation_generation"):
        return getPegAnimationFrame(pegs, dt, target, completed_target)

### main menu ###
selection, editorSelection = menus.start(screen, clock, gameVars)

# prevent accidental click on launch
delayTimer = TimedEvent(0.2)

if selection != "quit":
    if editorSelection != "play":
        (
            gameVars.pegs,
            gameVars.originPegs,
            gameVars.orangeCount,
            levelFileName,
        ) = menus.select_level(screen)

        delayTimer = TimedEvent(0.2)
    else:
        levelFileName = "Unsaved Editor Level"
        
    # set the caption to include the level name
    loadingLevelName = levelFileName
    pygame.display.set_caption("PegglePy   -   " + levelFileName)

    loadingScreenProgress.begin(loadingLevelName)
    if len(gameVars.pegs) >= IMMEDIATE_LOADING_SCREEN_PEG_THRESHOLD:
        loadingScreenProgress.show_immediately(
            LEVEL_DATA_PROGRESS_END,
            "Rendering level...",
        )
    else:
        renderLoadingProgress(
            LEVEL_DATA_PROGRESS_END,
            "Rendering level...",
        )
    staticImage = createStaticImageMeasured(
        gameVars.pegs,
        progress_callback=lambda progress, status: renderLoadingProgress(
            LEVEL_DATA_PROGRESS_END
            + progress
            * (STATIC_IMAGE_PROGRESS_END - LEVEL_DATA_PROGRESS_END),
            status,
        ),
    )
    gameVars.staticImage = staticImage

    loadRandMusic()
    setMusicVolume(configs["MUSIC_VOLUME"])
    if configs["MUSIC_ENABLED"]:
        playMusic()
    else:
        stopMusic()

else:
    gameVars.gameRunning = False
    
# Set up the quadtree
boundary = Rectangle(configs["WIDTH"]/2, configs["HEIGHT"]/2, configs["WIDTH"]/2, configs["HEIGHT"]/2)
quadtree = QuadtreePegs(boundary, 4)
gameVars.boundary = boundary
gameVars.quadtree = quadtree
queryRect = Rectangle(0, 0, 0, 0)
nearbyPegs = []
joystick = None


def resetRound() -> None:
    global ball, staticImage, quadtree, zenballSearch
    global trajectory, trajectoryCalculation
    global loadingLevelName
    global levelDataProgressPending
    loadingLevelName = levelFileName
    resetStart = time.perf_counter_ns()
    zenballSearch = None
    trajectoryCalculation = None
    trajectory = []
    if levelDataProgressPending:
        loadingScreenProgress.begin(loadingLevelName)
        if len(gameVars.originPegs) >= IMMEDIATE_LOADING_SCREEN_PEG_THRESHOLD:
            loadingScreenProgress.show_immediately(
                LEVEL_DATA_PROGRESS_END,
                "Preparing peg data",
            )
        else:
            renderLoadingProgress(
                LEVEL_DATA_PROGRESS_END,
                "Preparing peg data",
            )
        progress_callback = lambda progress, status: renderLoadingProgress(
            LEVEL_DATA_PROGRESS_END
            + (1.0 - LEVEL_DATA_PROGRESS_END) * progress,
            status,
        )
    else:
        loadingScreenProgress.begin(loadingLevelName)
        if len(gameVars.originPegs) >= IMMEDIATE_LOADING_SCREEN_PEG_THRESHOLD:
            loadingScreenProgress.show_immediately(
                0.0,
                "Preparing peg data",
            )
        progress_callback = renderLoadingProgress
    staticImage, quadtree = gameVars.resetRound(
        gameVars.originPegs,
        createPegColors,
        createStaticImageMeasured,
        newSong,
        progress_callback=progress_callback,
    )
    levelDataProgressPending = False
    performance.record_ms(
        "peg_state_reset",
        gameVars.pegStateResetTime * 1000,
    )
    performance.record_ms(
        "quadtree_build",
        gameVars.quadtreeBuildTime * 1000,
    )
    performance.record_since("round_reset_total", resetStart)
    ball = gameVars.ball


isNewGameAnimationSequenceActive = True
isRemovePegsAnimationSequenceActive = False
hitPegs: list[Peg] = []
animationStartTime = 0.0
largeLevelSpawnElapsed = 0.0
largeLevelSpawnReveal: float | None = None
zenballSearch: BestTrajectorySearch | None = None
zenballSearchStartTime = 0.0


def startNewGameAnimationSequence() -> None:
    global isNewGameAnimationSequenceActive
    global largeLevelSpawnElapsed, largeLevelSpawnReveal
    if not shouldAnimatePegs(len(gameVars.pegs)):
        isNewGameAnimationSequenceActive = True
        largeLevelSpawnElapsed = 0.0
        largeLevelSpawnReveal = 0.0
        completedAnimationFrameScreen.fill((0, 0, 0, 0))
        animationFrameScreen.fill((0, 0, 0, 0))
        renderer.prepare_spawn_frame(completedAnimationFrameScreen)
        return

    isNewGameAnimationSequenceActive = True
    largeLevelSpawnReveal = None
    animationScheduleStart = time.perf_counter_ns()
    renderer.prepare_spawn_frame(completedAnimationFrameScreen)

    for i, peg in enumerate(gameVars.pegs):
        animationTime = 50
        peg.animation.startFadeIn(((animationTime / len(gameVars.pegs)) * i) + 10)
    performance.record_since("animation_schedule", animationScheduleStart)


def completeNewGameAnimationSequence() -> None:
    global isNewGameAnimationSequenceActive
    global largeLevelSpawnReveal
    isNewGameAnimationSequenceActive = False
    largeLevelSpawnReveal = None


def startPegRemovalAnimationSequence() -> None:
    global animationStartTime, isRemovePegsAnimationSequenceActive
    isRemovePegsAnimationSequenceActive = True

    animationScheduleStart = time.perf_counter_ns()
    for i, peg in enumerate(hitPegs):
        peg.animation.startFadeOut(20 + peg.animation.duration * 0.18 * i)
    performance.record_since("animation_schedule", animationScheduleStart)

    animationStartTime = time.time()


def completePegRemovalAnimationSequence() -> None:
    global isRemovePegsAnimationSequenceActive
    isRemovePegsAnimationSequenceActive = False


subscribe(EventType.GAME_NEW_GAME_ANIMATION_STARTED, startNewGameAnimationSequence)
subscribe(EventType.GAME_NEW_GAME_ANIMATION_COMPLETED, completeNewGameAnimationSequence)
subscribe(EventType.GAME_PEG_REMOVAL_ANIMATION_STARTED, startPegRemovalAnimationSequence)
subscribe(EventType.GAME_PEG_REMOVAL_ANIMATION_COMPLETED, completePegRemovalAnimationSequence)
trajectory = []
trajectoryCalculation = None
if gameVars.gameRunning:
    postEvent(EventType.GAME_NEW_GAME_ANIMATION_STARTED)

##### main loop #####
while gameVars.gameRunning:

    clearEventList()
    startTotalTime = time.time()
    zenballSearchCompletedThisFrame = False
    staticImageRemovedPegs: list[Peg] = []
    staticImageChangedPegs: list[Peg] = []
    
    # minimum refresh rate is 120 (for now, this temporary fix allows the physics to update more frequently, improving accuracy)
    if configs["REFRESH_RATE"] <= 120 and configs["VSYNC"]:
        clock.tick(120)
    else:
        clock.tick(configs["REFRESH_RATE"])
    gameVars.setFrameTime(clock.get_time() / 5)
    gameVars.dt = gameVars.fixedPhysicsStep
    frameStart = time.perf_counter_ns()
    performance.begin_frame()
    
    
    if quadtree.pegs == [] and gameVars.pegs != []:
        quadtreeBuildStart = time.perf_counter_ns()
        quadtree.insert_many(
            gameVars.pegs,
            progress_callback=lambda progress, status: renderLoadingProgress(
                STATIC_IMAGE_PROGRESS_END
                + progress * (1.0 - STATIC_IMAGE_PROGRESS_END),
                status,
            ),
        )
        performance.record_since("quadtree_build", quadtreeBuildStart)
    
    gamePadFineTuneAmount = 0
    inputStart = time.perf_counter_ns()
    for event in pygame.event.get():  # check events and quit if the program is closed
        if renderer.handle_debug_panel_event(
            event,
            performance_enabled=gameVars.physicsTimeDebug,
            developer_enabled=(
                configs["DEBUG_MODE"] or gameVars.physicsTimeDebug or gameVars.cheats
            ),
        ):
            continue
        if event.type == pygame.QUIT:
            gameVars.gameRunning = False
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                postEvent(EventType.INPUT_KEY_PRESS_SPACE)
                resetRound()
                if not configs["MUSIC_ENABLED"]:
                    stopMusic()
                delayTimer = TimedEvent(0.50)
                postEvent(EventType.GAME_NEW_GAME_ANIMATION_STARTED)
            if event.key == pygame.K_1:  # enable or disable configs["DEBUG_MODE"] features
                postEvent(EventType.INPUT_KEY_PRESS_1)
                configs["DEBUG_MODE"] = not configs["DEBUG_MODE"]
            if event.key == pygame.K_2:  # enable or disable gameVars.cheats
                postEvent(EventType.INPUT_KEY_PRESS_2)
                gameVars.cheats = not gameVars.cheats
            if event.key == pygame.K_3:  # cycle through all power up types
                postEvent(EventType.INPUT_KEY_PRESS_3)
                gameVars.changePowerUp()
            if event.key == pygame.K_4:  # toggle quadtreeDebug
                postEvent(EventType.INPUT_KEY_PRESS_4)
                gameVars.quadtreeDebug = not gameVars.quadtreeDebug
                if gameVars.quadtreeDebug:
                    gameVars.quadtreeStaticScreen.fill((0, 0, 0, 0))
                    quadtree.show(gameVars.quadtreeStaticScreen)
            if event.key == pygame.K_5:  # toggle quadtree vs brute force collision detection
                postEvent(EventType.INPUT_KEY_PRESS_5)
                gameVars.useQuadtree = not gameVars.useQuadtree
            if event.key == pygame.K_6:  # toggle physics time debug
                postEvent(EventType.INPUT_KEY_PRESS_6)
                gameVars.physicsTimeDebug = not gameVars.physicsTimeDebug
            if event.key == pygame.K_7:  # configs["DEBUG_MODE"] - enable or disable full trajectory drawing
                postEvent(EventType.INPUT_KEY_PRESS_7)
                debugTrajectory = not debugTrajectory
            if event.key == pygame.K_l:  # load a new level
                postEvent(EventType.INPUT_KEY_PRESS_L)
                stopMusic()
                (
                    gameVars.pegs,
                    gameVars.originPegs,
                    gameVars.orangeCount,
                    levelFileName,
                ) = menus.select_level(screen)
                levelDataProgressPending = True
                pygame.display.set_caption("PegglePy   -   " + levelFileName)
                resetRound()
                if not configs["MUSIC_ENABLED"]:
                    stopMusic()
                delayTimer = TimedEvent(0.50)
                postEvent(EventType.GAME_NEW_GAME_ANIMATION_STARTED)
            if event.key == pygame.K_ESCAPE:  # enable or disable gameVars.cheats
                postEvent(EventType.INPUT_KEY_PRESS_ESCAPE)
                gameVars.gamePaused = not gameVars.gamePaused
            if event.key == pygame.K_0:
                postEvent(EventType.INPUT_KEY_PRESS_0)
                gameVars.timeScale = (
                    gameVars.baseTimeScale
                    if gameVars.timeScale != gameVars.baseTimeScale
                    else gameVars.closeCallTimeScale
                )
            if event.key == pygame.K_m:
                postEvent(EventType.INPUT_KEY_PRESS_M)
                configs["SOUND_ENABLED"] = not configs["SOUND_ENABLED"]
            if event.key == pygame.K_n:
                postEvent(EventType.INPUT_KEY_PRESS_N)
                configs["MUSIC_ENABLED"] = not configs["MUSIC_ENABLED"]
                autoPauseMusic()
            if event.key == pygame.K_8:
                postEvent(EventType.INPUT_KEY_PRESS_8)
                gameVars.speedHack = not gameVars.speedHack
            if event.key == pygame.K_9:
                postEvent(EventType.INPUT_KEY_PRESS_9)
                gameVars.debugAutoRemovePegsTimer = not gameVars.debugAutoRemovePegsTimer
            if event.key == pygame.K_x:  # toggle zoom
                postEvent(EventType.INPUT_KEY_PRESS_X)
                gameVars.zoomInOnBall = not gameVars.zoomInOnBall
            if event.key == pygame.K_t:  # triple the time scale
                postEvent(EventType.INPUT_KEY_PRESS_T)
                gameVars.timeScale = (
                    gameVars.baseTimeScale * 3
                    if gameVars.timeScale == gameVars.baseTimeScale
                    else gameVars.baseTimeScale
                )
            if event.key == pygame.K_p:  # toggle debugBallPrevPos
                postEvent(EventType.INPUT_KEY_PRESS_P)
                gameVars.debugBallPrevPos = not gameVars.debugBallPrevPos
            if event.key == pygame.K_v:  # toggle VSYNC
                postEvent(EventType.INPUT_KEY_PRESS_V)
                if configs["REFRESH_RATE"] == 0:
                    configs["VSYNC"] = True
                    configs["REFRESH_RATE"] = pygame.display.get_current_refresh_rate()
                else:
                    configs["VSYNC"] = False
                    configs["REFRESH_RATE"] = 0
                saveSettings()
            if event.key == pygame.K_f:  # toggle FULLSCREEN
                postEvent(EventType.INPUT_KEY_PRESS_F)
                configs["FULLSCREEN"] = not configs["FULLSCREEN"]
                if configs["FULLSCREEN"]:
                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    configs["WIDTH"] = defaultConfigs["WIDTH"]
                    configs["HEIGHT"] = defaultConfigs["HEIGHT"]
                    screen = pygame.display.set_mode((configs["WIDTH"], configs["HEIGHT"]))
                saveSettings()
            if event.key == pygame.K_z:  # open the main menu
                postEvent(EventType.INPUT_KEY_PRESS_Z)
                selection, editor_played = menus.navigate_main_menu(
                    screen, clock, gameVars
                )

                if selection == "quit":
                    gameVars.gameRunning = False
                elif selection == "start" and not editor_played:
                    levelFileName = menus.load_selected_level(
                        screen, gameVars
                    )
                    levelDataProgressPending = True
                if editor_played:
                    levelFileName = "Unsaved Editor Level"

                # reset the game
                resetRound()

                # prevent accidental click on launch
                delayTimer = TimedEvent(0.50)
                
                postEvent(EventType.GAME_NEW_GAME_ANIMATION_STARTED)

                if not configs["MUSIC_ENABLED"]:
                    # change the song
                    newSong()

                # set the caption to include the level name
                pygame.display.set_caption(
                    "PegglePy   -   " + levelFileName)

        if event.type == pygame.MOUSEWHEEL:
            gameVars.fineTuneAmount -= event.y / 12
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            postEvent(EventType.INPUT_LAUNCH_REQUESTED)

        if event.type == pygame.MOUSEMOTION and gameVars.controllerInput:
            gameVars.controllerInput = False
            pygame.mouse.set_visible(True)

        # check for gamepad dpad buttons
        if event.type == pygame.JOYHATMOTION:
            if event.value == (0, 1):
                postEvent(EventType.INPUT_DPAD_UP)
                gamePadFineTuneAmount += 0.11
            if event.value == (0, -1):
                postEvent(EventType.INPUT_DPAD_DOWN)
                gamePadFineTuneAmount -= 0.11
            if event.value == (1, 0):
                postEvent(EventType.INPUT_DPAD_RIGHT)
                gamePadFineTuneAmount += 0.11
            if event.value == (-1, 0):
                postEvent(EventType.INPUT_DPAD_LEFT)
                gamePadFineTuneAmount -= 0.11

        if event.type == pygame.JOYAXISMOTION and not gameVars.controllerInput:
            if event.axis == 0 or event.axis == 1:
                postEvent(EventType.INPUT_JOYSTICK_AXIS_MOTION)
                if abs(event.value) > 0.15:
                    gameVars.controllerInput = True
                    pygame.mouse.set_visible(False)
        if event.type == pygame.JOYBUTTONDOWN:
            joystick = pygame.joystick.Joystick(0)
            # if the controller is a 'sony' or 'playstation' controller (Sometimes "Wireless Controller" is the name of the ps4 controller, so we will include that as well)
            if joystick.get_name().lower().find("sony") != -1 or joystick.get_name().lower().find("playstation") != -1 or joystick.get_name().lower().find("wireless") != -1:
                if event.button == 0:  # the 'X'/cross button on a ps4 controller
                    postEvent(EventType.INPUT_BUTTON_PRESS_A)
                    postEvent(EventType.INPUT_LAUNCH_REQUESTED)
                if event.button == 3:  # the '[]'/square button on a ps4 controller
                    postEvent(EventType.INPUT_BUTTON_PRESS_X)
                    postEvent(EventType.INPUT_LAUNCH_REQUESTED)
                if event.button == 1:  # the 'O'/circle button on a ps4 controller
                    postEvent(EventType.INPUT_BUTTON_PRESS_B)
                    gameVars.changePowerUp()
                if event.button == 2:  # the '△'/triangle button on a ps4 controller
                    postEvent(EventType.INPUT_BUTTON_PRESS_Y)
                    resetRound()
                    postEvent(EventType.GAME_NEW_GAME_ANIMATION_STARTED)
                if event.button == 4:  # the 'L1' button on a ps4 controller
                    postEvent(EventType.INPUT_BUTTON_PRESS_LB)
                    joystick.rumble(1, 1, 100)
                if event.button == 5:  # the 'R1' button on a ps4 controller
                    postEvent(EventType.INPUT_BUTTON_PRESS_RB)
                    gameVars.cheats = not gameVars.cheats
                if event.button == 8:  # the 'share' button on a ps4 controller
                    postEvent(EventType.INPUT_BUTTON_PRESS_SELECT)
                    configs["DEBUG_MODE"] = not configs["DEBUG_MODE"]
                if event.button == 9:  # the 'options' button on a ps4 controller
                    postEvent(EventType.INPUT_BUTTON_PRESS_START)
                    gameVars.gamePaused = not gameVars.gamePaused
                if event.button == 11: # the 'L3' joystick button on a ps4 controller
                    postEvent(EventType.INPUT_BUTTON_PRESS_LS)
                if event.button == 12: # the 'R3' joystick button on a ps4 controller
                    postEvent(EventType.INPUT_BUTTON_PRESS_RS)
                if event.button in (11, 12):
                    if configs["MUSIC_ENABLED"]:
                        autoPauseMusic()
                    else:
                        stopMusic()
                    configs["SOUND_ENABLED"] = not configs["SOUND_ENABLED"]

            else:  # xbox controller (default)
                if event.button == 0:  # the 'A' button on an xbox controller
                    postEvent(EventType.INPUT_BUTTON_PRESS_A)
                    postEvent(EventType.INPUT_LAUNCH_REQUESTED)
                if event.button == 2:  # the 'X' button on an xbox controller
                    postEvent(EventType.INPUT_BUTTON_PRESS_X)
                    postEvent(EventType.INPUT_LAUNCH_REQUESTED)
                if event.button == 1:  # the 'B' button on an xbox controller
                    postEvent(EventType.INPUT_BUTTON_PRESS_B)
                    gameVars.changePowerUp()
                if event.button == 3:  # the 'Y' button on an xbox controller
                    postEvent(EventType.INPUT_BUTTON_PRESS_Y)
                    resetRound()
                    postEvent(EventType.GAME_NEW_GAME_ANIMATION_STARTED)
                if event.button == 6:  # the 'start' button on an xbox controller
                    postEvent(EventType.INPUT_BUTTON_PRESS_START)
                    configs["DEBUG_MODE"] = not configs["DEBUG_MODE"]
                if event.button == 7:  # the 'back' button on an xbox controller
                    postEvent(EventType.INPUT_BUTTON_PRESS_SELECT)
                    gameVars.gamePaused = not gameVars.gamePaused
                if event.button == 9:  # the 'left joystick' button on an xbox controller
                    postEvent(EventType.INPUT_BUTTON_PRESS_LS)
                if event.button == 10:  # the 'right joystick' button on an xbox controller
                    postEvent(EventType.INPUT_BUTTON_PRESS_RS)
                if event.button in (9, 10):
                    if configs["MUSIC_ENABLED"]:
                        autoPauseMusic()
                    else:
                        stopMusic()
                    configs["SOUND_ENABLED"] = not configs["SOUND_ENABLED"]
                if event.button == 4:  # the 'left bumper' button on an xbox controller
                    postEvent(EventType.INPUT_BUTTON_PRESS_LB)
                    joystick.rumble(1, 1, 100)
                if event.button == 5:  # the 'right bumper' button on an xbox controller
                    postEvent(EventType.INPUT_BUTTON_PRESS_RB)
                    gameVars.cheats = not gameVars.cheats

    performance.record_since("input_events", inputStart)
    aimInputStart = time.perf_counter_ns()
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
        gameVars.controllerInput = False
        pygame.mouse.set_visible(True)

    if gameVars.controllerInput and not gameVars.ball.isAlive:  # controller joystick
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

        posX = inputAim.x + gameVars.ball.pos.x
        posY = inputAim.y + gameVars.ball.pos.y
    elif not gameVars.controllerInput:  # mouse
        # 1) Compute analytic launch angles
        targetPos = Vector(mx, my)
        angles = getLaunchAngles(gameVars.ball.pos, targetPos)

        if angles:
            θ = angles[0] # pick the low‐arc solution
            # screen‐space dir: +x right, +y down
            dir = Vector(cos(θ), -sin(θ))
            # build an "aim point" one unit away from the ball
            launchAim = gameVars.ball.pos.copy()
            launchAim.add(dir)
        else:
            # fallback: aim directly at the cursor
            launchAim = targetPos.copy()

        # 2) apply fine‐tune rotation (mouse wheel / backtick tweaks)
        rel = subVectors(launchAim, gameVars.ball.pos)
        rel.setAngleDeg(rel.getAngleDeg() + gameVars.fineTuneAmount)
        launchAim = gameVars.ball.pos.copy()
        launchAim.add(rel)

        # 3) write back into posX/posY so the rest of the code picks it up
        posX, posY = launchAim.x, launchAim.y

    performance.record_since("aim_input", aimInputStart)
    # reset the game when the game is over and the mouse is clicked
    if eventOccured(EventType.INPUT_LAUNCH_REQUESTED) and gameVars.gameOver:
        # prevent the click from instantly launching a ball
        delayTimer = TimedEvent(0.50)
        resetRound()
        gameVars.shouldClear = False
        if not configs["MUSIC_ENABLED"]:
            stopMusic()
    
        postEvent(EventType.GAME_NEW_GAME_ANIMATION_STARTED)

    animationUpdateStart = time.perf_counter_ns()
    if isNewGameAnimationSequenceActive:
        tempDt = gameVars.frameDt
        if not delayTimer.isTriggered or gameVars.gamePaused:
            tempDt = 0

        if largeLevelSpawnReveal is not None:
            largeLevelSpawnElapsed = min(
                50.0,
                largeLevelSpawnElapsed + tempDt,
            )
            largeLevelSpawnReveal = largeLevelSpawnElapsed / 50.0
            if largeLevelSpawnElapsed >= 50.0:
                postEvent(EventType.GAME_NEW_GAME_ANIMATION_COMPLETED)
        else:
            animationFrameScreen = renderPegAnimationFrame(
                gameVars.pegs,
                tempDt,
                animationFrameScreen,
                completedAnimationFrameScreen,
            )

            if all(peg.animation.done for peg in gameVars.pegs):
                postEvent(EventType.GAME_NEW_GAME_ANIMATION_COMPLETED)
            
    if isRemovePegsAnimationSequenceActive:
        if not shouldAnimatePegs(len(hitPegs)):
            staticImageRemovedPegs.extend(hitPegs)
            animationFrameScreen.fill((0, 0, 0, 0))
            postEvent(EventType.GAME_PEG_REMOVAL_ANIMATION_COMPLETED)
        else:
            tempDt = gameVars.frameDt
            if not delayTimer.isTriggered or gameVars.gamePaused:
                tempDt = 0
            
            # play sound when a peg has started its animation (startTrigger)
            for peg in hitPegs:
                if peg.animation.startTrigger and peg.animation.fadeOut:
                    staticImageRemovedPegs.append(peg)
                    if configs["SOUND_ENABLED"] and configs["SOUND_VOLUME"] > 0:
                        playSoundPitch(pegPopSound, volume=configs["SOUND_VOLUME"] + 0.05)
        
            # track elapsed animation time and increase the speed if its taking longer
            elapsedTime = time.time() - animationStartTime
            if elapsedTime > 10 and elapsedTime < 20:
                animationFrameScreen = renderPegAnimationFrame(
                    hitPegs, tempDt * 2, animationFrameScreen
                )
            elif elapsedTime > 20 and elapsedTime < 25:
                animationFrameScreen = renderPegAnimationFrame(
                    hitPegs, tempDt * 5, animationFrameScreen
                )
            elif elapsedTime > 25:
                animationFrameScreen = renderPegAnimationFrame(
                    hitPegs, tempDt * 15, animationFrameScreen
                )
            else:
                animationFrameScreen = renderPegAnimationFrame(
                    hitPegs, tempDt, animationFrameScreen
                )

            if all(peg.animation.done for peg in hitPegs):
                staticImageRemovedPegs.extend(hitPegs)
                postEvent(EventType.GAME_PEG_REMOVAL_ANIMATION_COMPLETED)
    performance.record_since("animation_update", animationUpdateStart)

    # do not update any game physics or game logic if the game is paused or over
    if not gameVars.gamePaused and not gameVars.gameOver:
        gameplayUpdateStart = time.perf_counter_ns()
        # use the mouse position as a vector to calculate the path that is being aimed
        # check if the mouse is being moved to determine whether or not to use the fine tune amount
        if mx_rel != 0 and my_rel != 0:
            gameVars.fineTuneAmount = 0

        # calculate trajectory
        aimPredictionStart = time.perf_counter_ns()
        if not gameVars.ball.isAlive:
            if gameVars.powerUpActive and gameVars.powerUpType == "guideball":
                gameVars.trajectoryDepth = 750  # powerup
            else:
                gameVars.trajectoryDepth = 75  # normal
                if debugTrajectory:
                    gameVars.trajectoryDepth = 2500
            # only calculate the trajectory if the mouse has been moved - reduces cpu time
            if gameVars.previousAim.x != launchAim.x or gameVars.previousAim.y != launchAim.y:
                trajectoryCalculation = TrajectoryCalculation(
                    launchAim,
                    gameVars.ball.pos,
                    gameVars.pegs.copy(),
                    gameVars.bucket.fakePegs.copy(),
                    quadtree,
                    gameVars.dt,
                    gameVars.powerUpType == "guideball" and gameVars.powerUpActive,
                    gameVars.trajectoryDepth,
                    debugTrajectory,
                    zeroGravity=(
                        gameVars.powerUpActive
                        and gameVars.powerUpType == "no-gravity"
                    ),
                    wrapAtBottom=(
                        gameVars.powerUpActive
                        and gameVars.powerUpType
                        in ("spooky", "spooky-multiball")
                    ),
                    bucket=gameVars.bucket,
                    useQuadtree=gameVars.useQuadtree,
                )
                trajectory = trajectoryCalculation.points
            if trajectoryCalculation is not None:
                if trajectoryCalculation.advance(0.002):
                    if trajectoryCalculation.result is None:
                        raise RuntimeError(
                            "Completed trajectory calculation has no result"
                        )
                    trajectory = trajectoryCalculation.result
                    trajectoryCalculation = None
                else:
                    trajectory = trajectoryCalculation.points
        else:
            trajectoryCalculation = None
        gameVars.previousAim = Vector(launchAim.x, launchAim.y)
        performance.record_since("aim_prediction", aimPredictionStart)

        delayTimer.update()  # prevent the ball from launching instantly after the game is reset
        # if mouse clicked then trigger ball launch
        if eventOccured(EventType.INPUT_LAUNCH_REQUESTED) and not gameVars.ball.isAlive and delayTimer.isTriggered and len(gameVars.balls) < 2 and not isNewGameAnimationSequenceActive and not isRemovePegsAnimationSequenceActive:
            if gameVars.powerUpActive and gameVars.powerUpType == "guideball":
                gameVars.powerUpCount -= 1
                if gameVars.powerUpCount < 1:
                    gameVars.powerUpActive = False
            gameVars.ball.isLaunch = True
            gameVars.ball.isAlive = True

        # launch ball
        if gameVars.ball.isLaunch and gameVars.ball.isAlive:
            if not gameVars.powerUpType == "zenball":  # if powerup type is anything but zenball, launch normal
                gameVars.launchBall(launchAim)
                if configs["SOUND_ENABLED"]:
                    playSoundPitch(launch_sound)
            # if powerup type is zenball and it is not active then normal launch
            elif not gameVars.powerUpActive and gameVars.powerUpType == "zenball":
                gameVars.launchBall(launchAim)
                if configs["SOUND_ENABLED"]:
                    playSoundPitch(launch_sound)
                gameVars.drawTrajectory = False

        # gameVars.cheats (force enable power up)
        if gameVars.cheats:
            gameVars.powerUpActive = True

        # if active zenball powerup - launch
        zenballStart = time.perf_counter_ns()
        if gameVars.ball.isLaunch and gameVars.ball.isAlive and gameVars.powerUpType == "zenball" and gameVars.powerUpActive:
            if zenballSearch is None:
                if configs["SOUND_ENABLED"]:
                    playSoundPitch(powerUpZenBall, 0.93)
                if configs["DEBUG_MODE"]:
                    print("Debug: Zenball launched")
                zenballSearchStartTime = time.perf_counter()
                zenballSearch = BestTrajectorySearch(
                    Vector(launchAim.x, launchAim.y),
                    gameVars.ball.pos.copy(),
                    gameVars.pegs.copy(),
                    quadtree,
                    gameVars.dt,
                    bucket=gameVars.bucket,
                )

            if zenballSearch.advance(0.008):
                search_result = zenballSearch.result
                if search_result is None:
                    raise RuntimeError("Completed Zenball search has no result")
                bestAim, bestScore, gameVars.bestTrajectory = search_result
                reachedBucket = zenballSearch.reached_bucket
                zenballSearchCompletedThisFrame = True
                zenballSearch = None

                if configs["DEBUG_MODE"]:
                    print(
                        "Debug: Zenball best aim found in "
                        f"{time.perf_counter() - zenballSearchStartTime} seconds"
                    )

                for p in gameVars.pegs:
                    p.isHit = False

                if bestScore >= 10 or reachedBucket:
                    if configs["SOUND_ENABLED"]:
                        playSoundPitch(powerUpZenBall, 0.99)
                    gameVars.ball.applyForce(bestAim)
                else:
                    if configs["SOUND_ENABLED"]:
                        playSoundPitch(failSound)
                    gameVars.ball.applyForce(
                        subVectors(launchAim, gameVars.ball.pos)
                    )

                if configs["SOUND_ENABLED"]:
                    playSoundPitch(launch_sound)
                gameVars.ball.isLaunch = False
                gameVars.shouldClear = True
                gameVars.powerUpCount -= 1
                if gameVars.powerUpCount < 1:
                    gameVars.powerUpActive = False or gameVars.cheats
        elif zenballSearch is not None:
            zenballSearch = None
        performance.record_since("zenball_search", zenballStart)

        # gameVars.cheats, place ball anywhere on screen with right click
        if gameVars.cheats and mouseClicked[2] and gameVars.ball.isAlive and not gameVars.ball.isLaunch:
            isValidPlacement = True
            for ball in gameVars.balls:
                mouseBall = Ball(mx, my)
                if isBallTouchingPeg(ball, mouseBall, 1):
                    isValidPlacement = False
            if isValidPlacement:
                newCheatBall = Ball(mx, my)
                newCheatBall.isAlive = True
                gameVars.balls.append(newCheatBall)
                ball = newCheatBall
                
        # if no-gravity powerup is active
        isGravityPowerUpActive = False
        if gameVars.powerUpActive and gameVars.powerUpType == "no-gravity":
            noGravityPowerUpTimer.update()
            isGravityPowerUpActive = True
            if noGravityPowerUpTimer.isTriggered:
                isGravityPowerUpActive = False
                noGravityPowerUpTimer.cancelTimer()
                gameVars.powerUpCount -= 1
                gameVars.powerUpActive = False or gameVars.cheats
        else:
            isGravityPowerUpActive = False

        performance.record_since("gameplay_update", gameplayUpdateStart)
        gameVars.beginPhysicsFrame()
        if zenballSearch is None:
            gameVars.accumulateFrameTime()
        physicsFrameStart = time.perf_counter()
        while (
            gameVars.physicsAccumulator + 1e-9 >= gameVars.fixedPhysicsStep
            and gameVars.physicsStepsThisFrame < gameVars.maxPhysicsStepsPerFrame
            and not gameVars.gameOver
            and zenballSearch is None
        ):
            physicsStepStart = time.perf_counter_ns()
            pegTimerScanStart = time.perf_counter_ns()
            for moving_peg in gameVars.quadtree.moving_pegs:
                moving_peg.update_movement(gameVars.dt)
            gameVars.validateActiveStuckTimers()
            performance.record_since("peg_timer_scan", pegTimerScanStart)

            lastOrangePegNotHit = None
            if gameVars.orangeCount == 1:
                for p in gameVars.pegs:
                    if p.color == "orange" and not p.isHit:
                        lastOrangePegNotHit = p
                        break

            for b in gameVars.balls:
                closeCallFound = False
                if lastOrangePegNotHit is not None:
                    ballTouchingPeg = isBallTouchingPeg(
                        b,
                        lastOrangePegNotHit,
                        gameVars.dt,
                        peg_radius_multiplier=5,
                    )
                    if ballTouchingPeg:
                        closeCallFound = True
                        if gameVars.timeScale != gameVars.closeCallTimeScale and len(gameVars.balls) < 2:
                            # only play sound once
                            if configs["SOUND_ENABLED"]:
                                playSoundPitch(drumRoll)
                        gameVars.timeScale = gameVars.closeCallTimeScale # slow motion
                        closeBall = b
                    elif gameVars.timeScale != gameVars.baseTimeScale:
                        closeCallFound = True
                        # only play sound once
                        if configs["SOUND_ENABLED"]:
                            playSoundPitch(sighSound)
                        gameVars.timeScale = gameVars.baseTimeScale
                        break
                if closeCallFound:
                    break
        
            # update ball physics and pegs, additional game logic
            removeDeadBalls = False
            for b in gameVars.balls:
                if b.isAlive:
                    gameVars.recordBallPhysicsPosition(b)
                    #### collision ####
                    collisionStart = time.perf_counter_ns()
                    # get the pegs that are in the same screen location as the ball (scaled by gameVars.queryRectSize)
                    updateSweptCollisionBounds(b, gameVars.queryRectSize, queryRect)
                    if gameVars.useQuadtree:
                        nearbyPegs.clear()
                        quadtree.queryInto(queryRect, nearbyPegs)
                    else:
                        nearbyPegs[:] = gameVars.pegs
                    collidedPeg = resolveCollisionAndGetPeg(b, nearbyPegs)
                    performance.record_since("collision_query", collisionStart)
                    for p in (collidedPeg,) if collidedPeg is not None else ():
                        gameVars.recordBallPhysicsPosition(b)
                        ballTouchingPeg = True
                        if ballTouchingPeg:
                            b.lastPegHit = p

                            # automatically remove pegs that a ball is stuck on
                            if gameVars.autoRemovePegs:
                                if p.update_ball_stuck_timer(
                                    b, gameVars.autoRemovePegsTimerValue
                                ):
                                    removed_cluster = gameVars.remove_peg_cluster(
                                        p,
                                        quadtree,
                                        b.vel
                                        if b.vel.getMag() > 0.1
                                        else b.pos - p.pos,
                                    )
                                    b.lastPegHit = None
                                    for removed_peg in removed_cluster:
                                        postEvent(EventType.GAME_PEG_REMOVED)
                                        staticImageRemovedPegs.append(removed_peg)
                                    if removed_cluster and gameVars.quadtreeDebug:
                                        gameVars.quadtreeStaticScreen.fill((0, 0, 0, 0))
                                        quadtree.show(gameVars.quadtreeStaticScreen)
                                elif p.ballStuckTimer.isActive:
                                    gameVars.pegsWithActiveStuckTimers.add(p)

                                if b.vel.getMag() > 1.5:
                                    if not p.ballStuckTimer.isActive:
                                        gameVars.pegsWithActiveStuckTimers.discard(p)
                                    b.lastPegHit = None

                            # check for long shot bonus
                            if b.lastPegHitPos != p.pos and b.lastPegHitPos != None and p.color == "orange" and not p.isHit:
                                if distBetweenTwoPoints(b.lastPegHitPos.x, b.lastPegHitPos.y, p.pos.x, p.pos.y) > gameVars.longShotDistance:
                                    if not gameVars.longShotBonus:
                                        if configs["SOUND_ENABLED"]:
                                            playSoundPitch(longShotSound)
                                        gameVars.score += 25000
                                        b.lastPegHitPos = None
                                        gameVars.longShotBonus = True

                                        # used for showing the bonus gameVars.score
                                        gameVars.longShotPos = Vector(
                                            p.pos.x, p.pos.y)

                                        if pygame.joystick.get_count() > 0 and gameVars.controllerInput:
                                            if configs["DEBUG_MODE"]:
                                                print("Debug: Rumble")
                                            joystick = pygame.joystick.Joystick(
                                                0)
                                            joystick.rumble(1, 1, 100)

                            # used for long shot check
                            b.lastPegHitPos = p.pos

                            # peg color update and powerup sounds
                            if not p.isHit:
                                postEvent(EventType.GAME_PEG_HIT)
                                staticImageChangedPegs.append(p)
                                p.isHit = True
                                gameVars.pegsHit += 1
                                p.update_color()  # change the color to signify it has been hit
                                gameVars.pitchRaiseCount += 1
                                if p.color == "orange":
                                    gameVars.orangeCount -= 1
                                if p.isPowerUp:
                                    if gameVars.powerUpType == "spooky":
                                        if gameVars.powerUpCount < 1:
                                            if configs["SOUND_ENABLED"]:
                                                playSoundPitch(powerUpSpooky1)
                                            firstSpookyHit = True
                                        elif gameVars.powerUpCount == 1:
                                            if configs["SOUND_ENABLED"]:
                                                playSoundPitch(powerUpSpooky2)
                                            firstSpookyHit = False
                                    if gameVars.powerUpType == "multiball":
                                        if configs["SOUND_ENABLED"]:
                                            playSoundPitch(powerUpMultiBall)
                                        postEvent(EventType.GAME_MULTIBALL_POWERUP_TRIGGERED)
                                    if gameVars.powerUpType == "zenball":
                                        if configs["SOUND_ENABLED"]:
                                            playSoundPitch(powerUpZenBallHit)
                                    if gameVars.powerUpType == "guideball":
                                        if configs["SOUND_ENABLED"]:
                                            playSoundPitch(powerUpGuideBall)
                                        gameVars.powerUpCount += 2
                                    if gameVars.powerUpType == "spooky-multiball":
                                        if configs["SOUND_ENABLED"]:
                                            playSoundPitch(powerUpMultiBall)
                                        postEvent(EventType.GAME_MULTIBALL_POWERUP_TRIGGERED)
                                        gameVars.powerUpCount += 1
                                    if gameVars.powerUpType == "no-gravity":
                                        if gameVars.powerUpCount < 1:
                                            # start the no gravity powerup timer
                                            noGravityPowerUpTimer.setTimer(
                                                gameVars.noGravityTimeLength)
                                        if configs["SOUND_ENABLED"]:
                                            playSoundPitch(powerUpNoGravity, 1.9)
                                            playSoundPitch(powerUpNoGravity, 0.8)
                                    
                                    
                                    gameVars.powerUpCount += 1
                                    gameVars.powerUpActive = True

                                # peg hit sounds
                                if gameVars.pitchRaiseCount <= 7:
                                    if not p.isPowerUp:
                                        if configs["SOUND_ENABLED"]:
                                            playSoundPitch(low_hit_sound, gameVars.pitch)
                                    gameVars.pitch -= 0.05  # magic number
                                if gameVars.pitchRaiseCount == 7:
                                    gameVars.pitch = 1.34  # magic number
                                elif gameVars.pitchRaiseCount > 7 and gameVars.pitchRaiseCount < 28:
                                    if not p.isPowerUp:
                                        if configs["SOUND_ENABLED"]:
                                            playSoundPitch(normal_hit_sound, gameVars.pitch)
                                    gameVars.pitch -= 0.045  # magic number
                                elif gameVars.pitchRaiseCount >= 28:
                                    if not p.isPowerUp:
                                        if configs["SOUND_ENABLED"]:
                                            playSoundPitch(normal_hit_sound, gameVars.pitch)

                                # gameVars.cheats
                                if gameVars.cheats:
                                    if gameVars.powerUpType == "spooky":
                                        # if configs["SOUND_ENABLED"]:
                                        #   playSoundPitch(powerUpSpooky1)
                                        gameVars.powerUpCount += 1
                                    if gameVars.powerUpType == "multiball":
                                        if configs["SOUND_ENABLED"]:
                                            playSoundPitch(powerUpMultiBall)
                                        postEvent(EventType.GAME_MULTIBALL_POWERUP_TRIGGERED)
                                        gameVars.powerUpCount += 1
                                    if gameVars.powerUpType == "guideball":
                                        gameVars.powerUpCount += 2
                                    if gameVars.powerUpType == "spooky-multiball":
                                        if configs["SOUND_ENABLED"]:
                                            playSoundPitch(powerUpMultiBall)
                                        # if configs["SOUND_ENABLED"]:
                                        #   playSoundPitch(powerUpSpooky1)
                                        postEvent(EventType.GAME_MULTIBALL_POWERUP_TRIGGERED)
                                        gameVars.powerUpCount += 2
                                    if gameVars.powerUpType == "zenball":
                                        gameVars.powerUpCount += 1
                                    if gameVars.powerUpType == "no-gravity":
                                        isGravityPowerUpActive = True

                                # keep track of points earned
                                # gameVars.pointsEarned.append(p.points)
                                gameVars.score += (p.points *
                                            getScoreMultiplier(gameVars.orangeCount, gameVars.pegsHit))

                    #if no-gravity powerup is active
                    if isGravityPowerUpActive:
                        # keep a minimum velocity
                        if b.vel.getMag() < 1.5:
                            b.vel.setMag(1.5)
                        if b.vel.getMag() < 0.2:
                            b.vel.add(Vector(0, 1))
                
                    # check if ball has hit the sides of the gameVars.bucket (this is a special case handled after the pegs have been checked)
                    collidedPeg = gameVars.bucket.isBallCollidingWithBucketEdge(b, gameVars.dt)
                    if collidedPeg:
                        b = resolveCollision(b, [collidedPeg], gameVars.dt)
                        gameVars.recordBallPhysicsPosition(b)
                    
                    ballUpdateStart = time.perf_counter_ns()
                    b.update(gameVars.dt, isGravityPowerUpActive)
                    performance.record_since("ball_update", ballUpdateStart)

                    # if active spooky powerup
                    if gameVars.powerUpActive and (gameVars.powerUpType == "spooky" or gameVars.powerUpType == "spooky-multiball"):
                        if b.pos.y + b.radius > configs["HEIGHT"]:
                            b.pos.y = 0 + b.radius
                            b.inBucket = False
                            # set previous values to current values to prevent collision detection breaking during screen wrap
                            b.prevPos = Vector(b.pos.x, b.pos.y)
                            b.prevAcc = Vector(b.acc.x, b.acc.y)
                            b.prevVel = Vector(b.vel.x, b.vel.y)
                            gameVars.recordBallPhysicsPosition(b)
                            if gameVars.powerUpCount == 1 and firstSpookyHit:
                                if configs["SOUND_ENABLED"]:
                                    playSoundPitch(powerUpSpooky2)
                            elif gameVars.powerUpCount == 1 and not firstSpookyHit:
                                if configs["SOUND_ENABLED"]:
                                    playSoundPitch(powerUpSpooky4)
                            elif gameVars.powerUpCount == 2 and not firstSpookyHit:
                                if configs["SOUND_ENABLED"]:
                                    playSoundPitch(powerUpSpooky3)
                            elif gameVars.cheats:
                                if configs["SOUND_ENABLED"]:
                                    playSoundPitch(powerUpSpooky2)
                            gameVars.powerUpCount -= 1
                            if gameVars.powerUpCount < 1:
                                gameVars.powerUpActive = False or gameVars.cheats

                    gameVars.recordBallPhysicsPosition(b)

                    # if active multiball powerup
                    if (
                        consumeEvent(EventType.GAME_MULTIBALL_POWERUP_TRIGGERED)
                        and gameVars.powerUpType in ("multiball", "spooky-multiball")
                    ):
                        newBall = Ball(b.pos.x, b.pos.y)
                        newBall.vel.x = b.vel.x * -1
                        newBall.vel.y = b.vel.y * -1
                        newBall.isAlive = True
                        gameVars.balls.append(newBall)

                    # if ball went in the gameVars.bucket
                    if not b.inBucket and gameVars.bucket.isInBucket(b.pos.x, b.pos.y):
                        b.inBucket = True  # prevent the ball from triggering it multiple times
                        if configs["SOUND_ENABLED"]:
                            playSoundPitch(freeBallSound)
                        gameVars.ballsRemaining += 1
                elif b is not ball:
                    removeDeadBalls = True

            if removeDeadBalls:
                # Compact once rather than shifting the list for each dead ball.
                aliveBallCount = 0
                for b in gameVars.balls:
                    if b.isAlive or b is ball:
                        gameVars.balls[aliveBallCount] = b
                        aliveBallCount += 1
                del gameVars.balls[aliveBallCount:]

            # Defer full redraws until all fixed steps for this rendered frame finish.
            if eventOccured(EventType.GAME_PEG_REMOVED):
                if gameVars.quadtreeDebug:
                    quadtreeStaticScreen.fill((0, 0, 0, 0))
                    quadtree.show(quadtreeStaticScreen)

            # this little loop and if statement will determine if any of the balls are still alive and therfore if everything should be cleared/reset or not
            done = True
            for b in gameVars.balls:
                if b.isAlive:
                    done = False
                    break

            # check if their are any orange pegs or if the player has no balls (lol)
            if done and (gameVars.orangeCount == 0 or gameVars.ballsRemaining < 1) and not gameVars.gameOver:
                if not isRemovePegsAnimationSequenceActive:
                    gameVars.gameOver = True
                    if gameVars.ballsRemaining < 1 and gameVars.orangeCount > 0:
                        if configs["SOUND_ENABLED"]:
                            playSoundPitch(failSound)

            # check if the last orange peg has been hit, play ode to joy and change the buckets
            if gameVars.orangeCount < 1 and not gameVars.ballsRemaining < 1 and not gameVars.alreadyPlayedOdeToJoy:
                pygame.mixer.music.load("resources/audio/music/ode_to_joy.wav")
                if configs["MUSIC_ENABLED"]:
                    pygame.mixer.music.play(-1)
                if configs["SOUND_ENABLED"]:
                    playSoundPitch(cymbal)
                gameVars.alreadyPlayedOdeToJoy = True
                gameVars.timeScale = gameVars.odeToJoyTimeScale # slow motion but not as slow as close call

            # reset everything and remove hit pegs
            if done and gameVars.shouldClear:
                gameVars.shouldClear = False
                gameVars.balls[:] = [gameVars.ball]
                ball = gameVars.ball
                gameVars.ball.reset()
                gameVars.pitch = 1.0
                gameVars.pitchRaiseCount = 0
                freeBall = False
                done = False
                gameVars.ballsRemaining -= 1
                gameVars.pegsHit = 0
                gameVars.longShotBonus = False
                if gameVars.timeScale == gameVars.closeCallTimeScale:
                    gameVars.timeScale = gameVars.baseTimeScale
                # forces the trajectory to be recalculated in case the mouse aim has not changed
                gameVars.previousAim = Vector(0, 1)
                if gameVars.powerUpType == "multiball" or gameVars.powerUpType == "spooky-multiball":
                    gameVars.powerUpActive = False or gameVars.cheats
                    gameVars.powerUpCount = 0
            
                # save hit pegs for animation
                hitPegs = [p for p in gameVars.pegs if p.isHit]

                # start the peg removal animation sequence
                postEvent(EventType.GAME_PEG_REMOVAL_ANIMATION_STARTED)
            
                staticImage = updateStaticImageMeasured(
                    staticImage,
                    gameVars.pegs,
                    staticImageChangedPegs,
                )
                staticImageChangedPegs.clear()
                animationFrameScreen.fill((0, 0, 0, 0))
            
                delayTimer = TimedEvent(0.25)
            
                # remove hit pegs
                gameVars.pegs = [p for p in gameVars.pegs if not p.isHit]
                for peg in hitPegs:
                    gameVars.pegsWithActiveStuckTimers.discard(peg)
                    quadtree.remove(peg)
                for s in gameVars.pointsEarned:
                    gameVars.score += s
            
                if gameVars.quadtreeDebug:
                    quadtreeStaticScreen.fill((0, 0, 0, 0))
                    quadtree.show(quadtreeStaticScreen)

            # bucket, pass the power up info for the bucket to update its collison and image
            gameVars.bucket.update(gameVars.dt, gameVars.powerUpType, gameVars.powerUpActive)

            gameVars.consumePhysicsStep()
            performance.record_since("physics_step", physicsStepStart)
        gameVars.finishPhysicsFrame()
        gameVars.physicsTime = time.perf_counter() - physicsFrameStart
        performance.record_ms("physics_frame", gameVars.physicsTime * 1000)
        if zenballSearch is not None:
            gameVars.updateBucketDuringZenballSearch()
        if zenballSearchCompletedThisFrame:
            gameVars.bestTrajectoryBucketPoints = (
                gameVars.bucket.predictMarkerPositions(
                    len(gameVars.bestTrajectory),
                    gameVars.dt,
                )
            )
    if staticImageChangedPegs or staticImageRemovedPegs:
        staticImage = updateStaticImageMeasured(
            staticImage,
            gameVars.pegs,
            staticImageChangedPegs,
            staticImageRemovedPegs,
        )
    # measure time for draw calls
    startDrawTime = time.time()

    renderer.screen = screen
    with performance.measure("world_render"):
        done = renderer.draw_world(
            gameVars,
            staticImage,
            animationFrameScreen,
            trajectory,
            isGravityPowerUpActive,
            isNewGameAnimationSequenceActive,
            isRemovePegsAnimationSequenceActive,
            completedAnimationFrameScreen,
            performance,
            largeLevelSpawnReveal,
        )

    # show if paused
    if gameVars.gamePaused and not gameVars.gameOver:
        pauseSelection = menus.pause_selection(screen, mx, my, mouseClicked[0])
        if pauseSelection == "resume":
            gameVars.gamePaused = False
            delayTimer = TimedEvent(0.50)
        elif pauseSelection == "restart":
            # reset the game
            resetRound()
            if not configs["MUSIC_ENABLED"]:
                stopMusic()
            gameVars.gamePaused = False
            delayTimer = TimedEvent(0.50)
            postEvent(EventType.GAME_NEW_GAME_ANIMATION_STARTED)
        elif pauseSelection == "load":
            pygame.mixer.music.stop()
            (
                gameVars.pegs,
                gameVars.originPegs,
                gameVars.orangeCount,
                levelFileName,
            ) = menus.select_level(screen)
            levelDataProgressPending = True
            # set the caption to include the level name
            pygame.display.set_caption(
                "PegglePy   -   " + levelFileName)
            resetRound()
            if not configs["MUSIC_ENABLED"]:
                stopMusic()
            gameVars.gamePaused = False
            delayTimer = TimedEvent(0.50)
            postEvent(EventType.GAME_NEW_GAME_ANIMATION_STARTED)
        elif pauseSelection == "quit":
            gameVars.gameRunning = False
            time.sleep(0.15)
        elif pauseSelection == "mainMenu":
            gameVars.gamePaused = False
            selection, editor_played = menus.navigate_main_menu(
                screen, clock, gameVars
            )
            if selection == "start" and not editor_played:
                levelFileName = menus.load_selected_level(
                    screen, gameVars
                )
                levelDataProgressPending = True
            if editor_played:
                levelFileName = "Unsaved Editor Level"

            # reset the game
            resetRound()

            postEvent(EventType.GAME_NEW_GAME_ANIMATION_STARTED)

            # prevent accidental click on launch
            delayTimer = TimedEvent(0.50)

            #change the song
            if configs["MUSIC_ENABLED"]:
                newSong()

            # set the caption to include the level name
            pygame.display.set_caption(
                "PegglePy   -   " + levelFileName)

        elif pauseSelection == "editor":
            gameVars.gamePaused = False
            levelEditorPauseSelection, editor_played = menus.open_editor(
                screen, clock, gameVars
            )
            if editor_played:
                levelFileName = "Unsaved Editor Level"
            if levelEditorPauseSelection != "quit":
                resetRound()
                postEvent(EventType.GAME_NEW_GAME_ANIMATION_STARTED)
                delayTimer = TimedEvent(0.50)
                if configs["MUSIC_ENABLED"]:
                    newSong()

        elif pauseSelection == "settings":
            isFullscreen = configs["FULLSCREEN"] # check state before settings menu opens
            menus.open_settings(screen)
            
            if configs["MUSIC_ENABLED"]:
                newSong()
                
            # if the fullscreen state has changed, update positions to handle fullscreen toggle
            if configs["FULLSCREEN"] != isFullscreen:
                # adjust the positions of every peg to be centered on the screen based on configs["WIDTH"] and configs["HEIGHT"]
                # get the position of the left most peg
                leftMostPeg = gameVars.pegs[0]
                for peg in gameVars.pegs:
                    if peg.pos.x < leftMostPeg.pos.x:
                        leftMostPeg = peg
                rightMostPeg = gameVars.pegs[0]
                for peg in gameVars.pegs:
                    if peg.pos.x > rightMostPeg.pos.x:
                        rightMostPeg = peg

                # find the center of the left most and right most gameVars.pegs
                centerOfLeftAndRightPegs = (leftMostPeg.pos.x + rightMostPeg.pos.x)/2
                # find the center of the screen
                screenCenter = configs["WIDTH"]/2
                # find the difference between the center of the screen and the center of the left and right most gameVars.pegs
                difference = screenCenter - centerOfLeftAndRightPegs

                # adjust the position of every peg by the difference
                for peg in gameVars.pegs:
                    peg.pos.x += difference
                    
                # adjust the position of each ball by the difference
                for ball in gameVars.balls:
                    ball.pos.x += difference
                    
                
                # Do same process again for the Y axis
                topMostPeg = gameVars.pegs[0]
                for peg in gameVars.pegs:
                    if peg.pos.y < topMostPeg.pos.y:
                        topMostPeg = peg
                bottomMostPeg = gameVars.pegs[0]
                for peg in gameVars.pegs:
                    if peg.pos.y > bottomMostPeg.pos.y:
                        bottomMostPeg = peg
                    
                # find the center of the top most and bottom most gameVars.pegs
                centerOfTopAndBottomPegs = (topMostPeg.pos.y + bottomMostPeg.pos.y)/2
                # find the center of the screen
                screenCenter = configs["HEIGHT"]/2
                # find the difference between the center of the screen and the center of the top and bottom most gameVars.pegs
                difference = screenCenter - centerOfTopAndBottomPegs
                
                # adjust the position of every peg by the difference
                for peg in gameVars.pegs:
                    peg.pos.y += difference
                
                # adjust the position of each ball by the difference
                for ball in gameVars.balls:
                    ball.pos.y += difference
                    
                # update ball position if none of the balls are alive
                if not any([ball.isAlive for ball in gameVars.balls]):
                    gameVars.ball.pos = Vector(configs["WIDTH"]/2, configs["HEIGHT"]/25)
                    gameVars.ball.prevPos = gameVars.ball.pos.copy()
                    
                    inputAim = Vector(configs["WIDTH"]/2, (configs["HEIGHT"]/25)+50)
                    
                # update the quadtree boundary
                boundary = Rectangle(configs["WIDTH"]/2, configs["HEIGHT"]/2, configs["WIDTH"]/2, configs["HEIGHT"]/2)
                
                # update the quadtree
                quadtree = QuadtreePegs(boundary, 4)
                queryRect = Rectangle(0, 0, 0, 0)
                nearbyPegs = []
                
                # update the bucket y position to be at the bottom of the screen
                gameVars.bucket.pos = Vector(configs["WIDTH"]/2, configs["HEIGHT"] - gameVars.bucket.bucketBackImg.get_height())  # position
                                
                # update the static image
                staticImage = createStaticImageMeasured(gameVars.pegs)
                

    with performance.measure("game_overlay_render"):
        renderer.draw_game_over(gameVars)
        renderer.draw_long_shot(gameVars, gameVars.longShotPos)

    # save the draw time
    drawTime = time.time() - startDrawTime

    with performance.measure("debug_render"):
        renderer.draw_debug(
            gameVars,
            clock,
            (mx, my),
            done,
            joystick,
            nearbyPegs,
            queryRect,
            quadtree,
            gameVars.totalTime,
            drawTime,
        )

    if gameVars.physicsTimeDebug:
        with performance.measure("performance_overlay"):
            renderer.draw_performance_metrics(performance)

    displayStart = time.perf_counter_ns()
    pygame.display.update()
    performance.record_since("display_present", displayStart)
    
    gameVars.totalTime = time.time() - startTotalTime
    performance.record_since("frame_cpu", frameStart)
    performance.end_frame()

print("Goodbye")
