import pygame
import time
import webbrowser # for opening github page

from local.config import configs
from local.resources import menuMusicPath, buttonClickSound, largeButtonUnpressedImg, largeButtonPressedImg, settingsButtonImg, startButtonImg, buttonUnpressedImg, buttonPressedImg
from local.resources import restartButtonImg, buttonPressedImg, buttonUnpressedImg
from local.resources import altBackgroundImg as altBgImg
from local.resources import menuFont, menuButtonFont, infoFont, debugFont
from local.resources import buttonClickSound
from local.vectors import Vector
from local.audio import playSoundPitch

# this menu will serve as the point where the game and the editor can both be accessed
def mainMenu(screen: pygame.Surface):
    # play menu music
    pygame.mixer.music.load(menuMusicPath)
    if configs["MUSIC_ENABLED"]:
        pygame.mixer.music.play(-1)
        pygame.mixer.music.set_volume(configs["MUSIC_VOLUME"])

    # button positions
    buttonScale = 2.5
    startButtonPos = Vector(configs["WIDTH"]/2 - 50*buttonScale, configs["HEIGHT"]/2 - 30*buttonScale)
    startButtonSize = Vector(100*buttonScale, 50*buttonScale)
    editorButtonPos = Vector(configs["WIDTH"]/2 - 50*buttonScale, configs["HEIGHT"]/2 + 30*buttonScale)
    editorButtonSize = Vector(100*buttonScale, 50*buttonScale)
    quitButtonPos = Vector(configs["WIDTH"]/2 - 50*buttonScale, configs["HEIGHT"]/2 + 90*buttonScale)
    quitButtonSize = Vector(100*buttonScale, 50*buttonScale)
    settingsButtonPos = Vector(configs["WIDTH"] - 50*buttonScale-20, configs["HEIGHT"] - 50*buttonScale-20)
    settingsButtonSize = Vector(50*buttonScale, 50*buttonScale)

     # scale the button images
    menuButtonUnpressedImg = pygame.transform.scale(largeButtonUnpressedImg, (editorButtonSize.x, editorButtonSize.y))
    menuButtonPressedImg = pygame.transform.scale(largeButtonPressedImg, (editorButtonSize.x, editorButtonSize.y))
    settingsButtonImgScaled = pygame.transform.scale(settingsButtonImg, (int(50*buttonScale), int(50*buttonScale)))

    # 'highlighted' versions of the buttons
    menuButtonUnpressedImgHighlighted = menuButtonUnpressedImg.copy()
    # add blue tint to the image
    menuButtonUnpressedImgHighlighted.fill((205, 205, 255, 255), None, pygame.BLEND_RGBA_MULT)

    selection: str = "none" # this will be returned as the user selection made in the menu

    # controller variables
    controllerConnected = False
    moveControllerSelector = None
    controllerMenuSelectionIndex = -1

    clock = pygame.time.Clock()

    pygame.display.set_caption("PegglePy  -  Main Menu")

    # main loop
    while True:
        mouseDown = False
        selectButtonPressed = False
        backButtonPressed = False
        dpadDirection = None
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
                    configs["DEBUG_MODE"] = not configs["DEBUG_MODE"]

                    # check for gamepad dpad buttons
            if event.type == pygame.JOYHATMOTION:
                if event.value == (0, 1):
                    dpadDirection = "up"
                if event.value == (0, -1):
                    dpadDirection = "down"

            if event.type == pygame.JOYBUTTONDOWN:
                # if the controller is a 'sony' or 'playstation' controller (Sometimes "Wireless Controller" is the name of the ps4 controller, so we will include that as well)
                if joystick.get_name().lower().find("sony") != -1 or joystick.get_name().lower().find("playstation") != -1 or joystick.get_name().lower().find("wireless") != -1:
                    if event.button == 0:  # the 'X'/cross button on a ps4 controller
                        selectButtonPressed = True
                    if event.button == 1:  # the 'O'/circle button on a ps4 controller
                        backButtonPressed = True
                    if event.button == 8:  # the 'share' button on a ps4 controller
                        # enable or disable debug
                        configs["DEBUG_MODE"] = not configs["DEBUG_MODE"]

                else:  # xbox controller (default)
                    if event.button == 0:  # the 'A' button on an xbox controller
                        selectButtonPressed = True
                    if event.button == 1:  # the 'B' button on an xbox controller
                        backButtonPressed = True
                    if event.button == 6:  # the 'start' button on an xbox controller
                        configs["DEBUG_MODE"] = not configs["DEBUG_MODE"]

        # check for joystick input
        previousControllerSelector = moveControllerSelector
        moveControllerSelector = None
        if pygame.joystick.get_count() > 0:
            # connect to the first controller
            joystick = pygame.joystick.Joystick(0)
            joystick.init()

            # 1 is the Y axis on the left joystick (at least on xbox controllers)
            joystickY = joystick.get_axis(1)

            # check if the joystick is moved up or down
            if joystickY < -0.5:
                controllerConnected = True
                moveControllerSelector = "up"
            if joystickY > 0.5:
                controllerConnected = True
                moveControllerSelector = "down"

            # set dpad direction to move controller selector
            if dpadDirection == "up":
                controllerConnected = True
                moveControllerSelector = "up"
            if dpadDirection == "down":
                controllerConnected = True
                moveControllerSelector = "down"
        else:
            # no controller connected
            controllerConnected = False

        if pygame.mouse.get_rel() != (0, 0):
            controllerConnected = False
            # unhide the mouse cursor
            pygame.mouse.set_visible(True)

        if controllerConnected:
            # hide the mouse cursor
            pygame.mouse.set_visible(False)

            # handle up or down events
            if moveControllerSelector == "up" and previousControllerSelector != "up":
                controllerMenuSelectionIndex -= 1
            if moveControllerSelector == "down" and previousControllerSelector != "down":
                controllerMenuSelectionIndex += 1

            # wrap the index around
            if controllerMenuSelectionIndex < 0:
                controllerMenuSelectionIndex = 3
            elif controllerMenuSelectionIndex > 2:
                controllerMenuSelectionIndex = 0

            # if the select button is pressed
            if selectButtonPressed:
                if controllerMenuSelectionIndex == 0:
                    selection = "start"
                if controllerMenuSelectionIndex == 1:
                    selection = "editor"
                if controllerMenuSelectionIndex == 2:
                    selection = "quit"
        else:
            # update mouse posistion
            mx, my = pygame.mouse.get_pos()
            mousePos = Vector(mx, my)

        ## check mouse input
        if not controllerConnected:
            # check if mouse is over start button
            if mousePos.x > startButtonPos.x and mousePos.x < startButtonPos.x + startButtonSize.x and mousePos.y > startButtonPos.y and mousePos.y < startButtonPos.y + startButtonSize.y:
                # mouse button is down
                if mouseDown:
                    selection = "start"
            
            # check if mouse is over editor button
            if mousePos.x > editorButtonPos.x and mousePos.x < editorButtonPos.x + editorButtonSize.x and mousePos.y > editorButtonPos.y and mousePos.y < editorButtonPos.y + editorButtonSize.y:
                # mouse button is down
                if mouseDown:
                    selection = "editor"
            
            # check if mouse is over quit button
            if mousePos.x > quitButtonPos.x and mousePos.x < quitButtonPos.x + quitButtonSize.x and mousePos.y > quitButtonPos.y and mousePos.y < quitButtonPos.y + quitButtonSize.y:
                # mouse button is down
                if mouseDown:
                    selection = "quit"
            
            # check if mouse is over settings button
            if mousePos.x > settingsButtonPos.x and mousePos.x < settingsButtonPos.x + settingsButtonSize.x and mousePos.y > settingsButtonPos.y and mousePos.y < settingsButtonPos.y + settingsButtonSize.y:
                # mouse button is down
                if mouseDown:
                    selection = "settings"


        # draw the background
        altBackgroundImg = pygame.transform.scale(altBgImg, (configs["WIDTH"], configs["HEIGHT"]))
        screen.blit(altBackgroundImg, (0, 0))

        # draw the title
        menuTitle = menuFont.render("Peggle Py", True, (255, 255, 255))
        screen.blit(menuTitle, (configs["WIDTH"]/2 - menuTitle.get_width()/2, configs["HEIGHT"]/4 - menuTitle.get_height()/2))

        # draw the buttons
        # start button
        if selection != "start":
            if controllerConnected and controllerMenuSelectionIndex == 0:
                screen.blit(menuButtonUnpressedImgHighlighted, (startButtonPos.x, startButtonPos.y))
            else:
                screen.blit(menuButtonUnpressedImg, (startButtonPos.x, startButtonPos.y))
        else:
            screen.blit(menuButtonPressedImg, (startButtonPos.x, startButtonPos.y))
        text = menuButtonFont.render("Start", True, (255, 255, 255))
        screen.blit(text, (startButtonPos.x + (startButtonSize.x - text.get_width()) / 2, startButtonPos.y + (startButtonSize.y - text.get_height()) / 2))

        # editor button
        if selection != "editor":
            if controllerConnected and controllerMenuSelectionIndex == 1:
                screen.blit(menuButtonUnpressedImgHighlighted, (editorButtonPos.x, editorButtonPos.y))
            else:
                screen.blit(menuButtonUnpressedImg, (editorButtonPos.x, editorButtonPos.y))
        else:
            screen.blit(menuButtonPressedImg, (editorButtonPos.x, editorButtonPos.y))
        text = menuButtonFont.render("Editor", True, (255, 255, 255))
        screen.blit(text, (editorButtonPos.x + (editorButtonSize.x - text.get_width()) / 2, editorButtonPos.y + (editorButtonSize.y - text.get_height()) / 2))

        # quit button
        if selection != "quit":
            if controllerConnected and controllerMenuSelectionIndex == 2:
                screen.blit(menuButtonUnpressedImgHighlighted, (quitButtonPos.x, quitButtonPos.y))
            else:
                screen.blit(menuButtonUnpressedImg, (quitButtonPos.x, quitButtonPos.y))
        else:
            screen.blit(menuButtonPressedImg, (quitButtonPos.x, quitButtonPos.y))
        text = menuButtonFont.render("Quit", True, (255, 255, 255))
        screen.blit(text, (quitButtonPos.x + (quitButtonSize.x - text.get_width()) / 2, quitButtonPos.y + (quitButtonSize.y - text.get_height()) / 2))

        # settings button (bottom right corner)
        screen.blit(settingsButtonImgScaled, (settingsButtonPos.x, settingsButtonPos.y))

        # github link (top right corner)
        # if the mouse is over the github link, change the color
        githubText = infoFont.render("Github: Mr0o", True, (255, 255, 255))
        if mousePos.x > configs["WIDTH"] - githubText.get_width() - 10 and mousePos.x < configs["WIDTH"] - 10 and mousePos.y > 10 and mousePos.y < 10 + githubText.get_height():
            # if clicked, open the github page
            if mouseDown:
                try:
                    webbrowser.open("https://github.com/Mr0o/PegglePy")
                except Exception:
                    print("webbrowser.open() failed")
                    print("Error: ", Exception)
            githubText = infoFont.render("Github: Mr0o", True, (0, 255, 255))
            # draw a blue line under the text
            pygame.draw.line(screen, (0, 255, 255), (configs["WIDTH"] - githubText.get_width() - 10, 10 + githubText.get_height()), (configs["WIDTH"] - 10, 10 + githubText.get_height()), 2)
        else:
            githubText = infoFont.render("Github: Mr0o", True, (255, 255, 255))
            # draw a white line under the text
            pygame.draw.line(screen, (255, 255, 255), (configs["WIDTH"] - githubText.get_width() - 10, 10 + githubText.get_height()), (configs["WIDTH"] - 10, 10 + githubText.get_height()), 2)
        screen.blit(githubText, (configs["WIDTH"] - githubText.get_width() - 10, 10))


        # debug
        if configs["DEBUG_MODE"]:
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

        clock.tick(configs["REFRESH_RATE"])


        # check if the user has made a selection
        if selection != "none":
            if configs["SOUND_ENABLED"]:
                playSoundPitch(buttonClickSound)
            return selection


