# refer to the vectors.py module for information on these functions
from local.vectors import Vector

from local.config import WIDTH, HEIGHT, bucketVelocity

from local.peg import Peg

from local.collision import isBallTouchingPeg

import pygame

class Bucket:
    def __init__(self):
        ## normal bucket
        self.bucketBackImg = pygame.image.load("resources/images/bucket/back150x28.png")
        self.bucketFrontImg = pygame.image.load("resources/images/bucket/front150x28.png")
        #increase the width by twice its original width
        self.bucketBackImg = pygame.transform.scale(self.bucketBackImg, (self.bucketBackImg.get_width()*2, self.bucketBackImg.get_height()))
        self.bucketFrontImg = pygame.transform.scale(self.bucketFrontImg, (self.bucketFrontImg.get_width()*2, self.bucketFrontImg.get_height()))

        ## closed bucket
        self.bucketClosedImg = pygame.image.load("resources/images/bucket/closed150x28.png")
        #increase the width by twice its original width
        self.bucketClosedImg = pygame.transform.scale(self.bucketClosedImg, (self.bucketClosedImg.get_width()*2, self.bucketClosedImg.get_height()))

        # TODO delete this warning message when the lerping is properly implemented
        if WIDTH != 1200: print("WARN: Bucket cannot be lerped because WIDTH is not 1200, this needs to be fixed...")

        self.bucketCenterX = self.bucketBackImg.get_width() / 2

        self.pos = Vector(WIDTH/2, HEIGHT - self.bucketBackImg.get_height())  # position
        self.vel = Vector(-bucketVelocity/2, 0)  # velocity

        # fake pegs on edges of bucket, allows the ball to bounce off the bucket
        peg1 = Peg(self.pos.x+34, self.pos.y+30)
        peg1.radius = 20
        peg2 = Peg(self.pos.x + self.bucketBackImg.get_width()-34, self.pos.y+30)
        peg2.radius = 20
        self.fakePegs = [peg1, peg2]

    def update(self, powerUp = "none", powerActive = False):
        back_img_width = self.bucketBackImg.get_width()
        # TODO properly implemnt lerping (Only works if WIDTH == 1200)
        if WIDTH == 1200:
            # remaining distance if velocity is negative
            if self.vel.x < 0:
                remainingDistToEdge = self.pos.x
            # remaining distance if velocity is positive
            elif self.vel.x > 0:
                remainingDistToEdge = WIDTH - self.pos.x - back_img_width
            #slow down the bucket as it apporaches the egde of the screen
            if remainingDistToEdge < WIDTH/5.5:
                self.vel.x *= 0.99
            #speed up the bucket as it moves away from the edge of the screen
            elif remainingDistToEdge > WIDTH/9:
                self.vel.x /= 0.99
            
            if abs(self.vel.x) < 0.1:
                if self.vel.x >= 0: self.vel.x = 0.1
                else: self.vel.x = -0.1
            
            if abs(self.vel.x) > bucketVelocity:
                if self.vel.x >= 0: self.vel.x = bucketVelocity
                else: self.vel.x = -bucketVelocity

        # if bucket collided with wall
        if self.pos.x > (WIDTH - back_img_width) or self.pos.x < back_img_width - 300:
            self.vel.x *= -1

        # resolve out of bounds edge cases
        if self.pos.x < back_img_width - 300:
            self.pos.x = back_img_width - 300
        elif self.pos.x > WIDTH - back_img_width:
            self.pos.x = WIDTH - back_img_width
        
        # update position
        self.pos.add(self.vel)
        
        for fakePeg in self.fakePegs:
            fakePeg.pos.add(self.vel)
            fakePeg.vel = self.vel

        # create a fake peg for the closed bucket, to add collision
        if powerUp == "spooky" and powerActive and len(self.fakePegs) == 2:
            closedBucketFakePeg = Peg(self.pos.x+150, self.pos.y+453)
            closedBucketFakePeg.radius = 450
            self.fakePegs.append(closedBucketFakePeg)
        elif (powerUp != "spooky" or not powerActive) and len(self.fakePegs) > 2:
            self.fakePegs.pop() # remove the last peg
  
    def reset(self):
        self.pos = Vector(WIDTH/2, HEIGHT - self.bucketBackImg.get_height())  # position
        self.vel = Vector(-bucketVelocity/2, 0)  # velocity

        peg1 = Peg(self.pos.x+34, self.pos.y+30)
        peg1.radius = 20
        peg2 = Peg(self.pos.x + self.bucketBackImg.get_width()-34, self.pos.y+30)
        peg2.radius = 20
        self.fakePegs = [peg1, peg2]

    # return the image based on the powerup type
    def getImage(self, powerUp = "none", powerActive = False):
        if powerUp == "spooky" and powerActive:
            # return closed bucket, use the same back image because you cant see it anyways
            return self.bucketBackImg, self.bucketClosedImg
        # normal
        else:
            return self.bucketBackImg, self.bucketFrontImg
    
    # the bucket has fake pegs on the edges, this is so the ball can bounce off of the bucket
    def isBallCollidingWithBucketEdge(self, ball):
        for fakePeg in self.fakePegs:
            if isBallTouchingPeg(ball.pos.x, ball.pos.y, ball.radius, fakePeg.pos.x, fakePeg.pos.y, fakePeg.radius):
                return fakePeg
        return None

    def isInBucket(self, x, y):
        return (y > HEIGHT - self.bucketBackImg.get_height()+12 and (x > self.pos.x - self.bucketBackImg.get_width() + 165*2 and x < self.pos.x + self.bucketBackImg.get_width() - 30))