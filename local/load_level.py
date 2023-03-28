try:
    import tkinter
    from tkinter import filedialog
except ImportError:
    print("ERROR: Unable to import tkinter! Please install tkinter.")
import pickle # sort of abusing pickle to save the level data (it works, but I dont really think pickle is meant for this)

from local.config import debug, WIDTH, HEIGHT

from local.peg import Peg

def fileSelectWindow():
    #initiate tinker and hide window 
    main_win = tkinter.Tk() 
    main_win.withdraw()

    main_win.overrideredirect(True)
    main_win.geometry('0x0+0'+str(round(WIDTH/2))+'+'+str(round(HEIGHT/2)))

    main_win.deiconify()
    main_win.lift()
    main_win.focus_force()

    #open file selector 
    main_win.sourceFile = filedialog.askopenfilename(parent=main_win, initialdir= "./levels", title='Please select a level to open', 
                                                        filetypes = (("PegglePy Level File", "*.lvl*"), ("all files", "*")))

    selected_file = main_win.sourceFile

    #close window after selection 
    main_win.destroy()

    if str(selected_file) == '()' or str(selected_file) == '':
        selected_file = None

    if debug:
        print("File selected: '" + str(selected_file) +"'")

    # returns the path to the selected file
    return selected_file


def fileSaveWindow():
    #initiate tinker and hide window 
    main_win = tkinter.Tk() 
    main_win.withdraw()

    main_win.overrideredirect(True)
    main_win.geometry('0x0+0'+str(round(WIDTH/2))+'+'+str(round(HEIGHT/2)))

    main_win.deiconify()
    main_win.lift()
    main_win.focus_force()

    #open file selector 
    main_win.sourceFile = filedialog.asksaveasfile(parent=main_win, initialdir= "./levels", title='Please name the level', 
                                                        filetypes = (("PegglePy Level File", "*.lvl*"), ("all files", "*")),
                                                        defaultextension = ".lvl", initialfile = "Untitled Level")

    selected_file = main_win.sourceFile

    #close window after selection 
    main_win.destroy()

    if selected_file == None:
        if debug:
            print("WARN: File was not saved")
        return None

    if debug:
        print("File saved: '" + str(selected_file.name) +"'")

    # returns the path to the selected file
    return str(selected_file.name)


def loadData():
    filePath = fileSelectWindow()

    posList = createDefaultPegsPos()
    if filePath != None:
        try:
            with open(filePath, 'rb') as f:
                posList = pickle.load(f)

        except Exception: # if the file selected is invalid generate the default level and use it instead
            if debug:
                print("WARN: Unable to open file, using default generated level (No file created or loaded)")

            posList = createDefaultPegsPos()

    # if no file was selected
    elif filePath == None and debug:
        print("WARN: No file selected, using default generated level (No file created or loaded)")
        

    # using x and y tuple, create list of peg objects
    pegs = []
    for xyPos in posList:
        x, y = xyPos
        pegs.append(Peg(x, y))

    
    return pegs


def saveData(pegs):
    filePath = fileSaveWindow()
    posList = getPegPosList(pegs)
    try:
        # create a new pickle file
        with open(filePath, 'wb') as f:
            pickle.dump(posList, f)
    except Exception:
        if debug:
            print("ERROR: Unable to save file - Exception: " + str(Exception))
            print("Do you have permission to write to this directory??")
        return str(Exception)



def getPegPosList(pegs):
    posList = []
    for peg in pegs:
        x, y = peg.pos.vx, peg.pos.vy
        posList.append((x, y))

    return posList


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
    print("Warning !!! Be careful, files may be overwritten or deleted")

    testPegs = loadData()
    print (str(len(testPegs)) + " pegs found in the level")
    
    testPegs = [Peg(1,1)]
    #saveData(testPegs)
    print(fileSaveWindow())
