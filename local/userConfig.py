# module to load and set game settings and variables persistently between game sessions

# dictionary to store the settings (key, value) pairs
# the values here are defaults, they will be overwritten by the user.cfg file
configs = {
    "WIDTH": 1200,
    "HEIGHT": 900,
    "FULLSCREEN": False,
    "VSYNC": True,
    "REFRESH_RATE": -1,
    "DEBUG_MODE": False,
    "SOUND_ENABLED": True,
    "SOUND_VOLUME": 0.25,
    "MUSIC_ENABLED": True,
    "MUSIC_VOLUME": 0.25,
    "ANIMATIONS_ENABLED": True,
}

defaultConfigs = configs.copy()

# read the user.cfg file and set the variables
def loadSettings() -> None:
    # the user.cfg contains settings such as resolution, sound volume, music volume, etc.
    if configs["DEBUG_MODE"]:
        print("DEBUG: Loading settings...")
    ### read the file ###
    try:
        with open("user.cfg", "r") as f:
            # read the file line by line
            for line in f:
                # parse the key and value from the line
                key, value = line.strip().split("=")
                if key in ["FULLSCREEN", "DEBUG_MODE", "SOUND_ENABLED", "MUSIC_ENABLED", "VSYNC", "ANIMATIONS_ENABLED"]:
                    value = value == "True"
                elif key in ["SOUND_VOLUME", "MUSIC_VOLUME", "WIDTH", "HEIGHT"]:
                    value = float(value)
                    
                # set the value in the configs dictionary
                configs[key] = value
                
        # check if REFRESH_RATE is set to -1, if so, set it to the monitor's refresh rate
        if configs["REFRESH_RATE"] == -1:
            import pygame
            pygame.init()
            configs["REFRESH_RATE"] = pygame.display.get_current_refresh_rate()
            defaultConfigs["REFRESH_RATE"] = configs["REFRESH_RATE"]
            saveSettings()
                
    except FileNotFoundError:
        # if the file doesn't exist, create it
        saveSettings()
    except Exception as e:
        print(f"Failed loading settings: {e}")
        return
       
        
def saveSettings() -> None:
    # save the variables to the user.cfg file
    if configs["DEBUG_MODE"]:
        print("DEBUG: Saving settings...")

    try:
        with open("user.cfg", "w") as f:
            for key, value in configs.items():
                f.write(f"{key}={value}\n")
    except Exception as e:
        print(f"Failed saving settings: {e}")
        
if __name__ == "__main__":
    loadSettings()
    saveSettings()
    print(configs)
    print("Settings loaded and saved successfully.")
    