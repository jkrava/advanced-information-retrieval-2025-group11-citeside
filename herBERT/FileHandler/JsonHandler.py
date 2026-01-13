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

    def getOutgoingRefs(self, paper_id: str):
        return self.getHelper(paper_id, "references")

    def getAuthors(self, paper_id: str):
        return self.getHelper(paper_id, "authors")
        
    def getYear(self, paper_id: str):
        return self.getHelper(paper_id, "year")
    
    def getHypothesis(self, e_id: str):
        return self.getHelper(e_id, "hypothesis")
    
    def getPremise(self, e_id: str):
        return self.getHelper(e_id, "premise")

    def getHelper(self, paper_id: str, field: str):
        item = self._files.get(paper_id)
        if item:
            return item.get(field)
        return None

    def loadRefTrain(self):
        path = self.getInputPath() / "PompeiDataset.json"
        self.load(path)

    def loadCovid(self):
        path = self.getInputPath() / "CovidDataset.json"
        self.load(path)

    def loadEntailmentData(self, path: str = None):
        if path is None:
            path = self.getInputPath() / "EntailmentData.json"
        else:
            path = self.getInputPath() / path
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

            if first == "[":
                file = json.load(f)
            else:
                file =[]
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    file.append(json.loads(line))
        self._files = {item["paper_id"]: item for item in file}