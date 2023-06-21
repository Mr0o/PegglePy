# PegglePy
A clone of peggle written in python using pygame

The codebase is a bit of a mess... maybe some day I will be able to clean this up and create a better architecture for the game. But most of the core elements of the game have been implemented, and getting it working has been more important than following strict conventions and *proper* design patterns, etc. If you have stumbled upon this repo, feel free to play the game and use the editor to create your own levels.


# Screenshots
<img src="screenshots/Screenshot from 2023-06-14 21-07-23.png" width="700"/>
<img src="screenshots/Screenshot from 2023-06-14 21-07-53.png" width="700"/>
<img src="screenshots/Screenshot from 2023-06-14 21-15-21.png" width="700"/>




# Installation instructions
### __Windows__
- Make sure Python 3 and pip is installed [(link)](https://www.python.org/downloads/)
- [Download](https://github.com/Mr0o/PegglePy/archive/refs/heads/main.zip) the PegglePy repository 
- Extract the zip file
- Navigate to the PegglePy folder within the extracted folder
- Double click on ```run.pyw``` to start the game

### __Linux__
- Make sure Python 3 and pip is installed (it should be installed by default on most distros) [(link)](https://www.python.org/downloads/)
- Install [tkinter](https://tkdocs.com/tutorial/install.html)
- This can be done by running the following command on debian and debian based distros (ubuntu, mint, etc)
```
sudo apt install python3-tk
```
- [Download](https://github.com/Mr0o/PegglePy/archive/refs/heads/main.zip) the PegglePy repository or use git to clone the repository
```
git clone https://github.com/Mr0o/PegglePy.git
```
- Extract the zip file
- Navigate to the PegglePy folder within the extracted folder
- Open a terminal in the PegglePy folder
- Run the following command
```
python3 run.pyw
```
</br>

### Dependencies
- pygame, numpy, samplerate, *__tkinter__*

These should be installed automatically when you run the game, but if they are not, you can install them manually by running the following command
```
pip3 install -r requirements.txt
```
Tkinter will need to be installed separately on linux

<br/>

# Usage instructions
### Play the game
-  To start, execute 'run.pyw' in python or double click on ```run.pyw``` if you are on windows
-  Once started, you will be taken to the main menu. (see the first screenshot above)
-  Press the 'Start' button to start playing the game
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

### Power ups
- "spooky"    : When the ball reaches the bottom of the screen, it will start back at the top
- "multiball" : A second ball will be spwaned in the game wherever you hit the green peg
- "zenball"   : When you launch the ball on your next turn, the computer will calculate the best possible move and adjust your aim
- "guideball" : For the next 3 turns, you will get a better aim trajectory visual
- "spooky-multiball" : A combination of the spooky and multiball powerups

### Create Levels
-  To start the editor, click on the 'Editor' button on the main menu
-  Left click anywhere on the game window to place a peg on the screen
-  All of your pegs will be blue, but when you play the game, they will be randomly assigned a color
-  To delete pegs, click on a peg with the right mouse button
-  To save your level, press S on the keyboard and enter the name of the level
-  To play the level, press excape and press L, then select your level when prompted
-  To load a level into the editor, press L on the keyboard and select the level you want to edit

### Settings and debug
- To mute sound effects, press M
- To mute music, press N
- To Load a level, press L
- To Reset the level, press SPACE
- To pause the game, press ESC
- To enable the debug features, press 1
- To enable cheats, press 2
- To change the current powerup, press 3
- To show the screen segment lines, press 4 (must have debug enabled)
- To decrease segment count, press 5 (Note: changing this number live during gameplay will break the physics)
- To increase segment count, press 6 (Note: changing this number live during gameplay will break the physics)
- To show full calculated trajectory, press 7 (must have debug enabled) (this can also be useful for cheating, lol)
- To enable a perfomance hack (speedHack), press 8
- to show the timer values on all the pegs, press 9 (must have debug enabled)
- To enable slow motion (cap framerate to 30), press 0

### Additional notes
- There is some C code in the c_src folder, I am working on some C implementations of the physics calculations to improve performance
- In the config.py there is a useCPhysics variable, this can be set to True to use the C code or False to use the python code. By default it is set to True.
- The C code is using ctypes and currently does seem to have an increased overhead, so it can actually be slower than the python code. But in most cases it makes almost no difference. (Hopefully this will lead to some performance improvements in the future)

### Command line arguements
-  You may pass the arguement '-h' or '--help' to see a list of all the command line arguements
```
python3 run.pyw -h
```
-  You may pass the arguement '-f' or '--fullscreen' to start the game in fullscreen mode
```
python3 run.pyw -f
```
-  You may pass the arguement '-d' or '--debug' to start the game with debug mode enabled
```
python3 run.pyw -d
```
-  You may pass the arguement '--no-cphysics to start the game without using the C implementation of the physics calculations
```
python3 run.pyw --no-cphysics
```