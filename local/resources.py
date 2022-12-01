import pygame
from local.config import WIDTH, HEIGHT

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
freeBallSound = pygame.mixer.Sound("resources/audio/sounds/freeball2.ogg")
failSound = pygame.mixer.Sound("resources/audio/sounds/fail.ogg")
drumRoll = pygame.mixer.Sound("resources/audio/sounds/drum_roll.ogg")
cymbal = pygame.mixer.Sound("resources/audio/sounds/cymbal.ogg")
longShotSound = pygame.mixer.Sound("resources/audio/sounds/long_shot.ogg")
sighSound = pygame.mixer.Sound("resources/audio/sounds/sigh.ogg")

#Background image
backgroundImg = pygame.image.load("resources/images/background960x720.jpg")
backgroundImg =  pygame.transform.scale(backgroundImg, (WIDTH, HEIGHT))

#Icon
gameIconImg = pygame.image.load("resources/images/balls/200x200/ball.png")

#FONT
ballCountFont = pygame.font.Font("resources/fonts/Evogria.otf", 30)
infoFont = pygame.font.Font("resources/fonts/Evogria.otf", 16)
debugFont = pygame.font.Font("resources/fonts/Evogria.otf", 14)
menuFont = pygame.font.Font("resources/fonts/Evogria.otf", 90)