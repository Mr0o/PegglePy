import pygame
from local.vectors import Vector

class AnimationFadeIn:
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
        self.delay     = delay
        
    def set_image(self, image: pygame.Surface):
        """Set a new image for the animation."""
        self.original = image.convert_alpha()

    def reset(self):
        """Restart the animation from zero."""
        self.elapsed = 0.0
        self.done    = False

    def update(self, dt: float):
        if self.delay > 0:
            self.delay -= dt
            if self.delay > 0:
                return
            # delay is over, reset elapsed time
            self.elapsed = 0.0
        if self.done:
            return
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.elapsed = self.duration
            self.done    = True

    def draw(self, surf: pygame.Surface):
        if self.delay > 0:
            return
        # progress 0→1
        p = min(self.elapsed / self.duration, 1.0)
        # scale interpolation (easing in/out)
        scale = self.start + (self.end - self.start) * (p * p)
        # alpha interpolation
        alpha = int(255 * p)

        w = int(self.original.get_width()  * scale)
        h = int(self.original.get_height() * scale)
        img = pygame.transform.smoothscale(self.original, (w, h))
        img.set_alpha(alpha)

        x = self.pos.x - w//2
        y = self.pos.y - h//2
        surf.blit(img, (x, y))