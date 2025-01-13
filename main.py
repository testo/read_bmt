from __future__ import annotations

from parseData.parseData import parseDataTree
from parseXml.parseMetadata import parseMetadata
from parseXml.parseToFo import parseToFo
import json
if __name__ == "__main__":
    with open("Haus 2.BMT", "rb") as f:
        # parsing is done in sequence, do not read additional bytes inbetween
        toFo = parseToFo(f)
        xmlSize = next(int(child.attributes["size"]) for child in toFo.children if child.name == "xml")
        endianness = next(child.attributes["endianness"] for child in toFo.children if child.name == "data")
        metadata = parseMetadata(f, xmlSize)
        f.read(1)

        data = parseDataTree(f, endianness, metadata)
        
        print(json.dumps(data, indent=1))

