import pygame.mixer, pygame.sndarray
from random import randint
try:
    from samplerate import resample
except ImportError:
    print("WARN: samplerate is not installed, some audio effects will not work")
    def resample(array, ratio, mode):
        return array

from local.userConfig import configs


pygame.mixer.init(44100,-16,2,4096)
def playSoundPitch(sound_file, pitch = 1.0, volume = configs["SOUND_VOLUME"]) -> None:
    try:
        if configs["SOUND_ENABLED"]:
            # choose a file and make a sound object
            sound = pygame.mixer.Sound(sound_file)

            # load the sound into an array
            snd_array = pygame.sndarray.array(sound)

            # resample. args: (target array, ratio, mode), outputs ratio * target array.
            snd_resample = resample(snd_array, pitch, "sinc_fastest").astype(snd_array.dtype)

            # take the resampled array, make it an object and stop playing after 2 seconds.
            snd_out = pygame.sndarray.make_sound(snd_resample)
            snd_out.set_volume(volume) # set the volume
            snd_out.play()
    except Exception as e:
        if configs["DEBUG_MODE"]:
            print(f"WARN: Unable to play sound '{sound_file}' - Exception:  {e}")
            print("Does the file exist?")


def loadRandMusic():
    # load random music
    r = randint(1, 10)
    pygame.mixer.music.load(
        "resources/audio/music/Peggle Beat " + str(r) + " (Peggle Deluxe).mp3")
    
def playMusic():
    if configs["MUSIC_ENABLED"]:
        setMusicVolume(configs["MUSIC_VOLUME"])
        pygame.mixer.music.play(-1) # looping forever
    else:
        stopMusic()

def pauseMusic():
    pygame.mixer.music.pause()

def unpauseMusic():
    pygame.mixer.music.unpause()
    
def autoPauseMusic():
    # pause if playing, unpause if paused
    if pygame.mixer.music.get_busy():
        pauseMusic()
    else:
        unpauseMusic()

def stopMusic():
    pygame.mixer.music.stop()

def setMusicVolume(volume):
    pygame.mixer.music.set_volume(volume)
    
def newSong():
    stopMusic()
    loadRandMusic()
    playMusic()
