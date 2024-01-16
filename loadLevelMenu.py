import pygame
import time
import os

from local.config import WIDTH, HEIGHT, debug, soundVolume
from local.resources import *
from local.vectors import Vector
from local.audio import playSoundPitch
from local.load_level import loadData
from local.misc import createPegColors, loadDefaultLevel


def getLevelName(levelFilePath: str) -> str:
    # check that the filepath is not empty
    if levelFilePath == "" or levelFilePath == None:
        levelFilePath = "Default"
    else:
        # remove the path from the file path (check for both "/" and "\")
        if "/" in levelFilePath:
            levelFilePath = levelFilePath.split("/")[-1]
        elif "\\" in levelFilePath:
            levelFilePath = levelFilePath.split("\\")[-1]
        # remove the file extension '.lvl'
        levelFilePath = levelFilePath[:-4]
    
    return levelFilePath


def getLevelsList(levelsDirectory: str = "levels") -> list[str]:
    # get a list of all the level files in the levels folder
    levelsList = []
    try:
        for file in os.listdir(levelsDirectory):
            if file.endswith(".lvl"):
                levelsList.append(os.path.join(levelsDirectory, file))

    except FileNotFoundError:
        levelsList = []
        print("Levels folder not found, creating folder...")
        try:
            os.mkdir(levelsDirectory)
            print("Levels folder created.")
        except Exception:
            print("ERROR: Unable to create levels folder, please create the folder manually.")
        
        print("Loading default level...")

    # sort the list of levels by name alphabetically
    levelsList.sort()
    
    return levelsList


def loadLevel(levelFilePath) -> tuple[list[Peg], list[Peg], int]:
    # load the pegs from a level file (pickle)
    pegs, levelFileName = loadData(levelFilePath)
    originPegs = pegs.copy()

    pegs = createPegColors(pegs)

    orangeCount = 0
    for peg in pegs:
        if peg.color == "orange":
            orangeCount += 1

    return pegs, originPegs, orangeCount, getLevelName(levelFilePath)


