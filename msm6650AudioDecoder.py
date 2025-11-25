import sys
import wave
import struct
import os
import msvcrt
import tkinter as tk
from pydub import AudioSegment
from tkinter.filedialog import askopenfilenames
tk.Tk().withdraw()

menuItems = ["Browse", "Amplify", "Low-Pass Filter", "Decode", "Decode Segments"]
menuDesc = ["", "", "", "", ""]
selectedItem = 0
selectedFileNames = ""
highlight = False
amplify = "0"
lowPass = "0"
selectedFiles = None


STEP_MODE = "MSM6650"
SAMPLE_RATE = 16000
OUTPUT_WAV = None             
TRIM_PADDING = False           
PADDING_RUN_MIN = 64          
NIBBLE_ORDER = "highfirst"     
RESET_PREDICTOR_EACH_BLOCK = False
RESET_INDEX_EACH_BLOCK = False
HEADER_SIZE = 64           
BLOCK_RESET_BYTE = 0xFF        



MSM6650_STEP_TABLE = [
    0x0007, 0x0008, 0x0009, 0x000A, 0x000B, 0x000C, 0x000D, 0x000E,
    0x0010, 0x0011, 0x0013, 0x0015, 0x0017, 0x0019, 0x001C, 0x001F,
    0x0022, 0x0025, 0x0029, 0x002D, 0x0032, 0x0037, 0x003D, 0x0043,
    0x004A, 0x0051, 0x0059, 0x0062, 0x006C, 0x0077, 0x0083, 0x0090,
    0x009E, 0x00AE, 0x00BF, 0x00D2, 0x00E7, 0x00FE, 0x0117, 0x0133,
    0x0152, 0x0174, 0x0199, 0x01C2, 0x01EF, 0x0221, 0x0257, 0x0293,
    0x02D5
]
MSM6650_INDEX_MAX = len(MSM6650_STEP_TABLE) - 1

INDEX_TABLE = [
    -1, -1, -1, -1, 2, 4, 6, 8,
    -1, -1, -1, -1, 2, 4, 6, 8
]

def smooth_index_update(index: int, code: int, index_table: list, index_max: int) -> int:
    index += index_table[code]
    if abs(index_table[code]) > 2:
        index = max(0, min(index_max, index))
    return index

def trim_padding(data: bytes) -> bytes:
    if len(data) < PADDING_RUN_MIN:
        return data
    tail = data[-PADDING_RUN_MIN:]
    if all(b == 0x00 for b in tail):
        i = len(data) - 1
        while i >= 0 and data[i] == 0x00:
            i -= 1
        return data[:i + 1]
    if all(b == 0xFF for b in tail):
        i = len(data) - 1
        while i >= 0 and data[i] == 0xFF:
            i -= 1
        return data[:i + 1]
    return data

def adaptive_predictor_clamp(predictor: int, diff: int) -> int:
    new_predictor = predictor + diff
    if new_predictor < -32768:
        return -32768
    elif new_predictor > 32767:
        return 32767
    return new_predictor


