from local.vectors import Vector # used for gravity

import pygame

# hard coded window size
WIDTH = 1200
HEIGHT = 900

#power up (spooky, multiball, zenball, guideball, spooky-multiball)
powerUpType = "spooky"

# gives you a power up on every ball, can be useful for debugging/testing or if you just want to cheat
cheats = False

# debugging (displays debugging information to the screen)
debug = False

# enable or diasble sound effects
soundEnabled = True

# enable or disable music
musicEnabled = True

# a bunch of variables (defaults)
LAUNCH_FORCE = 4.5
maxBallVelocity = 6
gravity = Vector(0, 0.025)
trajectoryDepth = 75 # how many steps to take in the normal (non-powerup) launch trajectory calculation
bucketVelocity = 2.5 # max set velocity of the bucket
ballsRemaining = 10
freeBall = False
powerUpActive = False
powerUpCount = 0
pitch = 1.0
pitchRaiseCount = 0
showCollision = False
previousAim = Vector(0,1)
shouldClear = False
segmentCount = 16
autoRemovePegs = True
longShotDistance = WIDTH/3
frameRate = 144
ballRad = 10
pegRad = 20

#images
ballImg = pygame.image.load("resources/images/balls/200x200/ball.png")
#transform
ballImg = pygame.transform.scale(ballImg, (ballRad*2, ballRad*2))
#ballImg.convert_alpha()

#non hit peg
bluePegImg = pygame.image.load("resources/images/pegs/200x200/unlit_blue_peg.png")
orangePegImg = pygame.image.load("resources/images/pegs/200x200/unlit_red_peg.png")
greenPegImg = pygame.image.load("resources/images/pegs/200x200/unlit_green_peg.png")
#transform
bluePegImg = pygame.transform.scale(bluePegImg, (pegRad*2, pegRad*2))
orangePegImg = pygame.transform.scale(orangePegImg, (pegRad*2, pegRad*2))
greenPegImg = pygame.transform.scale(greenPegImg, (pegRad*2, pegRad*2))
#bluePegImg.convert_alpha()
#orangePegImg.convert_alpha()
#greenPegImg.convert_alpha()
#hit peg
hitBluePegImg = pygame.image.load("resources/images/pegs/200x200/lit_blue_peg.png")
hitOrangePegImg = pygame.image.load("resources/images/pegs/200x200/lit_red_peg.png")
hitGreenPegImg = pygame.image.load("resources/images/pegs/200x200/lit_green_peg.png")
#transform
hitPegRad = pegRad*2
hitBluePegImg = pygame.transform.scale(hitBluePegImg, (hitPegRad, hitPegRad))
hitOrangePegImg = pygame.transform.scale(hitOrangePegImg, (hitPegRad, hitPegRad))
hitGreenPegImg = pygame.transform.scale(hitGreenPegImg, (hitPegRad, hitPegRad))

#hitBluePegImg.convert_alpha()
#hitOrangePegImg.convert_alpha()
#hitGreenPegImg.convert_alpha()