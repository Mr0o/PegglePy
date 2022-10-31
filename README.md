# PegglePy
A clone of peggle written in python using pygame

The code itself is quite messy and I plan to eventually rewrite/refactor most of the project to clean it up
However, this will take a long time, and I don't know when I will ever get around to this

# Installation instructions
*Windows*
- Download the PegglePy repository as a zip
- Extract PegglePy.zip
- Install python 3 from the python website
- From within the PegglePy directory, open the cmd prompt and type: 
-     pip3 install -r requirements.txt 
- or alternatively:
-     pip3 install pygame, numpy, samplerate, tkinter, pickle
- From within the PegglePy folder on your computer, run "run.py"

*Linux*
- Install python 3 (most distributions already have python 3 installed)
- From within the PegglePy directory, open a terminal and type: 
-     pip3 install -r requirements.txt 
- or alternatively:
-     pip3 install pygame, numpy, samplerate, tkinter, pickle
- From within the PegglePy directory, type into the terminal:
-     python3 run.py

# Usage instructions
*Play the game*
-  To start, execute 'run.py'
-  You will be prompted to select a level, if you dont have any levels just click cancel, this will load a default level
-  The game works similar to peggle, to launch the ball just point with the mouse and left click
-  To win, try to hit all the orange pegs before you run out of balls (you start with 10)
-  Each peg scores a number of points and the total score is represented by the blue text in the top left
-  Orange pegs are 100 points
-  Blue pegs are 10 points
-  Green pegs are alos 10 points, but when they are hit, they activate your power up
-  Your powerup is shown by the green text at the top center of the screen, when it is glowing, your powerup is active
-  If the ball goes into the bucket moving accross the bottom of the screen, you will get a free ball added to your ball count
-  You can use the scroll wheel to help fine tune your aim
-  The game is over when you have cleared all the orange pegs

*power ups*
- "Spooky"    : When the ball reaches the bottom of the screen, it will start back at the top
- "Multiball" : A second ball will be spwaned in the game wherever you hit the green peg
- "Zenball"   : When you launch the ball on your next turn, the computer will calculate the best possible move and adjust your aim
- "guideball" : For the next 3 turns, you will get a better aim trajectory visual

*Create Levels*
-  To start the editor, execute 'editor.py'
-  Left click anywhere on the game window to place a peg on the screen
-  All of your pegs will be blue, but when you play the game, they will be randomly assigned a color
-  To delete pegs, click on a peg with the right mouse button
-  To save your level, press S on the keyboard and enter the name of the level
-  To play the level exit the editor and execute 'run.py', then select your level when prompted
-  To load a level into the editor, press L on the keyboard and select the level you want to edit

*Settings and debug*
- To mute sound effects, press M
- To mute music, press N
- To Load a level, press L
- To Reset the level, press SPACE
- To pause the game, press ESC
- To enable the debug features, press 1
- To enable cheats, press 2
- To change the current powerup, press 3
- To show the screen segment lines, press 4 (must have debug enabled)
- To decrease segment count, press 5
- To increase segment count, press 6
- To show full calculated trajectory, press 7 (must have debug enabled)
- To enable slow motion (cap framerate to 30), press 0