# this menu will be used to load levels
def loadLevelMenu(screen: pygame.Surface, debug: bool = debug) -> tuple[list[Peg], list[Peg], int]:
    # play menu music
    pygame.mixer.music.load(menuMusicPath)
    pygame.mixer.music.play(-1)
    pygame.mixer.music.set_volume(soundVolume)

    # button positions
    buttonScale = 2.5
    editorButtonSize = Vector(100*buttonScale, 50*buttonScale)
    backButtonPos = Vector(WIDTH - 50*buttonScale-20, HEIGHT - 50*buttonScale-20)
    backButtonSize = Vector(50*buttonScale, 50*buttonScale)

     # scale the button images
    menuButtonUnpressedImg = pygame.transform.scale(largeButtonUnpressedImg, (editorButtonSize.x, editorButtonSize.y))
    menuButtonPressedImg = pygame.transform.scale(largeButtonPressedImg, (editorButtonSize.x, editorButtonSize.y))
    buttonUnpressedImgScaled = pygame.transform.scale(buttonUnpressedImg, (int(50*buttonScale), int(50*buttonScale)))
    buttonPressedImgScaled = pygame.transform.scale(buttonPressedImg, (int(50*buttonScale), int(50*buttonScale)))


    selection: str = "none" # this will be returned as the user selection made in the menu

    clock = pygame.time.Clock()

    pygame.display.set_caption("PegglePy  -  Level Select")

    scrollValue = 0
    lastRectPos = 1
    # get the names of each level in the levels folder
    levelsList = getLevelsList()

    controllerConnected = False
    controllerCursorIndex = 0
    moveControllerSelector = None

    # if there are no levels in the levels folder, load the default level
    if len(levelsList) == 0:
        return loadDefaultLevel()

    # create a list of pygame.Surface objects and load the level preview images
    levelPreviewImgSizeW = WIDTH*0.3
    levelPreviewImgSizeH = HEIGHT*0.3
    # find the value that should be used to scale the peg img and positions
    levelPreviewImgScaleW = levelPreviewImgSizeW / WIDTH
    levelPreviewImgScaleH = levelPreviewImgSizeH / HEIGHT
    levelPreviewImgs: list[pygame.Surface] = []
    for i in range(len(levelsList)):
        levelFilePath = levelsList[i]
        pegs = loadData(levelFilePath, False)[0]
        # create a surface to draw the level preview on
        levelPreviewImg = pygame.Surface((int(levelPreviewImgSizeW), int(levelPreviewImgSizeH)))

        # blit the background
        scaledBackgroundImg = pygame.transform.scale(backgroundImg, (int(levelPreviewImgSizeW), int(levelPreviewImgSizeH)))
        levelPreviewImg.blit(scaledBackgroundImg, (0, 0))

        # scale the peg image
        p = pegs[0]
        scaledPegImg = pygame.transform.scale(p.pegImg.copy(), (int(p.pegImg.get_width()*levelPreviewImgScaleW), int(p.pegImg.get_height()*levelPreviewImgScaleH)))
        # draw the pegs
        for peg in pegs:
            levelPreviewImg.blit(scaledPegImg, (peg.pos.x*levelPreviewImgScaleW, peg.pos.y*levelPreviewImgScaleW))
        
        # add the level preview image to the list    
        levelPreviewImgs.append(levelPreviewImg)

    # main loop
    while True:
        mouseDown = False
        dpadDirection = None
        backButtonPressed = False
        selectButtonPressed = False
        # event handling
        for event in pygame.event.get():
            # quit if the user clicks the close button
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            # check if the mouse button is pressed (mouse button down)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouseDown = True
            
                # if scroll wheel is used
                if event.button == 4:
                    # scroll up
                    scrollValue += 1
                if event.button == 5:
                    # scroll down
                    scrollValue -= 1
            
            # check if 1 is pressed (debug)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    debug = not debug

            # check for gamepad dpad buttons
            if event.type == pygame.JOYHATMOTION:
                if event.value == (0, 1):
                    dpadDirection = "up"
                    controllerConnected = True
                if event.value == (0, -1):
                    dpadDirection = "down"
                    controllerConnected = True

            if event.type == pygame.JOYBUTTONDOWN:
                # if the controller is a 'sony' or 'playstation' controller (Sometimes "Wireless Controller" is the name of the ps4 controller, so we will include that as well)
                if joystick.get_name().lower().find("sony") != -1 or joystick.get_name().lower().find("playstation") != -1 or joystick.get_name().lower().find("wireless") != -1:
                    if event.button == 0:  # the 'X'/cross button on a ps4 controller
                        selectButtonPressed = True
                    if event.button == 1:  # the 'O'/circle button on a ps4 controller
                        backButtonPressed = True
                    if event.button == 8:  # the 'share' button on a ps4 controller
                        # enable or disable debug
                        debug = not debug

                else:  # xbox controller (default)
                    if event.button == 0:  # the 'A' button on an xbox controller
                        selectButtonPressed = True
                    if event.button == 1:  # the 'B' button on an xbox controller
                        backButtonPressed = True
                    if event.button == 6:  # the 'start' button on an xbox controller
                        debug = not debug
        

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

            # move the controller selector
            if (moveControllerSelector == "up" and previousControllerSelector is None) or dpadDirection == "up":
                scrollValue += 1
                controllerCursorIndex -= 1
                # wrap around
                if controllerCursorIndex < 0:
                    controllerCursorIndex = len(levelsList)-1
            if (moveControllerSelector == "down" and previousControllerSelector is None) or dpadDirection == "down":
                scrollValue -= 1
                controllerCursorIndex += 1
                # wrap around
                if controllerCursorIndex > len(levelsList)-1:
                    controllerCursorIndex = 0
                    # reset the scroll value
                    scrollValue = 0
                elif controllerCursorIndex < 0:
                    controllerCursorIndex = len(levelsList)-1
                    # reset the scroll value
                    scrollValue = 0
        else:
            # update mouse posistion
            mx, my = pygame.mouse.get_pos()
            mousePos = Vector(mx, my)


        ## check mouse input
        
        # check if mouse is over back button
        if not controllerConnected:
            if mousePos.x > backButtonPos.x and mousePos.x < backButtonPos.x + backButtonSize.x and mousePos.y > backButtonPos.y and mousePos.y < backButtonPos.y + backButtonSize.y:
                # mouse button is down
                if mouseDown:
                    selection = "mainMenu"

        if backButtonPressed:
            selection = "mainMenu"

        # draw the background
        screen.blit(altBackgroundImg, (0, 0))

        # draw the buttons

        # settings button (bottom right corner)
        screen.blit(buttonUnpressedImgScaled, (backButtonPos.x, backButtonPos.y))
        # draw the text
        backText = menuButtonFont.render("Back", True, (255, 255, 255))
        screen.blit(backText, (backButtonPos.x + backButtonSize.x/2 - backText.get_width()/2, backButtonPos.y + backButtonSize.y/2 - backText.get_height()/2))

        # draw a rectangle at the center of the screen and the text of the level name
        # draw the level names
        for i in range(len(levelsList)):
            levelFilePath = levelsList[i]
            levelName = getLevelName(levelsList[i])
            levelNameText = menuButtonFont.render(levelName, True, (255, 255, 255))
            color = (255, 255, 255)

            # draw the level selection rectangle
            # position it at WIDHT/3 at the same length across all levels
            rect = pygame.Rect(WIDTH/5, HEIGHT/3 - levelNameText.get_height()/2 + i*levelNameText.get_height() + 1, WIDTH/5*3, levelNameText.get_height() -1)

            # maximum scroll value (scale the value by the height of the level name text)
            # get the position of the last level rect
            if scrollValue > 0:
                scrollValue = 0

            ## calculate the maximum scroll value
            # get the position of the last level rect
            if i == len(levelsList)-1:
                lastRectPos = rect.y

            # how many levelNameText.get_height() will fit into HEIGHT
            maxNumOfLevels = int(HEIGHT/levelNameText.get_height()) - 1
            # subtract maxNumOfLevels from maxNumOfLevels/5
            maxNumOfLevels -= int(maxNumOfLevels/5)
            
            # if the abs(scroll value) * levelNameText.get_height() is greater than the last rect pos, set the scroll value to the maximum scroll value
            if abs(scrollValue*levelNameText.get_height()) > lastRectPos - maxNumOfLevels*levelNameText.get_height():
                scrollValue = -lastRectPos/levelNameText.get_height() + maxNumOfLevels

            # move the rect over to the left
            rect.x -= WIDTH/6

            # check if the mouse is over the level selection rectangle (apply scroll value)
            if not controllerConnected:
                if pygame.Rect(mousePos.x, mousePos.y - scrollValue*levelNameText.get_height(), 1, 1).colliderect(rect):
                    if mouseDown:
                        selection = levelFilePath
                        if debug:
                            print ("Level selected: " + str(levelFilePath))
                    # mouse is hovering over the level selection rectangle
                    else:
                        color = (0, 255, 0)
                        levelNameText = menuButtonFont.render(levelName, True, color)

                        # blit the preview image at the top right corner of the screen
                        screen.blit(levelPreviewImgs[i], (WIDTH - levelPreviewImgSizeW - 20, 20))
            
            # controller cursor
            if controllerConnected:
                if i == controllerCursorIndex:
                    color = (0, 255, 0)
                    levelNameText = menuButtonFont.render(levelName, True, color)

                    # blit the preview image at the top right corner of the screen
                    screen.blit(levelPreviewImgs[i], (WIDTH - levelPreviewImgSizeW - 20, 20))

                    controllerIndexRectPos = rect.y


            # apply scroll value
            rect.y += scrollValue*levelNameText.get_height()

            # only draw if the rect isn't off screen
            if rect.y > -levelNameText.get_height() and rect.y < HEIGHT:
                pygame.draw.rect(screen, color, rect, 2)

            
            # apply scroll value
            screen.blit(levelNameText, (WIDTH/5 +5 -WIDTH/6, HEIGHT/3 - levelNameText.get_height()/2 + i*levelNameText.get_height() + scrollValue*levelNameText.get_height()))


        # if the controller select button is pressed
        if selectButtonPressed:
            selection = levelsList[controllerCursorIndex]
            if debug:
                print ("Level selected: " + str(levelsList[controllerCursorIndex]))
            

        # draw the title (applying the scroll value)
        menuTitle = menuFont.render("Select a level", True, (255, 255, 255))
        # position at HEIGHT/5 and apply the scroll value
        screen.blit(menuTitle, (WIDTH/2 - menuTitle.get_width()/2 -WIDTH/6, HEIGHT/7 + (scrollValue*menuButtonFont.render("", True, (255, 255, 255)).get_height())))

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

            # show controller info
            if controllerConnected:
                joystickName = debugFont.render(
                    "Controller: " + joystick.get_name(), False, (255, 255, 255))
                screen.blit(joystickName, (5, 40))

        # update display
        pygame.display.update()

        clock.tick(60)

        # check if the user has made a selection
        if selection != "none":
            if selection == "mainMenu":
                return loadDefaultLevel()
                #return [], [], 0, selection
            playSoundPitch(buttonClickSound, volume=soundVolume)
            # draw a loading screen
            # draw the background
            screen.blit(altBackgroundImg, (0, 0))
            # draw the title
            menuTitle = menuFont.render("Loading...", True, (255, 255, 255))
            screen.blit(menuTitle, (WIDTH/2 - menuTitle.get_width()/2, HEIGHT/2 - menuTitle.get_height()/2))

            pegs, originPegs, orangeCount, levelFileName = loadLevel(selection)
            if len(pegs) > 400:
                # update display (draw loading screen)
                pygame.display.update()

            return pegs, originPegs, orangeCount, getLevelName(selection)



if __name__ == "__main__":
    # initiate pygame
    pygame.init()
    # create the screen
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    # run the menu
    print(loadLevelMenu(screen)[3])