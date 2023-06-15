// collision resolution functions implemented in c
#pragma once

#include <stdio.h>
#include <stdlib.h>
#include <math.h>

// boolean check if ball is touching peg
int isBallTouchingPeg(float b1x, float b1y, float b1r, float p1x, float p1y, float p1r)
{
    float distance = sqrt(pow((b1x - p1x), 2) + pow((b1y - p1y), 2));
    if (distance <= (b1r + p1r))
    {
        return 1;
    }
    return 0;
}

// Resolve elastic collisions against two spheres:

// - Both arguments are expected to be objects with a mass, radius, position and velocity\n
// - Returns an array of floats with the positions and velocities of the ball

float ballCalculations[4]; // array to store ball calculations
float *resolveCollision(float ballx, float bally, float ballvx, float ballvy, float ballRad, float ballMass, float pegRad, float pegx, float pegy)
{
    // find the distance between the ball and peg centers
    float distance = sqrt(pow((ballx - pegx), 2) + pow((bally - pegy), 2));
    // find the overlap between the ball and peg
    float overlap = 1.0 * (distance - ballRad - pegRad);

    // prevent divide by zero
    if (distance == 0)
    {
        distance = 0.0001; // arbitrary small number
    }

    // displace the ball away from the peg
    ballx -= overlap * (ballx - pegx) / distance;
    bally -= overlap * (bally - pegy) / distance;

    // workout dynamic collisions
    // normal
    float nx = (ballx - pegx) / distance;
    float ny = (bally - pegy) / distance;

    // tangent
    float tx = -ny;
    float ty = nx;

    // dot product tangent
    float dpTan1 = ballvx * tx + ballvy * ty;

    // dot product normal
    float dpNorm1 = ballvx * nx + ballvy * ny;
    float dpNorm2 = 0 * nx + 0 * ny; // peg velocity is 0

    // conservation of momentum in 1D
    float m1 = (dpNorm1 * (ballMass - pegRad) + 2.0 * pegRad * dpNorm2) / (ballMass + pegRad);

    // ball velocity after collision
    float ballvx1 = tx * dpTan1 + nx * m1;
    float ballvy1 = ty * dpTan1 + ny * m1;

    ballCalculations[0] = ballx;
    ballCalculations[1] = bally;
    ballCalculations[2] = ballvx1;
    ballCalculations[3] = ballvy1;

    // return the array of ball calculations
    return ballCalculations;
}