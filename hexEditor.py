import sys
import os
import msvcrt

cursorX = 0
cursorY = 0

def fileArgs():
    if len(sys.argv) < 2:
        print("No file specified.")
        return None, None
    if len(sys.argv) > 1:
        fileA = sys.argv[1]
        try:
            fileB = sys.argv[2]
        except IndexError:
            fileB = None
        return fileA, fileB


def printHex(file, y, start, updateHex, firstHex, secondHex):
    if not editMode:
        print("\033[97;44m  Data Inspector (LE)   \033[0m" + "\033[97;44mHex Editor - View Mode\033[0m" + "\033[97;44m \033[0m" * 74)
    elif editMode:
        print("\033[97;44m  Data Inspector (LE)   \033[0m" + "\033[97;44mHex Editor - Edit Mode\033[0m" + "\033[97;44m \033[0m" * 74)
    with open(file, "r+b") as fA:
        fA.seek(start * 16)
        for i in range(y):
            data = ""
            prevPos = fA.tell()
            if i == 0:
                data += "\033[97;44m" + os.path.basename(file)[:23].center(23, " ") + "\033[0m"
            elif i == 2:
                fA.seek(start * 16 + cursorY * 16 + cursorX)
                byteA = fA.read(1)
                data += "\033[97;44m 8-bit Integer:  \033[0m" + "\033[97;44m" + str(int.from_bytes(byteA, 'little')) + "\033[0m" + ("\033[97;44m \033[0m" * (6 - len(str(int.from_bytes(byteA, 'little')))))
            elif i == 3:
                fA.seek(start * 16 + cursorY * 16 + cursorX)
                byteA = fA.read(2)
                data += "\033[97;44m 16-bit Integer: \033[0m" + "\033[97;44m" + str(int.from_bytes(byteA, byteorder='little')) + "\033[0m" + ("\033[97;44m \033[0m" * (6 - len(str(int.from_bytes(byteA, 'little')))))
            elif i == 5:
                data += ("\033[97;44m        Binary         \033[0m")
            elif i == 6:
                fA.seek(start * 16 + cursorY * 16 + cursorX)
                byteA = fA.read(1)
                binString = "\033[97;44m    \033[0m"
                for e in reversed(range(8)):
                    bit = (byteA[0] >> e) & 1
                    if str(bit) == "1":
                        binString += "\033[97;44m● \033[0m"
                    else:
                        binString += "\033[97;44m○ \033[0m"
                binString += "\033[97;44m   \033[0m"
                data += binString
            else:
                data += "\033[97;44m                       \033[0m"
            fA.seek(prevPos)
            data += "\033[97;44m \033[0m"
            pos = start * 16 + (i * 16)
            posString = f"{pos:08X}"
            data += "\033[97;44m" + posString + "\033[0m"
            data += "\033[97;44m \033[0m"
            for x in range(8):
                if cursorY == i and cursorX == x and not updateHex:
                    data += "\033[30;107m" + (fA.read(1)).hex() + "\033[0m"
                    data += "\033[97;44m \033[0m"
                elif editMode and updateHex and cursorY == i and cursorX == x:
                    data += "\033[30;47m" + firstHex + secondHex + "\033[0m"
                    data += "\033[97;44m \033[0m"
                    if secondHex != " ":
                        fA.write(bytes.fromhex(firstHex + secondHex))
                        updateHex = False
                    fA.read(1)
                else:
                    byteA = fA.read(1)
                    data += "\033[97;44m" + byteA.hex() + " \033[0m"
                        
            data += "\033[97;44m \033[0m"
            for x in range(8):
                if cursorY == i and cursorX == x + 8 and not updateHex:
                    data += "\033[30;107m" + (fA.read(1)).hex() + "\033[0m"
                    data += "\033[97;44m \033[0m"
                elif editMode and updateHex and cursorY == i and cursorX == x + 8:
                    data += "\033[30;47m" + firstHex + secondHex + "\033[0m"
                    data += "\033[97;44m \033[0m"
                    if secondHex != " ":
                        fA.write(bytes.fromhex(firstHex + secondHex))
                        updateHex = False
                    fA.read(1)
                else:
                    byteA = fA.read(1)
                    data += "\033[97;44m" + byteA.hex() + " \033[0m"
                        
            data += "\033[97;44m \033[0m"
            fA.seek(-16, 1)
            for x in range(16):
                byteA = fA.read(1)
                char = byteA.decode('ascii', errors='replace')
                if not (32 <= ord(char) <= 126):
                    char = '·'
                if cursorX == x and cursorY == i:
                    data += "\033[30;107m" + char + "\033[0m"
                else:
                    data += "\033[97;44m" + char + "\033[0m"   
            if i == 24:
                data += "\033[97;44m \033[0m" + "\033[97;44mS - TOGGLE SEARCH\033[0m" + "\033[97;44m   \033[0m"   
            elif i == 25:
                data += "\033[97;44m \033[0m" + "\033[97;44mP - CHANGE MODE\033[0m" + "\033[97;44m     \033[0m" 
            elif i == 26:
                data += "\033[97;44m \033[0m" + "\033[97;44mBACKSPACE - EXIT\033[0m" + "\033[97;44m    \033[0m"
            else:
                data += "\033[97;44m \033[0m" * 21
            print(data)
        print("\033[97;44m \033[0m" * 120)

