try:
    import tkinter
    from tkinter import filedialog
    tkinterInstalled = True
except ImportError:
    print("WARN: Tkinter is not installed. You will be unable to save levels.")
    print("Please install tkinter")
    tkinterInstalled = False

from collections.abc import Callable

from local.userConfig import configs

from local.peg import Peg, createPegColors
from local.level_format import read_level_records, write_level_file
from local.moving_peg import MovingPegPath

if tkinterInstalled:
    # This function is no longer used, it was replaced with the new level select menu
    def fileSelectWindow():
        #initiate tinker and hide window 
        main_win = tkinter.Tk() 
        main_win.withdraw()

        main_win.overrideredirect(True)
        main_win.geometry('0x0+0'+str(round(configs["WIDTH"]/2))+'+'+str(round(configs["HEIGHT"]/2)))

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

        if configs["DEBUG_MODE"]:
            print("File selected: '" + str(selected_file) +"'")

        # returns the path to the selected file
        return selected_file

    # This is still used to save levels in the level editor (I would like to replace this with a new save menu at some point)
    def fileSaveWindow():
        #initiate tinker and hide window 
        main_win = tkinter.Tk() 
        main_win.withdraw()

        main_win.overrideredirect(True)
        main_win.geometry('0x0+0'+str(round(configs["WIDTH"]/2))+'+'+str(round(configs["HEIGHT"]/2)))

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
            if configs["DEBUG_MODE"]:
                print("WARN: File was not saved")
            return None

        if configs["DEBUG_MODE"]:
            print("File saved: '" + str(selected_file.name) +"'")

        # returns the path to the selected file
        return str(selected_file.name)
        
# tkinter is not installed (do nothing, default level will be used)
else:
    def fileSelectWindow():
        print("Tkinter is not installed, you will be unable to load or save levels.")
        print("Please install tkinter.")
        return None

    def fileSaveWindow():
        print("Tkinter is not installed, you will be unable to save levels.")
        print("Please install tkinter.")
        return None


ProgressCallback = Callable[[float, str], None]