# returns a surface of the pause screen to be overlayed on the game screen, also returns a string value to indicate a button press
def getPauseScreen(mx, my, mouseClick) -> tuple[pygame.Surface, str]:
    selection = "none"

    buttonScale = 2.5
    quitButtonPos = Vector(configs["WIDTH"]/2 - 50*buttonScale, configs["HEIGHT"]/2 + 90*buttonScale+40)
    quitButtonSize = Vector(100*buttonScale, 50*buttonScale)
    resumeButtonPos = Vector(configs["WIDTH"]/2 - 50*buttonScale, configs["HEIGHT"]/2 - 30*buttonScale)
    resumeButtonSize = Vector(50*buttonScale, 50*buttonScale)
    restartButtonPos = Vector(resumeButtonPos.x + resumeButtonSize.x, resumeButtonPos.y+5)
    restartButtonSize = Vector(50*buttonScale-10, 50*buttonScale-15)
    # position above the quit button
    loadLevelButtonPos = Vector(quitButtonPos.x, quitButtonPos.y - 50*buttonScale)
    loadLevelButtonSize = Vector(100*buttonScale, 50*buttonScale)
    # main menu button (positioned bottom left corner)
    mainMenuButtonPos = Vector(10, configs["HEIGHT"] - 25*buttonScale-10)
    mainMenuButtonSize = Vector(50*buttonScale, 25*buttonScale)
    # editor button (positioned bottom left corner above the main menu button)
    editorButtonSize = Vector(50*buttonScale, 25*buttonScale)
    editorButtonPos = Vector(mainMenuButtonPos.x, mainMenuButtonPos.y - editorButtonSize.y - 5)
    # settings button (positioned bottom right corner)
    settingsButtonPos = Vector(configs["WIDTH"] - 50*buttonScale-20, configs["HEIGHT"] - 50*buttonScale-20)
    settingsButtonSize = Vector(50*buttonScale, 50*buttonScale)


    # scale the button images
    menuButtonUnpressedImg = pygame.transform.scale(largeButtonUnpressedImg, (quitButtonSize.x, quitButtonSize.y))
    menuButtonPressedImg = pygame.transform.scale(largeButtonPressedImg, (quitButtonSize.x, quitButtonSize.y))
    smallMenuButtonUnpressedImg = pygame.transform.scale(buttonUnpressedImg, (int(50*buttonScale), int(50*buttonScale)))
    smallMenuButtonPressedImg = pygame.transform.scale(buttonPressedImg, (restartButtonSize.x, restartButtonSize.y))
    resumeButtonImg = pygame.transform.scale(startButtonImg, (int(50*buttonScale), int(50*buttonScale)))
    restartButtonImgScaled = pygame.transform.scale(restartButtonImg, (restartButtonSize.x, restartButtonSize.y))
    mainMenuButtonImgScaled = pygame.transform.scale(menuButtonUnpressedImg, (mainMenuButtonSize.x, mainMenuButtonSize.y))
    mainMenuButtonPressedImgScaled = pygame.transform.scale(menuButtonPressedImg, (mainMenuButtonSize.x, mainMenuButtonSize.y))
    settingsButtonImgScaled = pygame.transform.scale(settingsButtonImg, (settingsButtonSize.x, settingsButtonSize.y))

    ## check for button clicks ##
    # check if the mouse is over the resume button
    if mx > resumeButtonPos.x and mx < resumeButtonPos.x + resumeButtonSize.x and my > resumeButtonPos.y and my < resumeButtonPos.y + resumeButtonSize.y:
        # mouse button is down
        if mouseClick:
            selection = "resume"
            if configs["SOUND_ENABLED"]:
                playSoundPitch(buttonClickSound)
    
    # check if the mouse is over the restart button
    if mx > restartButtonPos.x and mx < restartButtonPos.x + restartButtonSize.x and my > restartButtonPos.y and my < restartButtonPos.y + restartButtonSize.y:
        # mouse button is down
        if mouseClick:
            selection = "restart"
            if configs["SOUND_ENABLED"]:
                playSoundPitch(buttonClickSound)
    
    # check if the mouse is over the load level button
    if mx > loadLevelButtonPos.x and mx < loadLevelButtonPos.x + loadLevelButtonSize.x and my > loadLevelButtonPos.y and my < loadLevelButtonPos.y + loadLevelButtonSize.y:
        # mouse button is down
        if mouseClick:
            selection = "load"
            if configs["SOUND_ENABLED"]:
                playSoundPitch(buttonClickSound)

    # check if the mouse is over the quit button
    if mx > quitButtonPos.x and mx < quitButtonPos.x + quitButtonSize.x and my > quitButtonPos.y and my < quitButtonPos.y + quitButtonSize.y:
        # mouse button is down
        if mouseClick:
            selection = "quit"
            if configs["SOUND_ENABLED"]:
                playSoundPitch(buttonClickSound)
        
    # check if the mouse is over the main menu button
    if mx > mainMenuButtonPos.x and mx < mainMenuButtonPos.x + mainMenuButtonSize.x and my > mainMenuButtonPos.y and my < mainMenuButtonPos.y + mainMenuButtonSize.y:
        # mouse button is down
        if mouseClick:
            selection = "mainMenu"
            if configs["SOUND_ENABLED"]:
                playSoundPitch(buttonClickSound)
    
    # check if the mouse is over the editor button
    if mx > editorButtonPos.x and mx < editorButtonPos.x + editorButtonSize.x and my > editorButtonPos.y and my < editorButtonPos.y + editorButtonSize.y:
        # mouse button is down
        if mouseClick:
            selection = "editor"
            if configs["SOUND_ENABLED"]:
                playSoundPitch(buttonClickSound)
                
    # check if the mouse is over the settings button
    if mx > settingsButtonPos.x and mx < settingsButtonPos.x + settingsButtonSize.x and my > settingsButtonPos.y and my < settingsButtonPos.y + settingsButtonSize.y:
        # mouse button is down
        if mouseClick:
            selection = "settings"
            
            

    # create a surface for the pause screen
    pauseScreen = pygame.Surface((configs["WIDTH"], configs["HEIGHT"]), pygame.SRCALPHA)
    # fill the surface with a black transparent color
    pauseScreen.fill((0, 0, 0, 100))

    # draw the text
    pauseText = menuFont.render("PAUSED", False, (255, 255, 255))
    pauseScreen.blit(pauseText, (configs["WIDTH"]/2 - pauseText.get_width()/2, configs["HEIGHT"]/4 - pauseText.get_height()/2))

    # draw the resume button
    if selection != "resume":
        pauseScreen.blit(resumeButtonImg, (resumeButtonPos.x, resumeButtonPos.y))
    else:
        pauseScreen.blit(smallMenuButtonPressedImg, (resumeButtonPos.x, resumeButtonPos.y))

    # draw the restart button
    if selection != "restart":
        pauseScreen.blit(restartButtonImgScaled, (restartButtonPos.x, restartButtonPos.y))
    else:
        pauseScreen.blit(smallMenuButtonPressedImg, (restartButtonPos.x, restartButtonPos.y))

    # draw the load level button
    if selection != "load":
        pauseScreen.blit(menuButtonUnpressedImg, (loadLevelButtonPos.x, loadLevelButtonPos.y))
    else:
        pauseScreen.blit(menuButtonPressedImg, (loadLevelButtonPos.x, loadLevelButtonPos.y))
    loadText = menuButtonFont.render("Load Level", False, (255, 255, 255))
    pauseScreen.blit(loadText, (loadLevelButtonPos.x + (loadLevelButtonSize.x - loadText.get_width()) / 2, loadLevelButtonPos.y + (loadLevelButtonSize.y - loadText.get_height()) / 2))

    # draw the quit button
    if selection != "quit":
        pauseScreen.blit(menuButtonUnpressedImg, (quitButtonPos.x, quitButtonPos.y))
    else:
        pauseScreen.blit(menuButtonPressedImg, (quitButtonPos.x, quitButtonPos.y))
    quitText = menuButtonFont.render("Quit", False, (255, 255, 255))
    pauseScreen.blit(quitText, (quitButtonPos.x + (quitButtonSize.x - quitText.get_width()) / 2, quitButtonPos.y + (quitButtonSize.y - quitText.get_height()) / 2))

    # draw the main menu button
    if selection != "mainMenu":
        pauseScreen.blit(mainMenuButtonImgScaled, (mainMenuButtonPos.x, mainMenuButtonPos.y))
    else:
        pauseScreen.blit(mainMenuButtonPressedImgScaled, (mainMenuButtonPos.x, mainMenuButtonPos.y))
    mainMenuText = infoFont.render("Main Menu", False, (255, 255, 255))
    pauseScreen.blit(mainMenuText, (mainMenuButtonPos.x + (mainMenuButtonSize.x - mainMenuText.get_width()) / 2, mainMenuButtonPos.y + (mainMenuButtonSize.y - mainMenuText.get_height()) / 2))

    # draw the editor button
    if selection != "editor":
        pauseScreen.blit(mainMenuButtonImgScaled, (editorButtonPos.x, editorButtonPos.y))
    else:
        pauseScreen.blit(smallMenuButtonPressedImg, (editorButtonPos.x, editorButtonPos.y))
    editorText = infoFont.render("Editor", False, (255, 255, 255))
    pauseScreen.blit(editorText, (editorButtonPos.x + (editorButtonSize.x - editorText.get_width()) / 2, editorButtonPos.y + (editorButtonSize.y - editorText.get_height()) / 2))
    
    # draw the settings button
    if selection != "settings":
        pauseScreen.blit(settingsButtonImgScaled, (settingsButtonPos.x, settingsButtonPos.y))
    else:
        pauseScreen.blit(settingsButtonImgScaled, (settingsButtonPos.x, settingsButtonPos.y))

    # return the surface
    return pauseScreen, selection
    

