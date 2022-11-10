class PowerUp():
    def __init__(self) -> None:
        # default powerup is spooky
        self.type = PowerUpTypes.SPOOKY


#enum
#(spooky, multiball, zenball, guideball, spooky-multiball)
class PowerUpTypes:
    SPOOKY = "spooky"
    MULTIBALL = "multiball"
    ZENBALL = "zenball"
    GUIDEBALL = "guideball"
    SPOOKY_MULTIBALL = "spooky-multiball"

    