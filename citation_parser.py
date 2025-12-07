import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# body.annotations.bib_ref[k].attributes.ref_id
# bibliography.annotations.bib_entry[m].attributes.id

PATH_2_DATASET = Path(r"Datasets\Training Data\s2orc\shard1\shard1.jsonl")

def iterate_papers(jsonl_path: Path, max_items: Optional[int] = 10):
    with jsonl_path.open('r', encoding='utf-8') as f:
        ctr = 0
        for line in f:
            if ctr >= max_items:
                break
            line = line.strip()
            if not line:
                continue
            ctr += 1
            yield json.loads(line)

def load_annotations_as_lists(annotations: Optional[Dict[str, Any]], attribute: str) -> List[Dict[str, Any]]:
    if not annotations:
        return []
    
    attribute = annotations.get(attribute)
    if not attribute:
        return []
    
    if isinstance(attribute, list):
        return attribute
    
    if isinstance(attribute, str):
        try:
            parsed = json.loads(attribute)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            return []
    
    return []

def get_bibliography_index(paper: Dict[str, Any]) -> Dict[str, Dict[str, Any]]: #do we want a dict?
    bibliography = paper.get("bibliography")
    bib_content = bibliography.get("text")
    annotations = bibliography.get("annotations")

    bibliography_entries = load_annotations_as_lists(annotations, "bib_entry")
    titles = load_annotations_as_lists(annotations, "bib_title")
    #print("titels: ->", titles)

    contents: Dict[str, Dict[str, Any]] = {}

    for ann in bibliography_entries:
        attributes = ann.get("attributes", {})
        id = attributes.get("id")
        if id is None:
            continue

        start = int(ann.get("start", 0))
        end = int(ann.get("end", 0))
        reference = bib_content[start:end]
        contents[id] = {
            "id": id,
            "reference": reference,
            "start": start,
            "end": end,
            "title": None,
            #add authors??? 
        }

        for t in titles:
            s = int(t.get("start", 0))
            e = int(t.get("end", 0))
            title_text = bib_content[s:e]

            for content in contents.values():
                if content["start"] <= s and content["end"] >= e:
                    content["title"] = title_text
                    break

    return contents

def get_citations(paper: Dict[str, Any]) -> Dict[str, Any]:
    body = paper.get("body")
    body_content = body.get("text")
    annotations = body.get("annotations")
    annotations = load_annotations_as_lists(annotations, "bib_ref")

    bibliography_index = get_bibliography_index(paper)
    citations: List[Dict[str, Any]]= []

    for ann in annotations:
        try:
            attribute = ann.get("attributes")
            ref_id = attribute.get("ref_id")
            matched_paper_id = attribute.get("matched_paper_id")

            if ref_id is None:
                continue

            start = ann.get("start", 0)
            end = ann.get("end", 0)
            if start is None or end is None:
                continue
            
            start = int(start)
            end = int(end)

            citation_text = body_content[start:end]
            bibliography_entry = bibliography_index.get(ref_id) #should be ref_id

            citations.append({
                "ref_id": ref_id,
                "citation_text": citation_text,
                "start": start,
                "end": end,
                "matched_paper_id": matched_paper_id, #doe we need it? it is in json file, might be useful
                "bibliography_entry": bibliography_entry,
            })

        except Exception:
            #print("Error. Function: get_citations -> Paper ID:", paper.get("paper_id"))
            continue

    return {
                "paper_id": paper.get("corpusid"),#or the doi?
                "title": paper.get("title"),  

                "citations": citations
            }


N = 20 
path = Path(r"Datasets\Training Data\s2orc\shard1\shard1.jsonl")
output_path = Path(r"Datasets\Training Data\s2orc\shard1\citations_shard1.json")

with output_path.open("w", encoding="utf-8") as out:
    for paper in iterate_papers(path, N): 
        citations = get_citations(paper)
        out.write(json.dumps(citations, ensure_ascii=False, indent=2))
        out.write("\n\n") 