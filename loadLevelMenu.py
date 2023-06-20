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
        # strip everything from the filepath except the filename
        levelFilePath = levelFilePath.split("/")[-1]
        # remove the file extension '.lvl'
        levelFilePath = levelFilePath[:-4]
    
    return levelFilePath


def getLevelsList(levelsDirectory: str = "levels") -> list[str]:
    # get a list of all the level files in the levels folder
    levelsList = []
    for file in os.listdir(levelsDirectory):
        if file.endswith(".lvl"):
            levelsList.append(os.path.join(levelsDirectory, file))
    
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
    # get the names of each level in the levels folder
    levelsList = getLevelsList()

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
    

            # maximum scroll value (scale the value by the height of the level name text)
            # get the position of the last level rect
            if i == len(levelsList)-1:
                maxScrollValue = -(rect.y + rect.height - HEIGHT + levelNameText.get_height())
            else:
                maxScrollValue = -HEIGHT*10
            if scrollValue < maxScrollValue:
                scrollValue = maxScrollValue
            elif scrollValue > 0:
                scrollValue = 0

            # apply scroll value
            rect.y += scrollValue*levelNameText.get_height()

            pygame.draw.rect(screen, color, rect, 2)
            
            # apply scroll value
            screen.blit(levelNameText, (WIDTH/5 +5, HEIGHT/3 - levelNameText.get_height()/2 + i*levelNameText.get_height() + scrollValue*levelNameText.get_height()))

        # draw the title (applying the scroll value)
        menuTitle = menuFont.render("Select a level", True, (255, 255, 255))
        screen.blit(menuTitle, (WIDTH/2 - menuTitle.get_width()/2, HEIGHT/5 - menuTitle.get_height()/2 + scrollValue*levelNameText.get_height()))

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