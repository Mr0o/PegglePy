import pygame
from math import sqrt

### local imports ###
from local.config import baseTimeScale
from local.userConfig import configs
from local.resources import backgroundImg, bluePegImg, orangePegImg, greenPegImg
from local.resources import hitBluePegImg, hitOrangePegImg, hitGreenPegImg
from local.resources import glowingBluePegImg, glowingOrangePegImg, glowingGreenPegImg
from local.peg import Peg
from local.ball import Ball
from local.audio import newSong
from local.quadtree import QuadtreePegs, Rectangle


# create a static image of the background and pegs, this avoids redrawing the background and pegs every frame
# -- dramatic performance improvement especially in levels with lots of pegs
def createStaticImage(pegs: list[Peg], bgImg=backgroundImg):
    staticImg = pygame.Surface((configs["WIDTH"], configs["HEIGHT"]))

    # draw background
    bgImg = pygame.image.load("resources/images/background960x720.jpg")
    bgImg =  pygame.transform.scale(backgroundImg, (configs["WIDTH"], configs["HEIGHT"]))
    staticImg.blit(bgImg, (0, 0))

    # draw pegs
    for p in pegs:
            # check peg color
        if p.color == "orange":
            pegImg = orangePegImg
        elif p.color == "green":
            pegImg = greenPegImg
        else:
            pegImg = bluePegImg
        # check if peg is hit
        if p.isHit:
            if p.color == "orange":
                pegImg = hitOrangePegImg
            elif p.color == "green":
                pegImg = hitGreenPegImg
            else:
                pegImg = hitBluePegImg
        staticImg.blit(
            pegImg, (p.pos.x - p.posAdjust, p.pos.y - p.posAdjust))

    # anti-aliasing
    # staticImg = pygame.transform.smoothscale(staticImg, (configs["WIDTH"], configs["HEIGHT"]))

    return staticImg


# blit a single peg to the static image rather than redrawing the entire image (this may not look correct if the peg is overlapping another peg)
def updateStaticImage(staticImg: pygame.Surface, peg: Peg):
    # check peg color
    if peg.color == "orange":
        pegImg = orangePegImg
    elif peg.color == "green":
        pegImg = greenPegImg
    else:
        pegImg = bluePegImg
    # check if peg is hit
    if peg.isHit:
        if peg.color == "orange":
            pegImg = hitOrangePegImg
        elif peg.color == "green":
            pegImg = hitGreenPegImg
        else:
            pegImg = hitBluePegImg
    # blit the peg to the static image
    staticImg.blit(pegImg, (peg.pos.x - peg.posAdjust,
                             peg.pos.y - peg.posAdjust))

    return staticImg


# create a static image of cicles used when debugging (zenball trajectory, to be specific)
def createStaticCircles(trajectory: list[Ball]) -> pygame.Surface:
    staticCircles = pygame.Surface((configs["WIDTH"], configs["HEIGHT"]))

    # surface is transparent
    staticCircles.set_colorkey((0, 0, 0))

    for fb in trajectory:
        pygame.draw.circle(staticCircles, (0, 220, 10), [fb.pos.x, fb.pos.y], 1)

    return staticCircles

# returns the next frame of the animation sequence
def getNewGamePegAnimationSequenceFrame(pegs: list[Peg], dt: float) -> pygame.Surface:
    # transparent surface
    animationFrameScreen = pygame.Surface((configs["WIDTH"], configs["HEIGHT"]), pygame.SRCALPHA)
    for peg in pegs:
        if peg.color == "orange":
            pegImg = orangePegImg
        elif peg.color == "green":
            pegImg = greenPegImg
        else:
            pegImg = bluePegImg
                
        # set animation image
        peg.animation.set_image(pegImg)
        peg.animation.update(dt)
        peg.animation.draw(animationFrameScreen)
        
    return animationFrameScreen


# quite horrendous, will be fixed in the future... hopefully :)
def resetGame(balls,  createPegColors, bucket, pegs, originPegs, quadtree):
    # reset everything
    balls.clear()  # clear all the balls
    balls.append(Ball(configs["WIDTH"]/2, configs["HEIGHT"]/25))  # recreate the original ball
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
    timeScale = baseTimeScale
    LongShotBonus = False
    # change the song
    newSong()
    staticImage = createStaticImage(pegs)
    boundary = Rectangle(configs["WIDTH"]/2, configs["HEIGHT"]/2, configs["WIDTH"]/2, configs["HEIGHT"]/2)
    quadtree = QuadtreePegs(boundary, len(pegs))
    for peg in pegs:
        quadtree.insert(peg)
    return ballsRemaining, powerUpActive, powerUpCount, pitch, pitchRaiseCount, ball, score, pegsHit, pegs, orangeCount, gameOver, alreadyPlayedOdeToJoy, timeScale, LongShotBonus, staticImage, quadtree


def distBetweenTwoPoints(x1, y1, x2, y2):
    return sqrt(((x1-x2)**2) + ((y1-y2)**2))
