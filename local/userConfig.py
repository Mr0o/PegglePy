# module to load and set game settings and variables persistently between game sessions

# dictionary to store the settings (key, value) pairs
# the values here are defaults, they will be overwritten by the user.cfg file
configs = {
    "RESOLUTION": (1200, 900),
    "FULLSCREEN": False,
    "DEBUG_MODE": False,
    "SOUND_ENABLED": True,
    "SOUND_VOLUME": 0.25,
    "MUSIC_ENABLED": True,
    "MUSIC_VOLUME": 0.25
}

defaultConfigs = configs.copy()

# read the user.cfg file and set the variables
def loadSettings() -> None:
    # the user.cfg contains settings such as resolution, sound volume, music volume, etc.
    ### read the file ###
    try:
        with open("user.cfg", "r") as f:
            # read the file line by line
            for line in f:
                # parse the key and value from the line
                key, value = line.strip().split("=")
                # convert the value to the appropriate type
                if key in ["RESOLUTION"]:
                    # convert the value to a tuple of integers and remove the parentheses
                    value = tuple(map(int, value.strip("()").split(",")))
                elif key in ["FULLSCREEN", "DEBUG_MODE", "SOUND_ENABLED", "MUSIC_ENABLED"]:
                    value = value == "True"
                elif key in ["SOUND_VOLUME", "MUSIC_VOLUME"]:
                    value = float(value)
                    
                # set the value in the configs dictionary
                configs[key] = value
                
    except FileNotFoundError:
        # if the file doesn't exist, create it
        saveSettings()
    except Exception as e:
        print(f"Failed loading settings: {e}")
        return
       
        
def saveSettings() -> None:
    # save the variables to the user.cfg file
    
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
    