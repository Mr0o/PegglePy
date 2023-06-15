import pygame
import time

from local.config import WIDTH, HEIGHT, debug
from local.resources import *
from local.vectors import Vector
from local.audio import playSoundPitch

# this menu will serve as the point where the game and the editor can both be accessed
def mainMenu(screen: pygame.Surface, debug: bool = debug):
    # play menu music
    pygame.mixer.music.load(menuMusicPath)
    pygame.mixer.music.play(-1)

    # button positions
    buttonScale = 2.5
    startButtonPos = Vector(WIDTH/2 - 50*buttonScale, HEIGHT/2 - 30*buttonScale)
    startButtonSize = Vector(100*buttonScale, 50*buttonScale)
    editorButtonPos = Vector(WIDTH/2 - 50*buttonScale, HEIGHT/2 + 30*buttonScale)
    editorButtonSize = Vector(100*buttonScale, 50*buttonScale)
    quitButtonPos = Vector(WIDTH/2 - 50*buttonScale, HEIGHT/2 + 90*buttonScale)
    quitButtonSize = Vector(100*buttonScale, 50*buttonScale)
    settingsButtonPos = Vector(WIDTH - 50*buttonScale-20, HEIGHT - 50*buttonScale-20)
    settingsButtonSize = Vector(50*buttonScale, 50*buttonScale)

     # scale the button images
    menuButtonUnpressedImg = pygame.transform.scale(largeButtonUnpressedImg, (editorButtonSize.vx, editorButtonSize.vy))
    menuButtonPressedImg = pygame.transform.scale(largeButtonPressedImg, (editorButtonSize.vx, editorButtonSize.vy))
    settingsButtonImgScaled = pygame.transform.scale(settingsButtonImg, (int(50*buttonScale), int(50*buttonScale)))

    selection: str = "none" # this will be returned as the user selection made in the menu

    clock = pygame.time.Clock()

    pygame.display.set_caption("PegglePy  -  Main Menu")

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

        # check if mouse is over start button
        if mousePos.vx > startButtonPos.vx and mousePos.vx < startButtonPos.vx + startButtonSize.vx and mousePos.vy > startButtonPos.vy and mousePos.vy < startButtonPos.vy + startButtonSize.vy:
            # mouse button is down
            if mouseDown:
                selection = "start"
        
        # check if mouse is over editor button
        if mousePos.vx > editorButtonPos.vx and mousePos.vx < editorButtonPos.vx + editorButtonSize.vx and mousePos.vy > editorButtonPos.vy and mousePos.vy < editorButtonPos.vy + editorButtonSize.vy:
            # mouse button is down
            if mouseDown:
                selection = "editor"
        
        # check if mouse is over quit button
        if mousePos.vx > quitButtonPos.vx and mousePos.vx < quitButtonPos.vx + quitButtonSize.vx and mousePos.vy > quitButtonPos.vy and mousePos.vy < quitButtonPos.vy + quitButtonSize.vy:
            # mouse button is down
            if mouseDown:
                selection = "quit"
        
        # check if mouse is over settings button
        if mousePos.vx > settingsButtonPos.vx and mousePos.vx < settingsButtonPos.vx + settingsButtonSize.vx and mousePos.vy > settingsButtonPos.vy and mousePos.vy < settingsButtonPos.vy + settingsButtonSize.vy:
            # mouse button is down
            if mouseDown:
                selection = "settings"


        # draw the background
        screen.blit(altBackgroundImg, (0, 0))

        # draw the title
        menuTitle = menuFont.render("Peggle Py", True, (255, 255, 255))
        screen.blit(menuTitle, (WIDTH/2 - menuTitle.get_width()/2, HEIGHT/4 - menuTitle.get_height()/2))

        # draw the buttons
        # start button
        if selection != "start":
            screen.blit(menuButtonUnpressedImg, (startButtonPos.vx, startButtonPos.vy))
        else:
            screen.blit(menuButtonPressedImg, (startButtonPos.vx, startButtonPos.vy))
        text = menuButtonFont.render("Start", True, (255, 255, 255))
        screen.blit(text, (startButtonPos.vx + (startButtonSize.vx - text.get_width()) / 2, startButtonPos.vy + (startButtonSize.vy - text.get_height()) / 2))

        # editor button
        if selection != "editor":
            screen.blit(menuButtonUnpressedImg, (editorButtonPos.vx, editorButtonPos.vy))
        else:
            screen.blit(menuButtonPressedImg, (editorButtonPos.vx, editorButtonPos.vy))
        text = menuButtonFont.render("Editor", True, (255, 255, 255))
        screen.blit(text, (editorButtonPos.vx + (editorButtonSize.vx - text.get_width()) / 2, editorButtonPos.vy + (editorButtonSize.vy - text.get_height()) / 2))

        # quit button
        if selection != "quit":
            screen.blit(menuButtonUnpressedImg, (quitButtonPos.vx, quitButtonPos.vy))
        else:
            screen.blit(menuButtonPressedImg, (quitButtonPos.vx, quitButtonPos.vy))
        text = menuButtonFont.render("Quit", True, (255, 255, 255))
        screen.blit(text, (quitButtonPos.vx + (quitButtonSize.vx - text.get_width()) / 2, quitButtonPos.vy + (quitButtonSize.vy - text.get_height()) / 2))

        # settings button (bottom right corner)
        screen.blit(settingsButtonImgScaled, (settingsButtonPos.vx, settingsButtonPos.vy))


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


