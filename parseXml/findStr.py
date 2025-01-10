def findStrInBytes(bytes: bytes, searchStr: str) -> bool | int:
    pos = bytes.find(searchStr.encode())
    return pos if pos > -1 else False