def printCompareHex(fileA, fileB, y, start):
    print("\033[97;44m  Data Inspector (LE)   \033[0m" + "\033[97;44mHex Editor - Compare Mode\033[0m" + "\033[97;44m \033[0m" * 71)
    with open(fileA, "rb") as fA, open(fileB, "rb") as fB:
        fA.seek(start * 16)
        for i in range(y):
            data = ""
            prevPos = fA.tell()
            if i == 0:
                data += "\033[97;44m" + os.path.basename(fileA)[:23].center(23, " ") + "\033[0m"
            elif i == 2:
                fA.seek(start * 16 + cursorY * 16 + cursorX)
                byteA = fA.read(1)
                data += "\033[97;44m 8-bit Integer:  \033[0m" + "\033[97;44m" + str(int.from_bytes(byteA, 'little')) + "\033[0m" + ("\033[97;44m \033[0m" * (6 - len(str(int.from_bytes(byteA, 'little')))))
            elif i == 3:
                fA.seek(start * 16 + cursorY * 16 + cursorX)
                byteA = fA.read(2)
                data += "\033[97;44m 16-bit Integer: \033[0m" + "\033[97;44m" + str(int.from_bytes(byteA, byteorder='little')) + "\033[0m" + ("\033[97;44m \033[0m" * (6 - len(str(int.from_bytes(byteA, 'little')))))
            elif i == 5:
                data += ("\033[97;44m        Binary         \033[0m")
            elif i == 6:
                fA.seek(start * 16 + cursorY * 16 + cursorX)
                byteA = fA.read(1)
                binString = "\033[97;44m    \033[0m"
                for e in reversed(range(8)):
                    bit = (byteA[0] >> e) & 1
                    if str(bit) == "1":
                        binString += "\033[97;44m● \033[0m"
                    else:
                        binString += "\033[97;44m○ \033[0m"
                binString += "\033[97;44m   \033[0m"
                data += binString
            else:
                data += "\033[97;44m                       \033[0m"
            fA.seek(prevPos)
            data += "\033[97;44m \033[0m"
            pos = start * 16 + (i * 16)
            posString = f"{pos:08X}"
            data += "\033[97;44m" + posString + "\033[0m"
            data += "\033[97;44m \033[0m"
            for x in range(8):
                if cursorY == i and cursorX == x:
                    data += "\033[30;107m" + (fA.read(1)).hex() + "\033[0m"
                    data += "\033[97;44m \033[0m"
                else:
                    byteA = fA.read(1)
                    fB.seek(fA.tell() - 1)
                    byteB = fB.read(1)
                    if byteA != byteB:
                        data += "\033[97;41m" + byteA.hex() + "\033[0m"
                        data += "\033[97;44m \033[0m"
                    else:
                        data += "\033[97;44m" + byteA.hex() + " \033[0m"
            data += "\033[97;44m \033[0m"
            for x in range(8):
                if cursorY == i and cursorX == x + 8:
                    data += "\033[30;107m" + (fA.read(1)).hex() + "\033[0m"
                    data += "\033[97;44m \033[0m"
                else:
                    byteA = fA.read(1)
                    fB.seek(fA.tell() - 1)
                    byteB = fB.read(1)
                    if byteA != byteB:
                        data += "\033[97;41m" + byteA.hex() + "\033[0m"
                        data += "\033[97;44m \033[0m"
                    else:
                        data += "\033[97;44m" + byteA.hex() + " \033[0m"
            data += "\033[97;44m \033[0m"
            fA.seek(-16, 1)
            for x in range(16):
                byteA = fA.read(1)
                fB.seek(fA.tell() - 1)
                byteB = fB.read(1)
                char = byteA.decode('ascii', errors='replace')
                if not (32 <= ord(char) <= 126):
                    char = '·'
                if cursorX == x and cursorY == i:
                    data += "\033[30;107m" + char + "\033[0m"
                else:
                    if byteA != byteB:
                        data += "\033[97;41m" + char + "\033[0m"
                    else:
                        data += "\033[97;44m" + char + "\033[0m"
            data += "\033[97;44m \033[0m" * 21
            print(data)
        print("\033[97;44m \033[0m" * 120)
        fB.seek(start * 16)
        for i in range(y):
            data = ""
            prevPos = fB.tell()
            if i == 0:
                data += "\033[97;44m" + os.path.basename(fileB)[:23].center(23, " ") + "\033[0m"
            elif i == 2:
                fB.seek(start * 16 + cursorY * 16 + cursorX)
                byteB = fB.read(1)
                data += "\033[97;44m 8-bit Integer:  \033[0m" + "\033[97;44m" + str(int.from_bytes(byteB, 'little')) + "\033[0m" + ("\033[97;44m \033[0m" * (6 - len(str(int.from_bytes(byteB, 'little')))))
            elif i == 3:
                fB.seek(start * 16 + cursorY * 16 + cursorX)
                byteB = fB.read(2)
                data += "\033[97;44m 16-bit Integer: \033[0m" + "\033[97;44m" + str(int.from_bytes(byteB, byteorder='little')) + "\033[0m" + ("\033[97;44m \033[0m" * (6 - len(str(int.from_bytes(byteB, 'little')))))
            elif i == 5:
                data += ("\033[97;44m        Binary         \033[0m")
            elif i == 6:
                fB.seek(start * 16 + cursorY * 16 + cursorX)
                byteB = fB.read(1)
                binString = "\033[97;44m    \033[0m"
                for e in reversed(range(8)):
                    bit = (byteB[0] >> e) & 1
                    if str(bit) == "1":
                        binString += "\033[97;44m● \033[0m"
                    else:
                        binString += "\033[97;44m○ \033[0m"
                binString += "\033[97;44m   \033[0m"
                data += binString
            else:
                data += "\033[97;44m                       \033[0m"
            fB.seek(prevPos)
            data += "\033[97;44m \033[0m"
            pos = start * 16 + (i * 16)
            posString = f"{pos:08X}"
            data += "\033[97;44m" + posString + "\033[0m"
            data += "\033[97;44m \033[0m"
            for x in range(8):
                if cursorY == i and cursorX == x:
                    data += "\033[30;107m" + (fB.read(1)).hex() + "\033[0m"
                    data += "\033[97;44m \033[0m"
                else:
                    byteB = fB.read(1)
                    fA.seek(fB.tell() - 1)
                    byteA = fA.read(1)
                    if byteA != byteB:
                        data += "\033[97;41m" + byteB.hex() + "\033[0m"
                        data += "\033[97;44m \033[0m"
                    else:
                        data += "\033[97;44m" + byteB.hex() + " \033[0m"
            data += "\033[97;44m \033[0m"
            for x in range(8):
                if cursorY == i and cursorX == x + 8:
                    data += "\033[30;107m" + (fB.read(1)).hex() + "\033[0m"
                    data += "\033[97;44m \033[0m"
                else:
                    byteB = fB.read(1)
                    fA.seek(fB.tell() - 1)
                    byteA = fA.read(1)
                    if byteA != byteB:
                        data += "\033[97;41m" + byteB.hex() + "\033[0m"
                        data += "\033[97;44m \033[0m"
                    else:
                        data += "\033[97;44m" + byteB.hex() + " \033[0m"
            data += "\033[97;44m \033[0m"
            fB.seek(-16, 1)
            for x in range(16):
                byteB = fB.read(1)
                fA.seek(fB.tell() - 1)
                byteA = fA.read(1)
                char = byteB.decode('ascii', errors='replace')
                if not (32 <= ord(char) <= 126):
                    char = '·'
                if cursorX == x and cursorY == i:
                    data += "\033[30;107m" + char + "\033[0m"
                else:
                    if byteA != byteB:
                        data += "\033[97;41m" + char + "\033[0m"
                    else:
                        data += "\033[97;44m" + char + "\033[0m"
            if i == 11:
                data += "\033[97;44m \033[0m" + "\033[97;44mENTER - DIFFERENCE\033[0m" + "\033[97;44m  \033[0m"
            elif i == 12:
                data += "\033[97;44m \033[0m" + "\033[97;44mBACKSPACE - EXIT\033[0m" + "\033[97;44m    \033[0m"
            else:
                data += "\033[97;44m \033[0m" * 21
            print(data)
        print("\033[97;44m \033[0m" * 120)

