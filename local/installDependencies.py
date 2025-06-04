# check if the dependencies are installed, if not, install them automatically
import sys
import subprocess

from local.userConfig import configs
    
# skip installing dependencies if the --skip-auto-install flag is passed
if "--skip-auto-install" not in sys.argv:
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

        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            import pygame
            import numpy
            import samplerate
        except Exception as e:
            print("ERROR: Failed to install dependencies.")
            print("Details: " + str(e))
            sys.exit(1)
    # exit if the --run-auto-install flag is passed
    if "--run-auto-install" in sys.argv:
        print("Dependencies are installed.")
        sys.exit(0)
    if configs["DEBUG_MODE"]:
        print("DEBUG: Dependencies are installed.\n")
else:
    print("Skipping automatic dependency installation. Please ensure all dependencies are installed manually.\n")
    
    # test if the dependencies are installed without try-except block
    import pygame
    import numpy
    import samplerate
