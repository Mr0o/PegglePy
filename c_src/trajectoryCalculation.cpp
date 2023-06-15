// comand to compile this file (you will need to have gcc installed):
//  g++ -fPIC -shared -o trajectoryCalculation.so trajectoryCalculation.cpp

#include <time.h>
#include <vector>
#include <array>

#include "vectors.h"
#include "ball.h"
#include "peg.h"
#include "collision.h"

// function that calculates the trajectory of a projectile
// input: aim vector, startPos vector, pegs array, pegs array size, bucketPegs array, bucketPegs array size,
//  collisionGuideBall boolean, depth integer, debug boolean

// returns an std::array of std::arrays of floats (x and y) for each position of the fakeBall
extern "C" std::array<std::array<float, 2>, 5000> *fakeBallPosListFloat = new std::array<std::array<float, 2>, 5000>();
extern "C" std::array<std::array<float, 2>, 5000> *calcTrajectory(float aimX, float aimY, float startPosX, float startPosY, bool collisionGuideBall, int depth, bool debug,
                                                 float ballMass, float ballRadius, float ballGravityX, float ballGravityY, float ballMaxBallVelocity, int WIDTH, int HEIGHT,
                                                 float *pegPosListX, float *pegPosListY, int pegPosListSize, float pegRad, float launchForce)
{
    // create a vector of peg positions
    std::vector<Vector> *pegPosList = new std::vector<Vector>();
    for (int i = 0; i < pegPosListSize; i++)
    {
        pegPosList->push_back(newVector(pegPosListX[i], pegPosListY[i]));
    }

    // clear the fakeBallPosListFloat
    fakeBallPosListFloat->fill({0, 0});

    // create a vector of balls
    std::vector<Ball> *balls = new std::vector<Ball>();

    // previous fakeball
    Ball previousFakeBall = newBall(startPosX, startPosY, ballMass, ballRadius, ballGravityX, ballGravityY, ballMaxBallVelocity, WIDTH, HEIGHT);

    bool hit = false; // boolean to check if the ball has hit a peg

    Vector traj; // trajectory vector

    // collection of fakeBall positions
    std::vector<Vector> *fakeBallPosList = new std::vector<Vector>();

    Ball fakeBall;
    for (int i = 0; i < depth; i++)
    {
        fakeBall = newBall(previousFakeBall.pos.vx, previousFakeBall.pos.vy, ballMass, ballRadius, ballGravityX, ballGravityY, ballMaxBallVelocity, WIDTH, HEIGHT);

        // only on the first iteration
        if (i == 0)
        {
            traj = subVectors(newVector(aimX, aimY), newVector(startPosX, startPosY));
            setMag(traj, launchForce);
            applyForce(fakeBall, traj);
        }

        // every iteration except the first
        if (i != 0)
        {
            applyForce(fakeBall, previousFakeBall.acc);
            applyForce(fakeBall, previousFakeBall.vel);
        }

        // --collision detection--
        if (hit) // -powerup- // if ball has collided then stop calculating and return
        {
            for (Vector pegPos : *pegPosList)
            {
                // check if ball is touching peg
                if (isBallTouchingPeg(fakeBall.pos.vx, fakeBall.pos.vy, fakeBall.radius, pegPos.vx, pegPos.vy, pegRad))
                {
                    // we are done, return the fakeBallPosList
                    return fakeBallPosListFloat;
                }
            }
        }
        else if (collisionGuideBall && !hit) // if guideball powerup is being used
        {
            for (Vector pegPos : *pegPosList)
            {
                // check if ball is touching peg
                if (isBallTouchingPeg(fakeBall.pos.vx, fakeBall.pos.vy, fakeBall.radius, pegPos.vx, pegPos.vy, pegRad))
                {
                    // resolve collision
                    float *ballCalculations = resolveCollision(fakeBall.pos.vx, fakeBall.pos.vy, fakeBall.vel.vx, fakeBall.vel.vy, fakeBall.radius, fakeBall.mass, pegRad, pegPos.vx, pegPos.vy);

                    // set the balls position and velocity to the returned values from the resolveCollision function
                    fakeBall.pos.vx = ballCalculations[0];
                    fakeBall.pos.vy = ballCalculations[1];
                    fakeBall.vel.vx = ballCalculations[2];
                    fakeBall.vel.vy = ballCalculations[3];

                    hit = true; // first hit, which means we can keep calculating until we hit the second peg
                }
            }
        }
        else if (!collisionGuideBall) // normal // if ball has collided then stop calculating and return
        {
            for (Vector pegPos : *pegPosList)
            {
                // check if ball is touching peg
                if (isBallTouchingPeg(fakeBall.pos.vx, fakeBall.pos.vy, fakeBall.radius, pegPos.vx, pegPos.vy, pegRad))
                {
                    if (!debug)
                    {
                        // we have hit a peg which means we are done
                        return fakeBallPosListFloat;
                    }
                    else
                    {
                        // resolve collision
                        float *ballCalculations = resolveCollision(fakeBall.pos.vx, fakeBall.pos.vy, fakeBall.vel.vx, fakeBall.vel.vy, fakeBall.radius, fakeBall.mass, pegRad, pegPos.vx, pegPos.vy);

                        // set the balls position and velocity to the returned values from the resolveCollision function
                        fakeBall.pos.vx = ballCalculations[0];
                        fakeBall.pos.vy = ballCalculations[1];
                        fakeBall.vel.vx = ballCalculations[2];
                        fakeBall.vel.vy = ballCalculations[3];
                    }
                }
            }
        }

        // update the fakeBall
        update(fakeBall);

        if (fakeBall.pos.vy > HEIGHT) // if the ball has gone off the screen we can stop calculating
        {
            break;
        }

        // append the fakeBall position to the fakeBallPosList
        fakeBallPosList->push_back(newVector(fakeBall.pos.vx, fakeBall.pos.vy));

        // append the fakeBall position to the fakeBallPosListFloat std::array
        (*fakeBallPosListFloat).at(i) = {fakeBall.pos.vx, fakeBall.pos.vy};

        // set the previousFakeBall to the current fakeBall
        previousFakeBall = newBall(fakeBall.pos.vx, fakeBall.pos.vy, ballMass, ballRadius, ballGravityX, ballGravityY, ballMaxBallVelocity, WIDTH, HEIGHT);
        previousFakeBall.vel = newVector(fakeBall.vel.vx, fakeBall.vel.vy);
        previousFakeBall.acc = newVector(fakeBall.acc.vx, fakeBall.acc.vy);
    }

    return fakeBallPosListFloat;
}