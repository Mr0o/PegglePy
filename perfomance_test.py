# run a performance test on the zenball findBestTrajectory function
from random import randint
import time
from local.misc import createPegColors, loadLevel
from local.trajectory import findBestTrajectory
from local.vectors import Vector
from local.userConfig import configs
from local.quadtree import QuadtreePegs, Rectangle

testMaxRange = 40
testDepth = 1200
testRunTime = 5
runTest = False

if __name__ == "__main__":
    import sys
    # take testMaxRange, testDepth, testRunTime and runTest as arguments
    if len(sys.argv) == 4:
        testMaxRange = int(sys.argv[1])
        testDepth = int(sys.argv[2])
        testRunTime = int(sys.argv[3])
        runTestArg = str(sys.argv[4])
        if runTestArg == "True":
            runTest = True
        elif runTestArg == "False":
            runTest = False
        else:
            print("Invalid argument for runTest, must be 'True' or 'False'")
            sys.exit(1)

    # dt for 165 fps
    dt = 1/165
    
    # load a level
    pegs, originPegs, orangeCount, levelFileName = loadLevel()
    print(f"Level: {levelFileName}")
    print(f"Number of pegs: {len(pegs)}")
    startPos = Vector(configs["WIDTH"]/2, 20)
    aim = Vector(configs["WIDTH"]/2, configs["HEIGHT"]/2)

    # run a performance test on the zenball findBestTrajectory function
    if runTest:
        times = []
        runStart = time.time()
        
        # create a quadtree
        quadtree = QuadtreePegs(Rectangle(configs["WIDTH"]/2, configs["HEIGHT"]/2, configs["WIDTH"]/2, configs["HEIGHT"]/2), len(pegs))
        for peg in pegs:
            quadtree.insert(peg)

        print(f"Running test for {testRunTime} seconds...")

        i = 0
        while(time.time() < runStart + testRunTime):
            start = time.time()
            findBestTrajectory(aim, startPos, pegs, testMaxRange, testDepth, quadtree, 0.016)
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
        
        # create a quadtree
        quadtree = QuadtreePegs(Rectangle(configs["WIDTH"]/2, configs["HEIGHT"]/2, configs["WIDTH"]/2, configs["HEIGHT"]/2), len(pegs))
        for peg in pegs:
            quadtree.insert(peg)

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
            findBestTrajectory(aim, startPos, pegs, quadtree, dt, maxRange, int(depth))
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
            findBestTrajectory(aim, startPos, pegs, quadtree, dt, maxRange, int(depth))
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
            findBestTrajectory(aim, startPos, pegs, quadtree, dt, maxRange, int(depth))
            end = time.time()
            elapsedTime = end-start
            print(f"({i}) Elapsed time:", elapsedTime)
        
        print("\nResults:")
        print(f"Max range: {maxRange}")
        print(f"Depth: {int(depth)}")