def loadData(
    filePath: str | None = None,
    centerPegs: bool = True,
    progress_callback: ProgressCallback | None = None,
    peg_limit: int | None = None,
) -> tuple[list[Peg], str]:
    if peg_limit is not None and peg_limit <= 0:
        raise ValueError("peg_limit must be greater than zero")

    if progress_callback is not None:
        progress_callback(0.0, "Reading level data")

    if filePath == None:
        filePath = fileSelectWindow()

    records = [
        {"x": x, "y": y}
        for x, y in createDefaultPegsPos()
    ]
    if filePath != None:
        try:
            records, _ = read_level_records(filePath)
        except (OSError, ValueError, TypeError) as error:
            print(f"WARN: Unable to read level file {filePath!r}: {error}; using the default level")
            records = [
                {"x": x, "y": y}
                for x, y in createDefaultPegsPos()
            ]

    # if no file was selected
    elif filePath == None and configs["DEBUG_MODE"]:
        print("WARN: No file selected, using default level (No file created or loaded)")
        
    if peg_limit is not None and len(records) > peg_limit:
        sample_count = len(records)
        if peg_limit == 1:
            records = records[:1]
        else:
            records = [
                records[index * (sample_count - 1) // (peg_limit - 1)]
                for index in range(peg_limit)
            ]

    if progress_callback is not None:
        progress_callback(0.15, "Creating pegs")

    # using x and y tuple, create list of peg objects
    pegs = []
    total_pegs = len(records)
    for index, record in enumerate(records):
        peg = Peg(record["x"], record["y"])
        motion = record.get("motion")
        if motion is not None:
            peg.set_movement(
                MovingPegPath(
                    motion["points"],
                    motion["speed"],
                    motion["type"],
                    motion["easing"],
                    motion["traversal"],
                )
            )
        pegs.append(peg)
        if progress_callback is not None and total_pegs:
            progress_callback(
                0.15 + 0.45 * (index + 1) / total_pegs,
                "Creating pegs",
            )
    
    if centerPegs and pegs:
        # adjust the positions of every peg to be centered on the screen based on configs["WIDTH"] and configs["HEIGHT"]
        x_coordinates = [
            coordinate
            for peg in pegs
            for coordinate in (
                [peg.pos.x]
                + ([] if peg.movement is None else [x for x, _ in peg.movement.points])
            )
        ]
        centerOfLeftAndRightPegs = (min(x_coordinates) + max(x_coordinates)) / 2
        # find the center of the screen
        screenCenter = configs["WIDTH"]/2
        # find the difference between the center of the screen and the center of the left and right most pegs
        difference = screenCenter - centerOfLeftAndRightPegs

        # adjust the position of every peg by the difference
        for peg in pegs:
            peg.translate(difference, 0)
        
        
        y_coordinates = [
            coordinate
            for peg in pegs
            for coordinate in (
                [peg.pos.y]
                + ([] if peg.movement is None else [y for _, y in peg.movement.points])
            )
        ]
        centerOfTopAndBottomPegs = (min(y_coordinates) + max(y_coordinates)) / 2
        # find the center of the screen
        screenCenter = configs["HEIGHT"]/2
        # find the difference between the center of the screen and the center of the top and bottom most pegs
        difference = screenCenter - centerOfTopAndBottomPegs
        
        # adjust the position of every peg by the difference
        for index, peg in enumerate(pegs):
            peg.translate(0, difference)
            if progress_callback is not None:
                progress_callback(
                    0.6 + 0.4 * (index + 1) / len(pegs),
                    "Centering level",
                )


    if progress_callback is not None:
        progress_callback(1.0, "Level data ready")

    return pegs, filePath


def saveData(pegs: list[Peg], filePath: str | None = None) -> str | None:
    if filePath == None:
        filePath = fileSaveWindow()

    if filePath is None:
        return None

    try:
        write_level_file(pegs, filePath)
    except (OSError, TypeError, ValueError) as e:
        if configs["DEBUG_MODE"]:
            print("ERROR: Unable to save file: \"" + str(filePath) + "\". Exception: " + str(e))
            print("Check that the file path is valid and that you have write permissions")
        return str(e)



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


def loadLevel(filePath = None) -> tuple[list[Peg], list[Peg], int, str]:
    # Load either a versioned JSON level or a legacy pickle level.
    pegs, levelFileName = loadData(filePath)
    originPegs = pegs.copy()

    pegs = createPegColors(pegs)

    orangeCount = 0
    for peg in pegs:
        if peg.color == "orange":
            orangeCount += 1

    # check that the filepath is not empty
    if levelFileName == "" or levelFileName == None:
        levelFileName = "Default"
    else:
        # strip everything from the filepath except the filename
        levelFileName = levelFileName.split("/")[-1]
        # remove the file extension '.lvl'
        levelFileName = levelFileName[:-4]

    return pegs, originPegs, orangeCount, levelFileName


def loadDefaultLevel(
    progress_callback: ProgressCallback | None = None,
) -> tuple[list[Peg], list[Peg], int, str]:
    pegsPosList = createDefaultPegsPos()
    if progress_callback is not None:
        progress_callback(0.0, "Creating default level")

    # using x and y tuple, create list of peg objects
    pegs = []
    total_pegs = len(pegsPosList)
    for index, xyPos in enumerate(pegsPosList):
        x, y = xyPos
        pegs.append(Peg(x, y))
        if progress_callback is not None and total_pegs:
            progress_callback(
                0.8 * (index + 1) / total_pegs,
                "Creating default level",
            )

    originPegs = pegs.copy()

    pegs = createPegColors(pegs)
    if progress_callback is not None:
        progress_callback(0.85, "Assigning peg colors")

    orangeCount = 0
    for index, peg in enumerate(pegs):
        if peg.color == "orange":
            orangeCount += 1
        if progress_callback is not None and pegs:
            progress_callback(
                0.85 + 0.14 * (index + 1) / len(pegs),
                "Counting orange pegs",
            )

    levelFileName = "Default"
    if progress_callback is not None:
        progress_callback(1.0, "Level data ready")

    return pegs, originPegs, orangeCount, levelFileName


# if __name__ == '__main__':
#     print("Warning !!! Be careful, files may be overwritten or deleted")

#     testPegs, filepath = loadData()
#     print (str(len(testPegs)) + " pegs found in the level")
    
#     testPegs = [Peg(1,1)]
#     #saveData(testPegs)
#     print(fileSaveWindow())
