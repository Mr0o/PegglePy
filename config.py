from vectors import Vector # used for gravity

import pygame

# hard coded window size
WIDTH = 1200
HEIGHT = 900

#power up (spooky, multiball, zenball, guideball)
powerUpType = "spooky"

# debugging (displays debugging information to the screen)
debug = False

# a bunch of variables (defaults)
LAUNCH_FORCE = 4.5
gravity = Vector(0, 0.02)
trajectoryDepth = 75 # how many steps to take in the trajectory calculation
bucketVelocity = -1.3
ballsRemaining = 10
freeBall = False
powerUpActive = False
powerUpCount = 0
pitch = 1.0
pitchRaiseCount = 0
showCollision = False
previousAim = Vector(0,1)
shouldClear = False


#images
ballImg = pygame.image.load("resources/images/balls/16x16/ball.png")
#non hit peg
bluePegImg = pygame.image.load("resources/images/pegs/28x28/unlit_blue_peg.png")
orangePegImg = pygame.image.load("resources/images/pegs/28x28/unlit_red_peg.png")
greenPegImg = pygame.image.load("resources/images/pegs/28x28/unlit_green_peg.png")
#hit peg
hitBluePegImg = pygame.image.load("resources/images/pegs/28x28/glowing_blue_peg.png")
hitOrangePegImg = pygame.image.load("resources/images/pegs/28x28/glowing_red_peg.png")
hitGreenPegImg = pygame.image.load("resources/images/pegs/28x28/glowing_green_peg.png")