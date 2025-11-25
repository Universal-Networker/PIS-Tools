# pis tool
import tkinter as tk
from tkinter.filedialog import askopenfilenames
import sys
import os
import msvcrt
import subprocess
tk.Tk().withdraw()

menuItems = ["Hex Editor", "MSM6650 Audio Decoder"]
menuDesc = [" - General purpose hex editor", " - Decode binary audio files used on EPROMs with a MSM6650"]
selectedItem = 0
reDraw = False

def inputHandler(selectedItem):
    reDraw = False
    if msvcrt.kbhit():
        key = msvcrt.getch()
        if key in (b'\xe0', b'\x00'):  # Arrow or function key prefix
            key2 = msvcrt.getch()
            if key2 == b'H':
                selectedItem -= 1
                if(selectedItem < 0):
                    selectedItem = 0
                updateScreen(selectedItem)
            elif key2 == b'P':
                selectedItem += 1
                if(selectedItem > len(menuItems) - 1):
                    selectedItem = len(menuItems) - 1
                updateScreen(selectedItem)
        elif key == b'\x08':
            sys.exit(0)
        elif key == b'\r':
            if(selectedItem == 0):
                fn = askopenfilenames()
                if(len(fn) == 1):
                    subprocess.run(['python', 'hexEditor.py', fn[0]])
                elif(len(fn) == 2):
                    subprocess.run(['python', 'hexEditor.py', fn[0], fn[1]])
                reDraw = True
            elif(selectedItem == 1):
                subprocess.run(['python', 'msm6650AudioDecoder.py'])
                reDraw = True
    return selectedItem, reDraw

def mainMenu(selectedItem):
    print("\033[97;44m    465/3 PIS Tools     \033[0m" + "\033[97;44mMain Menu - Select Tool\033[0m" + "\033[97;44m \033[0m" * 73)
    print("\033[97;44m \033[0m" * 120)
    for item in menuItems:
        if(menuItems.index(item) == selectedItem):
            print("\033[97;44m    - \033[0m" + "\033[30;107m" + item + "\033[0m" + "\033[97;44m" + menuDesc[menuItems.index(item)] + "\033[0m" + "\033[97;44m \033[0m" * ((114 - len(item)) - len(menuDesc[menuItems.index(item)])))
        else:
            print("\033[97;44m    - \033[0m" + "\033[97;44m" + item + "\033[0m" + "\033[97;44m" + menuDesc[menuItems.index(item)] + "\033[0m" + "\033[97;44m \033[0m" * ((114 - len(item)) - len(menuDesc[menuItems.index(item)])))
    for i in range(24 - len(menuItems)):
        print("\033[97;44m \033[0m" * 120)
    print("\033[97;44m \033[0m" * 100 + "\033[97;44mENTER - SELECT      \033[0m")
    print("\033[97;44m \033[0m" * 100 + "\033[97;44mBACKSPACE - EXIT    \033[0m")
    print("\033[97;44m \033[0m" * 120)

def updateScreen(selectedItem):
    mainMenu(selectedItem)

mainMenu(selectedItem)
while(True):
    selectedItem, reDraw = inputHandler(selectedItem)
    if(reDraw):
        updateScreen(selectedItem)
        reDraw = False
    a = 1

