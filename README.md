# PegglePy
A clone of peggle written in python using pygame

### Changes Log May 2025
- Added animation sequnce for spawning pegs at the start of the game
- Added animation sequnce for removing pegs after they've been hit and are being tallied for score

### Changes Log Febuary 2025
- Implemented quadtree algorithm for collision detection (doubles the performance in some cases)
- Added 8 more levels to the game (bringing the total to 10)
- Improved the collision physics, allowing for more robust collisions at lower framerates or higher velocities

### Changes Log September 2024
- The game now finally runs the physics independently of the frame rate (uses delta time)
- Massively improved the collisions for ball vs peg, much less buggy and chaotic now
- Tweaked the ball and peg elastics and mass values to make the ball bounciness feel right
- Added a new powerup called "no-gravity" (kinda suck ngl, probably won't keep it)
- Added circle vs line collision detection and response (not used yet but plans for future)
- Settings menu now has working sound and music volume sliders and mute buttons
- Settings are saved locally and persist between game sessions
- Removed all ctypes and 'CPhysics' from the project (it was not helping performance)
- Finally got the bucket x axis sliding movement working as intended (no longer janky looking)

# Screenshots
<img src="screenshots/Screenshot from 2023-06-14 21-07-23.png" width="700"/>
<img src="screenshots/Screenshot from 2023-06-14 21-07-53.png" width="700"/>
<img src="screenshots/Screenshot from 2023-06-14 21-15-21.png" width="700"/>

_Art/Resources borrowed from [FergusGriggs](https://github.com/FergusGriggs/PeggleTutorial)_

_PopCap and Peggle are trademarks of Electronic Arts Inc. This project is not affiliated with or endorsed by Electronic Arts Inc._

# Installation instructions
### __Windows__
- Make sure Python 3 and pip is installed [(link)](https://www.python.org/downloads/)
- [Download](https://github.com/Mr0o/PegglePy/archive/refs/heads/main.zip) the PegglePy repository 
- Extract the zip file
- Navigate to the PegglePy folder within the extracted folder
- Double click on ```run.py``` to start the game

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
python3 run.py
```
</br>

### Dependencies
- pygame-ce, numpy, samplerate, *__tkinter__*

These should be installed automatically when you run the game, but if they are not, you can install them manually by running the following command
```
pip3 install -r requirements.txt
```
Tkinter may need to be installed separately on linux

To skip the automated installation of the dependencies, you can pass the arguement '--skip-auto-install' when running the game
```
python3 run.py --skip-auto-install
```

<br/>

# Usage instructions
### Play the game
-  To start, execute 'run.py' in python or double click on ```run.py``` if you are on windows
-  Once started, you will be taken to the main menu. (see the first screenshot above)
-  Press the 'Start' button to start playing the game
-  The game works similar to peggle, to launch the ball just point with the mouse and left click
-  To win, try to hit all the orange pegs before you run out of balls (you start with 10)
-  Each peg scores a number of points and the total score is represented by the blue text in the top left
-  Orange pegs are 100 points
-  Blue pegs are 10 points
-  Green pegs are also 10 points, but when they are hit, they activate your power up
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
- "no-gravity" : The ball will experience zero gravity for the next 10 seconds

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
- To show the quadtree debug, press 4 (must have debug enabled)
- To disable or enable the quadtree algorithm, press 5 (You should leave it enabled, but disabling is useful to compare performance)
- To show full calculated trajectory, press 7 (must have debug enabled) (this can also be useful for cheating, lol)
- To enable a perfomance hack (speedHack), press 8
- to show the timer values on all the pegs, press 9 (must have debug enabled)
- To enable slow motion, press 0
- To test the zoom feature, press X (Will zoom in on the ball, unless there is one last orange peg, then it will zoom in on the peg)

### Command line arguements
-  You may pass the arguement '-h' or '--help' to see a list of all the command line arguements
```
python3 run.py -h
```
-  You may pass the arguement '-f' or '--fullscreen' to start the game in fullscreen mode
```
python3 run.py -f
```
-  You may pass the arguement '-d' or '--debug' to start the game with debug mode enabled
```
python3 run.py -d
```
- You may pass the arguement '--run-auto-install' to automatically install the dependencies
```
python3 run.py --run-auto-install
```
- You may pass the arguement '--skip-auto-install' to skip the automatic installation of the dependencies
```
python3 run.py --skip-auto-install
```


I started this project after thinking that recreating Peggle would be simple and fun. Turns out it was actually quite challenging. But I learned a lot in the making of this. The end result is a clone of Peggle that I am proud of, however the resulting code is something I am less proud of. That is to say that it has become a mess. Each new feature was essentially hacked into it. If I did this again, I would work on a better foundational architecture, where each new feature is modular and can be easily added, removed or changed. Although some things are kinda broken or straight up missing, this is pretty much finished. I might still make some minor updates in the future though. Thanks for checking this out!