# returns a surface of the pause screen to be overlayed on the game screen, also returns a string value to indicate a button press
def getPauseScreen(mx, my, mouseClick) -> tuple[pygame.Surface, str]:
    selection = "none"

    buttonScale = 2.5
    quitButtonPos = Vector(WIDTH/2 - 50*buttonScale, HEIGHT/2 + 90*buttonScale)
    quitButtonSize = Vector(100*buttonScale, 50*buttonScale)
    resumeButtonPos = Vector(WIDTH/2 - 50*buttonScale, HEIGHT/2 - 30*buttonScale)
    resumeButtonSize = Vector(50*buttonScale, 50*buttonScale)
    restartButtonPos = Vector(resumeButtonPos.vx + resumeButtonSize.vx, resumeButtonPos.vy+5)
    restartButtonSize = Vector(50*buttonScale-10, 50*buttonScale-15)
    # position above the quit button
    loadLevelButtonPos = Vector(quitButtonPos.vx, quitButtonPos.vy - 50*buttonScale)
    loadLevelButtonSize = Vector(100*buttonScale, 50*buttonScale)
    # main menu button (positioned bottom left corner)
    mainMenuButtonPos = Vector(10, HEIGHT - 25*buttonScale-10)
    mainMenuButtonSize = Vector(50*buttonScale, 25*buttonScale)


    # scale the button images
    menuButtonUnpressedImg = pygame.transform.scale(largeButtonUnpressedImg, (quitButtonSize.vx, quitButtonSize.vy))
    menuButtonPressedImg = pygame.transform.scale(largeButtonPressedImg, (quitButtonSize.vx, quitButtonSize.vy))
    smallMenuButtonUnpressedImg = pygame.transform.scale(buttonUnpressedImg, (int(50*buttonScale), int(50*buttonScale)))
    smallMenuButtonPressedImg = pygame.transform.scale(buttonPressedImg, (restartButtonSize.vx, restartButtonSize.vy))
    resumeButtonImg = pygame.transform.scale(startButtonImg, (int(50*buttonScale), int(50*buttonScale)))
    restartButtonImgScaled = pygame.transform.scale(restartButtonImg, (restartButtonSize.vx, restartButtonSize.vy))
    mainMenuButtonImgScaled = pygame.transform.scale(menuButtonUnpressedImg, (mainMenuButtonSize.vx, mainMenuButtonSize.vy))
    mainMenuButtonPressedImgScaled = pygame.transform.scale(menuButtonPressedImg, (mainMenuButtonSize.vx, mainMenuButtonSize.vy))

    ## check for button clicks ##
    # check if the mouse is over the resume button
    if mx > resumeButtonPos.vx and mx < resumeButtonPos.vx + resumeButtonSize.vx and my > resumeButtonPos.vy and my < resumeButtonPos.vy + resumeButtonSize.vy:
        # mouse button is down
        if mouseClick:
            selection = "resume"
            playSoundPitch(buttonClickSound)
    
    # check if the mouse is over the restart button
    if mx > restartButtonPos.vx and mx < restartButtonPos.vx + restartButtonSize.vx and my > restartButtonPos.vy and my < restartButtonPos.vy + restartButtonSize.vy:
        # mouse button is down
        if mouseClick:
            selection = "restart"
            playSoundPitch(buttonClickSound)
    
    # check if the mouse is over the load level button
    if mx > loadLevelButtonPos.vx and mx < loadLevelButtonPos.vx + loadLevelButtonSize.vx and my > loadLevelButtonPos.vy and my < loadLevelButtonPos.vy + loadLevelButtonSize.vy:
        # mouse button is down
        if mouseClick:
            selection = "load"
            playSoundPitch(buttonClickSound)

    # check if the mouse is over the quit button
    if mx > quitButtonPos.vx and mx < quitButtonPos.vx + quitButtonSize.vx and my > quitButtonPos.vy and my < quitButtonPos.vy + quitButtonSize.vy:
        # mouse button is down
        if mouseClick:
            selection = "quit"
            playSoundPitch(buttonClickSound)
        
    # check if the mouse is over the main menu button
    if mx > mainMenuButtonPos.vx and mx < mainMenuButtonPos.vx + mainMenuButtonSize.vx and my > mainMenuButtonPos.vy and my < mainMenuButtonPos.vy + mainMenuButtonSize.vy:
        # mouse button is down
        if mouseClick:
            selection = "mainMenu"
            playSoundPitch(buttonClickSound)

    # create a surface for the pause screen
    pauseScreen = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    # fill the surface with a black transparent color
    pauseScreen.fill((0, 0, 0, 100))

    # draw the text
    pauseText = menuFont.render("PAUSED", False, (255, 255, 255))
    pauseScreen.blit(pauseText, (WIDTH/2.65, HEIGHT/4))

    # draw the resume button
    if selection != "resume":
        pauseScreen.blit(resumeButtonImg, (resumeButtonPos.vx, resumeButtonPos.vy))
    else:
        pauseScreen.blit(smallMenuButtonPressedImg, (resumeButtonPos.vx, resumeButtonPos.vy))

    # draw the restart button
    if selection != "restart":
        pauseScreen.blit(restartButtonImgScaled, (restartButtonPos.vx, restartButtonPos.vy))
    else:
        pauseScreen.blit(smallMenuButtonPressedImg, (restartButtonPos.vx, restartButtonPos.vy))

    # draw the load level button
    if selection != "load":
        pauseScreen.blit(menuButtonUnpressedImg, (loadLevelButtonPos.vx, loadLevelButtonPos.vy))
    else:
        pauseScreen.blit(menuButtonPressedImg, (loadLevelButtonPos.vx, loadLevelButtonPos.vy))
    loadText = menuButtonFont.render("Load Level", False, (255, 255, 255))
    pauseScreen.blit(loadText, (loadLevelButtonPos.vx + (loadLevelButtonSize.vx - loadText.get_width()) / 2, loadLevelButtonPos.vy + (loadLevelButtonSize.vy - loadText.get_height()) / 2))

    # draw the quit button
    if selection != "quit":
        pauseScreen.blit(menuButtonUnpressedImg, (quitButtonPos.vx, quitButtonPos.vy))
    else:
        pauseScreen.blit(menuButtonPressedImg, (quitButtonPos.vx, quitButtonPos.vy))
    quitText = menuButtonFont.render("Quit", False, (255, 255, 255))
    pauseScreen.blit(quitText, (quitButtonPos.vx + (quitButtonSize.vx - quitText.get_width()) / 2, quitButtonPos.vy + (quitButtonSize.vy - quitText.get_height()) / 2))

    # draw the main menu button
    if selection != "mainMenu":
        pauseScreen.blit(mainMenuButtonImgScaled, (mainMenuButtonPos.vx, mainMenuButtonPos.vy))
    else:
        pauseScreen.blit(mainMenuButtonPressedImgScaled, (mainMenuButtonPos.vx, mainMenuButtonPos.vy))
    mainMenuText = infoFont.render("Main Menu", False, (255, 255, 255))
    pauseScreen.blit(mainMenuText, (mainMenuButtonPos.vx + (mainMenuButtonSize.vx - mainMenuText.get_width()) / 2, mainMenuButtonPos.vy + (mainMenuButtonSize.vy - mainMenuText.get_height()) / 2))

    # return the surface
    return pauseScreen, selection
    

