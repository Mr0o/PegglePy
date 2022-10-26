# refer to the vectors.py module for information on these functions
from vectors import Vector

from config import WIDTH, HEIGHT, bucketVelocity

from peg import Peg

from collision import isBallTouchingPeg, resolveCollision

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

        # fake pegs on edges of bucket, allows the ball to bounce off the bucket
        peg1 = Peg(self.pos.vx+32, self.pos.vy+27)
        peg1.radius = 20
        peg2 = Peg(self.pos.vx + self.bucketBackImg.get_width()-32, self.pos.vy+27)
        peg2.radius = 20
        self.fakePegs = [peg1, peg2]

    def update(self):
        self.pos.add(self.vel)

        # if bucket collided with wall
        if self.pos.vx > (WIDTH - self.bucketBackImg.get_width()) or self.pos.vx < self.bucketBackImg.get_width() - 300:
            self.vel.vx *= -1
        
        for fakePeg in self.fakePegs:
            fakePeg.pos.add(self.vel)
            fakePeg.vel = self.vel
    
    def reset(self):
        self.pos = Vector(WIDTH/2, HEIGHT - self.bucketBackImg.get_height())  # position
        self.vel = Vector(bucketVelocity, 0)  # velocity

        peg1 = Peg(self.pos.vx+32, self.pos.vy+27)
        peg1.radius = 20
        peg2 = Peg(self.pos.vx + self.bucketBackImg.get_width()-32, self.pos.vy+27)
        peg2.radius = 20
        self.fakePegs = [peg1, peg2]
    
    # the bucket has fake pegs on the edges, this is so the ball can bounce off of the bucket
    def isBallCollidingWithBucketEdge(self, ball):
        for fakePeg in self.fakePegs.copy():
            if isBallTouchingPeg(ball.pos.vx, ball.pos.vy, ball.radius, fakePeg.pos.vx, fakePeg.pos.vy, fakePeg.radius):
                return True, fakePeg
        return False, None

    def isInBucket(self, x, y):
        return (y > HEIGHT - self.bucketBackImg.get_height()+8 and (x > self.pos.vx - self.bucketBackImg.get_width() + 165*2 and x < self.pos.vx + self.bucketBackImg.get_width() - 30))