# returns a surface of the editor pause screen to be overlayed on the editor screen, also returns a string value to indicate a button press
def getEditorPauseScreen(mx, my, mouseClick, standalone: bool = False) -> tuple[pygame.Surface, str]:
    selection = "none"

    buttonScale = 2.5
    resumeButtonPos = Vector(configs["WIDTH"]/2 - 50*buttonScale, configs["HEIGHT"]/2 - 30*buttonScale)
    resumeButtonSize = Vector(50*buttonScale, 50*buttonScale)
    restartButtonPos = Vector(resumeButtonPos.x + resumeButtonSize.x, resumeButtonPos.y+5)
    restartButtonSize = Vector(50*buttonScale-10, 50*buttonScale-15)
    quitButtonPos = Vector(configs["WIDTH"]/2 - 50*buttonScale, configs["HEIGHT"]/2 + 90*buttonScale+40)
    quitButtonSize = Vector(100*buttonScale, 50*buttonScale)
    # position above the quit button and to the left
    loadLevelButtonPos = Vector(quitButtonPos.x - 100*buttonScale, quitButtonPos.y - 50*buttonScale)
    loadLevelButtonSize = Vector(100*buttonScale, 50*buttonScale)
    # position to the right of the load level button
    saveButtonPos = Vector(loadLevelButtonPos.x + loadLevelButtonSize.x, loadLevelButtonPos.y)
    saveButtonSize = Vector(100*buttonScale, 50*buttonScale)
    # position to the right of the save button
    playLevelButtonPos = Vector(saveButtonPos.x + saveButtonSize.x, saveButtonPos.y)
    playLevelButtonSize = Vector(100*buttonScale, 50*buttonScale)
    # main menu button (positioned bottom left corner)
    mainMenuButtonPos = Vector(10, configs["HEIGHT"] - 25*buttonScale-10)
    mainMenuButtonSize = Vector(50*buttonScale, 25*buttonScale)


    # scale the button images
    menuButtonUnpressedImg = pygame.transform.scale(largeButtonUnpressedImg, (quitButtonSize.x, quitButtonSize.y))
    menuButtonPressedImg = pygame.transform.scale(largeButtonPressedImg, (quitButtonSize.x, quitButtonSize.y))
    smallMenuButtonUnpressedImg = pygame.transform.scale(buttonUnpressedImg, (int(50*buttonScale), int(50*buttonScale)))
    smallMenuButtonPressedImg = pygame.transform.scale(buttonPressedImg, (restartButtonSize.x, restartButtonSize.y))
    resumeButtonImg = pygame.transform.scale(startButtonImg, (int(50*buttonScale), int(50*buttonScale)))
    restartButtonImgScaled = pygame.transform.scale(restartButtonImg, (restartButtonSize.x, restartButtonSize.y))
    mainMenuButtonImgScaled = pygame.transform.scale(menuButtonUnpressedImg, (mainMenuButtonSize.x, mainMenuButtonSize.y))
    mainMenuButtonPressedImgScaled = pygame.transform.scale(menuButtonPressedImg, (mainMenuButtonSize.x, mainMenuButtonSize.y))

    ## check for button clicks ##
    # check if the mouse is over the resume button
    if mx > resumeButtonPos.x and mx < resumeButtonPos.x + resumeButtonSize.x and my > resumeButtonPos.y and my < resumeButtonPos.y + resumeButtonSize.y:
        # mouse button is down
        if mouseClick:
            selection = "resume"
            if configs["SOUND_ENABLED"]:
                playSoundPitch(buttonClickSound)
    
    # check if the mouse is over the restart button
    if mx > restartButtonPos.x and mx < restartButtonPos.x + restartButtonSize.x and my > restartButtonPos.y and my < restartButtonPos.y + restartButtonSize.y:
        # mouse button is down
        if mouseClick:
            selection = "restart"
            if configs["SOUND_ENABLED"]:
                playSoundPitch(buttonClickSound)
    
    # check if the mouse is over the load level button
    if mx > loadLevelButtonPos.x and mx < loadLevelButtonPos.x + loadLevelButtonSize.x and my > loadLevelButtonPos.y and my < loadLevelButtonPos.y + loadLevelButtonSize.y:
        # mouse button is down
        if mouseClick:
            selection = "load"
            if configs["SOUND_ENABLED"]:
                playSoundPitch(buttonClickSound)

    # check if the mouse is over the save button
    if mx > saveButtonPos.x and mx < saveButtonPos.x + saveButtonSize.x and my > saveButtonPos.y and my < saveButtonPos.y + saveButtonSize.y:
        # mouse button is down
        if mouseClick:
            selection = "save"
            if configs["SOUND_ENABLED"]:
                playSoundPitch(buttonClickSound)

    # check if the mouse is over the play level button
    if mx > playLevelButtonPos.x and mx < playLevelButtonPos.x + playLevelButtonSize.x and my > playLevelButtonPos.y and my < playLevelButtonPos.y + playLevelButtonSize.y and not standalone:
        # mouse button is down
        if mouseClick:
            selection = "play"
            if configs["SOUND_ENABLED"]:
                playSoundPitch(buttonClickSound)

    # check if the mouse is over the quit button
    if mx > quitButtonPos.x and mx < quitButtonPos.x + quitButtonSize.x and my > quitButtonPos.y and my < quitButtonPos.y + quitButtonSize.y:
        # mouse button is down
        if mouseClick:
            selection = "quit"
            if configs["SOUND_ENABLED"]:
                playSoundPitch(buttonClickSound)
        
    # check if the mouse is over the main menu button
    if mx > mainMenuButtonPos.x and mx < mainMenuButtonPos.x + mainMenuButtonSize.x and my > mainMenuButtonPos.y and my < mainMenuButtonPos.y + mainMenuButtonSize.y and not standalone:
        # mouse button is down
        if mouseClick:
            selection = "mainMenu"
            if configs["SOUND_ENABLED"]:
                playSoundPitch(buttonClickSound)

    # create a surface for the pause screen
    pauseScreen = pygame.Surface((configs["WIDTH"], configs["HEIGHT"]), pygame.SRCALPHA)
    # fill the surface with a black transparent color
    pauseScreen.fill((0, 0, 0, 100))

    # draw the text
    pauseText = menuFont.render("PAUSED", False, (255, 255, 255))
    pauseScreen.blit(pauseText, (configs["WIDTH"]/2 - pauseText.get_width()/2, configs["HEIGHT"]/4 - pauseText.get_height()/2))

    # draw the resume button
    if selection != "resume":
        pauseScreen.blit(resumeButtonImg, (resumeButtonPos.x, resumeButtonPos.y))
    else:
        pauseScreen.blit(smallMenuButtonPressedImg, (resumeButtonPos.x, resumeButtonPos.y))

    # draw the restart button
    if selection != "restart":
        pauseScreen.blit(restartButtonImgScaled, (restartButtonPos.x, restartButtonPos.y))
    else:
        pauseScreen.blit(smallMenuButtonPressedImg, (restartButtonPos.x, restartButtonPos.y))

    # draw the load level button
    if selection != "load":
        pauseScreen.blit(menuButtonUnpressedImg, (loadLevelButtonPos.x, loadLevelButtonPos.y))
    else:
        pauseScreen.blit(menuButtonPressedImg, (loadLevelButtonPos.x, loadLevelButtonPos.y))
    loadText = menuButtonFont.render("Load Level", False, (255, 255, 255))
    pauseScreen.blit(loadText, (loadLevelButtonPos.x + (loadLevelButtonSize.x - loadText.get_width()) / 2, loadLevelButtonPos.y + (loadLevelButtonSize.y - loadText.get_height()) / 2))

    # draw the save button
    if selection != "save":
        pauseScreen.blit(menuButtonUnpressedImg, (saveButtonPos.x, saveButtonPos.y))
    else:
        pauseScreen.blit(menuButtonPressedImg, (saveButtonPos.x, saveButtonPos.y))
    saveText = menuButtonFont.render("Save Level", False, (255, 255, 255))
    pauseScreen.blit(saveText, (saveButtonPos.x + (saveButtonSize.x - saveText.get_width()) / 2, saveButtonPos.y + (saveButtonSize.y - saveText.get_height()) / 2))

    # draw the play level button
    if not standalone:
        if selection != "play":
            pauseScreen.blit(menuButtonUnpressedImg, (playLevelButtonPos.x, playLevelButtonPos.y))
        else:
            pauseScreen.blit(menuButtonPressedImg, (playLevelButtonPos.x, playLevelButtonPos.y))
        playText = menuButtonFont.render("Play Level", False, (255, 255, 255))
        pauseScreen.blit(playText, (playLevelButtonPos.x + (playLevelButtonSize.x - playText.get_width()) / 2, playLevelButtonPos.y + (playLevelButtonSize.y - playText.get_height()) / 2))

    # draw the quit button
    if selection != "quit":
        pauseScreen.blit(menuButtonUnpressedImg, (quitButtonPos.x, quitButtonPos.y))
    else:
        pauseScreen.blit(menuButtonPressedImg, (quitButtonPos.x, quitButtonPos.y))
    quitText = menuButtonFont.render("Quit", False, (255, 255, 255))
    pauseScreen.blit(quitText, (quitButtonPos.x + (quitButtonSize.x - quitText.get_width()) / 2, quitButtonPos.y + (quitButtonSize.y - quitText.get_height()) / 2))

    # draw the main menu button
    if not standalone:
        if selection != "mainMenu":
            pauseScreen.blit(mainMenuButtonImgScaled, (mainMenuButtonPos.x, mainMenuButtonPos.y))
        else:
            pauseScreen.blit(mainMenuButtonPressedImgScaled, (mainMenuButtonPos.x, mainMenuButtonPos.y))
        mainMenuText = infoFont.render("Main Menu", False, (255, 255, 255))
        pauseScreen.blit(mainMenuText, (mainMenuButtonPos.x + (mainMenuButtonSize.x - mainMenuText.get_width()) / 2, mainMenuButtonPos.y + (mainMenuButtonSize.y - mainMenuText.get_height()) / 2))

    # return the surface
    return pauseScreen, selection