# returns a surface of the editor pause screen to be overlayed on the editor screen, also returns a string value to indicate a button press
def getEditorPauseScreen(mx, my, mouseClick) -> tuple[pygame.Surface, str]:
    selection = "none"

    buttonScale = 2.5
    quitButtonPos = Vector(WIDTH/2 - 50*buttonScale, HEIGHT/2 + 90*buttonScale)
    quitButtonSize = Vector(100*buttonScale, 50*buttonScale)
    resumeButtonPos = Vector(WIDTH/2 - 50*buttonScale, HEIGHT/2 - 30*buttonScale)
    resumeButtonSize = Vector(50*buttonScale, 50*buttonScale)
    restartButtonPos = Vector(resumeButtonPos.vx + resumeButtonSize.vx, resumeButtonPos.vy+5)
    restartButtonSize = Vector(50*buttonScale-10, 50*buttonScale-15)
    # position above the quit button
    loadLevelButtonPos = Vector(quitButtonPos.vx, quitButtonPos.vy - 50*buttonScale)
    loadLevelButtonSize = Vector(100*buttonScale, 50*buttonScale)
    # main menu button (positioned bottom left corner)
    mainMenuButtonPos = Vector(10, HEIGHT - 25*buttonScale-10)
    mainMenuButtonSize = Vector(50*buttonScale, 25*buttonScale)


    # scale the button images
    menuButtonUnpressedImg = pygame.transform.scale(largeButtonUnpressedImg, (quitButtonSize.vx, quitButtonSize.vy))
    menuButtonPressedImg = pygame.transform.scale(largeButtonPressedImg, (quitButtonSize.vx, quitButtonSize.vy))
    smallMenuButtonUnpressedImg = pygame.transform.scale(buttonUnpressedImg, (int(50*buttonScale), int(50*buttonScale)))
    smallMenuButtonPressedImg = pygame.transform.scale(buttonPressedImg, (restartButtonSize.vx, restartButtonSize.vy))
    resumeButtonImg = pygame.transform.scale(startButtonImg, (int(50*buttonScale), int(50*buttonScale)))
    restartButtonImgScaled = pygame.transform.scale(restartButtonImg, (restartButtonSize.vx, restartButtonSize.vy))
    mainMenuButtonImgScaled = pygame.transform.scale(menuButtonUnpressedImg, (mainMenuButtonSize.vx, mainMenuButtonSize.vy))
    mainMenuButtonPressedImgScaled = pygame.transform.scale(menuButtonPressedImg, (mainMenuButtonSize.vx, mainMenuButtonSize.vy))

    ## check for button clicks ##
    # check if the mouse is over the resume button
    if mx > resumeButtonPos.vx and mx < resumeButtonPos.vx + resumeButtonSize.vx and my > resumeButtonPos.vy and my < resumeButtonPos.vy + resumeButtonSize.vy:
        # mouse button is down
        if mouseClick:
            selection = "resume"
            playSoundPitch(buttonClickSound)
    
    # check if the mouse is over the restart button
    if mx > restartButtonPos.vx and mx < restartButtonPos.vx + restartButtonSize.vx and my > restartButtonPos.vy and my < restartButtonPos.vy + restartButtonSize.vy:
        # mouse button is down
        if mouseClick:
            selection = "restart"
            playSoundPitch(buttonClickSound)
    
    # check if the mouse is over the load level button
    if mx > loadLevelButtonPos.vx and mx < loadLevelButtonPos.vx + loadLevelButtonSize.vx and my > loadLevelButtonPos.vy and my < loadLevelButtonPos.vy + loadLevelButtonSize.vy:
        # mouse button is down
        if mouseClick:
            selection = "load"
            playSoundPitch(buttonClickSound)

    # check if the mouse is over the quit button
    if mx > quitButtonPos.vx and mx < quitButtonPos.vx + quitButtonSize.vx and my > quitButtonPos.vy and my < quitButtonPos.vy + quitButtonSize.vy:
        # mouse button is down
        if mouseClick:
            selection = "quit"
            playSoundPitch(buttonClickSound)
        
    # check if the mouse is over the main menu button
    if mx > mainMenuButtonPos.vx and mx < mainMenuButtonPos.vx + mainMenuButtonSize.vx and my > mainMenuButtonPos.vy and my < mainMenuButtonPos.vy + mainMenuButtonSize.vy:
        # mouse button is down
        if mouseClick:
            selection = "mainMenu"
            playSoundPitch(buttonClickSound)

    # create a surface for the pause screen
    pauseScreen = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    # fill the surface with a black transparent color
    pauseScreen.fill((0, 0, 0, 100))

    # draw the text
    pauseText = menuFont.render("PAUSED", False, (255, 255, 255))
    pauseScreen.blit(pauseText, (WIDTH/2.65, HEIGHT/4))

    # draw the resume button
    if selection != "resume":
        pauseScreen.blit(resumeButtonImg, (resumeButtonPos.vx, resumeButtonPos.vy))
    else:
        pauseScreen.blit(smallMenuButtonPressedImg, (resumeButtonPos.vx, resumeButtonPos.vy))

    # draw the restart button
    if selection != "restart":
        pauseScreen.blit(restartButtonImgScaled, (restartButtonPos.vx, restartButtonPos.vy))
    else:
        pauseScreen.blit(smallMenuButtonPressedImg, (restartButtonPos.vx, restartButtonPos.vy))

    # draw the load level button
    if selection != "load":
        pauseScreen.blit(menuButtonUnpressedImg, (loadLevelButtonPos.vx, loadLevelButtonPos.vy))
    else:
        pauseScreen.blit(menuButtonPressedImg, (loadLevelButtonPos.vx, loadLevelButtonPos.vy))
    loadText = menuButtonFont.render("Load Level", False, (255, 255, 255))
    pauseScreen.blit(loadText, (loadLevelButtonPos.vx + (loadLevelButtonSize.vx - loadText.get_width()) / 2, loadLevelButtonPos.vy + (loadLevelButtonSize.vy - loadText.get_height()) / 2))

    # draw the quit button
    if selection != "quit":
        pauseScreen.blit(menuButtonUnpressedImg, (quitButtonPos.vx, quitButtonPos.vy))
    else:
        pauseScreen.blit(menuButtonPressedImg, (quitButtonPos.vx, quitButtonPos.vy))
    quitText = menuButtonFont.render("Quit", False, (255, 255, 255))
    pauseScreen.blit(quitText, (quitButtonPos.vx + (quitButtonSize.vx - quitText.get_width()) / 2, quitButtonPos.vy + (quitButtonSize.vy - quitText.get_height()) / 2))

    # draw the main menu button
    if selection != "mainMenu":
        pauseScreen.blit(mainMenuButtonImgScaled, (mainMenuButtonPos.vx, mainMenuButtonPos.vy))
    else:
        pauseScreen.blit(mainMenuButtonPressedImgScaled, (mainMenuButtonPos.vx, mainMenuButtonPos.vy))
    mainMenuText = infoFont.render("Main Menu", False, (255, 255, 255))
    pauseScreen.blit(mainMenuText, (mainMenuButtonPos.vx + (mainMenuButtonSize.vx - mainMenuText.get_width()) / 2, mainMenuButtonPos.vy + (mainMenuButtonSize.vy - mainMenuText.get_height()) / 2))

    # return the surface
    return pauseScreen, selection