import pygame
import time
import os
from collections.abc import Callable

from local.config import configs
from local.resources import *
from local.vectors import Vector
from local.audio import playSoundPitch, newSong
from local.loadLevel import loadData, loadDefaultLevel
from local.peg import Peg, createPegColors
import re

MAX_LEVEL_PREVIEW_PEGS = 5000
LEVEL_DATA_PROGRESS_END = 0.55
LOADING_SCREEN_DELAY = 1.0
LOADING_SCREEN_UPDATE_INTERVAL = 0.1


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

    levelsList = sorted(levelsList, key=natural_key)
    
    return levelsList


def natural_key(filePath: str):
        name = getLevelName(filePath)
        primary = 0 if name.startswith("Level") else 1
        return (primary, [int(text) if text.isdigit() else text.lower() for text in re.split('(\d+)', name)])


def loadLevel(
    levelFilePath: str,
    progress_callback: Callable[[float, str], None] | None = None,
) -> tuple[list[Peg], list[Peg], int, str]:
    # load the pegs from a level file (pickle)
    def report_data_progress(progress: float, status: str) -> None:
        if progress_callback is not None:
            progress_callback(progress * 0.7, status)

    pegs, levelFileName = loadData(
        levelFilePath, progress_callback=report_data_progress
    )
    originPegs = pegs.copy()

    if progress_callback is not None:
        progress_callback(0.72, "Assigning peg colors")
    pegs = createPegColors(pegs)

    orangeCount = 0
    for index, peg in enumerate(pegs):
        if peg.color == "orange":
            orangeCount += 1
        if progress_callback is not None and pegs:
            progress_callback(
                0.72 + 0.27 * (index + 1) / len(pegs),
                "Counting orange pegs",
            )

    if progress_callback is not None:
        progress_callback(1.0, "Rendering level...")
    return pegs, originPegs, orangeCount, getLevelName(levelFileName)


