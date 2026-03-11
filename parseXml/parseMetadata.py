
from io import BufferedReader

from xml.sax import parseString
from parseXml.handlers.metadata import xmlMetadataHandler


def parseMetadata(file: BufferedReader, size: int):
    metadataBytes = file.read(size)
    metadataString = metadataBytes.decode().lstrip('\n').lstrip('\x00')
    handler = xmlMetadataHandler()
    parseString(metadataString, handler)
    return handler.currentElement
