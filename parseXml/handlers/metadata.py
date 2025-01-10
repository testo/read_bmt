from __future__ import annotations
from dataclasses import dataclass

from parseXml.handlers.xmlNodes import XmlNodeHandler

@dataclass
class xmlMetadataItem():
    name: str
    type: str
    size: int

@dataclass
class xmlMetadataGroup():
    name: str
    children: list[xmlMetadataGroup | xmlMetadataItem]

class xmlMetadataHandler(XmlNodeHandler):
    def __init__(self):
        super().__init__()
        self.elementStack: list[xmlMetadataGroup | xmlMetadataItem] = []

    @property
    def currentElement(self):
        return self.elementStack[-1]

    def startElement(self, _, attrs):
        attributes = dict(attrs)
        match list(attributes.keys()):
            case ["name"]:
                self.elementStack.append(xmlMetadataGroup(attributes["name"], []))
            case ["name", "type", "size"]: # assumes correct order
                self.elementStack.append(xmlMetadataItem(attributes["name"], attributes["type"], int(attributes["size"])))
            case _:
                raise TypeError
    def characters(self, _):
        return
