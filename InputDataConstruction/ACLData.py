import os
import re
import tarfile
import textwrap

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Dict, List, Optional, Tuple, Iterable, Iterator

import pandas as pd
import xml.etree.ElementTree as ET


# Helpers to handle the ACL dataset
#  ----------------------------------------------------------------------------------------------------------------------------------------
# Download at https://github.com/shauryr/ACL-anthology-corpus?tab=readme-ov-file
#
# Dataset contains
# - > All bib files in ACL anthology with abstracts : size 172Mb
# - > Raw grobid extraction results on all the ACL anthology pdfs which includes full text and references : size 3.6Gb
# - > Dataframe with extracted metadata (table below with details) and full text of the collection for analysis : size 489M
# ----------------------------------------------------------------------------------------------------------------------------------------
#    @Misc{acl_anthology_corpus,
#        author =       {Shaurya Rohatgi},
#        title =        {ACL Anthology Corpus with Full Text},
#        howpublished = {Github},
#        year =         {2022},
#        url =          {https://github.com/shauryr/ACL-anthology-corpus}
#    }
# ----------------------------------------------------------------------------------------------------------------------------------------

DATA_DIR = Path("C:/Users/User/Desktop/Julian/Uni/WS 25/AIR/herBERT/Datasets/Training Data/ACL")
CORPUS_PATH = DATA_DIR / "acl_corpus_grobid_full_text.80k.v9_22.tar.gz"
BIB_PATH = DATA_DIR /"acl_corpus_bibs.80k.v9_22.tar.gz"
META_DATA_PARQUET = DATA_DIR / "acl-publication-info.74k.parquet"
NS = {"tei": "http://www.tei-c.org/ns/1.0"}

ACL_ID_PATTERNS = [
    re.compile(r"\b[A-Z]\d{2}-\d{4}\b"),              # e.g. P07-2007, W05-0819
    re.compile(r"\b\d{4}\.[a-z0-9\-]+\.\d+\b"),       # e.g. 2020.emnlp-main.50
]


def open_tei_tar(path : Path = CORPUS_PATH) -> tarfile.TarFile:
    try:
        tei_tar = tarfile.open(path, "r")
        return tei_tar
    except Exception as e:
        raise RuntimeError(f"Could not open corpus tar file at {path}: {e}")

def load_file(aclID: str) -> str:
    file_name = f"grobid_full_text/{aclID}.tei.xml"
    try:
        tarfile = open_tei_tar()
        file = tarfile.getmember(file_name)
        file_content = tarfile.extractfile(file).read()
        return file_content

    except KeyError:
        raise FileNotFoundError(f"File {file_name} not found in {CORPUS_PATH}")
    except Exception as e:
        raise RuntimeError(f"An error occurred while processing {file_name}: {e}")


def save_file(aclID: str)-> Path:
    file_content = load_file(aclID)
    output_path = Path(f"LoadedPapers") / (f"{aclID}.txt")
    with open(output_path, "wb") as f_out:
        f_out.write(file_content)
    return output_path
    
# TODO either write better on own or research proper citation of AI
# Generated with ChatGPT    
def parse_tei_metadata(xml_bytes):
    
    root = ET.fromstring(xml_bytes)

    title_el = root.find(".//tei:titleStmt/tei:title", NS)
    year_el  = root.find(".//tei:sourceDesc//tei:date", NS)
    # count references
    ref_list = root.findall(".//tei:listBibl/tei:biblStruct", NS)

    title = (title_el.text or "").strip() if title_el is not None else None
    year  = None
    if year_el is not None:
        year = year_el.get("when") or (year_el.text or "").strip()

    return {
        "title": title,
        "year": year,
        "n_references": len(ref_list),
    }
# END Generated with ChatGPT

def get_file_info(aclID: str):
    file_name = f"grobid_full_text/{aclID}.tei.xml"
    tarfile = open_tei_tar()
    entry = tarfile.getmember(file_name)
    with tarfile.extractfile(entry) as f:
        xml_bytes = f.read()

    info = parse_tei_metadata(xml_bytes)
    info["acl_id"] = aclID
    info["tei_file"] = entry.name
    info["size_bytes"] = entry.size
    return info

def display_fileinfo_as_df(aclIDs):
    rows = []
    for aclID in aclIDs:
        try:
            info = get_file_info(aclID)
            rows.append(info)
        except Exception:
            continue
    print(pd.DataFrame.from_records(rows))

def tei_id_from_name(name: str) -> str:
    p = PurePosixPath(name)
    stem = p.name
    if stem.endswith(".tei.xml"):
        stem = stem[:-len(".tei.xml")]
    return stem

def bib_id_from_name(name: str) -> str:
    p = PurePosixPath(name)
    stem = p.name
    if stem.endswith(".bib"):
        stem = stem[:-len(".bib")]
    return stem
    
