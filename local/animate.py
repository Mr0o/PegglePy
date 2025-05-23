from __future__ import annotations
import pygame
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from local.peg import Peg
from local.vectors import Vector
from local.config import configs
from local.resources import hitBluePegImg, hitOrangePegImg, hitGreenPegImg
from local.resources import bluePegImg, orangePegImg, greenPegImg

class AnimationFade:
    def __init__(self,
                 pos: Vector,
                 duration: float = 0.5,
                 start_scale: float = 1.5,
                 delay: float = 0.0):
        """
        Simple fade+shrink animation.
        :param image: original Surface (already scaled to pegRad*2).
        :param pos:    local.vectors.Vector center position.
        :param duration: total seconds of the pop‐in.
        :param start_scale: initial scale factor.
        """
        self.original = None
        self.pos      = pos
        self.duration = duration
        self.start    = start_scale
        self.end      = 1.0
        self.elapsed  = 0.0
        self.done     = False
        self.delay    = delay
        self.startTrigger = False
        self.fadeIn   = True
        self.fadeOut  = False

    def set_image(self, image: pygame.Surface):
        """Set a new image for the animation."""
        self.original = image.convert_alpha()

    def startFadeIn(self, delay: float = 0.0):
        """start the fade in animation from zero."""
        self.delay = delay
        self.elapsed = 0.0
        self.done    = False
        self.fadeIn  = True
        self.fadeOut  = False
        if delay > 0:
            self.startTrigger = False
        else:
            self.startTrigger = True

    def startFadeOut(self, delay: float = 0.0):
        """Start the fade out animation from zero."""
        self.delay = delay
        self.elapsed = 0.0
        self.done    = False
        self.fadeIn  = False
        self.fadeOut  = True
        if delay > 0:
            self.startTrigger = False
        else:
            self.startTrigger = True

    def update(self, dt: float):
        if self.delay > 0:
            self.delay -= dt
            if self.delay > 0:
                return
            # delay is over, reset elapsed time
            self.elapsed = 0.0
            self.startTrigger = True
        else:
            self.startTrigger = False
        if self.done:
            return
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.elapsed = self.duration
            self.done    = True

    def draw(self, surf: pygame.Surface):
        
        if self.fadeIn:
            # progress 0→1
            p = min(self.elapsed / self.duration, 1.0)
            # scale interpolation (easing in/out)
            scale = self.start + (self.end - self.start) * (p * p)
            # alpha interpolation
            alpha = int(255 * p)
        elif self.fadeOut:
            # progress 1→0
            p = min(self.elapsed / self.duration, 1.0)
            # scale interpolation (easing in/out)
            scale = self.start + (self.end - self.start) * ((1 - p) * (1 - p))
            # alpha interpolation
            alpha = int(255 * (1 - p))

        w = int(self.original.get_width()  * scale)
        h = int(self.original.get_height() * scale)
        img = pygame.transform.smoothscale(self.original, (w, h))
        img.set_alpha(alpha)

        x = self.pos.x - w//2
        y = self.pos.y - h//2
        surf.blit(img, (x, y))
        
        
# returns the next frame of the animation sequence
def getPegAnimationFrame(pegs: list[Peg], dt: float) -> pygame.Surface:
    # transparent surface
    animationFrameScreen = pygame.Surface((configs["WIDTH"], configs["HEIGHT"]), pygame.SRCALPHA)
    for peg in pegs:
        if peg.color == "orange":
            if peg.isHit:
                pegImg = hitOrangePegImg
            else:
                pegImg = orangePegImg
        elif peg.color == "green":
            if peg.isHit:
                pegImg = hitGreenPegImg
            else:
                pegImg = greenPegImg
        else:
            if peg.isHit:
                pegImg = hitBluePegImg
            else:
                pegImg = bluePegImg
                    
            # set animation image
            peg.animation.original = pegImg
        
        # update and draw the animation
        peg.animation.set_image(pegImg)
        peg.animation.update(dt)
        peg.animation.draw(animationFrameScreen)
        
    return animationFrameScreen