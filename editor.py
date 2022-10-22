import sys # used to exit the program immediately

## disable pygame init message - "Hello from the pygame community..." ##
import contextlib
with contextlib.redirect_stdout(None):
    import pygame # used for input, audio and graphics

from random import randint
import pickle

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


# play random music
r = randint(1, 3)
if r == 1:
    pygame.mixer.music.load("resources/audio/music/peggle_music_1.wav")
if r == 2:
    pygame.mixer.music.load("resources/audio/music/peggle_music_2.wav")
if r == 3:
    pygame.mixer.music.load("resources/audio/music/peggle_music_9.wav")
pygame.mixer.music.play(-1) # looping forever


#Background image
backgroundImg = pygame.image.load("resources/images/background960x720.jpg")
backgroundImg =  pygame.transform.scale(backgroundImg, (WIDTH, HEIGHT))

#font
ballCountFont = pygame.font.Font("resources/fonts/Evogria.otf", 30)
infoFont = pygame.font.Font("resources/fonts/Evogria.otf", 16)
debugFont = pygame.font.Font("resources/fonts/Evogria.otf", 12)

##### drawing functions #####
def drawCircle(x, y, rad, rgb):
    pygame.draw.circle(screen, (rgb), [x, y], rad)

def drawLine(x1,y1,x2,y2):
    pygame.draw.line(screen, (255, 0, 0),[x1, y1],[x2,y2])

debugCollision = False

# load the pegs ffrom a level file (pickle)
pegs = loadData()

##### main loop #####
while True:
    for event in pygame.event.get():  # check events and quit if the program is closed
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                pass


    mouseClicked = pygame.mouse.get_pressed() # get the mouse click state
    mx, my =  pygame.mouse.get_pos()  # get mouse position as 'mx' and 'my'

    #if mouse clicked 
    if mouseClicked[0]:
        pass
    

    ##### draw #####
    screen.fill((0, 0, 0))  # black screen
    screen.blit(backgroundImg, (0, 0))
    
    #draw pegs
    for p in pegs:
        screen.blit(p.pegImg, (p.pos.vx - p.posAdjust, p.pos.vy - p.posAdjust))

    pygame.display.update()
    clock.tick(144)  # lock game framerate to 144 fps