def smooth_pcm(pcm: list) -> list:
    smoothed_pcm = []
    for i in range(1, len(pcm)):
        smoothed_pcm.append((pcm[i] + pcm[i - 1]) // 2)
    return smoothed_pcm

def smooth_predictor(predictor: int, last_predictor: int, alpha: float = 0.1) -> int:
    return int(last_predictor * (1 - alpha) + predictor * alpha)

def smooth_index(index: int, last_index: int, alpha: float = 0.1) -> int:
    return int(last_index * (1 - alpha) + index * alpha)

def normalize_pcm(pcm_samples):
    max_sample = max(abs(min(pcm_samples)), max(pcm_samples))
    if max_sample == 0:
        return pcm_samples 
    normalization_factor = 32767 / max_sample 
    normalized_pcm = [int(sample * normalization_factor) for sample in pcm_samples]
    return normalized_pcm

def apply_soft_clipping(pcm_samples):
    clipped_pcm = []
    for sample in pcm_samples:
        if sample > 32767:
            clipped_pcm.append(32767)
        elif sample < -32768:
            clipped_pcm.append(-32768)
        else:
            clipped_pcm.append(sample)
    return clipped_pcm

def apply_volume_control(pcm_samples, volume_factor=0.5):
    return [int(sample * volume_factor) for sample in pcm_samples]

def decode_adpcm_stream(data: bytes,
                        predictor: int = 0,
                        index: int = 0,
                        step_table=None,
                        index_max: int = 48,
                        nibble_order: str = "lowfirst"):
    pcm = []
    
    if step_table is None:
        raise ValueError("step_table must be provided")

    i = 0
    recent_samples = []
    max_recent_length = 80 
    
    while i < len(data):
        b = data[i]


        if b == BLOCK_RESET_BYTE:
            i += 1
            continue

        nibbles = [(b & 0x0F), ((b >> 4) & 0x0F)]
        if nibble_order == "highfirst":
            nibbles.reverse()

        for code in nibbles:
            step = step_table[index]
            
      
            diff = step >> 3
            if code & 0x01:
                diff += step >> 2
            if code & 0x02:
                diff += step >> 1
            if code & 0x04:
                diff += step
            if code & 0x08:
                diff = -diff

    
            predictor += diff
            
       
            recent_samples.append(predictor)
            if len(recent_samples) > max_recent_length:
                recent_samples.pop(0)
                

            if len(recent_samples) == max_recent_length and len(pcm) % 30 == 0:
                recent_avg = sum(recent_samples) / len(recent_samples)
             
                if abs(recent_avg) > 300:
              
                    correction = -int(recent_avg * 0.04)  
                    predictor += correction
                
                    recent_samples = [predictor] * (max_recent_length // 2) 
            
      
            if predictor > 32767:
                predictor = 32767
            elif predictor < -32768:
                predictor = -32768
                
            pcm.append(predictor)

           
            index += INDEX_TABLE[code & 0x07]
            if index < 0:
                index = 0
            elif index > index_max:
                index = index_max

        i += 1

    return pcm, predictor, index



def scale_pcm(pcm_samples):
    max_amplitude = max(abs(min(pcm_samples)), max(pcm_samples))
    scale_factor = 32767 / max_amplitude if max_amplitude > 0 else 1  
    scaled_pcm = [int(sample * scale_factor) for sample in pcm_samples]
    return scaled_pcm




def write_wav(filename: str, pcm_samples, samplerate: int = 16000):
    if not pcm_samples:
        return
        

    mean = sum(pcm_samples) / len(pcm_samples)
    dc_removed = [int(sample - mean) for sample in pcm_samples]
    
   
    max_val = max(abs(min(dc_removed)), abs(max(dc_removed)))
    if max_val > 32767:
  
        scale_factor = 32767.0 / max_val
        scaled_pcm = [int(sample * scale_factor * 0.95) for sample in dc_removed] 
    else:
        scaled_pcm = dc_removed

    with wave.open(filename, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(samplerate)
        
        frames = struct.pack('<' + 'h' * len(scaled_pcm), *scaled_pcm)
        w.writeframes(frames)



def create_files(bin, out_path, amplify_value, lowPass):
    print("TRYING")
    ann = []
    with open(bin, 'rb') as f:
        f.seek(0x800)
        firstTime = True
        i = -1
        while f.tell() < 0xA00:
            print("LES THAN A00")
            byte = f.read(1)
            if(byte == b'\x07'):
                print("FOUND")
                i += 1
                byteRead = f.read(3)
                if(firstTime):
                    start = int.from_bytes(byteRead, byteorder='big')
                    firstTime = False
                elif(not firstTime):
                    end = int.from_bytes(byteRead, byteorder='big')
                    pos = f.tell()
                    f.seek(start)
                    data = f.read(end - start)
                    with open(out_path + "ANN_" + str(i) + ".bin", "wb") as output:
                        output.write(data)
                    ann.append(out_path + "ANN_" + str(i) + ".bin")
                    f.seek(pos)
                    print("EXPORT")
                    start = end
        i += 1
        pos = f.tell()
        f.seek(start)
        data = f.read(int.from_bytes(b'\x80000', byteorder='big') - start)
        with open(out_path + "ANN_" + str(i) + ".bin", "wb") as output:
            output.write(data)
        ann.append(out_path + "ANN_" + str(i) + ".bin")
        f.seek(pos)
        print("EXPORT")
        start = end
        for file in ann:
            main(file, None, amplify_value, lowPass)



def main(in_path, out_path, amplify_val, lowPassVal):
    debugLog = ""
    with open(in_path, 'rb') as f:
        data = f.read()

    if len(data) > HEADER_SIZE:
        data = data[HEADER_SIZE:]

    if TRIM_PADDING:
        data = trim_padding(data)

    if out_path is None:
        if in_path.lower().endswith('.bin'):
            out_path = in_path[:-4] + '.wav'
        else:
            out_path = in_path + '.wav'

    if STEP_MODE.upper() == 'MSM6650':
        step_table = MSM6650_STEP_TABLE
        index_max = MSM6650_INDEX_MAX

    predictor = 0
    index = 0

    pcm, predictor, index = decode_adpcm_stream(
        data,
        predictor=predictor,
        index=index,
        step_table=step_table,
        index_max=index_max,
        nibble_order=NIBBLE_ORDER
    )


    write_wav(out_path, pcm, SAMPLE_RATE)
    
  
    if amplify_val != 0:
        audio_amp = AudioSegment.from_wav(out_path)
        audio_amp = audio_amp + amplify_val
        audio_amp.export(out_path, format="wav")

    if lowPassVal != "0":
        lowPass = AudioSegment.from_wav(out_path)
        lowPass = lowPass.low_pass_filter(int(lowPassVal))
        lowPass.export(out_path, format="wav")

    debugLog += f"Decoded {len(pcm)} samples -> {os.path.split(out_path)[1]}"
    return debugLog
    
def ui(selectedItem, selectedFileNames, highlight, amplify, Log, lowPass):
    print("\033[97;44m MSM6650 Audio Decoder  \033[0m" + "\033[97;44m \033[0m" * 96)
    print("\033[97;44m \033[0m" * 120)
    print("\033[97;44m    Input Files\033[0m" + "\033[97;44m \033[0m" * 105)
    print("\033[97;44m    Selected : \033[0m" + "\033[97;44m" + selectedFileNames + "\033[0m" + "\033[97;44m \033[0m" * (105 - len(selectedFileNames)))
    if(selectedItem == 0):
        print("\033[97;44m    - \033[0m" + "\033[30;107m" + menuItems[0] + "\033[0m" + "\033[97;44m" + menuDesc[menuItems.index(menuItems[0])] + "\033[0m" + "\033[97;44m \033[0m" * ((114 - len(menuItems[0])) - len(menuDesc[menuItems.index(menuItems[0])])))
    else:
        print("\033[97;44m    - \033[0m" + "\033[97;44m" + menuItems[0] + "\033[0m" + "\033[97;44m" + menuDesc[menuItems.index(menuItems[0])] + "\033[0m" + "\033[97;44m \033[0m" * ((114 - len(menuItems[0])) - len(menuDesc[menuItems.index(menuItems[0])])))
    print("\033[97;44m \033[0m" * 120)
    print("\033[97;44m    Post Processing\033[0m" + "\033[97;44m \033[0m" * 101)
    if(selectedItem == 1):
        if(not highlight):
            print("\033[97;44m    - \033[0m" + "\033[30;107m" + menuItems[1] + "\033[0m" + "\033[97;44m" + " - " + "\033[0m" + "\033[97;44m" + (amplify + (" " * (3 - len(amplify)))) + "\033[0m" + "\033[97;44m \033[0m" * ((108 - len(menuItems[1])) - len(menuDesc[menuItems.index(menuItems[1])])))
        else:
            print("\033[97;44m    - \033[0m" + "\033[30;107m" + menuItems[1] + "\033[0m" + "\033[97;44m" + " - " + "\033[0m" + "\033[30;107m" + (amplify + (" " * (3 - len(amplify)))) + "\033[0m" + "\033[97;44m \033[0m" * ((108 - len(menuItems[1])) - len(menuDesc[menuItems.index(menuItems[1])])))
    else:
        print("\033[97;44m    - \033[0m" + "\033[97;44m" + menuItems[1] + "\033[0m" + "\033[97;44m" + " - " + "\033[0m" + "\033[97;44m" + (amplify + (" " * (3 - len(amplify)))) + "\033[0m" + "\033[97;44m \033[0m" * ((108 - len(menuItems[1])) - len(menuDesc[menuItems.index(menuItems[1])])))
    if(selectedItem == 2):
        if(not highlight):
            print("\033[97;44m    - \033[0m" + "\033[30;107m" + menuItems[2] + "\033[0m" + "\033[97;44m" + " - " + "\033[0m" + "\033[97;44m" + (lowPass + (" " * (4 - len(lowPass)))) + "\033[0m" + "\033[97;44m \033[0m" * ((108 - len(menuItems[2])) - len(menuDesc[menuItems.index(menuItems[2])])))
        else:
            print("\033[97;44m    - \033[0m" + "\033[30;107m" + menuItems[2] + "\033[0m" + "\033[97;44m" + " - " + "\033[0m" + "\033[30;107m" + (lowPass + (" " * (4 - len(lowPass)))) + "\033[0m" + "\033[97;44m \033[0m" * ((108 - len(menuItems[2])) - len(menuDesc[menuItems.index(menuItems[2])])))
    else:
        print("\033[97;44m    - \033[0m" + "\033[97;44m" + menuItems[2] + "\033[0m" + "\033[97;44m" + " - " + "\033[0m" + "\033[97;44m" + (lowPass + (" " * (4 - len(lowPass)))) + "\033[0m" + "\033[97;44m \033[0m" * ((108 - len(menuItems[2])) - len(menuDesc[menuItems.index(menuItems[2])])))
    print("\033[97;44m \033[0m" * 120)
    if(selectedItem == 3):
        print("\033[97;44m    - \033[0m" + "\033[30;107m" + menuItems[3] + "\033[0m" + "\033[97;44m" + menuDesc[menuItems.index(menuItems[3])] + "\033[0m" + "\033[97;44m \033[0m" * ((114 - len(menuItems[3])) - len(menuDesc[menuItems.index(menuItems[3])])))
    else:
        print("\033[97;44m    - \033[0m" + "\033[97;44m" + menuItems[3] + "\033[0m" + "\033[97;44m" + menuDesc[menuItems.index(menuItems[3])] + "\033[0m" + "\033[97;44m \033[0m" * ((114 - len(menuItems[3])) - len(menuDesc[menuItems.index(menuItems[3])])))
    if(selectedItem == 4):
        print("\033[97;44m    - \033[0m" + "\033[30;107m" + menuItems[4] + "\033[0m" + "\033[97;44m" + menuDesc[menuItems.index(menuItems[4])] + "\033[0m" + "\033[97;44m \033[0m" * ((114 - len(menuItems[4])) - len(menuDesc[menuItems.index(menuItems[4])])))
    else:
        print("\033[97;44m    - \033[0m" + "\033[97;44m" + menuItems[4] + "\033[0m" + "\033[97;44m" + menuDesc[menuItems.index(menuItems[4])] + "\033[0m" + "\033[97;44m \033[0m" * ((114 - len(menuItems[4])) - len(menuDesc[menuItems.index(menuItems[4])])))
    for i in range(14):
        print("\033[97;44m \033[0m" * 120)
    print("\033[97;44m \033[0m" * 100 + "\033[97;44mENTER - SELECT      \033[0m")
    print("\033[97;44m \033[0m" * 100 + "\033[97;44mBACKSPACE - EXIT    \033[0m")
    print("\033[97;44m" + Log + "\033[0m" + "\033[97;44m \033[0m" * (120 - len(Log)))
    
        

def inputHandler(selectedItem, selectedFileNames, highlight, amplify, selectedFiles, lowPass):
    reDraw = False
    if msvcrt.kbhit():
        key = msvcrt.getch()
        if key in (b'\xe0', b'\x00'): 
            key2 = msvcrt.getch()
            if key2 == b'H':
                highlight = False
                selectedItem -= 1
                if(selectedItem < 0):
                    selectedItem = 0
                updateScreen(selectedItem, selectedFileNames, highlight, amplify, "", lowPass)
            elif key2 == b'P':
                highlight = False
                selectedItem += 1
                if(selectedItem > len(menuItems) - 1):
                    selectedItem = len(menuItems) - 1
                updateScreen(selectedItem, selectedFileNames, highlight, amplify, "", lowPass)
        elif key == b'\x08':
            sys.exit(0)
        elif key == b'\r':
            if(selectedItem == 0):
                fn = askopenfilenames()
                selectedFiles = fn
                selectedFileNames = ""
                for file in range(len(fn)):
                    selectedFileNames += os.path.split(fn[file])[1]
                    if(file < len(fn) - 1):
                        selectedFileNames += ", "
                reDraw = True
            elif(selectedItem == 1):
                if(highlight == False):
                    amplify = ""
                    highlight = True
                elif(highlight == True):
                    highlight = False
                updateScreen(selectedItem, selectedFileNames, highlight, amplify, "", lowPass)
            elif(selectedItem == 2):
                if(highlight == False):
                    lowPass = ""
                    highlight = True
                elif(highlight == True):
                    highlight = False
                updateScreen(selectedItem, selectedFileNames, highlight, amplify, "", lowPass)
            elif(selectedItem == 3):
                if(amplify == ""):
                    amplify = "0"
                if(lowPass == ""):
                    lowPass = "0"
                amplify_value = int(amplify)
                for file in selectedFiles:
                    in_path = file
                    out_path = None
                    main(in_path, out_path, amplify_value, lowPass)
                updateScreen(selectedItem, selectedFileNames, highlight, amplify, "DONE!", lowPass)
            elif(selectedItem == 4):
                if(amplify == ""):
                    amplify = "0"
                if(lowPass == ""):
                    lowPass = "0"
                amplify_value = int(amplify)
                os.makedirs(os.path.split(selectedFiles[0])[0] + "/ANN/", exist_ok=True)
                with open(os.path.split(selectedFiles[0])[0] + "/ANN/combined.bin", 'wb') as outfile:
                        for file_name in selectedFiles:
                            with open(file_name, 'rb') as infile:
                                outfile.write(infile.read())
                in_path = os.path.split(selectedFiles[0])[0] + "/ANN/combined.bin"
                out_path = None
                create_files(in_path, os.path.split(selectedFiles[0])[0] + "/ANN/", amplify_value, lowPass)
                
                updateScreen(selectedItem, selectedFileNames, highlight, amplify, "DONE!", lowPass)
                

        elif key == b'0' or key == b'1' or key == b'2' or key == b'3' or key == b'4' or key == b'5' or key == b'6' or key == b'7' or key == b'8' or key == b'9':
            if(highlight and selectedItem == 1):
                amplify += key.decode('utf-8')
                updateScreen(selectedItem, selectedFileNames, highlight, amplify, "", lowPass)
            if(highlight and selectedItem == 2):
                lowPass += key.decode('utf-8')
                updateScreen(selectedItem, selectedFileNames, highlight, amplify, "", lowPass)
    return selectedItem, selectedFileNames, reDraw, selectedFiles, highlight, amplify, lowPass

def updateScreen(selectedItem, selectedFileNames, highlight, amplify, Log, lowPass):
    ui(selectedItem, selectedFileNames, highlight, amplify, Log, lowPass)



ui(selectedItem, selectedFileNames, highlight, amplify, "", lowPass)

while(True):
    selectedItem, selectedFileNames, reDraw, selectedFiles, highlight, amplify, lowPass = inputHandler(selectedItem, selectedFileNames, highlight, amplify, selectedFiles, lowPass)
    if(reDraw):
        updateScreen(selectedItem, selectedFileNames, highlight, amplify, "", lowPass)
        reDraw = False