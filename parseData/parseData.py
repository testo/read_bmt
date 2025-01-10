from io import BufferedReader
from struct import unpack
from parseXml.handlers.metadata import xmlMetadataGroup, xmlMetadataItem


def parseDataTree(file: BufferedReader, endianness: str, item: xmlMetadataItem | xmlMetadataGroup):
    match item:
        case xmlMetadataItem():
            return {item.name: parseDataPoint(file, endianness, item)}
        case xmlMetadataGroup():
            if item.name.lower() == "images":
                skipParse(file, item)
                return "[images]"
            return {item.name: [parseDataTree(file, endianness, child) for child in item.children]}

def parseDataPoint(file: BufferedReader, endianness: str, item: xmlMetadataItem):
    match item.type.lower():
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
