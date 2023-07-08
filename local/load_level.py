try:
    import tkinter
    from tkinter import filedialog
    tkinterInstalled = True
except ImportError:
    print("WARN: Tkinter is not installed. You will be unable to load or save levels.")
    print("Please install tkinter")
    tkinterInstalled = False

import pickle # sort of abusing pickle to save the level data (it works, but I dont really think pickle is meant for this)

from local.config import debug, WIDTH, HEIGHT

from local.peg import Peg

if tkinterInstalled:
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
        
# tkinter is not installed (do nothing, default level will be used)
else:
    def fileSelectWindow():
        print("Tkinter is not installed, you will be unable to load or save levels.")
        print("Please install tkinter.")
        print("Loading default level...")
        return None

    def fileSaveWindow():
        print("Tkinter is not installed, you will be unable to load or save levels.")
        print("Please install tkinter.")
        print("Loading default level...")
        return None


def loadData(filePath: str | None = None, centerPegs: bool = True) -> tuple[list[Peg], str]:
    if filePath == None:
        filePath = fileSelectWindow()

    posList = createDefaultPegsPos()
    if filePath != None:
        try:
            with open(filePath, 'rb') as f:
                posList = pickle.load(f)

        except Exception: # if the file selected is invalid generate the default level and use it instead
            if debug:
                print("WARN: Unable to open file: \"" + str(filePath) + "\". using default level (No file created or loaded)")

            posList = createDefaultPegsPos()

    # if no file was selected
    elif filePath == None and debug:
        print("WARN: No file selected, using default level (No file created or loaded)")
        

    # using x and y tuple, create list of peg objects
    pegs = []
    for xyPos in posList:
        x, y = xyPos
        pegs.append(Peg(x, y))
    
    if centerPegs:
        # adjust the positions of every peg to be centered on the screen based on WIDTH and HEIGHT
        # get the position of the left most peg
        leftMostPeg = pegs[0]
        for peg in pegs:
            if peg.pos.x < leftMostPeg.pos.x:
                leftMostPeg = peg
        rightMostPeg = pegs[0]
        for peg in pegs:
            if peg.pos.x > rightMostPeg.pos.x:
                rightMostPeg = peg

        # find the center of the left most and right most pegs
        centerOfLeftAndRightPegs = (leftMostPeg.pos.x + rightMostPeg.pos.x)/2
        # find the center of the screen
        screenCenter = WIDTH/2
        # find the difference between the center of the screen and the center of the left and right most pegs
        difference = screenCenter - centerOfLeftAndRightPegs

        # adjust the position of every peg by the difference
        for peg in pegs:
            peg.pos.x += difference


    
    return pegs, filePath


def saveData(pegs: list[Peg], filePath: str | None = None):
    if filePath == None:
        filePath = fileSaveWindow()

    posList = getPegPosList(pegs)
    try:
        # create a new pickle file
        with open(filePath, 'wb') as f:
            pickle.dump(posList, f)
    except Exception as e:
        if debug:
            print("ERROR: Unable to save file: \"" + str(filePath) + "\". Exception: " + str(e))
            print("Check that the file path is valid and that you have write permissions")
        return str(Exception)



def getPegPosList(pegs):
    posList = []
    for peg in pegs:
        x, y = peg.pos.x, peg.pos.y
        posList.append((x, y))

    return posList


def createDefaultPegsPos():
    # default level ("peggle clone")
    posList = [(111, 200), 
                (104, 229), 
                (97, 259), 
                (92, 291), 
                (92, 326), 
                (92, 358), 
                (99, 392), 
                (105, 421), 
                (113, 450), 
                (141, 201), 
                (167, 216), 
                (180, 243), 
                (161, 270), 
                (133, 279), 
                (623, 279), 
                (646, 300), 
                (675, 291), 
                (708, 287), 
                (724, 320), 
                (734, 357), 
                (737, 390), 
                (867, 231), 
                (873, 264), 
                (882, 305), 
                (886, 340), 
                (889, 373), 
                (889, 409), 
                (882, 438), 
                (976, 349), 
                (1010, 359), 
                (1043, 357), 
                (1074, 344), 
                (1091, 318), 
                (1093, 288), 
                (1073, 261), 
                (1042, 251), 
                (1010, 255), 
                (989, 279), 
                (975, 308), 
                (973, 385), 
                (986, 417), 
                (1005, 443), 
                (1032, 467), 
                (1061, 476), 
                (1095, 481), 
                (1125, 479), 
                (579, 611), 
                (571, 642), 
                (567, 672), 
                (576, 700), 
                (608, 699), 
                (633, 676), 
                (647, 650), 
                (643, 621), 
                (617, 606), 
                (905, 461), 
                (439, 553), 
                (433, 583), 
                (432, 615), 
                (434, 645), 
                (436, 676), 
                (441, 705), 
                (313, 533), 
                (282, 536), 
                (265, 560), 
                (257, 592), 
                (258, 625), 
                (269, 657), 
                (291, 679), 
                (317, 696), 
                (724, 573), 
                (728, 606), 
                (730, 638), 
                (737, 669), 
                (749, 697), 
                (759, 725), 
                (760, 643), 
                (791, 644), 
                (812, 666), 
                (827, 692), 
                (838, 721), 
                (957, 656), 
                (987, 661), 
                (1017, 653), 
                (1030, 625), 
                (1024, 594), 
                (1001, 573), 
                (974, 560), 
                (951, 585), 
                (937, 611), 
                (922, 639), 
                (921, 671), 
                (936, 697), 
                (965, 711), 
                (995, 719), 
                (1026, 721), 
                (1055, 717), 
                (603, 257), 
                (601, 227), 
                (622, 206), 
                (650, 195), 
                (678, 204), 
                (700, 225), 
                (706, 254), 
                (724, 417), 
                (710, 444), 
                (688, 464), 
                (658, 460), 
                (452, 203), 
                (433, 230), 
                (430, 260), 
                (446, 285), 
                (471, 302), 
                (499, 285), 
                (511, 258), 
                (481, 196), 
                (510, 189), 
                (518, 219), 
                (520, 307), 
                (520, 337), 
                (523, 367), 
                (521, 399), 
                (513, 428), 
                (492, 450), 
                (463, 454), 
                (435, 445), 
                (271, 332), 
                (302, 333), 
                (323, 310), 
                (317, 280), 
                (294, 260), 
                (265, 268), 
                (244, 290), 
                (233, 318), 
                (231, 348), 
                (239, 379), 
                (252, 406), 
                (276, 425), 
                (304, 436), 
                (1143, 588), 
                (1144, 626), 
                (1149, 664), 
                (1146, 754)]

    return posList

if __name__ == '__main__':
    print("Warning !!! Be careful, files may be overwritten or deleted")

    testPegs, filepath = loadData()
    print (str(len(testPegs)) + " pegs found in the level")
    
    testPegs = [Peg(1,1)]
    #saveData(testPegs)
    print(fileSaveWindow())
