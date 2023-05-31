// this is a copy of the ball class in python, but in C++.
#pragma once

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include "vectors.h"

// ball struct
typedef struct Ball
{
    int originX;
    int originY; // origin position of the ball for the reset function
    Vector pos;
    Vector vel;
    Vector acc;

    float mass;
    float radius;

    bool isLaunch;
    bool isAlive;

    bool inBucket;

    // gravity vector
    Vector gravity;

    float maxBallVelocity;

    // the width and height of the window
    int WIDTH;
    int HEIGHT;
} Ball;

// ball constructor
Ball newBall(int x, int y, float mass, float radius, int gravityX, int gravityY, float maxBallVelocity, int WIDTH, int HEIGHT)
{
    Ball b;
    b.originX = x;
    b.originY = y;

    b.pos = newVector(x, y);
    b.vel = newVector(0, 0);
    b.acc = newVector(0, 0);

    b.mass = mass;
    b.radius = radius;

    b.isLaunch = false;
    b.isAlive = false;

    b.inBucket = false;

    b.gravity = newVector(gravityX, gravityY);

    b.maxBallVelocity = maxBallVelocity;

    b.WIDTH = WIDTH;
    b.HEIGHT = HEIGHT;
    return b;
}

// ball methods

// F = M*A
// adds a force(vector) to the velocity of the ball
void applyForce(Ball b, Vector force)
{
    Vector fcopy = copy(force);
    // f.vx /= b.mass;
    // f.vy /= b.mass;
    add(b.vel, fcopy);
}

void update(Ball b)
{
    applyForce(b, b.gravity);

    b.vel.vx *= 0.9993; // drag
    add(b.vel, b.acc);
    add(b.pos, b.vel);
    mult(b.acc, 0);

    // stop the ball from going crazy, this resolves the occasional physics glitches
    limitMag(b.vel, b.maxBallVelocity);

    // if the ball collided with wall or has falled through the floor
    if (b.pos.vx > (b.WIDTH - b.radius) || b.pos.vx < b.radius)
    {
        if (b.pos.vx > (b.WIDTH - b.radius))
            b.pos.vx = b.WIDTH - b.radius;
        else if (b.pos.vx < b.radius)
            b.pos.vx = b.radius;
        b.vel.vx *= -1;
    }
    if (b.pos.vy > (b.HEIGHT - b.radius) || b.pos.vy < b.radius)
    {
        if (b.pos.vy > (b.HEIGHT - b.radius))
            b.pos.vy = b.HEIGHT - b.radius;
        else if (b.pos.vy < b.radius)
            b.pos.vy = b.radius;
        b.vel.vy *= -1;
    }
    if (b.pos.vy > (b.HEIGHT + b.radius)) {
        b.isAlive = false;
    }
}

// reset
void reset(Ball b)
{
    b.pos.vx = b.originX;
    b.pos.vy = b.originY;
    mult(b.vel, 0);
    mult(b.acc, 0);
    b.isLaunch = false;
    b.isAlive = false;
    b.inBucket = false;
}
