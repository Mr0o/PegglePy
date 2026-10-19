from __future__ import annotations
from collections import OrderedDict
import pygame
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from local.peg import Peg
from local.vectors import Vector
from local.userConfig import configs
from local.resources import hitBluePegImg, hitOrangePegImg, hitGreenPegImg
from local.resources import bluePegImg, orangePegImg, greenPegImg

_scaled_animation_images: OrderedDict[
    tuple[pygame.Surface, int, int, int], pygame.Surface
] = OrderedDict()
_SCALED_ANIMATION_CACHE_SIZE = 512
_converted_animation_images: dict[pygame.Surface, pygame.Surface] = {}
_ANIMATION_PROGRESS_STEPS = 32
MAX_ANIMATED_PEGS = 2000


def shouldAnimatePegs(peg_count: int) -> bool:
    return peg_count <= MAX_ANIMATED_PEGS


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
        self._source_image = None
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
        self.completion_drawn = False

    def set_image(self, image: pygame.Surface):
        """Set a new image for the animation."""
        if image is self._source_image:
            return
        self._source_image = image
        self.original = _converted_animation_images.get(image)
        if self.original is None:
            self.original = image.convert_alpha()
            _converted_animation_images[image] = self.original

    def startFadeIn(self, delay: float = 0.0):
        """start the fade in animation from zero."""
        self.delay = delay
        self.elapsed = 0.0
        self.done    = False
        self.completion_drawn = False
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
        if configs["ANIMATIONS_ENABLED"] is False:
            self.done = True
            self.startTrigger = False
            return
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
        if self.original is None:
            return
        if self.done:
            if self.fadeIn:
                surf.blit(
                    self.original,
                    (
                        self.pos.x - self.original.get_width() // 2,
                        self.pos.y - self.original.get_height() // 2,
                    ),
                )
            return
        if self.delay > 0:
            return

        if self.fadeIn:
            # progress 0→1
            p = min(self.elapsed / self.duration, 1.0)
        elif self.fadeOut:
            # progress 1→0
            p = min(self.elapsed / self.duration, 1.0)
        else:
            return

        p = round(p * _ANIMATION_PROGRESS_STEPS) / _ANIMATION_PROGRESS_STEPS
        if self.fadeIn:
            scale = self.start + (self.end - self.start) * (p * p)
            alpha = int(255 * p)
        else:
            scale = self.start + (self.end - self.start) * ((1 - p) * (1 - p))
            alpha = int(255 * (1 - p))

        w = int(self.original.get_width()  * scale)
        h = int(self.original.get_height() * scale)
        cache_key = (self.original, w, h, alpha)
        img = _scaled_animation_images.get(cache_key)
        if img is None:
            img = pygame.transform.scale(self.original, (w, h))
            img.set_alpha(alpha)
            _scaled_animation_images[cache_key] = img
            if len(_scaled_animation_images) > _SCALED_ANIMATION_CACHE_SIZE:
                _scaled_animation_images.popitem(last=False)
        else:
            _scaled_animation_images.move_to_end(cache_key)

        x = self.pos.x - w//2
        y = self.pos.y - h//2
        surf.blit(img, (x, y))
        
        
# returns the next frame of the animation sequence
def getPegAnimationFrame(
    pegs: list[Peg],
    dt: float,
    target: pygame.Surface | None = None,
    completed_target: pygame.Surface | None = None,
) -> pygame.Surface:
    if target is None or target.get_size() != (
        configs["WIDTH"],
        configs["HEIGHT"],
    ):
        target = pygame.Surface(
            (configs["WIDTH"], configs["HEIGHT"]), pygame.SRCALPHA
        )
    else:
        target.fill((0, 0, 0, 0))

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
        
        # update and draw the animation
        peg.animation.set_image(pegImg)
        peg.animation.update(dt)
        if peg.animation.done and peg.animation.fadeIn:
            if completed_target is None:
                peg.animation.draw(target)
            elif not peg.animation.completion_drawn:
                peg.animation.draw(completed_target)
                peg.animation.completion_drawn = True
            continue
        peg.animation.draw(target)
        
    return target