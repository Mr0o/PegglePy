# refer to the vectors.py module for information on these functions
from local.vectors import Vector
from local.config import bucketVelocity
from local.userConfig import configs
from local.peg import Peg
from local.collision import isBallTouchingPeg

import pygame
import math

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

        self.bucketCenterX = self.bucketBackImg.get_width() / 2

        self.pos = Vector(configs["WIDTH"]/2, configs["HEIGHT"] - self.bucketBackImg.get_height())  # position
        self.prevPos = self.pos.copy()  # previous position
        self.vel = Vector(-bucketVelocity/2, 0)  # velocity
        self.prevVel = self.vel.copy()  # previous velocity

        # fake pegs on edges of bucket, allows the ball to bounce off the bucket
        peg1 = Peg(self.pos.x+34, self.pos.y+30)
        peg1.radius = 20
        peg2 = Peg(self.pos.x + self.bucketBackImg.get_width()-34, self.pos.y+30)
        peg2.radius = 20
        self.fakePegs = [peg1, peg2]
        
        self.t = 0.0  # Time parameter for interpolation
        self.t_direction = 1  # Direction of t increment (1 or -1)
        
        # Adjusted speed at which 't' increments (controls overall movement speed)
        self.t_speed = 0.00225  # Units per second (magic number, 0.00225 works well)
        
        self.back_img_width = self.bucketBackImg.get_width()
        
        # fakePegOffsets are the offsets from the bucket's position to the fake pegs
        self.fakePegOffsets = [
            (34, 30),  # Left fake peg
            (self.bucketBackImg.get_width() - 34, 30)  # Right fake peg
        ]


    def update(self, dt, powerUp="none", powerActive=False):
        self.prevPos = self.pos.copy()  # previous position
        self.prevVel = self.vel.copy()  # previous velocity

        # Define the left and right edges based on the bucket's image width
        left_edge = self.back_img_width - 300
        right_edge = configs["WIDTH"] - self.back_img_width

        # Update 't' based on 'dt' and direction
        self.t += self.t_direction * self.t_speed * dt

        # Reverse direction when 't' reaches 0.0 or 1.0
        if self.t >= 1.0:
            self.t = 1.0
            self.t_direction = -1
        elif self.t <= 0.0:
            self.t = 0.0
            self.t_direction = 1

        # Use an easing function to adjust position
        # This function creates smooth acceleration and deceleration
        # Easing function: x = left_edge + (right_edge - left_edge) * (0.5 - 0.5 * cos(pi * t))
        eased_t = 0.5 - 0.5 * math.cos(math.pi * self.t)
        self.pos.x = left_edge + (right_edge - left_edge) * eased_t

        for i, fakePeg in enumerate(self.fakePegs[:2]):
            offsetX, offsetY = self.fakePegOffsets[i]
            fakePeg.pos.x = self.pos.x + offsetX
            fakePeg.pos.y = self.pos.y + offsetY

        # Handle the "spooky" power-up fake peg
        if powerUp == "spooky" and powerActive:
            if len(self.fakePegs) < 3:
                # Create the fake peg if it doesn't exist
                closedBucketFakePeg = Peg(self.pos.x + 150, self.pos.y + 453)
                closedBucketFakePeg.radius = 450
                self.fakePegs.append(closedBucketFakePeg)
            else:
                # Update its position
                fakePeg = self.fakePegs[2]
                fakePeg.pos.x = self.pos.x + 150
                fakePeg.pos.y = self.pos.y + 453
        else:
            # Remove the "spooky" fake peg if it exists
            if len(self.fakePegs) > 2:
                self.fakePegs.pop()  # Remove the last peg
                
        self.fakePegs[0].vel.x = self.vel.x
        self.fakePegs[1].vel.x = self.vel.x

  
    def reset(self):
        self.pos = Vector(configs["WIDTH"]/2, configs["HEIGHT"] - self.bucketBackImg.get_height())  # position
        self.vel = Vector(-bucketVelocity/2, 0)  # velocity
        self.prevPos = self.pos.copy()  # previous position
        self.prevVel = self.vel.copy()  # previous velocity

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
    def isBallCollidingWithBucketEdge(self, ball, dt):
        for fakePeg in self.fakePegs:
            if isBallTouchingPeg(ball, fakePeg, dt):
                return fakePeg
        return None

    def isInBucket(self, x, y):
        return (y > configs["HEIGHT"] - self.bucketBackImg.get_height()+12 and (x > self.pos.x - self.bucketBackImg.get_width() + 165*2 and x < self.pos.x + self.bucketBackImg.get_width() - 30))