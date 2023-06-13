import pygame

from local.config import WIDTH, HEIGHT
from local.resources import backgroundImg, menuFont, menuButtonFont, menuMusicPath, buttonHoverSound, buttonClickSound
from local.vectors import Vector
from local.audio import playSoundPitch


# this menu will serve as the point where the game and the editor can both be accessed
def mainMenu(screen: pygame.Surface):
    # play menu music
    pygame.mixer.music.load(menuMusicPath)
    pygame.mixer.music.play(-1)

    # button positions
    startButtonPos = Vector(100, 100)
    startButtonSize = Vector(100, 50)
    startButtoncolor = (0, 200, 0)
    startButtoncolorOriginal = startButtoncolor
    editorButtonPos = Vector(100, 200)
    editorButtonSize = Vector(100, 50)
    editorButtonColor = (0, 0, 200)
    editorButtonColorOriginal = editorButtonColor
    quitButtonPos = Vector(100, 300)
    quitButtonSize = Vector(100, 50)
    quitButtonColor = (200, 0, 0)
    quitButtonColorOriginal = quitButtonColor

    selection: str = "none" # this will be returned as the user selection made in the menu

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
        startButtoncolor = startButtoncolorOriginal
        if mousePos.vx > startButtonPos.vx and mousePos.vx < startButtonPos.vx + startButtonSize.vx and mousePos.vy > startButtonPos.vy and mousePos.vy < startButtonPos.vy + startButtonSize.vy:
            # mouse button is down
            if mouseDown:
                selection = "start"
                playSoundPitch(buttonClickSound)
            
            # increase the green value of the start button color
            startButtoncolor = (startButtoncolor[0], startButtoncolor[1] + 50, startButtoncolor[2])
        
        # check if mouse is over editor button
        editorButtonColor = editorButtonColorOriginal
        if mousePos.vx > editorButtonPos.vx and mousePos.vx < editorButtonPos.vx + editorButtonSize.vx and mousePos.vy > editorButtonPos.vy and mousePos.vy < editorButtonPos.vy + editorButtonSize.vy:
            # mouse button is down
            if mouseDown:
                selection = "editor"
                playSoundPitch(buttonClickSound)
            
            # increase the blue value of the editor button color
            editorButtonColor = (editorButtonColor[0], editorButtonColor[1], editorButtonColor[2] + 50)
        
        # check if mouse is over quit button
        quitButtonColor = quitButtonColorOriginal
        if mousePos.vx > quitButtonPos.vx and mousePos.vx < quitButtonPos.vx + quitButtonSize.vx and mousePos.vy > quitButtonPos.vy and mousePos.vy < quitButtonPos.vy + quitButtonSize.vy:
            # mouse button is down
            if mouseDown:
                selection = "quit"
                playSoundPitch(buttonClickSound)
            
            # increase the red value of the quit button color
            quitButtonColor = (quitButtonColor[0] + 50, quitButtonColor[1], quitButtonColor[2])


        # draw the background
        screen.blit(backgroundImg, (0, 0))

        # draw the buttons
        # start button
        pygame.draw.rect(screen, (startButtoncolor), (startButtonPos.vx, startButtonPos.vy, startButtonSize.vx, startButtonSize.vy))
        text = menuButtonFont.render("Start", True, (0, 0, 0))
        screen.blit(text, (startButtonPos.vx + (startButtonSize.vx - text.get_width()) / 2, startButtonPos.vy + (startButtonSize.vy - text.get_height()) / 2))

        # editor button
        pygame.draw.rect(screen, (editorButtonColor), (editorButtonPos.vx, editorButtonPos.vy, editorButtonSize.vx, editorButtonSize.vy))
        text = menuButtonFont.render("Editor", True, (0, 0, 0))
        screen.blit(text, (editorButtonPos.vx + (editorButtonSize.vx - text.get_width()) / 2, editorButtonPos.vy + (editorButtonSize.vy - text.get_height()) / 2))

        # quit button
        pygame.draw.rect(screen, (quitButtonColor), (quitButtonPos.vx, quitButtonPos.vy, quitButtonSize.vx, quitButtonSize.vy))
        text = menuButtonFont.render("Quit", True, (0, 0, 0))
        screen.blit(text, (quitButtonPos.vx + (quitButtonSize.vx - text.get_width()) / 2, quitButtonPos.vy + (quitButtonSize.vy - text.get_height()) / 2))

        # update display
        pygame.display.update()


        # check if the user has made a selection
        if selection != "none":
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
    