def locateNextDiff(fileA, fileB, start):
    with open(fileA, "rb") as fA, open(fileB, "rb") as fB:
        fA.seek(((start * 16) + (cursorY * 16) + (cursorX + 1)))
        fB.seek(((start * 16) + (cursorY * 16) + (cursorX + 1)))
        pos = ((start * 16) + (cursorY * 16) + (cursorX + 1))
        while True:
            byteA = fA.read(1)
            byteB = fB.read(1)
            if not byteA or not byteB:
                break
            if byteA != byteB:
                return pos // 16, pos
            pos += 1
        return None


startPos = 0
editMode = False
firstLetter = True
updateHex = False
firstHex = " "
secondHex = " "

def update(single):
    if not single:
        printCompareHex(fileA, fileB, 13, startPos)
    elif single:
        printHex(fileA, 27, startPos, updateHex, firstHex, secondHex)


fileA, fileB = fileArgs()
if fileA != None and fileB != None:
    update(False)
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key in (b'\xe0', b'\x00'):  # Arrow or function key prefix
                key2 = msvcrt.getch()
                if key2 == b'H':
                    cursorY -= 1
                    if cursorY < 0 and startPos > 0:
                        cursorY = 0
                        startPos -= 1
                    elif cursorY < 0 and startPos == 0:
                        cursorY = 0
                    update(False)
                elif key2 == b'P':
                    cursorY += 1
                    if cursorY > 12:
                        cursorY = 12
                        startPos += 1
                    update(False)
                elif key2 == b'K' and cursorX > 0:
                    cursorX -= 1
                    update(False)
                elif key2 == b'M' and cursorX < 15:
                    cursorX += 1
                    update(False)
            elif key == b'\r':
                startPos, Rpos = locateNextDiff(fileA, fileB, startPos)
                cursorX = Rpos - (startPos * 16)
                cursorY = 0
                update(False)
            elif key == b'\x08':
                sys.exit(0)
