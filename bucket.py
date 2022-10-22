# refer to the vectors.py module for information on these functions
from vectors import Vector

from config import WIDTH, HEIGHT, bucketVelocity

import pygame

class Bucket:
    def __init__(self):
        self.bucketBackImg = pygame.image.load("resources/images/bucket/back150x28.png")
        self.bucketFrontImg = pygame.image.load("resources/images/bucket/front150x28.png")
        #increase the width by twice its original width
        self.bucketBackImg = pygame.transform.scale(self.bucketBackImg, (self.bucketBackImg.get_width()*2, self.bucketBackImg.get_height()))
        self.bucketFrontImg = pygame.transform.scale(self.bucketFrontImg, (self.bucketFrontImg.get_width()*2, self.bucketFrontImg.get_height()))

        self.bucketCenterX = self.bucketBackImg.get_width() / 2

        self.pos = Vector(WIDTH/2, HEIGHT - self.bucketBackImg.get_height())  # position
        self.vel = Vector(bucketVelocity, 0)  # velocity

    def update(self):
        self.pos.add(self.vel)

        # if bucket collided with wall
        if self.pos.vx > (WIDTH - self.bucketBackImg.get_width()) or self.pos.vx < self.bucketBackImg.get_width() - 300:
            self.vel.vx *= -1
    
    def reset(self):
        self.pos = Vector(WIDTH/2, HEIGHT - self.bucketBackImg.get_height())  # position
        self.vel = Vector(bucketVelocity, 0)  # velocity

    def isInBucket(self, x, y):
        return (y > HEIGHT - self.bucketBackImg.get_height() and (x > self.pos.vx - self.bucketBackImg.get_width() + 165*2 and x < self.pos.vx + self.bucketBackImg.get_width() - 30))