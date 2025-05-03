from local.vectors import Vector # used for gravity

def installDependencies():
    try: # check that the dependencies are installed
        import pygame
        import numpy
        import samplerate
        
        # check for pygame.IS_CE
        try:
            from pygame import IS_CE
        except ImportError:
            print("pygame is installed, but pygame-ce is required.") 
            print("Installing pygame-ce...\n")
            import subprocess
            import sys
            try:
                #subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "pygame", "-y"])
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
                import pygame
            except Exception as e:
                print("ERROR: Failed to install pygame-ce.")
                print("Details: " + str(e))
                sys.exit(1)
            
    except Exception:
        # automatically install PegglePy dependencies
        print("Installing dependencies...")

        # attempt 1
        import sys
        import subprocess
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            import pygame
            import numpy
            import samplerate
        except Exception as e:
            print("ERROR: Failed to install dependencies.")
            print("Details: " + str(e))
            sys.exit(1)
    
    return True


import sys

# run the function to install the dependencies if the --run-auto-install flag is passed
if "--run-auto-install" in sys.argv:
    if installDependencies():
        print("\nDependencies installed successfully.")
        print("Game started")
    exit()
    
# skip installing dependencies if the --skip-auto-install flag is passed
if "--skip-auto-install" not in sys.argv:
    installDependencies()
    

# check if the script has been passed '-h' or '--help' as an argument
if "-h" in sys.argv or "--help" in sys.argv:
    print("Usage: python3 run.py [OPTIONS]")
    print("Options:")
    print(" -h, --help         \t Display this help message")
    print(" -f, --fullscreen   \t Launch the game in fullscreen mode")
    print(" -d, --debug        \t Show debugging information")
    print(" --no-max-velocity  \t Disable the maximum velocity of the ball")
    print(" --no-gravity       \t Disable gravity")
    print(" --run-auto-install \t Automatically install dependencies")
    print(" --skip-auto-install\t Skip automatically installing dependencies")
    sys.exit(0)


### load user settings ###
from local.userConfig import configs, loadSettings
loadSettings()

import pygame

# check if the script has been passed '-f' or '--fullscreen' as an argument
if "-f" in sys.argv or "--fullscreen" in sys.argv:
    configs["FULLSCREEN"] = True

userResolution = (configs["WIDTH"], configs["HEIGHT"])
if configs["FULLSCREEN"]:
    # get the resolution of the display monitor
    pygame.init()
    infoObject = pygame.display.Info()
    (configs["WIDTH"], configs["HEIGHT"]) = (infoObject.current_w, infoObject.current_h)
else:
    # set the resolution to userResolution
    (configs["WIDTH"], configs["HEIGHT"]) = userResolution

#power up (spooky, multiball, zenball, guideball, spooky-multiball)
powerUpType = "spooky"

# gives you a power up on every ball, can be useful for debugging/testing or if you just want to cheat
cheats = False

# debugging (displays debugging information to the screen)
# check if the script has been passed '-d' or '--debug' as an argument
if "-d" in sys.argv or "--debug" in sys.argv:
    configs["DEBUG_MODE"] = True

# when there are lots of pegs on the screen (perhaps more than a few hundred, lol), you might see performance hiccups
# this can be set to true to improve performance at the cost of visual weirdness 
# (when a peg gets hit, normally the entire frame of pegs is redrawn, but with this enabled, only the peg that was hit is redrawn, which means the pegs that are hit will be drawn out of order)
speedHack = False

# a bunch of variables (defaults)
LAUNCH_FORCE = 5.0
# check if the script has been passed '--no-max-velocity' as an argument
if "--no-max-velocity" in sys.argv:
    maxBallVelocity = 9999
else:
    maxBallVelocity = 10 # by limiting the velocity, we can prevent the ball from going crazy (physics glitches).
defaultBallMass = 4
defaultPegMass = 20 # even though the pegs do not move, they still have mass because this has an effect on the collision physics (20 is a magic number, that happens to work well)
# check if the script has been passed '--no-gravity' as an argument
if "--no-gravity" in sys.argv:
    gravity = Vector(0,0)
else:
    gravity = Vector(0, 0.045)
trajectoryDepth = 75 # how many steps to take in the normal (non-powerup) launch trajectory calculation
bucketVelocity = 2.8 # max set velocity of the bucket
ballsRemaining = 10
freeBall = False
powerUpActive = False
powerUpCount = 0
pitch = 1.0
pitchRaiseCount = 0
showCollision = False
previousAim = Vector(0,1)
shouldClear = False
autoRemovePegs = True
autoRemovePegsTimerValue = 0.4 # how much time in seconds to wait before removing a peg that a ball is stuck on
debugAutoRemovePegsTimer = False # if true, each pegs autoRemovePegsTimer will be displayed on the screen
longShotDistance = configs["WIDTH"] / 3
ballRad = 12
pegRad = 25
noGravityTimeLength = 10 # how many seconds the no-gravity power up lasts
# value to slow down or speed up the game
baseTimeScale = 1.0
timeScale = baseTimeScale
closeCallTimeScale = 0.15
odeToJoyTimeScale = 0.3
# size of rect query (radius of the ball and the peg)
queryRectSize = ballRad*1.2 + pegRad*1.2
# value to determine number of samples for collision detection
collisionSampleSize = 10