def drawLoadingScreen(
    screen: pygame.Surface,
    level_name: str,
    progress: float,
    status: str,
) -> None:
    progress = min(max(progress, 0.0), 1.0)
    screen.blit(altBackgroundImg, (0, 0))

    title = menuButtonFont.render(f"Loading {level_name}", True, (255, 255, 255))
    status_text = infoFont.render(status, True, (220, 220, 220))
    percent_text = infoFont.render(
        f"{round(progress * 100)}%", True, (255, 255, 255)
    )
    screen_rect = screen.get_rect()
    center_x = screen_rect.centerx
    gap_title_status = 24
    gap_status_bar = 24
    gap_bar_percent = 14
    bar_width = min(600, screen_rect.width - 80)
    bar_height = 24
    content_height = (
        title.get_height()
        + gap_title_status
        + status_text.get_height()
        + gap_status_bar
        + bar_height
        + gap_bar_percent
        + percent_text.get_height()
    )
    content_top = screen_rect.centery - content_height // 2
    title_y = content_top
    status_y = title_y + title.get_height() + gap_title_status
    bar_rect = pygame.Rect(
        center_x - bar_width // 2,
        status_y + status_text.get_height() + gap_status_bar,
        bar_width,
        bar_height,
    )
    percent_y = bar_rect.bottom + gap_bar_percent

    screen.blit(title, (center_x - title.get_width() // 2, title_y))
    screen.blit(
        status_text,
        (center_x - status_text.get_width() // 2, status_y),
    )
    pygame.draw.rect(screen, (35, 35, 50), bar_rect, border_radius=8)
    fill_rect = bar_rect.copy()
    fill_rect.width = round(bar_width * progress)
    if fill_rect.width:
        pygame.draw.rect(screen, (0, 180, 255), fill_rect, border_radius=8)
    screen.blit(
        percent_text,
        (center_x - percent_text.get_width() // 2, percent_y),
    )
    pygame.display.flip()
    pygame.event.pump()


class LoadingScreenProgress:
    def __init__(self, screen: pygame.Surface, level_name: str = "level"):
        self.screen = screen
        self.level_name = level_name
        self.started_at: float | None = None
        self.last_draw_time = 0.0
        self.last_progress_percent = -1
        self.last_status = ""
        self.has_drawn = False

    def set_level(self, level_name: str) -> None:
        self.level_name = level_name

    @staticmethod
    def _check_for_quit() -> None:
        if pygame.event.peek(pygame.QUIT):
            pygame.quit()
            raise SystemExit

    def begin(self, level_name: str | None = None) -> None:
        if level_name is not None:
            self.level_name = level_name
        self.started_at = time.perf_counter()
        self.last_draw_time = 0.0
        self.last_progress_percent = -1
        self.last_status = ""
        self.has_drawn = False

    def show_immediately(self, progress: float, status: str) -> None:
        progress = min(max(progress, 0.0), 1.0)
        now = time.perf_counter()
        self.last_draw_time = now
        self.last_progress_percent = round(progress * 100)
        self.last_status = status
        self.has_drawn = True
        drawLoadingScreen(self.screen, self.level_name, progress, status)

    def __call__(self, progress: float, status: str) -> None:
        self._check_for_quit()
        progress = min(max(progress, 0.0), 1.0)
        progress_percent = round(progress * 100)
        now = time.perf_counter()
        if self.started_at is None:
            self.started_at = now
        if now - self.started_at < LOADING_SCREEN_DELAY:
            return

        if self.has_drawn and (
            progress_percent == self.last_progress_percent
            and status == self.last_status
        ):
            return

        is_complete = progress >= 1.0
        if (
            self.has_drawn
            and now - self.last_draw_time < LOADING_SCREEN_UPDATE_INTERVAL
            and not is_complete
        ):
            return

        self.last_draw_time = now
        self.last_progress_percent = progress_percent
        self.last_status = status
        self.has_drawn = True
        drawLoadingScreen(self.screen, self.level_name, progress, status)


# this menu will be used to load levels
def loadLevelMenu(
    screen: pygame.Surface,
    debug: bool = configs["DEBUG_MODE"],
) -> tuple[list[Peg], list[Peg], int, str]:
    loading_progress = LoadingScreenProgress(screen)

    def render_progress(progress: float, status: str) -> None:
        loading_progress(progress * LEVEL_DATA_PROGRESS_END, status)

    # check if music is already playing
    if not pygame.mixer.music.get_busy():
        # play menu music
        pygame.mixer.music.stop()
        # load the menu music
        pygame.mixer.music.load(menuMusicPath)
        # play the music
        if configs["MUSIC_ENABLED"]:
            pygame.mixer.music.play(-1)

    # button positions
    buttonScale = 2.5
    editorButtonSize = Vector(100*buttonScale, 50*buttonScale)
    backButtonPos = Vector(configs["WIDTH"] - 50*buttonScale-20, configs["HEIGHT"] - 50*buttonScale-20)
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
        print("WARN: No levels found, loading default level...")
        loading_progress.set_level("Default")
        return loadDefaultLevel(progress_callback=render_progress)

    # create a list of pygame.Surface objects and load the level preview images
    levelPreviewImgSizeW = configs["WIDTH"]*0.3
    levelPreviewImgSizeH = configs["HEIGHT"]*0.3
    # find the value that should be used to scale the peg img and positions
    levelPreviewImgScaleW = levelPreviewImgSizeW / configs["WIDTH"]
    levelPreviewImgScaleH = levelPreviewImgSizeH / configs["HEIGHT"]
    levelPreviewImgs: list[pygame.Surface] = []
    for i in range(len(levelsList)):
        levelFilePath = levelsList[i]
        pegs = loadData(
            levelFilePath,
            False,
            peg_limit=MAX_LEVEL_PREVIEW_PEGS,
        )[0]
        # create a surface to draw the level preview on
        levelPreviewImg = pygame.Surface((int(levelPreviewImgSizeW), int(levelPreviewImgSizeH)))

        # blit the background
        scaledBackgroundImg = pygame.transform.scale(backgroundImg, (int(levelPreviewImgSizeW), int(levelPreviewImgSizeH)))
        levelPreviewImg.blit(scaledBackgroundImg, (0, 0))

        # scale the peg image
        scaledPegImg = pygame.transform.scale(bluePegImg.copy(), (int(bluePegImg.get_width()*levelPreviewImgScaleW), int(bluePegImg.get_height()*levelPreviewImgScaleH)))
        for peg in pegs:
            levelPreviewImg.blit(
                scaledPegImg,
                (
                    peg.pos.x * levelPreviewImgScaleW,
                    peg.pos.y * levelPreviewImgScaleH,
                ),
            )
        
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
                exit()
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
                    configs["DEBUG_MODE"] = not configs["DEBUG_MODE"]

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
        altBgImg = pygame.transform.scale(altBackgroundImg, (configs["WIDTH"], configs["HEIGHT"]))
        screen.blit(altBgImg, (0, 0))

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
            rect = pygame.Rect(configs["WIDTH"]/5, configs["HEIGHT"]/3 - levelNameText.get_height()/2 + i*levelNameText.get_height(), configs["WIDTH"]/5*3, levelNameText.get_height())

            # maximum scroll value (scale the value by the height of the level name text)
            # get the position of the last level rect
            if scrollValue > 0:
                scrollValue = 0

            ## calculate the maximum scroll value
            # get the position of the last level rect
            if i == len(levelsList)-1:
                lastRectPos = rect.y

            # how many levelNameText.get_height() will fit into configs["HEIGHT"]
            maxNumOfLevels = int(configs["HEIGHT"]/levelNameText.get_height()) - 1
            # subtract maxNumOfLevels from maxNumOfLevels/5
            maxNumOfLevels -= int(maxNumOfLevels/5)
            
            # if the abs(scroll value) * levelNameText.get_height() is greater than the last rect pos, set the scroll value to the maximum scroll value
            if abs(scrollValue*levelNameText.get_height()) > lastRectPos - maxNumOfLevels*levelNameText.get_height():
                scrollValue = -lastRectPos/levelNameText.get_height() + maxNumOfLevels

            # move the rect over to the left
            rect.x -= configs["WIDTH"]/6

            # check if the mouse is over the level selection rectangle (apply scroll value)
            if not controllerConnected:
                if pygame.Rect(mousePos.x, mousePos.y - scrollValue*levelNameText.get_height(), 1, 1).colliderect(rect):
                    if mouseDown:
                        selection = levelFilePath
                        if configs["DEBUG_MODE"]:
                            print ("Level selected: " + str(levelFilePath))
                    # mouse is hovering over the level selection rectangle
                    else:
                        color = (0, 180, 255)
                        levelNameText = menuButtonFont.render(levelName, True, color)

                        # blit the preview image at the top right corner of the screen
                        screen.blit(levelPreviewImgs[i], (configs["WIDTH"] - levelPreviewImgSizeW - 20, 20))
            
            # controller cursor
            if controllerConnected:
                if i == controllerCursorIndex:
                    color = (0, 180, 255)
                    levelNameText = menuButtonFont.render(levelName, True, color)

                    # blit the preview image at the top right corner of the screen
                    screen.blit(levelPreviewImgs[i], (configs["WIDTH"] - levelPreviewImgSizeW - 20, 20))

                    controllerIndexRectPos = rect.y


            # apply scroll value
            rect.y += scrollValue*levelNameText.get_height()

            # only draw if the rect isn't off screen
            if rect.y > -levelNameText.get_height() and rect.y < configs["HEIGHT"]:
                pygame.draw.rect(screen, color, rect, 2)

            
            # apply scroll value
            screen.blit(levelNameText, (configs["WIDTH"]/5 +5 -configs["WIDTH"]/6, configs["HEIGHT"]/3 - levelNameText.get_height()/2 + i*levelNameText.get_height() + scrollValue*levelNameText.get_height()))


        # if the controller select button is pressed
        if selectButtonPressed:
            selection = levelsList[controllerCursorIndex]
            if configs["DEBUG_MODE"]:
                print ("Level selected: " + str(levelsList[controllerCursorIndex]))
            

        # draw the title (applying the scroll value)
        menuTitle = menuFont.render("Select a level", True, (255, 255, 255))
        # position at configs["HEIGHT"]/5 and apply the scroll value
        screen.blit(menuTitle, (configs["WIDTH"]/2 - menuTitle.get_width()/2 -configs["WIDTH"]/6, configs["HEIGHT"]/7 + (scrollValue*menuButtonFont.render("", True, (255, 255, 255)).get_height())))

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

            # show controller info
            if controllerConnected:
                joystickName = debugFont.render(
                    "Controller: " + joystick.get_name(), False, (255, 255, 255))
                screen.blit(joystickName, (5, 40))

        # update display
        pygame.display.update()

        clock.tick(configs["REFRESH_RATE"])

        # check if the user has made a selection
        if selection != "none":
            if selection == "mainMenu":
                loading_progress.set_level("Default")
                return loadDefaultLevel(progress_callback=render_progress)
                #return [], [], 0, selection
            if configs["SOUND_ENABLED"]:
                playSoundPitch(buttonClickSound)
            loading_progress.set_level(getLevelName(selection))
            render_progress(0.0, "Starting")
            pegs, originPegs, orangeCount, levelFileName = loadLevel(
                selection, progress_callback=render_progress
            )

            return pegs, originPegs, orangeCount, getLevelName(selection)



if __name__ == "__main__":
    # initiate pygame
    pygame.init()
    # create the screen
    screen = pygame.display.set_mode((configs["WIDTH"], configs["HEIGHT"]))
    
    configs["REFRESH_RATE"] = 60

    # run the menu
    print(loadLevelMenu(screen)[3])