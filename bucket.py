# refer to the vectors.py module for information on these functions
from vectors import Vector

from config import WIDTH, HEIGHT

import pygame

class Bucket:
    def __init__(self):
        self.bucketBackImg = pygame.image.load("resources/images/bucket/back150x28.png")
        self.bucketFrontImg = pygame.image.load("resources/images/bucket/front150x28.png")

        self.bucketCenterX = self.bucketBackImg.get_width() / 2

        self.pos = Vector(WIDTH/2, HEIGHT - self.bucketBackImg.get_height())  # position
        self.acc = Vector(0, 0)  # acceleration
        self.vel = Vector(0, 0)  # velocity
