# refer to the vectors.py module for information on these functions
from vectors import Vector

from config import WIDTH, HEIGHT, bucketVelocity

import pygame

class Bucket:
    def __init__(self):
        self.bucketBackImg = pygame.image.load("resources/images/bucket/back150x28.png")
        self.bucketFrontImg = pygame.image.load("resources/images/bucket/front150x28.png")

        self.bucketCenterX = self.bucketBackImg.get_width() / 2

        self.pos = Vector(WIDTH/2, HEIGHT - self.bucketBackImg.get_height())  # position
        self.vel = Vector(bucketVelocity, 0)  # velocity

    def update(self):
        self.pos.add(self.vel)

        # if bucket collided with wall
        if self.pos.vx > (WIDTH - self.bucketBackImg.get_width()) or self.pos.vx < self.bucketBackImg.get_width() - 150:
            self.vel.vx *= -1
    
    def isInBucket(self, x, y):
        if (y > HEIGHT - self.bucketBackImg.get_height() and (x > self.pos.vx - self.bucketBackImg.get_width() + 165 and x < self.pos.vx + self.bucketBackImg.get_width() - 15)):
            return True
        else:
            return False