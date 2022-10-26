from vectors import Vector # used for gravity

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

# a bunch of variables (defaults)
LAUNCH_FORCE = 4.5
gravity = Vector(0, 0.025)
trajectoryDepth = 75 # how many steps to take in the normal (non-powerup) launch trajectory calculation
bucketVelocity = -1.25
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
frameRate = 144

#images
ballImg = pygame.image.load("resources/images/balls/16x16/ball.png")
#ballImg.convert_alpha()
#non hit peg
bluePegImg = pygame.image.load("resources/images/pegs/28x28/unlit_blue_peg.png")
orangePegImg = pygame.image.load("resources/images/pegs/28x28/unlit_red_peg.png")
greenPegImg = pygame.image.load("resources/images/pegs/28x28/unlit_green_peg.png")
#bluePegImg.convert_alpha()
#orangePegImg.convert_alpha()
#greenPegImg.convert_alpha()
#hit peg
hitBluePegImg = pygame.image.load("resources/images/pegs/28x28/glowing_blue_peg.png")
hitOrangePegImg = pygame.image.load("resources/images/pegs/28x28/glowing_red_peg.png")
hitGreenPegImg = pygame.image.load("resources/images/pegs/28x28/glowing_green_peg.png")
#hitBluePegImg.convert_alpha()
#hitOrangePegImg.convert_alpha()
#hitGreenPegImg.convert_alpha()