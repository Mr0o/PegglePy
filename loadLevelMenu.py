import pygame
import time
import os

from local.config import WIDTH, HEIGHT, debug
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

    pygame.display.set_caption("PegglePy  -  Level Select")

    scrollValue = 0
    lastRectPos = 1
    # get the names of each level in the levels folder
    levelsList = getLevelsList()

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
            levelPreviewImg.blit(scaledPegImg, (peg.pos.vx*levelPreviewImgScaleW, peg.pos.vy*levelPreviewImgScaleW))
        
        # add the level preview image to the list    
        levelPreviewImgs.append(levelPreviewImg)

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
                if event.button == 1:
                    mouseDown = True
            
                # if scroll wheel is used
                if event.button == 4:
                    # scroll up
                    scrollValue += 1
                if event.button == 5:
                    # scroll down
                    scrollValue -= 1
                    pass
            
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

        # draw the buttons

        # settings button (bottom right corner)
        screen.blit(buttonUnpressedImgScaled, (backButtonPos.vx, backButtonPos.vy))
        # draw the text
        backText = menuButtonFont.render("Back", True, (255, 255, 255))
        screen.blit(backText, (backButtonPos.vx + backButtonSize.vx/2 - backText.get_width()/2, backButtonPos.vy + backButtonSize.vy/2 - backText.get_height()/2))

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
            if pygame.Rect(mousePos.vx, mousePos.vy - scrollValue*levelNameText.get_height(), 1, 1).colliderect(rect):
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

            # apply scroll value
            rect.y += scrollValue*levelNameText.get_height()

            pygame.draw.rect(screen, color, rect, 2)
            
            # apply scroll value
            screen.blit(levelNameText, (WIDTH/5 +5 -WIDTH/6, HEIGHT/3 - levelNameText.get_height()/2 + i*levelNameText.get_height() + scrollValue*levelNameText.get_height()))

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

        # update display
        pygame.display.update()

        clock.tick(60)

        # check if the user has made a selection
        if selection != "none":
            if selection == "mainMenu":
                return loadDefaultLevel()
                #return [], [], 0, selection
            playSoundPitch(buttonClickSound)
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