// this is a copy of the python vectors library that I wrote, but in C++.
#pragma once

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

extern "C"
{
    // vector struct
    typedef struct Vector
    {
        float vx;
        float vy;
        float angleRad;
    } Vector;

    // vector constructor
    Vector newVector(float vx, float vy)
    {
        Vector v;
        v.vx = vx;
        v.vy = vy;
        v.angleRad = atan2(vy, vx); // find the angle of the vector in radians
        return v;
    }

    // vector methods
    float getMag(Vector v)
    {
        return sqrt(v.vx * v.vx + v.vy * v.vy); // find the magnitude of the vector using pythagorean theorem
    }

    void normalize(Vector v)
    {
        float mag = getMag(v);
        if (mag == 0)
        {
            return;
        }
        // divide the vector by its magnitude to create a unit vector
        v.vx /= mag;
        v.vy /= mag;
    }

    void setMag(Vector v, float mag)
    {
        normalize(v);
        v.vx *= mag; // scale the vector by the magnitude
        v.vy *= mag;
    }

    // similar to setMag, but only scales the vector if its magnitude is greater than the maxMag
    void limitMag(Vector v, float maxMag)
    {
        if (getMag(v) >= maxMag)
        {
            setMag(v, maxMag);
        }
    }

    // add another vector to this vector
    void add(Vector v, Vector v2)
    {
        v.vx += v2.vx;
        v.vy += v2.vy;
    }

    // subtract another vector from this vector
    void sub(Vector v, Vector v2)
    {
        v.vx -= v2.vx;
        v.vy -= v2.vy;
    }

    // multiply this vector by a scalar
    void mult(Vector v, float scalar)
    {
        v.vx *= scalar;
        v.vy *= scalar;
    }

    // divide this vector by a scalar
    void divide(Vector v, float scalar)
    {
        v.vx /= scalar;
        v.vy /= scalar;
    }

    // return the angle of the vector in radians
    float getAngleRad(Vector v)
    {
        return atan2(v.vy, v.vx);
    }

    // return the angle of the vector in degrees
    float getAngleDeg(Vector v)
    {
        return getAngleRad(v) * 180 / M_PI;
    }

    // set the angle of the vector in radians
    void setAngleRad(Vector v, float angleRad)
    {
        float mag = getMag(v);
        v.vx = cos(angleRad) * mag;
        v.vy = sin(angleRad) * mag;
        v.angleRad = angleRad;
    }

    // set the angle of the vector in degrees
    void setAngleDeg(Vector v, float angleDeg)
    {
        setAngleRad(v, angleDeg * M_PI / 180);
    }

    // create a copy of this vector
    Vector copy(Vector v)
    {
        return newVector(v.vx, v.vy);
    }

    // creates a random vector with a maximum and minimum based on random_max
    Vector createRandomVector(int random_max)
    {
        float vx = (float)rand() / (float)(RAND_MAX / random_max) - random_max / 2;
        float vy = (float)rand() / (float)(RAND_MAX / random_max) - random_max / 2;
        return newVector(vx, vy);
    }

    // subtracts two vectors and returns the resulting vector
    Vector subVectors(Vector v, Vector v2)
    {
        Vector v3 = copy(v);
        sub(v3, v2);
        return v3;
    }

    // adds two vectors and returns the resulting vector
    Vector addVectors(Vector v, Vector v2)
    {
        Vector v3 = copy(v);
        add(v3, v2);
        return v3;
    }
}