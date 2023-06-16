import pygame
import time

from local.config import WIDTH, HEIGHT, debug
from local.resources import *
from local.vectors import Vector
from local.audio import playSoundPitch

# this menu will serve as the point where the game and the editor can both be accessed
def settingsMenu(screen: pygame.Surface, debug: bool = debug):
    # play menu music
    pygame.mixer.music.load(menuMusicPath)
    pygame.mixer.music.play(-1)

    # button positions
    buttonScale = 2.5
    editorButtonSize = Vector(100*buttonScale, 50*buttonScale)
    backButtonPos = Vector(WIDTH - 50*buttonScale-20, HEIGHT - 50*buttonScale-20)
    backButtonSize = Vector(50*buttonScale, 50*buttonScale)

     # scale the button images
    menuButtonUnpressedImg = pygame.transform.scale(largeButtonUnpressedImg, (editorButtonSize.vx, editorButtonSize.vy))
    menuButtonPressedImg = pygame.transform.scale(largeButtonPressedImg, (editorButtonSize.vx, editorButtonSize.vy))
    buttonUnpressedImgScaled = pygame.transform.scale(buttonUnpressedImg, (int(50*buttonScale), int(50*buttonScale)))
    buttonPressedImgScaled = pygame.transform.scale(buttonPressedImg, (int(50*buttonScale), int(50*buttonScale)))


    selection: str = "none" # this will be returned as the user selection made in the menu

    clock = pygame.time.Clock()

    pygame.display.set_caption("PegglePy  -  Settings")

    # main loop
    while True:
        mouseDown = False
        # event handling
        for event in pygame.event.get():
            # quit if the user clicks the close button
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            # check if the mouse button is pressed (mouse button down)
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouseDown = True
            
            # check if 1 is pressed (debug)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    debug = not debug
        # update mouse posistion
        mx, my = pygame.mouse.get_pos()
        mousePos = Vector(mx, my)

        ## check mouse input
        
        # check if mouse is over back button
        if mousePos.vx > backButtonPos.vx and mousePos.vx < backButtonPos.vx + backButtonSize.vx and mousePos.vy > backButtonPos.vy and mousePos.vy < backButtonPos.vy + backButtonSize.vy:
            # mouse button is down
            if mouseDown:
                selection = "mainMenu"


        # draw the background
        screen.blit(altBackgroundImg, (0, 0))

        # draw the title
        menuTitle = menuFont.render("Settings", True, (255, 255, 255))
        screen.blit(menuTitle, (WIDTH/2 - menuTitle.get_width()/2, HEIGHT/4 - menuTitle.get_height()/2))

        # stub
        # draw a message text
        messageText = menuButtonFont.render("This menu is a stub", True, (255, 255, 255))
        screen.blit(messageText, (WIDTH/2 - messageText.get_width()/2, HEIGHT/2 - messageText.get_height()/2))

        messageText = menuButtonFont.render("Settings have not been implemented yet", True, (255, 255, 255))
        screen.blit(messageText, (WIDTH/2 - messageText.get_width()/2, HEIGHT/2 - messageText.get_height()/2 + 30))

        # draw the buttons

        # settings button (bottom right corner)
        screen.blit(buttonUnpressedImgScaled, (backButtonPos.vx, backButtonPos.vy))
        # draw the text
        backText = menuButtonFont.render("Back", True, (255, 255, 255))
        screen.blit(backText, (backButtonPos.vx + backButtonSize.vx/2 - backText.get_width()/2, backButtonPos.vy + backButtonSize.vy/2 - backText.get_height()/2))


        # debug
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



        # update display
        pygame.display.update()

        clock.tick(60)


        # check if the user has made a selection
        if selection != "none":
            playSoundPitch(buttonClickSound)
            return selection