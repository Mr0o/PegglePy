import pygame
from local.config import configs, pegRad, ballRad

pygame.init()

# AUDIO
launch_sound = pygame.mixer.Sound("resources/audio/sounds/shoot_ball.ogg")
low_hit_sound = pygame.mixer.Sound("resources/audio/sounds/peghit_low.ogg")
normal_hit_sound = pygame.mixer.Sound("resources/audio/sounds/peghit.ogg")
max_hit_sound = pygame.mixer.Sound("resources/audio/sounds/peg_hit_max.ogg")
powerUpSpooky1 = pygame.mixer.Sound("resources/audio/sounds/powerup_spooky1.ogg")
powerUpSpooky2 = pygame.mixer.Sound("resources/audio/sounds/powerup_spooky2.ogg")
powerUpSpooky3 = pygame.mixer.Sound("resources/audio/sounds/powerup_spooky3.ogg")
powerUpSpooky4 = pygame.mixer.Sound("resources/audio/sounds/powerup_spooky4.ogg")
powerUpMultiBall = pygame.mixer.Sound("resources/audio/sounds/powerup_multiball.ogg")
powerUpZenBall = pygame.mixer.Sound("resources/audio/sounds/gong.ogg")
powerUpZenBallHit = pygame.mixer.Sound("resources/audio/sounds/powerup_zen3.ogg")
powerUpGuideBall = pygame.mixer.Sound("resources/audio/sounds/powerup_guide.ogg")
powerUpNoGravity = pygame.mixer.Sound("resources/audio/sounds/aah.ogg")
freeBallSound = pygame.mixer.Sound("resources/audio/sounds/freeball2.ogg")
failSound = pygame.mixer.Sound("resources/audio/sounds/fail.ogg")
drumRoll = pygame.mixer.Sound("resources/audio/sounds/drum_roll.ogg")
cymbal = pygame.mixer.Sound("resources/audio/sounds/cymbal.ogg")
longShotSound = pygame.mixer.Sound("resources/audio/sounds/long_shot.ogg")
sighSound = pygame.mixer.Sound("resources/audio/sounds/sigh.ogg")
pegPopSound = pygame.mixer.Sound("resources/audio/sounds/peg_pop.ogg")

#Background image
backgroundImg = pygame.image.load("resources/images/background960x720.jpg")
backgroundImg =  pygame.transform.scale(backgroundImg, (configs["WIDTH"], configs["HEIGHT"]))
altBackgroundImg = pygame.image.load("resources/images/alt_background960x720.jpg")
altBackgroundImg =  pygame.transform.scale(altBackgroundImg, (configs["WIDTH"], configs["HEIGHT"]))

#Icon
gameIconImg = pygame.image.load("resources/images/balls/200x200/ball.png")
editorIconImg = pygame.image.load("resources/images/pegs/200x200/glowing_green_peg.png")

#FONT
ballCountFont = pygame.font.Font("resources/fonts/Evogria.otf", 30)
infoFont = pygame.font.Font("resources/fonts/Evogria.otf", 16)
debugFont = pygame.font.Font("resources/fonts/Evogria.otf", 14)
menuFont = pygame.font.Font("resources/fonts/Evogria.otf", 90)
menuButtonFont = pygame.font.Font("resources/fonts/Evogria.otf", 30)
helpFont = pygame.font.Font("resources/fonts/Evogria.otf", 14)
warnFont = pygame.font.Font("resources/fonts/Evogria.otf", 25)

#images
ballImg = pygame.image.load("resources/images/balls/200x200/ball.png")
#transform
ballImg = pygame.transform.scale(ballImg, (ballRad*2, ballRad*2))
#ballImg.convert_alpha()

#non hit peg
bluePegImg = pygame.image.load("resources/images/pegs/200x200/unlit_blue_peg.png")
orangePegImg = pygame.image.load("resources/images/pegs/200x200/unlit_red_peg.png")
greenPegImg = pygame.image.load("resources/images/pegs/200x200/unlit_green_peg.png")
#transform
bluePegImg = pygame.transform.scale(bluePegImg, (pegRad*2, pegRad*2))
orangePegImg = pygame.transform.scale(orangePegImg, (pegRad*2, pegRad*2))
greenPegImg = pygame.transform.scale(greenPegImg, (pegRad*2, pegRad*2))
#bluePegImg.convert_alpha()
#orangePegImg.convert_alpha()
#greenPegImg.convert_alpha()
#hit peg
hitBluePegImg = pygame.image.load("resources/images/pegs/200x200/lit_blue_peg.png")
hitOrangePegImg = pygame.image.load("resources/images/pegs/200x200/lit_red_peg.png")
hitGreenPegImg = pygame.image.load("resources/images/pegs/200x200/lit_green_peg.png")
#transform
hitPegRad = pegRad*2
hitBluePegImg = pygame.transform.scale(hitBluePegImg, (hitPegRad, hitPegRad))
hitOrangePegImg = pygame.transform.scale(hitOrangePegImg, (hitPegRad, hitPegRad))
hitGreenPegImg = pygame.transform.scale(hitGreenPegImg, (hitPegRad, hitPegRad))
#glowing peg
glowingBluePegImg = pygame.image.load("resources/images/pegs/200x200/glowing_blue_peg.png")
glowingOrangePegImg = pygame.image.load("resources/images/pegs/200x200/glowing_red_peg.png")
glowingGreenPegImg = pygame.image.load("resources/images/pegs/200x200/glowing_green_peg.png")
#transform
glowingBluePegImg = pygame.transform.scale(glowingBluePegImg, (hitPegRad, hitPegRad))
glowingOrangePegImg = pygame.transform.scale(glowingOrangePegImg, (hitPegRad, hitPegRad))
glowingGreenPegImg = pygame.transform.scale(glowingGreenPegImg, (hitPegRad, hitPegRad))

