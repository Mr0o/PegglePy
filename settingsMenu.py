import pygame
import time

from local.userConfig import configs, saveSettings, defaultConfigs
from local.resources import buttonUnpressedImg, buttonPressedImg, largeButtonUnpressedImg, largeButtonPressedImg, buttonClickSound
from local.resources import menuButtonFont, menuFont, debugFont
from local.resources import altBackgroundImg
from local.vectors import Vector
from local.audio import playSoundPitch, setMusicVolume, newSong
from local.slider import Slider

# this menu will serve as the point where the game and the editor can both be accessed
def settingsMenu(screen: pygame.Surface):
    # check if music is already playing
    if not pygame.mixer.music.get_busy():
        if configs["MUSIC_ENABLED"]:
            newSong()

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

    # volume sliders
    musicSlider = Slider(Vector(50, 50), 300, 50)
    musicSlider.min = 0
    musicSlider.max = 100
    musicSlider.setValue(configs["MUSIC_VOLUME"]*100)

    soundSlider = Slider(Vector(50, 150), 300, 50)
    soundSlider.min = 0
    soundSlider.max = 100
    soundSlider.setValue(configs["SOUND_VOLUME"]*100)

    selection: str = "none" # this will be returned as the user selection made in the menu

    clock = pygame.time.Clock()

    pygame.display.set_caption("PegglePy  -  Settings")
    
    altBackgroundImg = pygame.image.load("resources/images/alt_background960x720.jpg")
    altBackgroundImg =  pygame.transform.scale(altBackgroundImg, (configs["WIDTH"], configs["HEIGHT"]))

    # main loop
    while True:
        mouseDown = False
        # event handling
        for event in pygame.event.get():
            # quit if the user clicks the close button
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            # check if the mouse button is pressed (mouse button down)
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouseDown = True
            
            # check if 1 is pressed (debug)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    configs["DEBUG_MODE"] = not configs["DEBUG_MODE"]
        # update mouse posistion
        mx, my = pygame.mouse.get_pos()
        mousePos = Vector(mx, my)

        ## check mouse input
        
        # check if mouse is over back button
        if mousePos.x > backButtonPos.x and mousePos.x < backButtonPos.x + backButtonSize.x and mousePos.y > backButtonPos.y and mousePos.y < backButtonPos.y + backButtonSize.y:
            # mouse button is down
            if mouseDown:
                selection = "mainMenu"
                
        # check if mouse is over set defaults button
        if mousePos.x > configs["WIDTH"]/2 - editorButtonSize.x/2 and mousePos.x < configs["WIDTH"]/2 - editorButtonSize.x/2 + editorButtonSize.x and mousePos.y > configs["HEIGHT"] - editorButtonSize.y - 20 and mousePos.y < configs["HEIGHT"] - 20:
            # mouse button is down
            if mouseDown:
                # set the settings to the default values
                for key, value in defaultConfigs.items():
                    configs[key] = value
                    
                # update the sliders
                musicSlider.setValue(configs["MUSIC_VOLUME"]*100)
                soundSlider.setValue(configs["SOUND_VOLUME"]*100)
                
                saveSettings()
                playSoundPitch(buttonClickSound)
                
        # check if mouse is over music checkbox
        if mousePos.x > 50 and mousePos.x < 100 and mousePos.y > 250 and mousePos.y < 300:
            # mouse button is down
            if mouseDown:
                configs["MUSIC_ENABLED"] = not configs["MUSIC_ENABLED"]
                playSoundPitch(buttonClickSound)
                if configs["MUSIC_ENABLED"]:
                    setMusicVolume(configs["MUSIC_VOLUME"])
                else:
                    setMusicVolume(0)
                    
        # check if mouse is over sound checkbox
        if mousePos.x > 50 and mousePos.x < 100 and mousePos.y > 350 and mousePos.y < 400:
            # mouse button is down
            if mouseDown:
                configs["SOUND_ENABLED"] = not configs["SOUND_ENABLED"]
                playSoundPitch(buttonClickSound)
                
        # check if mouse is over vsync checkbox
        if mousePos.x > 50 and mousePos.x < 100 and mousePos.y > 450 and mousePos.y < 500:
            # mouse button is down
            if mouseDown:
                configs["VSYNC"] = not configs["VSYNC"]
                playSoundPitch(buttonClickSound)
                
                # toggle VSYNC
                if configs["REFRESH_RATE"] == 0:
                    configs["VSYNC"] = True
                    configs["REFRESH_RATE"] = pygame.display.get_current_refresh_rate()
                else:
                    configs["VSYNC"] = False
                    configs["REFRESH_RATE"] = 0
                    
        # check if mouse is over fullscreen checkbox
        if mousePos.x > 50 and mousePos.x < 100 and mousePos.y > 550 and mousePos.y < 600:
            # mouse button is down
            if mouseDown:
                configs["FULLSCREEN"] = not configs["FULLSCREEN"]
                playSoundPitch(buttonClickSound)
                
                # toggle fullscreen
                if not configs["FULLSCREEN"]:
                    #pygame.display.toggle_fullscreen()
                    # change window size to default user resolution
                    configs["WIDTH"], configs["HEIGHT"] = defaultConfigs["WIDTH"], defaultConfigs["HEIGHT"]
                    screen = pygame.display.set_mode(
                        (configs["WIDTH"], configs["HEIGHT"]))
                else:
                    #pygame.display.toggle_fullscreen()
                    # change window size to monitor resolution
                    screen = pygame.display.set_mode(
                        (0, 0), pygame.FULLSCREEN)
                    configs["WIDTH"], configs["HEIGHT"] = screen.get_size()
                
                altBackgroundImg = pygame.image.load("resources/images/alt_background960x720.jpg")
                altBackgroundImg =  pygame.transform.scale(altBackgroundImg, (configs["WIDTH"], configs["HEIGHT"]))
                
                # update back button position
                backButtonPos = Vector(configs["WIDTH"] - 50*buttonScale-20, configs["HEIGHT"] - 50*buttonScale-20)
        
        # check if mouse is over the animations checkbox
        if mousePos.x > 50 and mousePos.x < 100 and mousePos.y > 650 and mousePos.y < 700:
            # mouse button is down
            if mouseDown:
                configs["ANIMATIONS_ENABLED"] = not configs["ANIMATIONS_ENABLED"]
                playSoundPitch(buttonClickSound)
        
        # check if mouse is over debug checkbox
        if mousePos.x > 50 and mousePos.x < 100 and mousePos.y > 750 and mousePos.y < 800:
            # mouse button is down
            if mouseDown:
                configs["DEBUG_MODE"] = not configs["DEBUG_MODE"]
                playSoundPitch(buttonClickSound)

        # draw the background
        screen.blit(altBackgroundImg, (0, 0))

        # draw the title
        menuTitle = menuFont.render("Settings", True, (255, 255, 255))
        screen.blit(menuTitle, (configs["WIDTH"]/2 - menuTitle.get_width()/2, configs["HEIGHT"]/10 - menuTitle.get_height()/2))

        # # stub
        # # draw a message text
        # messageText = menuButtonFont.render("This menu is a stub", True, (255, 255, 255))
        # screen.blit(messageText, (configs["WIDTH"]/2 - messageText.get_width()/2, configs["HEIGHT"]/2 - messageText.get_height()/2))

        # messageText = menuButtonFont.render("Settings have not been implemented yet", True, (255, 255, 255))
        # screen.blit(messageText, (configs["WIDTH"]/2 - messageText.get_width()/2, configs["HEIGHT"]/2 - messageText.get_height()/2 + 30))

        # update the volume sliders
        musicSlider.update(mousePos, pygame.mouse.get_pressed()[0])
        soundSlider.update(mousePos, pygame.mouse.get_pressed()[0])

        # update the volume
        configs["MUSIC_VOLUME"] = musicSlider.value/100
        configs["SOUND_VOLUME"] = soundSlider.value/100
        
        # update the music volume live
        if configs["MUSIC_ENABLED"]:
            setMusicVolume(configs["MUSIC_VOLUME"])

        # draw the volume sliders
        screen.blit(musicSlider.getSliderSurface(), (musicSlider.pos.x, musicSlider.pos.y))
        screen.blit(soundSlider.getSliderSurface(), (soundSlider.pos.x, soundSlider.pos.y))

        # draw the volume slider labels
        musicLabel = menuButtonFont.render("Music Volume: " + str(round(musicSlider.value)) + "%", True, (255, 255, 255))
        screen.blit(musicLabel, (musicSlider.pos.x + musicSlider.sliderRect.width/2 - musicLabel.get_width()/2, musicSlider.pos.y - musicLabel.get_height() - 5))

        soundLabel = menuButtonFont.render("Sound Volume: " + str(round(soundSlider.value)) + "%", True, (255, 255, 255))
        screen.blit(soundLabel, (soundSlider.pos.x + soundSlider.sliderRect.width/2 - soundLabel.get_width()/2, soundSlider.pos.y - soundLabel.get_height() - 5))
        
        # draw the sound and music checkboxes (square with x or no x)
        # music
        # draw the checkbox label
        musicLabel = menuButtonFont.render("Music", True, (255, 255, 255))
        screen.blit(musicLabel, (110, 250))
        # sound
        soundLabel = menuButtonFont.render("Sound", True, (255, 255, 255))
        screen.blit(soundLabel, (110, 350))
        if configs["MUSIC_ENABLED"]:
            # draw the checkbox
            pygame.draw.rect(screen, (255, 255, 255), (50, 250, 50, 50), 2)
            # draw the x
            pygame.draw.line(screen, (255, 0, 0), (50, 250), (100, 300), 2)
            pygame.draw.line(screen, (255, 0, 0), (100, 250), (50, 300), 2)
        else:
            # draw the checkbox
            pygame.draw.rect(screen, (255, 255, 255), (50, 250, 50, 50), 2)
        # sound
        if configs["SOUND_ENABLED"]:
            # draw the checkbox
            pygame.draw.rect(screen, (255, 255, 255), (50, 350, 50, 50), 2)
            # draw the x
            pygame.draw.line(screen, (255, 0, 0), (50, 350), (100, 400), 2)
            pygame.draw.line(screen, (255, 0, 0), (100, 350), (50, 400), 2)
        else:
            # draw the checkbox
            pygame.draw.rect(screen, (255, 255, 255), (50, 350, 50, 50), 2)
        # VSYNC
        vsyncLabel = menuButtonFont.render("Vsync", True, (255, 255, 255))
        screen.blit(vsyncLabel, (110, 450))
        if configs["VSYNC"]:
            # draw the checkbox
            pygame.draw.rect(screen, (255, 255, 255), (50, 450, 50, 50), 2)
            # draw the x
            pygame.draw.line(screen, (255, 0, 0), (50, 450), (100, 500), 2)
            pygame.draw.line(screen, (255, 0, 0), (100, 450), (50, 500), 2)
        else:
            # draw the checkbox
            pygame.draw.rect(screen, (255, 255, 255), (50, 450, 50, 50), 2)
        # FULLSCREEN
        fullscreenLabel = menuButtonFont.render("Fullscreen", True, (255, 255, 255))
        screen.blit(fullscreenLabel, (110, 550))
        if configs["FULLSCREEN"]:
            # draw the checkbox
            pygame.draw.rect(screen, (255, 255, 255), (50, 550, 50, 50), 2)
            # draw the x
            pygame.draw.line(screen, (255, 0, 0), (50, 550), (100, 600), 2)
            pygame.draw.line(screen, (255, 0, 0), (100, 550), (50, 600), 2)
        else:
            # draw the checkbox
            pygame.draw.rect(screen, (255, 255, 255), (50, 550, 50, 50), 2)
        # ANIMATIONS
        animationsLabel = menuButtonFont.render("Animations", True, (255, 255, 255))
        screen.blit(animationsLabel, (110, 650))
        if configs["ANIMATIONS_ENABLED"]:
            # draw the checkbox
            pygame.draw.rect(screen, (255, 255, 255), (50, 650, 50, 50), 2)
            # draw the x
            pygame.draw.line(screen, (255, 0, 0), (50, 650), (100, 700), 2)
            pygame.draw.line(screen, (255, 0, 0), (100, 650), (50, 700), 2)
        else:
            # draw the checkbox
            pygame.draw.rect(screen, (255, 255, 255), (50, 650, 50, 50), 2)
        # DEBUG
        debugLabel = menuButtonFont.render("Show debug info", True, (255, 255, 255))
        screen.blit(debugLabel, (110, 750))
        if configs["DEBUG_MODE"]:
            # draw the checkbox
            pygame.draw.rect(screen, (255, 255, 255), (50, 750, 50, 50), 2)
            # draw the x
            pygame.draw.line(screen, (255, 0, 0), (50, 750), (100, 800), 2)
            pygame.draw.line(screen, (255, 0, 0), (100, 750), (50, 800), 2)
        else:
            # draw the checkbox
            pygame.draw.rect(screen, (255, 255, 255), (50, 750, 50, 50), 2)
            

        # draw the buttons
        
        # set defaults button (located at the bottom center of the screen)
        screen.blit(menuButtonUnpressedImg, (configs["WIDTH"]/2 - editorButtonSize.x/2, configs["HEIGHT"] - editorButtonSize.y - 20))
        # draw the text
        setDefaultsText = menuButtonFont.render("Set Defaults", True, (255, 255, 255))
        screen.blit(setDefaultsText, (configs["WIDTH"]/2 - setDefaultsText.get_width()/2, configs["HEIGHT"] - editorButtonSize.y - 20 + editorButtonSize.y/2 - setDefaultsText.get_height()/2))

        # settings button (bottom right corner)
        screen.blit(buttonUnpressedImgScaled, (backButtonPos.x, backButtonPos.y))
        # draw the text
        backText = menuButtonFont.render("Back", True, (255, 255, 255))
        screen.blit(backText, (backButtonPos.x + backButtonSize.x/2 - backText.get_width()/2, backButtonPos.y + backButtonSize.y/2 - backText.get_height()/2))


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
            # save the settings
            configs["MUSIC_VOLUME"] = musicSlider.value/100
            configs["SOUND_VOLUME"] = soundSlider.value/100
            saveSettings()
            if configs["SOUND_ENABLED"]:
                playSoundPitch(buttonClickSound)
            return selection


# test
if __name__ == "__main__":
    # basic pygame setup
    pygame.init()
    screen = pygame.display.set_mode((configs["WIDTH"], configs["HEIGHT"]))
    clock = pygame.time.Clock()
    
    configs["REFRESH_RATE"] = 60

    # run the menu
    settingsMenu(screen)

    # quit pygame
    pygame.quit()
    quit()