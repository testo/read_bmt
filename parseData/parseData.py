from io import BufferedReader
from struct import unpack
from parseXml.handlers.metadata import xmlMetadataGroup, xmlMetadataItem
import os
import numpy as np

def parseDataTree(file: BufferedReader, endianness: str, item: xmlMetadataItem | xmlMetadataGroup):
    match item:
        case xmlMetadataItem():
            return {item.name: parseDataPoint(file, endianness, item)}
        case xmlMetadataGroup():
            return {item.name: [parseDataTree(file, endianness, child) for child in item.children]}

def parseDataPoint(file: BufferedReader, endianness: str, item: xmlMetadataItem):
    # print (item.name)
    match item.type.lower():
        case "vecuint8":
            if "Vis" in item.name:
                return readImage(file, item.size, endianness, item.name)
            if "Colors" == item.name:
                return readColors(file, item.size, endianness)
            else:
                skipParse(file, item)
                return ""
        case "cvmat":
            return readMat(file, item.size, endianness)
        case "string":
            return readStr(file, item.size)
        case "version":
            if item.size != 12: raise NotImplementedError
            return f"{readInt(file, 4, endianness)}.{readInt(file, 4, endianness)}.{readInt(file, 4, endianness)}"
        case "uuid":
            return readStr(file, item.size)
        case "cvpoint":
            return readPoint(file, endianness)
        case "cvrect":
            return (readPoint(file, endianness), readPoint(file, endianness))
        case typeName if "float" in typeName:
            if "Temperature" in item.type:
                #convert Kelvin to degrees Celsius
                return readFloat(file, item.size, endianness) - 273.15
            else:
                return readFloat(file, item.size, endianness)
        case _:
            return readInt(file, item.size, endianness)

def skipParse(file: BufferedReader, item: xmlMetadataGroup | xmlMetadataItem):
    file.seek(file.tell() + getSize(item))

def getSize(item: xmlMetadataGroup | xmlMetadataItem):
    match item:
        case xmlMetadataItem():
            return item.size
        case xmlMetadataGroup():
            return sum((getSize(child) for child in item.children))

def readMat(file: BufferedReader, size: int, endianness: str):
    dims = readInt(file, 4, endianness) #2 
    rows = readInt(file, 4, endianness) #240
    cols = readInt(file, 4, endianness) #320
    depth = readInt(file, 4, endianness) #2 CV_16U - 16-bit unsigned integers ( 0..65535 )
    channels = readInt(file, 4, endianness) #1
    element_size = readInt(file, 4, endianness) #2

    if dims != depth or depth != element_size or dims != element_size:
        raise NotImplementedError("Mat in wrong format")
    
    size_remaining = size - (6 * 4)
    data = file.read(size_remaining)
    np_array = np.frombuffer(data, dtype=np.int16)       
    mat_shape = (rows, cols, channels) 
    matInt16 = np_array.reshape(mat_shape) 
    matFloat32 = np.zeros((rows, cols, channels), dtype=np.float32)

    MAX = float(1001.0)
    MIN = float(-101.0)
    u16_TEMP_MAX = 0xFFFF

    with open('temps.csv', 'w') as csv:
        for y in range(rows):
            line = ""
            for x in range(cols):    
                matFloat32[y,x] = (matInt16[y,x] * ( (MAX-MIN) / u16_TEMP_MAX)) + MIN
                line +=  f"{matFloat32[y,x][0]};".replace('.',',')
            csv.write(line + "\n")                
    return matFloat32

def readColors(file: BufferedReader, size: int, endianness: str):
    sizeRemaining = readInt(file, 4, endianness)
    if sizeRemaining % 3 != 0:
        raise NotImplementedError("colors have to be multiple of 3")
    
    colors = []
    while(sizeRemaining > 0):
        colors.append({
            "r": readInt(file, 1, endianness),
            "g": readInt(file, 1, endianness),
            "b": readInt(file, 1, endianness) })
        sizeRemaining -=3
    return colors

def readImage(file: BufferedReader, size: int, endianness: str, name: str):
    sizeRead = readInt(file, 4, endianness)
    data = file.read(sizeRead)
    filename = name + ".jpg"
    with open(filename, "wb") as binary_file:
        binary_file.write(data)
    return os.path.join(os.getcwd(), filename)

def readInt(file: BufferedReader, size: int, endianness: str):
    return int.from_bytes(file.read(size), endianness)

def readFloat(file: BufferedReader, size: int, endianness: str):
    mode = ">" if endianness == "big" else "<"
    if size % 4 != 0: raise NotImplementedError
    readBytes = file.read(size)

    if size == 4: return unpack(f"{mode}{size // 4}f", readBytes)[0]
    return unpack(f"{mode}{size // 4}f", readBytes)

def readStr(file: BufferedReader, size: int):
    return file.read(size).decode().split("\x00")[-1]

def readPoint(file: BufferedReader, endianness):
    return (readInt(file, 4, endianness), readInt(file, 4, endianness))
