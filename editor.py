import sys
import time  # used to exit the program immediately

import pygame  # used for input, audio and graphics

from random import randint

##### local imports #####
from local.config import *
from local.load_level import loadData, saveData
from local.collision import isBallTouchingPeg
from local.peg import Peg
from local.misc import createStaticImage, updateStaticImage
from local.trigger_events import TimedEvent
from local.audio import playSoundPitch
from local.resources import editorIconImg, backgroundImg, infoFont, warnFont, helpFont, transparentPegImg, invalidPegImg, newPegSound, invalidPegSound, debugFont

from menu import getEditorPauseScreen


## the level editor function (called from run.py via the user menu selection) ##
def levelEditor(screen: pygame.Surface, clock: pygame.time.Clock, debug: bool = debug) -> str:
    # warning timer for displaying warning messages
    warningTimer = TimedEvent()
    savedTimer = TimedEvent()

    tempPeg = Peg(0, 0)
    isRunning = True
    editorPaused = False

    pegs: list[Peg]
    pegs = []

    staticImg = createStaticImage(pegs)

    skipValidPegCheck = False
    validNewPegPos = True
    mouseOutofBounds = False

    widthBound = 35
    heightBound = 150

    pygame.display.set_caption("PegglePy  -  Level Editor")

    # play random music
    r = randint(1, 10)
    pygame.mixer.music.load(
        "resources/audio/music/Peggle Beat " + str(r) + " (Peggle Deluxe).mp3")
    pygame.mixer.music.play(-1)

    ##### main loop #####
    while isRunning:
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
                        print(
                            "WARN: Level must have at least 30 pegs before it is saved...")
                        # start the warning timer to display the message for 4 seconds
                        warningTimer.setTimer(4)
                    else:
                        saveData(pegs)
                        savedTimer.setTimer(4)
                # load level
                if event.key == pygame.K_l:
                    pegs, filePath = loadData()
                    staticImg = createStaticImage(pegs)
                if event.key == pygame.K_1:
                    debug = not debug
                if event.key == pygame.K_2:
                    skipValidPegCheck = not skipValidPegCheck
                # print all the peg positions (x,y) to the terminal
                if event.key == pygame.K_p:
                    print("Pegs:")
                    pegsPos = []
                    for peg in pegs:
                        pegsPos.append((peg.pos.vx, peg.pos.vy))
                    print(pegsPos)
                # return when the escape key is pressed
                if event.key == pygame.K_ESCAPE:
                    editorPaused = not editorPaused
            # invalid position, play sound but only on mouse click (button down event)
            if event.type == pygame.MOUSEBUTTONDOWN and mouseOutofBounds:
                if event.button == 1 and not editorPaused:
                    # play sound
                    playSoundPitch(invalidPegSound, 0.35)


         # get current mouse state
        mouseClicked = pygame.mouse.get_pressed()  # get the mouse click state
        mx, my = pygame.mouse.get_pos()  # get mouse position as 'mx' and 'my'
        mousePos = Vector(mx, my)


        ##### update #####
        if not editorPaused:
            # check if mouse is out of bounds
            mouseOutofBounds = False
            if mousePos.vy > HEIGHT - heightBound or mousePos.vy < heightBound or mousePos.vx > WIDTH - widthBound or mousePos.vx < widthBound:
                mouseOutofBounds = True

            # if mouse clicked, create a new ball at the mouse position
            if mouseClicked[0]:
                validNewPegPos = True
                if not skipValidPegCheck:
                    # check if mouse is out of bounds
                    if mouseOutofBounds:
                        validNewPegPos = False
                    # check if mouse is touching any other already existing pegs
                    else:
                        for peg in pegs:
                            if isBallTouchingPeg(mousePos.vx, mousePos.vy, peg.radius/6, peg.pos.vx, peg.pos.vy, peg.radius):
                                validNewPegPos = False
                                break

                else:
                    validNewPegPos = True
                    for peg in pegs:
                        if isBallTouchingPeg(mousePos.vx, mousePos.vy, peg.radius/6, peg.pos.vx, peg.pos.vy, peg.radius/6):
                            validNewPegPos = False
                            break

                # valid position, add peg
                if validNewPegPos:
                    newPeg = Peg(mousePos.vx, mousePos.vy)
                    pegs.append(newPeg)
                    staticImg = updateStaticImage(staticImg, newPeg)
                    # play sound
                    playSoundPitch(newPegSound, 0.35)

            # if right clicked, remove peg
            elif mouseClicked[2]:
                selectedPegs = []
                for peg in pegs:
                    if isBallTouchingPeg(mousePos.vx, mousePos.vy, peg.radius, peg.pos.vx, peg.pos.vy, peg.radius):
                        selectedPegs.append(peg)

                # remove any selected pegs
                for selectedPeg in selectedPegs:
                    pegs.remove(selectedPeg)

                if len(selectedPegs) > 0:
                    staticImg = createStaticImage(pegs)
                    # play sound
                    playSoundPitch(newPegSound, 0.55)

        ##### draw #####
        screen.blit(staticImg, (0, 0))

        # check if the mouse is in a valid position to place a peg
        # draw a sqaure bounding box to indicate the valid area
        if not editorPaused: 
            # don't draw any of this while the game is paused (its distracting)
            if mouseOutofBounds:
                pygame.draw.rect(screen, (255, 0, 0), (widthBound, heightBound,
                                WIDTH - widthBound*2, HEIGHT - heightBound*2), 2)

                # draw invalid transparent peg img (red peg)
                screen.blit(invalidPegImg, (mousePos.vx -
                            tempPeg.posAdjust, mousePos.vy - tempPeg.posAdjust))

            else:
                # draw blue transparent peg img
                screen.blit(transparentPegImg, (mousePos.vx -
                            tempPeg.posAdjust, mousePos.vy - tempPeg.posAdjust))

        # draw peg count text
        pegCountColor = (5, 30, 100)
        if len(pegs) >= 100:
            pegCountColor = (120, 30, 60)
        pegCount = infoFont.render(
            "Pegs : " + str(len(pegs)), False, pegCountColor)
        screen.blit(pegCount, (int(WIDTH/2 - 50), 20))

        # draw help text
        helpText = helpFont.render(
            "Left click to add peg, right click to remove peg", False, (255, 255, 255))
        screen.blit(helpText, (int(WIDTH-350), 10))
        helpText2 = helpFont.render("S = Save", False, (255, 255, 255))
        screen.blit(helpText2, (int(WIDTH-150), 25))
        helpText3 = helpFont.render("L = Load", False, (255, 255, 255))
        screen.blit(helpText3, (int(WIDTH-150), 40))

        if editorPaused:
            pausedScreen, pauseSelection = getEditorPauseScreen(mx, my, mouseClicked[0])
            # blit over the scree
            screen.blit(pausedScreen, (0, 0))

            if pauseSelection == "resume":
                editorPaused = False
                time.sleep(0.25)
            elif pauseSelection == "restart":
                pegs = []
                staticImg = createStaticImage(pegs)
                editorPaused = False
                time.sleep(0.15)
            elif pauseSelection == "save":
                if len(pegs) == 0 or len(pegs) < 30:
                    print(
                        "WARN: Level must have at least 30 pegs before it is saved...")
                    # start the warning timer to display the message for 4 seconds
                    warningTimer.setTimer(4)
                    time.sleep(0.15)
                else:
                    saveData(pegs)
                    editorPaused = False
                    savedTimer.setTimer(4)
            elif pauseSelection == "load":
                pegs, filePath = loadData()
                staticImg = createStaticImage(pegs)
                editorPaused = False
                time.sleep(0.15)
            elif pauseSelection == "play":
                return "play"
            elif pauseSelection == "mainMenu":
                return "mainMenu"
            elif pauseSelection == "quit":
                return "quit"

        # draw warning text
        warningTimer.update()
        if warningTimer.isActive and len(pegs) == 0:
            warningText = warnFont.render(
                "Cannot save empty level...", False, (200, 20, 25))
            screen.blit(warningText, (int(WIDTH/2 - 150), HEIGHT/2 +55))
        elif warningTimer.isActive and len(pegs) > 0 and len(pegs) < 30:
            warningText = warnFont.render(
                "Level must have at least 30 pegs...", False, (200, 20, 25))
            screen.blit(warningText, (int(WIDTH/2 - 200), HEIGHT/2 +55))

        # draw saved text
        savedTimer.update()
        if savedTimer.isActive:
            savedText = warnFont.render(
                "Level saved!", False, (20, 200, 25))
            screen.blit(savedText, (int(WIDTH/2 - 100), HEIGHT/2))

        # draw debug text
        if debug:
            if (clock.get_rawtime() < 16):  # decide whether green text or red text
                frameColor = (0, 255, 50)  # green
            else:
                frameColor = (255, 50, 0)  # red
            # print frametime
            frameTime = debugFont.render(
                str(clock.get_rawtime()) + " ms", False, (frameColor))
            screen.blit(frameTime, (5, 10))
            framesPerSec = debugFont.render(
                str(round(clock.get_fps())) + " fps", False, (255, 255, 255))
            screen.blit(framesPerSec, (5, 25))

        pygame.display.update()

        if editorPaused:
            clock.tick(60)
        else:
            clock.tick(144)  # lock game framerate to 144 fps



if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    levelEditor(screen, clock)
