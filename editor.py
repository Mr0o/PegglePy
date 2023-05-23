import sys # used to exit the program immediately

## disable pygame init message - "Hello from the pygame community..." ##
import contextlib
with contextlib.redirect_stdout(None):
    import pygame # used for input, audio and graphics

from random import randint

##### local imports #####
from local.config import *
from local.load_level import loadData, saveData

from local.collision import isBallTouchingPeg

from local.peg import Peg

from local.misc import createStaticImage, updateStaticImage

from local.trigger_events import TimedEvent

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
helpFont = pygame.font.Font("resources/fonts/Evogria.otf", 14)
warnFont = pygame.font.Font("resources/fonts/Evogria.otf", 25)

# pegs img with transparency (for mouse hover and invalid peg placement (red))
tempPeg = Peg(0, 0)
transparentPegImg = tempPeg.pegImg.copy()
# set alpha to 50
transparentPegImg.fill((255, 255, 255, 50), None, pygame.BLEND_RGBA_MULT)

# create a second copy of the peg image, but with a red tint
invalidPegImg = tempPeg.pegImg.copy()
invalidPegImg.fill((255, 0, 0, 60), None, pygame.BLEND_RGBA_MULT)

# warning timer for displaying warning messages
warningTimer = TimedEvent()

##### drawing functions #####
def drawCircle(x, y, rad, rgb):
    pygame.draw.circle(screen, (rgb), [x, y], rad)

def drawLine(x1,y1,x2,y2):
    pygame.draw.line(screen, (255, 0, 0),[x1, y1],[x2,y2])

debugCollision = False
skipValidPegCheck = False

# load the pegs from a level file (pickle)
#pegs = loadData()
pegs : list[Peg]
pegs = []

widthBound = 35
heightBound = 150

debug = True

staticImg = createStaticImage(pegs)

##### main loop #####
while True:
    for event in pygame.event.get():  # check events and quit if the program is closed
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                pegs = []
                staticImg = createStaticImage(pegs)
            # save level
            if event.key == pygame.K_s:
                if len(pegs) == 0 or len(pegs) < 30:
                    print("WARN: Level must have at least 30 pegs before it is saved...")
                    # start the warning timer to display the message for 4 seconds
                    warningTimer.setTimer(4)
                else:
                    saveData(pegs)
            # load level
            if event.key == pygame.K_l:
                pegs = loadData()
                staticImg = createStaticImage(pegs)
            if event.key == pygame.K_1:
                skipValidPegCheck = not skipValidPegCheck
            if event.key == pygame.K_p: # print all the peg positions (x,y) to the terminal
                print("Pegs:")
                pegsPos = []
                for peg in pegs:
                    pegsPos.append((peg.pos.vx, peg.pos.vy))
                print(pegsPos)

    
    ##### update #####

    # get current mouse state
    mouseClicked = pygame.mouse.get_pressed() # get the mouse click state
    mx, my =  pygame.mouse.get_pos()  # get mouse position as 'mx' and 'my'
    mousePos = Vector(mx, my)

    #if mouse clicked, create a new ball at the mouse position
    if mouseClicked[0]:
        validNewPegPos = True
        if not skipValidPegCheck:
            # check if the mouse is in a valid position to place a peg
            if mousePos.vy > HEIGHT - heightBound or mousePos.vy < heightBound or mousePos.vx > WIDTH - widthBound or mousePos.vx < widthBound:
                validNewPegPos = False
            else:
                for peg in pegs:
                    if  isBallTouchingPeg(mousePos.vx, mousePos.vy, peg.radius/6, peg.pos.vx, peg.pos.vy, peg.radius):
                        validNewPegPos = False
                        break
        
        else:
            validNewPegPos = True
            for peg in pegs:
                if  isBallTouchingPeg(mousePos.vx, mousePos.vy, peg.radius/6, peg.pos.vx, peg.pos.vy, peg.radius/6):
                    validNewPegPos = False
                    break

        
        # valid position, add peg
        if validNewPegPos:     
            newPeg = Peg(mousePos.vx, mousePos.vy)
            pegs.append(newPeg)
            staticImg = updateStaticImage(staticImg, newPeg)
    
    # if right clicked, remove peg
    elif mouseClicked[2]:
        selectedPegs = []
        for peg in pegs:
            if isBallTouchingPeg(mousePos.vx, mousePos.vy, peg.radius, peg.pos.vx, peg.pos.vy, peg.radius):
                selectedPegs.append(peg)
        
        #remove any selected pegs
        for selectedPeg in selectedPegs:     
            pegs.remove(selectedPeg)

        if len(selectedPegs) > 0:
            staticImg = createStaticImage(pegs)
        
        

    ##### draw #####
    screen.blit(staticImg, (0, 0))

    # check if the mouse is in a valid position to place a peg
    # draw a red line across the screen to indicate that bounds
    if mousePos.vy > HEIGHT - heightBound:
        drawLine(0, HEIGHT-heightBound, WIDTH, HEIGHT-heightBound)
        # draw red invalid peg
        screen.blit(invalidPegImg, (mousePos.vx - tempPeg.posAdjust, mousePos.vy - tempPeg.posAdjust))
    elif mousePos.vy < heightBound:
        drawLine(0, heightBound, WIDTH, heightBound)
        # draw red invalid peg
        screen.blit(invalidPegImg, (mousePos.vx - tempPeg.posAdjust, mousePos.vy - tempPeg.posAdjust))
    elif mousePos.vx > WIDTH - widthBound:
        drawLine(WIDTH-widthBound, 0, WIDTH-widthBound, HEIGHT)
        # draw red invalid peg
        screen.blit(invalidPegImg, (mousePos.vx - tempPeg.posAdjust, mousePos.vy - tempPeg.posAdjust))
    elif mousePos.vx < widthBound:
        drawLine(widthBound, 0, widthBound, HEIGHT)
        # draw red invalid peg
        screen.blit(invalidPegImg, (mousePos.vx - tempPeg.posAdjust, mousePos.vy - tempPeg.posAdjust))
    else: # its a valid position
        # draw transparent peg
        screen.blit(transparentPegImg, (mousePos.vx - tempPeg.posAdjust, mousePos.vy - tempPeg.posAdjust))

    # draw peg count text
    pegCountColor = (5, 30, 100)
    if len(pegs) >= 100:
        pegCountColor = (120, 30, 60)
    pegCount = infoFont.render("Pegs : " + str(len(pegs)), False, pegCountColor)
    screen.blit(pegCount, (int(WIDTH/2 - 50), 20))

    # draw help text
    helpText = helpFont.render("Left click to add peg, right click to remove peg", False, (255,255,255))
    screen.blit(helpText, (int(WIDTH-350), 10))
    helpText2 = helpFont.render("S = Save", False, (255,255,255))
    screen.blit(helpText2, (int(WIDTH-150), 25))
    helpText3 = helpFont.render("L = Load", False, (255,255,255))
    screen.blit(helpText3, (int(WIDTH-150), 40))

    # draw warning text
    warningTimer.update()
    if warningTimer.isActive and len(pegs) == 0:
        warningText = warnFont.render("Cannot save empty level...", False, (200,20,25))
        screen.blit(warningText, (int(WIDTH/2 - 150), HEIGHT/2))
    elif warningTimer.isActive and len(pegs) > 0 and len(pegs) < 30:
        warningText = warnFont.render("Level must have at least 30 pegs...", False, (200,20,25))
        screen.blit(warningText, (int(WIDTH/2 - 200), HEIGHT/2))


    pygame.display.update()
    clock.tick(144)  # lock game framerate to 144 fps