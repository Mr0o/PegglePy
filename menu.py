import pygame

from local.config import WIDTH, HEIGHT
from local.resources import *
from local.vectors import Vector
from local.audio import playSoundPitch


# this menu will serve as the point where the game and the editor can both be accessed
def mainMenu(screen: pygame.Surface):
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

    selection: str = "none" # this will be returned as the user selection made in the menu

    # scale the button images
    menuButtonUnpressedImg = pygame.transform.scale(largeButtonUnpressedImg, (editorButtonSize.vx, editorButtonSize.vy))
    menuButtonPressedImg = pygame.transform.scale(largeButtonPressedImg, (editorButtonSize.vx, editorButtonSize.vy))
    settingsButtonImgScaled = pygame.transform.scale(settingsButtonImg, (int(50*buttonScale), int(50*buttonScale)))

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
        screen.blit(backgroundImg, (0, 0))

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


        # update display
        pygame.display.update()


        # check if the user has made a selection
        if selection != "none":
            playSoundPitch(buttonClickSound)
            return selection


# returns a surface of the pause screen to be overlayed on the game screen, also returns a boolean value to indicate a button press
def getPauseScreen(mx, my, mouseClick) -> tuple[pygame.Surface, str]:
    selection = "none"

    # create a surface for the pause screen
    pauseScreen = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    # fill the surface with a black transparent color
    pauseScreen.fill((0, 0, 0, 100))

    # draw the text
    pauseText = menuFont.render("PAUSED", False, (255, 255, 255))
    pauseScreen.blit(pauseText, (WIDTH/2.65, HEIGHT/4))

    # draw the resume button
    resumeButton = pygame.Rect(WIDTH/2.5 + 150, HEIGHT/3, 100, 50)
    pygame.draw.rect(pauseScreen, (0, 200, 0), resumeButton)
    resumeText = menuButtonFont.render("Resume", False, (0, 0, 0))
    pauseScreen.blit(resumeText, (resumeButton.x + (resumeButton.width - resumeText.get_width()) / 2, resumeButton.y + (resumeButton.height - resumeText.get_height()) / 2))

    # draw the quit button
    quitButton = pygame.Rect(WIDTH/2.5 + 150, HEIGHT/2 - 60, 100, 50)
    pygame.draw.rect(pauseScreen, (200, 0, 0), quitButton)
    quitText = menuButtonFont.render("Quit", False, (0, 0, 0))
    pauseScreen.blit(quitText, (quitButton.x + (quitButton.width - quitText.get_width()) / 2, quitButton.y + (quitButton.height - quitText.get_height()) / 2))


    ## check for button clicks ##
    # check if the mouse is over the resume button
    if mx > resumeButton.x and mx < resumeButton.x + resumeButton.width and my > resumeButton.y and my < resumeButton.y + resumeButton.height:
        # mouse button is down
        if mouseClick:
            selection = "resume"
            playSoundPitch(buttonClickSound)

    if mx > quitButton.x and mx < quitButton.x + quitButton.width and my > quitButton.y and my < quitButton.y + quitButton.height:
        # mouse button is down
        if mouseClick:
            selection = "quit"
            playSoundPitch(buttonClickSound)

    # return the surface
    return pauseScreen, selection
    