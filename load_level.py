import tkinter
from tkinter import filedialog
import pickle
from random import randint

from config import debug, WIDTH, HEIGHT

from peg import Peg

def fileSelectWindow():
    #initiate tinker and hide window 
    main_win = tkinter.Tk() 
    main_win.withdraw()

    main_win.overrideredirect(True)
    main_win.geometry('0x0+'+str(round(WIDTH/2))+'+'+str(round(HEIGHT/2)))

    main_win.deiconify()
    main_win.lift()
    main_win.focus_force()

    #open file selector 
    main_win.sourceFile = filedialog.askopenfilename(parent=main_win, initialdir= "./levels",
    title='Please select a level to open')

    selected_file = main_win.sourceFile

    #close window after selection 
    main_win.destroy()

    if str(selected_file) == '()' or str(selected_file) == '':
        selected_file = None

    if debug:
        print("File selected: '" + str(selected_file) +"'")

    # returns the path to the selected file
    return selected_file


def loadData():
    filePath = fileSelectWindow()

    posList = createDefaultPegsPos()
    if filePath != None:
        try:
            # load average mpg data from file
            with open(filePath, 'rb') as f:
                posList = pickle.load(f)


        except Exception: # if the file does not exist, generate a new file
            print("WARN: Unable to open file, using default generated level (No file created or loaded)")

            posList = createDefaultPegsPos()

            # generate a new pickle file with a blank array
            with open(filePath, 'wb') as f:
                pickle.dump(posList, f)
    elif filePath == None and debug:
        print("WARN: Unable to open file, using default generated level (No file created or loaded)")
        

    # using x and y tuple, create list of peg objects
    pegs = []
    for xyPos in posList:
        x, y = xyPos
        pegs.append(Peg(x, y))

    
    return pegs


def createDefaultPegsPos():
    posList = []
    spacing = 46
    heightSpacing = 9
    colCount = 7
    rowCount = 26
    for j in range(colCount):
        for i in range(rowCount):
            if (j%2):
                newPos = ((WIDTH-i * spacing) - spacing + 5, spacing + HEIGHT - j*(HEIGHT/heightSpacing) - 110)
            else:
                newPos = ((20 + WIDTH-i * spacing) - spacing, spacing + HEIGHT - j*(HEIGHT/heightSpacing) - 110)
            
            posList.append(newPos)

    return posList

if __name__ == '__main__':
    testPegs = loadData()
    print (str(len(testPegs)) + " pegs found in the level")
