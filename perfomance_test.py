# run a performance test on the zenball findBestTrajectory function
from random import randint
import time
from local.misc import createPegColors, loadLevel
from local.trajectory import findBestTrajectory
from local.vectors import Vector
from local.config import WIDTH, HEIGHT

runTest = False

if __name__ == "__main__":
    pegs, originPegs, orangeCount = loadLevel(createPegColors)
    startPos = Vector(WIDTH/2, 20)
    aim = Vector(WIDTH/2, HEIGHT/2)

    # run a performance test on the zenball findBestTrajectory function
    if runTest:
        testMaxRange = 40
        testDepth = 1200

        testRunTime = 5 # how long to run the test in seconds

        times = []
        runStart = time.time()

        print(f"Running test for {testRunTime} seconds...")

        i = 0
        while(time.time() < runStart + testRunTime):
            start = time.time()
            findBestTrajectory(aim, startPos, pegs, testMaxRange, testDepth)
            end = time.time()
            print(f"({i+1}) Time taken: {end-start} secs")
            times.append(end-start)
            i+=1
        runEnd = time.time()
        
        print("\nResults:")
        print(f"Total time taken:   {runEnd-runStart} secs")
        print(f"\nAverage time:       {sum(times)/len(times)} secs")
        print(f"Longest time:       {max(times)} secs")
        print(f"Shortest time:      {min(times)} secs")
        print(f"Number of pegs: {len(pegs)}")

    # find the largest depth and max range while keeping the time below the target
    else:
        targetTime = 3 # seconds

        maxRange = 20
        depth = 1000

        print("Running depth test...")
        elapsedTime = 0
        i = 0
        while(elapsedTime < targetTime/2):
            if elapsedTime < targetTime*0.80 and elapsedTime != 0:
                depth += 2500
            else:
                depth += 750
            i += 1
            start = time.time()
            findBestTrajectory(aim, startPos, pegs, maxRange, depth)
            end = time.time()
            elapsedTime = end-start
            print(f"({i}) Elapsed time:", elapsedTime)

        print("\nRunning max range test...")
        elapsedTime = 0
        i = 0
        depth *= 0.75
        while(elapsedTime < targetTime/2): 
            maxRange += 1
            i+=1
            start = time.time()
            findBestTrajectory(aim, startPos, pegs, maxRange, int(depth))
            end = time.time()
            elapsedTime = end-start
            print(f"({i}) Elapsed time:", elapsedTime)

        print("\nRunning depth test (final pass)...")
        depth = 1000
        elapsedTime = 0
        i = 0
        while(elapsedTime < targetTime):
            if elapsedTime < targetTime*0.80 and elapsedTime != 0:
                depth += 2500
            else:
                depth += 750
            i += 1
            start = time.time()
            findBestTrajectory(aim, startPos, pegs, maxRange, depth)
            end = time.time()
            elapsedTime = end-start
            print(f"({i}) Elapsed time:", elapsedTime)
        
        print("\nResults:")
        print(f"Max range: {maxRange}")
        print(f"Depth: {int(depth)}")





