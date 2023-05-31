// this is a copy of the python peg class but in c++
#pragma once

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include "vectors.h"

// peg struct
typedef struct Peg
{
    int x;
    int y;
    float radius;
    bool isHit;
} Peg;