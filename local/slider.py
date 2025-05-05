## gui element for slider
## slider is a horizontal bar with a knob that can be moved to change a value
import pygame

from local.vectors import Vector

class Slider:
    def __init__(self, pos : Vector, width : int, height : int) -> None:
        self.pos = pos
        self.min = 0
        self.max = 0
        self.value = 0
        self.knobPos = Vector(pos.x, 0)
        self.knobWidth = height * 2
        self.knobHeight = height
        self.knobColor = (0, 0, 0)

        self.sliderRect = pygame.Rect(self.pos.x, self.pos.y, width, height)
        self.dragging = False  # flag to track if slider is being dragged
        self.prevClick = False # flag to determine if click was already held down

    def getSliderSurface(self) -> pygame.Surface:
        # create a surface for the slider
        sliderSurface = pygame.Surface((self.sliderRect.width, self.sliderRect.height))
        sliderSurface.fill((255, 255, 255))

        # draw the sliderRect
        pygame.draw.rect(sliderSurface, (0, 0, 0), (0, 0, self.sliderRect.width, self.sliderRect.height), 2)
        
        # draw the knob
        pygame.draw.rect(
            sliderSurface,
            self.knobColor,
            (
                self.knobPos.x - self.pos.x,
                self.sliderRect.height / 2 - self.knobHeight / 2,
                self.knobWidth,
                self.knobHeight
            )
        )
        
        return sliderSurface

    def update(self, mousePos : Vector, isClick : bool) -> None:
        if isClick:
            # Only enable dragging if this is the start of a click while over the slider.
            if not self.prevClick and not self.dragging:
                if (mousePos.x > self.pos.x and mousePos.x < self.pos.x + self.sliderRect.width and
                    mousePos.y > self.pos.y and mousePos.y < self.pos.y + self.sliderRect.height):
                    self.dragging = True

            if self.dragging:
                # Update the knob position based on the mouse's x position even if the mouse leaves the slider bounds.
                self.knobPos.x = mousePos.x - self.knobWidth / 2

                # Enforce slider boundaries for the knob
                if self.knobPos.x < self.pos.x:
                    self.knobPos.x = self.pos.x
                elif self.knobPos.x > self.pos.x + self.sliderRect.width - self.knobWidth:
                    self.knobPos.x = self.pos.x + self.sliderRect.width - self.knobWidth

                # Update the value based on the knob's position
                self.value = round(self.min + (self.knobPos.x - self.pos.x) /
                                   (self.sliderRect.width - self.knobWidth) * (self.max - self.min))
            # Record that a click is currently held down
            self.prevClick = True
        else:
            # Reset both dragging and previous click once the click is released.
            self.dragging = False
            self.prevClick = False

    def setValue(self, value : int) -> None:
        # set the value
        self.value = value
        
        # update the knob position
        self.knobPos.x = self.pos.x + (self.value - self.min) / (self.max - self.min) * (self.sliderRect.width - self.knobWidth)