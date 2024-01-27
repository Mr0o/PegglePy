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
        
    def getSliderSurface(self) -> pygame.Surface:
        # create a surface for the slider
        sliderSurface = pygame.Surface((self.sliderRect.width, self.sliderRect.height))
        sliderSurface.fill((255, 255, 255))

        # draw the sliderRect
        pygame.draw.rect(sliderSurface, (0, 0, 0), (0, 0, self.sliderRect.width, self.sliderRect.height), 2)

        # draw the value
        font = pygame.font.SysFont("Arial", 20)
        text = font.render(str(self.value), True, (0, 0, 0))
        sliderSurface.blit(text, (self.sliderRect.width/ 2 - text.get_width() / 2, self.sliderRect.height / 2 - text.get_height() / 2))
        
        # draw the knob
        pygame.draw.rect(sliderSurface, self.knobColor, (self.knobPos.x - self.pos.x, self.sliderRect.height / 2 - self.knobHeight / 2, self.knobWidth, self.knobHeight))
        
        return sliderSurface
    
    def update(self, mousePos : Vector, isClick : bool) -> None:
        # check if the mouse is within the slider rect
        if mousePos.x > self.pos.x and mousePos.x < self.pos.x + self.sliderRect.width:
            if mousePos.y > self.pos.y and mousePos.y < self.pos.y + self.sliderRect.height:
                # check if the mouse is clicked
                if isClick:
                    # move the knob
                    self.knobPos.x = mousePos.x - self.knobWidth / 2
                    
                    # check if the knob is out of bounds
                    if self.knobPos.x < self.pos.x:
                        self.knobPos.x = self.pos.x
                    elif self.knobPos.x > self.pos.x + self.sliderRect.width - self.knobWidth:
                        self.knobPos.x = self.pos.x + self.sliderRect.width - self.knobWidth
                        
                    # update the value
                    self.value = round(self.min + (self.knobPos.x - self.pos.x) / (self.sliderRect.width - self.knobWidth) * (self.max - self.min))
    
    
    def setValue(self, value : int) -> None:
        # set the value
        self.value = value
        
        # update the knob position
        self.knobPos.x = self.pos.x + (self.value - self.min) / (self.max - self.min) * (self.sliderRect.width - self.knobWidth)