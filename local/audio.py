import pygame.mixer, pygame.sndarray
try:
    from samplerate import resample
except ImportError:
    print("WARN: Unable to import samplerate, please install it with 'pip install samplerate'")
    print("Some sound effects will not be played correctly.")
    def resample(array, ratio, mode):
        return array

from local.config import debug

def playSoundPitch(sound_file, pitch = 1.0):
    try:
        pygame.mixer.init(44100,-16,2,4096)
        # choose a file and make a sound object
        sound = pygame.mixer.Sound(sound_file)

        # load the sound into an array
        snd_array = pygame.sndarray.array(sound)

        # resample. args: (target array, ratio, mode), outputs ratio * target array.
        snd_resample = resample(snd_array, pitch, "sinc_fastest").astype(snd_array.dtype)

        # take the resampled array, make it an object and stop playing after 2 seconds.
        snd_out = pygame.sndarray.make_sound(snd_resample)
        snd_out.play()
    except Exception as e:
        if debug:
            print(f"WARN: Unable to play sound '{sound_file}' - Exception:  {e}")
            print("Does the file exist?")


class GameAudioPlayer:
    def __init__(self) -> None:
        self.soundEnabled = True
        self.musicEnabled = True

    def playPowerUpSound(self, powerUpType : str = "spooky"):
        playSoundPitch("")
