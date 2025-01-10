
from io import BufferedReader

from xml.sax import parseString
from parseXml.handlers.metadata import xmlMetadataHandler


def parseMetadata(file: BufferedReader, size: int):
    metadataString = file.read(size).decode()
    handler = xmlMetadataHandler()
    parseString(metadataString, handler)
    return handler.currentElement
