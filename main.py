from __future__ import annotations

from parseData.parseData import parseDataTree
from parseXml.parseMetadata import parseMetadata
from parseXml.parseToFo import parseToFo
import json
import sys

if __name__ == "__main__":
     if len(sys.argv) < 2:
          filename = "Haus 2.BMT"
     else:
          filename = sys.argv[1]
     with open(filename, "rb") as f:
         # parsing is done in sequence, do not read additional bytes inbetween
         toFo = parseToFo(f)
         xmlSize = next(int(child.attributes["size"]) for child in toFo.children if child.name == "xml")
         endianness = next(child.attributes["endianness"] for child in toFo.children if child.name == "data")
         metadata = parseMetadata(f, xmlSize)
         
         # Skip separator byte(s) after metadata
         # Some files have \n, others have \n\x00
         sep1 = f.read(1)
         if sep1 == b'\n':
             # Check if there's a null byte after the newline
             sep2 = f.read(1)
             if sep2 != b'\x00':
                 # No null byte, seek back
                 f.seek(-1, 1)
         
         data = parseDataTree(f, endianness, metadata)
         
         # print(json.dumps(data, indent=1))
         print(data)
