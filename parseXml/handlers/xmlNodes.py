from __future__ import annotations
from dataclasses import dataclass
from xml.sax import ContentHandler

@dataclass
class xmlNode():
    name: str
    attributes: dict[str, any]
    children: list[xmlNode]
    value: any


class XmlNodeHandler(ContentHandler):
    def __init__(self):
        super().__init__()
        self.elementStack: list[xmlNode] = []

    @property
    def currentElement(self):
        return self.elementStack[-1]

    def startElement(self, name: str, attrs):
        self.elementStack.append(xmlNode(name, dict(attrs), [], ""))

    def endElement(self, _):
        if (len(self.elementStack) > 1):
            child = self.elementStack.pop()
            self.currentElement.children.append(child)

    def characters(self, content):
        self.currentElement.value += content.strip()