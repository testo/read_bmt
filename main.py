from __future__ import annotations

from parseData.parseData import parseDataTree
from parseXml.parseMetadata import parseMetadata
from parseXml.parseToFo import parseToFo
import json
import sys
import numpy as np

def json_default(obj):
    if isinstance(obj, np.ndarray):
        flat = obj.flatten()
        preview = ", ".join(f"{v:.4g}" for v in flat[:6])
        if len(flat) > 6:
            preview += f", ... ({len(flat)} total)"
        return f"<ndarray shape={obj.shape} dtype={obj.dtype} [{preview}]>"
    if isinstance(obj, tuple):
        return list(obj)
    return repr(obj)

def compact_dumps(obj, indent=2, _level=0):
    """JSON serialiser:
    - Dicts: one key per line, values indented.
    - Lists of single-key dicts (BMT group pattern): each entry on one line
      as {"key": value}, no extra bracket lines.
    - Everything else: standard compact JSON on one line.
    """
    pad = " " * (indent * _level)
    inner = " " * (indent * (_level + 1))

    if isinstance(obj, dict):
        if not obj:
            return "{}"
        items = [f"{inner}{json.dumps(k)}: {compact_dumps(v, indent, _level + 1)}"
                 for k, v in obj.items()]
        return "{\n" + ",\n".join(items) + "\n" + pad + "}"

    if isinstance(obj, list):
        if not obj:
            return "[]"
        # BMT group pattern: list of single-key dicts.
        # Render each {"key": value} on its own line; value is rendered
        # recursively so nested groups still expand.
        if all(isinstance(el, dict) and len(el) == 1 for el in obj):
            lines = []
            for el in obj:
                k, v = next(iter(el.items()))
                rendered_v = compact_dumps(v, indent, _level + 1)
                lines.append(f"{inner}{json.dumps(k)}: {rendered_v}")
            return "[\n" + ",\n".join(lines) + "\n" + pad + "]"
        # Anything else: one-line array.
        return json.dumps(obj, default=json_default)

    return json.dumps(obj, default=json_default)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <filename.BMT>")
        sys.exit(1)
    
    filename = sys.argv[1]
    with open(filename, "rb") as f:
        # parsing is done in sequence, do not read additional bytes inbetween
        toFo = parseToFo(f)
        xmlSize = next(int(child.attributes["size"]) for child in toFo.children if child.name == "xml")
        endianness = next(child.attributes["endianness"] for child in toFo.children if child.name == "data")
        metadata = parseMetadata(f, xmlSize)
        f.read(1)

        data = parseDataTree(f, endianness, metadata)

        print(compact_dumps(data))
