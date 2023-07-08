import pygame
from math import sqrt
from random import randint

### local imports ###
from local.load_level import loadData, createDefaultPegsPos
from local.config import WIDTH, HEIGHT, debug, segmentCount
from local.resources import backgroundImg
from local.peg import Peg
from local.ball import Ball

# iterate through each peg x,y position to determine its location on the screen


def assignPegScreenLocation(pegs: list[Peg], segmentCount: int):
    segmentWidth = WIDTH/segmentCount
    for p in pegs:
        for i in range(segmentCount+1):
            if p.pos.x >= segmentWidth*(i-1) - p.radius and p.pos.x <= segmentWidth*i + p.radius:
                p.pegScreenLocations.append(i)


def getBallScreenLocation(b: Ball, segmentCount) -> list[int]:
    segmentWidth = WIDTH/segmentCount
    locations = []
    for i in range(segmentCount+1):
        if b.pos.x > segmentWidth*(i-1) - b.radius and b.pos.x < segmentWidth*i + b.radius:
            locations.append(i)

    return locations


def getScoreMultiplier(remainingOrangePegs, pegsHit=0) -> int:
    # first multiplier based on remaining orange pegs
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

    # second multiplier based on number of pegs hit by the current ball
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
    elif pegsHit >= 35:  # if you are hitting this many pegs with one ball, you are either very lucky or cheating but this is the reward either way
        multiplier *= 100
    return multiplier


def createPegColors(pegs: list[Peg]) -> list[Peg]:
    orangeCount = 25

    if len(pegs) < 25:
        if debug:
            print("WARN: Level has less than 25 pegs, continuing anyway...")
        orangeCount = len(pegs) - 1
    elif len(pegs) > 120:
        if debug:
            print(
                "WARN: Level has excessive number of pegs, expect performance issues...")

    # create orange pegs
    numOfOrangePegs = 0
    while (numOfOrangePegs < orangeCount):
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

    # create green pegs
    for _ in range(2):
        i = randint(0, len(pegs)-1)
        p = pegs[i]
        p.color = "green"
        p.isPowerUp = True
        p.update_color()

    return pegs


def loadLevel() -> tuple[list[Peg], list[Peg], int]:
    # load the pegs from a level file (pickle)
    pegs, levelFileName = loadData()
    originPegs = pegs.copy()

    pegs = createPegColors(pegs)

    orangeCount = 0
    for peg in pegs:
        if peg.color == "orange":
            orangeCount += 1

    # check that the filepath is not empty
    if levelFileName == "" or levelFileName == None:
        levelFileName = "Default"
    else:
        # strip everything from the filepath except the filename
        levelFileName = levelFileName.split("/")[-1]
        # remove the file extension '.lvl'
        levelFileName = levelFileName[:-4]

    return pegs, originPegs, orangeCount, levelFileName


def loadDefaultLevel() -> tuple[list[Peg], list[Peg], int]:
    pegsPosList = createDefaultPegsPos()
    # using x and y tuple, create list of peg objects
    pegs = []
    for xyPos in pegsPosList:
        x, y = xyPos
        pegs.append(Peg(x, y))

    originPegs = pegs.copy()

    pegs = createPegColors(pegs)

    orangeCount = 0
    for peg in pegs:
        if peg.color == "orange":
            orangeCount += 1

    levelFileName = "Default"

    return pegs, originPegs, orangeCount, levelFileName


def loadRandMusic():
    # load random music
    r = randint(1, 10)
    pygame.mixer.music.load(
        "resources/audio/music/Peggle Beat " + str(r) + " (Peggle Deluxe).mp3")


# create a static image of the background and pegs, this avoids redrawing the background and pegs every frame
# -- dramatic performance improvement especially in levels with lots of pegs
def createStaticImage(pegs: list[Peg], bgImg=backgroundImg):
    staticImg = pygame.Surface((WIDTH, HEIGHT))

    # draw background
    staticImg.blit(bgImg, (0, 0))

    # draw pegs
    for p in pegs:
        staticImg.blit(
            p.pegImg, (p.pos.x - p.posAdjust, p.pos.y - p.posAdjust))

    # anti-aliasing
    # staticImg = pygame.transform.smoothscale(staticImg, (WIDTH, HEIGHT))

    return staticImg


# blit a single peg to the static image rather than redrawing the entire image (this may not look correct if the peg is overlapping another peg)
def updateStaticImage(staticImg: pygame.Surface, peg: Peg):
    staticImg.blit(peg.pegImg, (peg.pos.x - peg.posAdjust,
                   peg.pos.y - peg.posAdjust))

    return staticImg


# create a static image of cicles used when debugging (zenball trajectory, to be specific)
def createStaticCircles(trajectory: list[Ball]) -> pygame.Surface:
    staticCircles = pygame.Surface((WIDTH, HEIGHT))

    # surface is transparent
    staticCircles.set_colorkey((0, 0, 0))

    for fb in trajectory:
        pygame.draw.circle(staticCircles, (0, 220, 10), [fb.pos.x, fb.pos.y], 1)

    return staticCircles


# quite horrendous, will be fixed in the future... hopefully :)
def resetGame(balls, assignPegScreenLocation, createPegColors, bucket, pegs, originPegs):
    # reset everything
    shouldClear = False
    balls.clear()  # clear all the balls
    balls.append(Ball(WIDTH/2, HEIGHT/25))  # recreate the original ball
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
        if peg.color == "orange":
            orangeCount += 1
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
    pygame.mixer.music.play(-1)  # looping forever
    staticImage = createStaticImage(pegs)
    return ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, frameRate, LongShotBonus, staticImage


def distBetweenTwoPoints(x1, y1, x2, y2):
    return sqrt(((x1-x2)**2) + ((y1-y2)**2))
