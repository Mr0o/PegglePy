import pygame
import time

from local.config import WIDTH, HEIGHT, debug, musicVolume as mvolume, soundVolume as soVolume
from local.resources import *
from local.vectors import Vector
from local.audio import playSoundPitch, loadRandMusic, playMusic, setMusicVolume
from local.slider import Slider

# this menu will serve as the point where the game and the editor can both be accessed
def settingsMenu(screen: pygame.Surface, debug: bool = debug):
    # play menu music
    loadRandMusic()
    playMusic()
    setMusicVolume(mvolume)

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

    # volume sliders
    musicSlider = Slider(Vector(50, 50), 300, 50)
    musicSlider.min = 0
    musicSlider.max = 100
    musicSlider.setValue(mvolume*100)

    soundSlider = Slider(Vector(50, 150), 300, 50)
    soundSlider.min = 0
    soundSlider.max = 100
    soundSlider.setValue(soVolume*100)

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
        if mousePos.x > backButtonPos.x and mousePos.x < backButtonPos.x + backButtonSize.x and mousePos.y > backButtonPos.y and mousePos.y < backButtonPos.y + backButtonSize.y:
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

        # update the volume sliders
        musicSlider.update(mousePos, pygame.mouse.get_pressed()[0])
        soundSlider.update(mousePos, pygame.mouse.get_pressed()[0])

        # update the volume
        setMusicVolume(musicSlider.value/100)
        sovolume = soundSlider.value/100

        # draw the volume sliders
        screen.blit(musicSlider.getSliderSurface(), (musicSlider.pos.x, musicSlider.pos.y))
        screen.blit(soundSlider.getSliderSurface(), (soundSlider.pos.x, soundSlider.pos.y))

        # draw the volume slider labels
        musicLabel = menuButtonFont.render("Music Volume", True, (255, 255, 255))
        screen.blit(musicLabel, (musicSlider.pos.x + musicSlider.sliderRect.width/2 - musicLabel.get_width()/2, musicSlider.pos.y - musicLabel.get_height() - 5))

        soundLabel = menuButtonFont.render("Sound Volume", True, (255, 255, 255))
        screen.blit(soundLabel, (soundSlider.pos.x + soundSlider.sliderRect.width/2 - soundLabel.get_width()/2, soundSlider.pos.y - soundLabel.get_height() - 5))

        # draw the buttons

        # settings button (bottom right corner)
        screen.blit(buttonUnpressedImgScaled, (backButtonPos.x, backButtonPos.y))
        # draw the text
        backText = menuButtonFont.render("Back", True, (255, 255, 255))
        screen.blit(backText, (backButtonPos.x + backButtonSize.x/2 - backText.get_width()/2, backButtonPos.y + backButtonSize.y/2 - backText.get_height()/2))


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
            playSoundPitch(buttonClickSound, volume=sovolume)
            return selection


# test
if __name__ == "__main__":
    # basic pygame setup
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    # run the menu
    settingsMenu(screen)

    # quit pygame
    pygame.quit()
    quit()