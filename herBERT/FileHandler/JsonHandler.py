import json
from pathlib import Path


class JsonHandler:
    def __init__(self):
        self._files: dict = {}

    def getFiles(self):
        return self._files

    def getIds(self):
        return self._files.keys()

    def getAll(self, paper_id: str):
        return self._map.get(paper_id)

    def getTitle(self, paper_id: str):
        return self.getHelper(paper_id, "title")

    def getFullText(self, paper_id: str):
        return self.getHelper(paper_id, "full_text")

    def getURL(self, paper_id: str):
        return self.getHelper(paper_id, "url")

    def getIncomingRefs(self, paper_id: str):
        return self.getHelper(paper_id, "incoming_acl_citations")

    def getOutgoingRefs(self, paper_id: str):
        return self.getHelper(paper_id, "outgoing_acl_citations")

    def getHelper(self, paper_id: str, field: str):
        item = self._files.get(paper_id)
        if item:
            return item.get(field)
        return None

    def loadRefTrain(self):
        path = self.getInputPath() / "ReferenceTraining.json"
        self.load(path)

    def getInputPath(self):
        return Path(__file__).resolve().parent.parent / "Data" / "Input"

    def load(self, path: str):
        file:list = None
        with open(path, "r", encoding="UTF8") as f:
            pos = f.tell()
            first = f.read(1)
            while first and first.isspace():
                first = f.read(1)
            f.seek(pos)

            file = json.load(f)
        self._files = {item["paper_id"]: item for item in file}