# TODO either write better on own or research proper citation of AI
# Generated with ChatGPT
def extract_refs_from_tei(xml_bytes: bytes):
    ns = {"tei": "http://www.tei-c.org/ns/1.0"}

    root = ET.fromstring(xml_bytes)

    bibl_structs = root.findall(".//tei:listBibl/tei:biblStruct", ns)
    refs = []

    for i, b in enumerate(bibl_structs):
        # try to get as much as possible: title, year, authors, DOI, URL
        title_el = b.find(".//tei:title", ns)
        date_el  = b.find(".//tei:date", ns)
        idno_doi = b.find(".//tei:idno[@type='DOI']", ns)
        idno_url = b.find(".//tei:idno[@type='url']", ns)

        authors = []
        for pers in b.findall(".//tei:author/tei:persName", ns):
            parts = []
            for child in pers:
                if child.text:
                    parts.append(child.text.strip())
            if parts:
                authors.append(" ".join(parts))

        title = (title_el.text or "").strip() if title_el is not None and title_el.text else None
        year = None
        if date_el is not None:
            year = date_el.get("when") or (date_el.text or "").strip()

        doi = idno_doi.text.strip() if idno_doi is not None and idno_doi.text else None
        url = idno_url.text.strip() if idno_url is not None and idno_url.text else None

        # fallback: raw text of the whole biblStruct
        raw_text = " ".join(b.itertext()).strip()

        refs.append({
            "ref_index": i,
            "title": title,
            "year": year,
            "authors": authors,
            "doi": doi,
            "url": url,
            "raw": raw_text,
        })

    return refs

def find_acl_id_in_text(text: str):
    if not text:
        return None
    # If it's a URL with aclanthology.org, grab the path part
    if "aclanthology.org" in text:
        # e.g. https://aclanthology.org/P07-2007.bib
        m = re.search(r"aclanthology\.org/([^.\s/]+)", text)
        if m:
            return m.group(1)
    # Otherwise try patterns
    for pat in ACL_ID_PATTERNS:
        m = pat.search(text)
        if m:
            return m.group(0)
    return None

def extract_refs_from_tei_with_acl(xml_bytes: bytes):
    ns = NS
    root = ET.fromstring(xml_bytes)
    bibl_structs = root.findall(".//tei:listBibl/tei:biblStruct", ns)
    refs = []

    for i, b in enumerate(bibl_structs):
        title_el = b.find(".//tei:title", ns)
        date_el  = b.find(".//tei:date", ns)
        idnos    = b.findall(".//tei:idno", ns)

        # authors
        authors = []
        for pers in b.findall(".//tei:author/tei:persName", ns):
            parts = []
            for child in pers:
                if child.text:
                    parts.append(child.text.strip())
            if parts:
                authors.append(" ".join(parts))

        title = (title_el.text or "").strip() if title_el is not None and title_el.text else None
        year = None
        if date_el is not None:
            year = date_el.get("when") or (date_el.text or "").strip()

        doi = url = None
        acl_id = None

        for idno in idnos:
            val = (idno.text or "").strip()
            if not val:
                continue
            # try to classify
            if idno.get("type", "").lower() == "doi":
                doi = val
            elif idno.get("type", "").lower() in {"url", ""}:
                url = url or val
            # Try to find ACL ID in any idno
            if acl_id is None:
                acl_id = find_acl_id_in_text(val)

        # fallback: search in raw text if still no acl_id
        raw_text = " ".join(b.itertext()).strip()
        if acl_id is None:
            acl_id = find_acl_id_in_text(raw_text)

        refs.append({
            "ref_index": i,
            "title": title,
            "year": year,
            "authors": authors,
            "doi": doi,
            "url": url,
            "acl_id": acl_id,
            "raw": raw_text,
        })

    return refs

# END Generated with ChatGPT

def build_citation_edges(ids=None, path_to_corpus: Path = CORPUS_PATH):
    tei_tar = open_tei_tar(path_to_corpus)
    members = tei_tar.getmembers()
    tei_members = [
        m for m in members
        if m.isfile() and m.name.endswith(".tei.xml")]
    
    tei_members_nontrivial = [m for m in tei_members if m.size > 1024]
    tei_by_id = {tei_id_from_name(m.name): m for m in tei_members_nontrivial}
    if ids is None:
        ids = tei_by_id.keys()

    edges = []
    for pid in ids:
        tei_member = tei_by_id[pid]
        with tei_tar.extractfile(tei_member) as f:
            xml_bytes = f.read()
        try:
            refs = extract_refs_from_tei_with_acl(xml_bytes)
        except ET.ParseError:
            continue
        for r in refs:
            cid = r.get("acl_id")
            if cid and cid in tei_by_id:
                edges.append((pid, cid))
    return edges

def build_outgoing(edges):
    outgoing = {}
    for u, v in edges:
        outgoing.setdefault(u, []).append(v)
        outgoing.setdefault(v, []) 
    return outgoing

def build_incoming(edges):
    incoming = {}
    for u, v in edges:
        incoming.setdefault(v, []).append(u)
        incoming.setdefault(u, []) 
    return incoming

def get_candidate_nodes(edges):
    outgoing = build_outgoing(edges)
    candidates = [pid for pid, vs in outgoing.items() if len(vs) > 0]
    return candidates

def save_list(lines, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for item in lines:
            f.write(str(item) + "\n")
    print(f"Saved {len(lines)} items to {path}")

def load_candidate_nodes(path):
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]
    
def load_edges_csv(path):
    edges = pd.read_csv(path).values.tolist()
    return edges

def save_edges_csv(edges, path):
    df = pd.DataFrame(edges, columns=["citing", "cited"])
    df.to_csv(path, index=False)
    print(f"Saved {len(edges)} edges to {path}")
