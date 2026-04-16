from io import BufferedReader
from xml.sax import parseString

from parseXml.findStr import findStrInBytes
from parseXml.handlers.xmlNodes import XmlNodeHandler

 
def readToFo(file: BufferedReader) -> str:
    toFoStart: int = 0
    tofoLen: int = 0
    for line in file:
        found = findStrInBytes(line, "<ToFo")
        toFoStart += found or len(line)
        if found: break
    file.seek(toFoStart)
    for line in file:
        found = findStrInBytes(line, "ToFo>")
        tofoLen += found or len(line)
        if found: break
    file.seek(toFoStart)
    header = file.read(tofoLen + len("ToFo>".encode()))
    return header.decode()

def parseToFo(file: BufferedReader):
    toFoString = readToFo(file)
    handler = XmlNodeHandler()
    parseString(toFoString, handler)
    return handler.currentElement
