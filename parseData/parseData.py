from io import BufferedReader
from struct import unpack
from parseXml.handlers.metadata import xmlMetadataGroup, xmlMetadataItem
import os
import numpy as np

MARKED_FLOAT_MARKERS = {
    0x00: None,           # Valid – no annotation needed
    0x01: "OtherMark",
    0x03: "Underrange",
    0x05: "Overrange",
    0x07: "Invalid",
}

def markedFloatAnnotation(raw_uint32: int) -> str | None:
    """Return a marker annotation string if the low 3 bits indicate a non-valid
    MarkedFloat, or None if the value is valid (bits [2:0] == 0x00).

    Also returns a special annotation when the low bits happen to be a known
    marker code but the source is likely a plain float written without marker
    awareness (i.e. the camera firmware wrote raw Kelvin bytes).  In that case
    the annotation is prefixed with '?' to indicate ambiguity."""
    bits = raw_uint32 & 0x07
    label = MARKED_FLOAT_MARKERS.get(bits)
    if label is None:
        return None          # properly valid MarkedFloat
    # bits [2:0] are non-zero – could be intentional marker OR accidental
    # collision from a plain-float writer (firmware).  Flag with '?'.
    return f"?{label}"

def parseDataTree(file: BufferedReader, endianness: str, item: xmlMetadataItem | xmlMetadataGroup):
    match item:
        case xmlMetadataItem():
            return {item.name: parseDataPoint(file, endianness, item)}
        case xmlMetadataGroup():
            return {item.name: [parseDataTree(file, endianness, child) for child in item.children]}

def parseDataPoint(file: BufferedReader, endianness: str, item: xmlMetadataItem):
    # print (item.name)
    print(item)
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
                return readMat(file, item.size, endianness, item.name == "Ir")
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
            value, raw_uint32 = readFloatRaw(file, item.size, endianness)
            is_marked = item.size == 4 and "MarkedFloat" in item.type
            if "Temperature" in item.type:
                value -= 273.15
            if is_marked:
                annotation = markedFloatAnnotation(raw_uint32)
                if annotation is not None:
                    print(f"  WARNING: {item.name} has non-valid MarkedFloat marker: {annotation} (raw=0x{raw_uint32:08X})")
                    return f"{value} [{annotation}]"
            return value
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

def readMat(file: BufferedReader, size: int, endianness: str, is_ir : bool):
    dims = readInt(file, 4, endianness) #2 
    rows = readInt(file, 4, endianness) #240
    cols = readInt(file, 4, endianness) #320
    depth = readInt(file, 4, endianness) #2 CV_16U - 16-bit unsigned integers ( 0..65535 )
    channels = readInt(file, 4, endianness) #1
    element_size = readInt(file, 4, endianness) #2
    print(f"dims:{dims}\nrows:{rows}\ncols:{cols}\ndepth:{depth}\nchannels:{channels}\nelement_size:{element_size}")

    
    if dims != depth or depth != element_size or dims != element_size:
        #raise NotImplementedError(f"Mat in wrong format: {dims} != {depth} or {depth} != {element_size} or {dims} != {element_size}")
        print("Mat in wrong format")
    
    size_remaining = size - (6 * 4)
    data = file.read(size_remaining)
    if not is_ir:
        return "ignoring mat"
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

def readFloatRaw(file: BufferedReader, size: int, endianness: str) -> tuple:
    """Read float(s) and return (value_or_tuple, raw_uint32_of_first_float).
    raw_uint32 is the little-endian uint32 of the first 4 bytes, used for
    MarkedFloat marker-bit inspection."""
    mode = ">" if endianness == "big" else "<"
    if size % 4 != 0: raise NotImplementedError
    readBytes = file.read(size)
    raw_uint32 = int.from_bytes(readBytes[:4], "little")
    if size == 4:
        return unpack(f"{mode}f", readBytes)[0], raw_uint32
    return unpack(f"{mode}{size // 4}f", readBytes), raw_uint32

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
