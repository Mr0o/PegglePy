from local.vectors import Vector # used for gravity

def installDependencies():
    try: # check that the dependencies are installed
        import pygame
        import numpy
        import samplerate
    except ImportError:
        # automatically install PegglePy dependencies
        print("Installing dependencies...")

        # attempt 1
        import sys
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        try:
            import pygame
            import numpy
            import samplerate
        except ImportError:
            # attempt 2
            try:
                import os
                os.system("pip install -r requirements.txt")
                import pygame
                import numpy
                import samplerate
            except ImportError:
                # attempt 3
                try:
                    import os
                    os.system("pip3 install -r requirements.txt")
                    import pygame
                    import numpy
                    import samplerate
                except ImportError as e:
                    print("ERROR: Failed to install dependencies. Please make sure that pip is installed and try again.")
                    print("Details: " + str(e))
                    sys.exit(1)


installDependencies()

import pygame
import sys

# hard coded window size, the game is not designed to be resized, even though it technically can be
WIDTH = 1200
HEIGHT = 900 

# check if the script has been passed '-f' or '--fullscreen' as an argument
if "-f" in sys.argv or "--fullscreen" in sys.argv:
    FULLSCREEN = True
else:
    FULLSCREEN = False

if FULLSCREEN:
    # get the resolution of the display monitor
    pygame.init()
    infoObject = pygame.display.Info()
    WIDTH = infoObject.current_w
    HEIGHT = infoObject.current_h

#power up (spooky, multiball, zenball, guideball, spooky-multiball)
powerUpType = "spooky"

# gives you a power up on every ball, can be useful for debugging/testing or if you just want to cheat
cheats = False

# debugging (displays debugging information to the screen)
debug = False

# when there are lots of pegs on the screen (perhaps more than a few hundred, lol), you might see performance hiccups
# this can be set to true to improve performance at the cost of visual weirdness 
# (when a peg gets hit, normally the entire frame of pegs is redrawn, but with this enabled, only the peg that was hit is redrawn, which means the pegs that are hit will be drawn out of order)
speedHack = False

# enable or diasble sound effects
soundEnabled = True

# enable or disable music
musicEnabled = True

# use c implementation of the collision physics (should be faster, but I have found in testing that it can actually be slower. Probably because of increased overhead)
useCPhysics = True

# a bunch of variables (defaults)
LAUNCH_FORCE = 5.0
maxBallVelocity = 8 # by limiting the velocity, we can prevent the ball from going crazy (physics glitches).
defaultBallMass = 6
defaultPegMass = 32 # the pegs mass doesnt really matter, but they need to have a mass in order for the physics to be calculated when a ball hits the pegs (in this case I have determined that 32 is a good number, magic)
gravity = Vector(0, 0.035)
trajectoryDepth = 75 # how many steps to take in the normal (non-powerup) launch trajectory calculation
bucketVelocity = 2.5 # max set velocity of the bucket
ballsRemaining = 10
freeBall = False
powerUpActive = False
powerUpCount = 0
pitch = 1.0
pitchRaiseCount = 0
showCollision = False
previousAim = Vector(0,1)
shouldClear = False
segmentCount = 20
autoRemovePegs = True
autoRemovePegsTimerValue = 0.8 # how much time in seconds to wait before removing a peg that a ball is stuck on
debugAutoRemovePegsTimer = False # if true, each pegs autoRemovePegsTimer will be displayed on the screen
longShotDistance = WIDTH/3
frameRate = 144 # the game speed is currently tied to the framerate, unfortunately, which means that you should NOT change this value
ballRad = 12
pegRad = 25

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

#hitBluePegImg.convert_alpha()
#hitOrangePegImg.convert_alpha()
#hitGreenPegImg.convert_alpha()
