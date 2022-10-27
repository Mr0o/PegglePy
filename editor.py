import sys # used to exit the program immediately

## disable pygame init message - "Hello from the pygame community..." ##
import contextlib
with contextlib.redirect_stdout(None):
    import pygame # used for input, audio and graphics

from random import randint

##### local imports #####
from config import *
from audio import playSoundPitch
from load_level import loadData, saveData

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
pygame.display.set_caption("Peggle Clone - Level Editor")


# play random music
r = randint(1, 10)
pygame.mixer.music.load("resources/audio/music/Peggle Beat " + str(r) + " (Peggle Deluxe).mp3")
pygame.mixer.music.play(-1)


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

# load the pegs from a level file (pickle)
#pegs = loadData()

pegs = []

##### main loop #####
while True:
    for event in pygame.event.get():  # check events and quit if the program is closed
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                pegs = []
            # save level
            if event.key == pygame.K_s:
                saveData(pegs)
            # load level
            if event.key == pygame.K_l:
                pegs = loadData()

    
    ##### update #####

    # get current mouse state
    mouseClicked = pygame.mouse.get_pressed() # get the mouse click state
    mx, my =  pygame.mouse.get_pos()  # get mouse position as 'mx' and 'my'
    mousePos = Vector(mx, my)

    #if mouse clicked, create a new ball at the mouse position
    if mouseClicked[0]:
        validNewPegPos = True
        for peg in pegs:
            if isBallTouchingPeg(mousePos.vx, mousePos.vy, peg.radius/2, peg.pos.vx, peg.pos.vy, peg.radius):
                validNewPegPos = False
                break

        if validNewPegPos:     
            newBall = Peg(mousePos.vx, mousePos.vy)
            pegs.append(newBall)
    
    # if right clicked, remove peg
    elif mouseClicked[2]:
        selectedPeg = None
        for peg in pegs:
            if isBallTouchingPeg(mousePos.vx, mousePos.vy, peg.radius, peg.pos.vx, peg.pos.vy, peg.radius):
                selectedPeg = peg
                break

        if selectedPeg != None:     
            pegs.remove(selectedPeg)

    ##### draw #####
    screen.fill((0, 0, 0))  # black screen
    screen.blit(backgroundImg, (0, 0))
    
    #draw pegs
    for p in pegs:
        screen.blit(p.pegImg, (p.pos.vx - p.posAdjust, p.pos.vy - p.posAdjust))

    # draw peg count text
    pegCount = infoFont.render("Pegs : " + str(len(pegs)), False, (5, 30, 100))
    screen.blit(pegCount, (int(WIDTH/2 - 50), 20))

    pygame.display.update()
    clock.tick(144)  # lock game framerate to 144 fps