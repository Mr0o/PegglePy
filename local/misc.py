import pygame
from math import sqrt, ceil
from random import randint

### local imports ###
from local.load_level import loadData, createDefaultPegsPos
from local.config import WIDTH, HEIGHT, debug, segmentCount
from local.resources import backgroundImg
from local.peg import Peg
from local.ball import Ball
from local.audio import loadRandMusic, playMusic, stopMusic

# iterate through each peg x,y position to determine its location on the screen


def assignPegScreenLocation(pegs: list[Peg], segmentCount: int):
    segmentWidth = WIDTH/segmentCount
    for p in pegs:
        for i in range(segmentCount+1):
            if p.pos.x >= segmentWidth*(i-1) - p.radius and p.pos.x <= segmentWidth*i + p.radius:
                p.pegScreenLocations.append(i)


def getBallScreenLocation(b: Ball, segmentCount) -> list[int]:
    segmentWidth = WIDTH/segmentCount
    pos1 = ceil((b.pos.x - b.radius)/segmentWidth)
    pos2 = ceil((b.pos.x + b.radius)/segmentWidth)

    if pos1 == pos2: return [pos1]
    else: return [pos1, pos2]

    # for i in range(segmentCount+1):
    #     if b.pos.x > segmentWidth*(i-1) - b.radius and b.pos.x < segmentWidth*i + b.radius:
    #         locations.append(i)
    #         break

    # return locations


def getScoreMultiplier(remainingOrangePegs, pegsHit=0) -> int:
    # first multiplier based on remaining orange pegs
    multiplier = 1
    if remainingOrangePegs <= 3:
        multiplier = 10
    elif remainingOrangePegs <= 6:
        multiplier = 5
    elif remainingOrangePegs <= 10:
        multiplier = 3
    elif remainingOrangePegs <= 15:
        multiplier = 2

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

def createPegColors(pegs: list[Peg], color_map: list = None) -> list[Peg]:
    if color_map:
        # update peg colors with a fixed map
        for i in range(0, len(pegs)):
            peg = pegs[i]
            peg.color = color_map[i]
            if peg.color == "orange":
                peg.isOrange = True
            elif peg.color == "green":
                peg.isPowerUp = True
            peg.update_color()
    else:
        target_oranges = 25
        target_greens = 2

        if len(pegs) < 25:
            if debug:
                print("WARN: Level has less than 25 pegs, continuing anyway...")
            target_oranges = 1 if len(pegs) <= 3 else len(pegs) - 2
            if len(pegs) <= 2:
                target_greens = len(pegs) - target_oranges
        elif len(pegs) > 120:
            if debug:
                print(
                    "WARN: Level has excessive number of pegs, expect performance issues...")

        peg_pool = pegs.copy()

        # create orange pegs
        orange_count = 0
        while orange_count < target_oranges:
            i = randint(0, len(peg_pool) - 1)
            p = peg_pool.pop(i)
            p.color = "orange"
            p.isOrange = True
            p.update_color()

            orange_count += 1

        # create green pegs
        for _ in range(target_greens):
            i = randint(0, len(peg_pool) - 1)
            p = peg_pool.pop(i)
            p.color = "green"
            p.isPowerUp = True
            p.update_color()

    return pegs


def loadLevel(filePath = None) -> tuple[list[Peg], list[Peg], int]:
    # load the pegs from a level file (pickle)
    pegs, levelFileName = loadData(filePath)
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
    balls.clear()  # clear all the balls
    balls.append(Ball(WIDTH/2, HEIGHT/25))  # recreate the original ball
    ball = balls[0]
    ball.reset()
    pitch = 1.0
    pitchRaiseCount = 0
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
    gameOver = False
    alreadyPlayedOdeToJoy = False
    frameRate = 144
    LongShotBonus = False
    # change the song
    stopMusic()
    loadRandMusic()
    playMusic()
    staticImage = createStaticImage(pegs)
    return ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, frameRate, LongShotBonus, staticImage


def distBetweenTwoPoints(x1, y1, x2, y2):
    return sqrt(((x1-x2)**2) + ((y1-y2)**2))