elif fileA != None and fileB == None:
    update(True)
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key in (b'\xe0', b'\x00'):  # Arrow or function key prefix
                key2 = msvcrt.getch()
                if key2 == b'H':
                    cursorY -= 1
                    if cursorY < 0 and startPos > 0:
                        cursorY = 0
                        startPos -= 1
                    elif cursorY < 0 and startPos == 0:
                        cursorY = 0
                    update(True)
                elif key2 == b'P':
                    cursorY += 1
                    if cursorY > 26:
                        cursorY = 26
                        startPos += 1
                    update(True)
                elif key2 == b'K' and cursorX > 0:
                    cursorX -= 1
                    update(True)
                elif key2 == b'M' and cursorX < 15:
                    cursorX += 1
                    update(True)
            elif key == b'\x08':
                sys.exit(0)
            elif key == b'p':
                editMode = not editMode
                update(True)
            elif key == b'0' or key == b'1' or key == b'2' or key == b'3' or key == b'4' or key == b'5' or key == b'6' or key == b'7' or key == b'8' or key == b'9' or key == b'a' or key == b'b' or key == b'c' or key == b'd' or key == b'e' or key == b'f':
                if editMode:
                    if firstLetter:
                        updateHex = True
                        firstHex = " "
                        secondHex = " "
                        firstHex = key.decode('utf-8')
                        firstLetter = False
                    else:
                        secondHex = key.decode('utf-8')
                        firstLetter = True
                    update(True)
                    if secondHex != " ":
                        updateHex = False
                        update(True)
                    
elif fileA == None and fileB == None:
    update(True)
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key in (b'\xe0', b'\x00'):  # Arrow or function key prefix
                key2 = msvcrt.getch()
                if key2 == b'H':
                    cursorY -= 1
                    if cursorY < 0 and startPos > 0:
                        cursorY = 0
                        startPos -= 1
                    elif cursorY < 0 and startPos == 0:
                        cursorY = 0
                    update(True)
                elif key2 == b'P':
                    cursorY += 1
                    if cursorY > 26:
                        cursorY = 26
                        startPos += 1
                    update(True)
                elif key2 == b'K' and cursorX > 0:
                    cursorX -= 1
                    update(True)
                elif key2 == b'M' and cursorX < 15:
                    cursorX += 1
                    update(True)
            elif key == b'\x08':
                sys.exit(0)