# Bucket
bucketBackImg = pygame.image.load("resources/images/bucket/back150x28.png")
bucketFrontImg = pygame.image.load("resources/images/bucket/front150x28.png")

#hitBluePegImg.convert_alpha()
#hitOrangePegImg.convert_alpha()
#hitGreenPegImg.convert_alpha()

#EDITOR stuff
# peg placement sound
newPegSound = pygame.mixer.Sound("resources/audio/sounds/peg_pop.ogg")
# delPegSound = pygame.mixer.Sound("resources/audio/sounds/hitmarker.wav")
invalidPegSound = pygame.mixer.Sound("resources/audio/sounds/tonelo.ogg")

# pegs img with transparency (for mouse hover (blue) and invalid peg placement (red))
transparentPegImg = bluePegImg.copy()
# set alpha to 50
transparentPegImg.fill((255, 255, 255, 50), None, pygame.BLEND_RGBA_MULT)

# create a second copy of the peg image, but with a red tint
invalidPegImg = bluePegImg.copy()
invalidPegImg.fill((255, 0, 0, 60), None, pygame.BLEND_RGBA_MULT)

#MENU stuff
# menu music
menuMusicPath = "resources/audio/music/Menu (Duel {Peggle Deluxe}).mp3"
buttonHoverSound = pygame.mixer.Sound("resources/audio/sounds/button_hover.ogg")
buttonClickSound = pygame.mixer.Sound("resources/audio/sounds/button_press.ogg")

#menu buttons
buttonScale = 1 # change this to scale the buttons (kinda pointless, but whatever)
startButtonImg = pygame.image.load("resources/images/game-menu-buttons/start.png")
startButtonImg = pygame.transform.scale(startButtonImg, (buttonScale * startButtonImg.get_width(), buttonScale * startButtonImg.get_height()))
stopButtonImg = pygame.image.load("resources/images/game-menu-buttons/stop.png")
stopButtonImg = pygame.transform.scale(stopButtonImg, (buttonScale * stopButtonImg.get_width(), buttonScale * stopButtonImg.get_height()))
settingsButtonImg = pygame.image.load("resources/images/game-menu-buttons/settings.png")
settingsButtonImg = pygame.transform.scale(settingsButtonImg, (buttonScale * stopButtonImg.get_width(), buttonScale * stopButtonImg.get_height()))
cancelButtonImg = pygame.image.load("resources/images/game-menu-buttons/cancel.png")
cancelButtonImg = pygame.transform.scale(cancelButtonImg, (buttonScale * stopButtonImg.get_width(), buttonScale * stopButtonImg.get_height()))
acceptButtonImg = pygame.image.load("resources/images/game-menu-buttons/accept.png")
acceptButtonImg = pygame.transform.scale(acceptButtonImg, (buttonScale * stopButtonImg.get_width(), buttonScale * stopButtonImg.get_height()))
restartButtonImg = pygame.image.load("resources/images/game-menu-buttons/restart.png")
restartButtonImg = pygame.transform.scale(restartButtonImg, (buttonScale * stopButtonImg.get_width(), buttonScale * stopButtonImg.get_height()))
musicONButtonImg = pygame.image.load("resources/images/game-menu-buttons/musicON.png")
musicONButtonImg = pygame.transform.scale(musicONButtonImg, (buttonScale * stopButtonImg.get_width(), buttonScale * stopButtonImg.get_height()))
musicOFFButtonImg = pygame.image.load("resources/images/game-menu-buttons/musicOFF.png")
musicOFFButtonImg = pygame.transform.scale(musicOFFButtonImg, (buttonScale * stopButtonImg.get_width(), buttonScale * stopButtonImg.get_height()))
buttonPressedImg = pygame.image.load("resources/images/game-menu-buttons/buttonPressed.png")
buttonPressedImg = pygame.transform.scale(buttonPressedImg, (buttonScale * stopButtonImg.get_width(), buttonScale * stopButtonImg.get_height()))
buttonUnpressedImg = pygame.image.load("resources/images/game-menu-buttons/buttonUnpressed.png")
buttonUnpressedImg = pygame.transform.scale(buttonUnpressedImg, (buttonScale * stopButtonImg.get_width(), buttonScale * stopButtonImg.get_height()))
largeButtonPressedImg = pygame.image.load("resources/images/game-menu-buttons/largeButtonPressed.png")
largeButtonPressedImg = pygame.transform.scale(largeButtonPressedImg, (buttonScale * stopButtonImg.get_width()*2, buttonScale * stopButtonImg.get_height()))
largeButtonUnpressedImg = pygame.image.load("resources/images/game-menu-buttons/largeButtonUnpressed.png")
largeButtonUnpressedImg = pygame.transform.scale(largeButtonUnpressedImg, (buttonScale * stopButtonImg.get_width()*2, buttonScale * stopButtonImg.get_height()))

